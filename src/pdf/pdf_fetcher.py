"""
PDF Fetcher Orchestrator für Academic Agent v2.3+

Koordiniert 2-Step Fallback-Chain (Python):
1. Unpaywall API    → ~40% Erfolg (1-2s, schnell)
2. CORE API         → +10% Erfolg (2s, Fallback)

Step 3 (DBIS Browser) ist jetzt Agent-basiert:
- Wird NICHT mehr hier aufgerufen
- linear_coordinator spawnt dbis_browser Agent (Sonnet + Chrome MCP)
- Für failed PDFs nach Unpaywall+CORE
- +35-40% Erfolg (15-25s, INSTITUTIONAL!)
- Gesamt: 85-90% 🎯

v2.1 Changes:
- output_dir is now REQUIRED (no default)
- PDFs saved to runs/{timestamp}/pdfs/
- No more ~/.cache/ pollution

Features:
- Batch-Processing (iterate über Papers)
- Progress-Tracking
- Skip-Logik (nach Fehlversuchen)
- Rate-Limiting zwischen Requests
"""

import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
import re

from src.pdf.unpaywall_client import UnpaywallClient
from src.pdf.core_client import COREClient


@dataclass
class PDFResult:
    """Result of PDF download attempt"""
    doi: str
    success: bool
    pdf_path: Optional[str] = None  # Local path if successful
    pdf_url: Optional[str] = None   # Original URL
    source: Optional[str] = None    # unpaywall/core/dbis_browser
    error: Optional[str] = None
    skipped: bool = False  # True if skipped after all strategies failed
    attempts: int = 0      # Number of strategies tried


class PDFFetcher:
    """
    Orchestrates PDF downloading with 3-step fallback chain
    """

    def __init__(
        self,
        output_dir: Path,
        unpaywall_email: Optional[str] = None,
        core_api_key: Optional[str] = None,
        fallback_chain: Optional[List[str]] = None,
        enable_dbis_browser: bool = False
    ):
        """
        Initialize PDF Fetcher

        Args:
            output_dir: Where to save PDFs (REQUIRED in v2.1)
                       Should be: runs/{timestamp}/pdfs/
            unpaywall_email: Optional email for Unpaywall API
            core_api_key: Optional API key for CORE API
            fallback_chain: Order of strategies (default: ["unpaywall", "core"])
            enable_dbis_browser: Enable DBIS Browser (deprecated, use Agent instead)

        Raises:
            ValueError: If output_dir is None

        Example:
            fetcher = PDFFetcher(output_dir=Path("runs/2026-02-27_14-30-00/pdfs"))
        """
        if output_dir is None:
            raise ValueError("output_dir is required in v2.1 (runs/{timestamp}/pdfs/)")

        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Fallback chain (order matters!)
        if fallback_chain:
            self.fallback_chain = fallback_chain
        elif enable_dbis_browser:
            self.fallback_chain = ["unpaywall", "core", "dbis_browser"]
        else:
            self.fallback_chain = ["unpaywall", "core"]

        # Initialize clients
        self.unpaywall_client = UnpaywallClient(email=unpaywall_email)
        self.core_client = COREClient(api_key=core_api_key)
        if enable_dbis_browser:
            from src.pdf.dbis_browser_downloader import DBISBrowserDownloader
            self.dbis_browser = DBISBrowserDownloader(output_dir=self.output_dir)
        else:
            self.dbis_browser = None

        # Stats
        self.stats = {
            "total": 0,
            "success": 0,
            "skipped": 0,
            "unpaywall": 0,
            "core": 0,
            "dbis_browser": 0
        }

    def fetch_single(self, doi: str, session_id: str) -> PDFResult:
        """
        Fetch PDF for a single DOI using fallback chain

        Args:
            doi: DOI of paper
            session_id: Research session ID (for organizing PDFs)

        Returns:
            PDFResult with success status and path
        """
        clean_doi = doi.replace("https://doi.org/", "").strip()
        output_path = self._get_output_path(clean_doi, session_id)

        # Check if already downloaded
        if output_path.exists():
            return PDFResult(
                doi=clean_doi,
                success=True,
                pdf_path=str(output_path),
                source="cached",
                attempts=0
            )

        # Try each strategy in fallback chain
        attempts = 0
        last_error = None

        for strategy in self.fallback_chain:
            attempts += 1

            try:
                if strategy == "unpaywall":
                    result = self._try_unpaywall(clean_doi, output_path)
                elif strategy == "core":
                    result = self._try_core(clean_doi, output_path)
                elif strategy == "dbis_browser":
                    result = self._try_dbis_browser(clean_doi, output_path)
                else:
                    print(f"⚠️ Unknown strategy: {strategy}")
                    continue

                # Success!
                if result.success:
                    self.stats["success"] += 1
                    self.stats[strategy] += 1
                    return PDFResult(
                        doi=clean_doi,
                        success=True,
                        pdf_path=str(output_path) if output_path.exists() else None,
                        pdf_url=result.pdf_url,
                        source=strategy,
                        attempts=attempts
                    )

                # Failed, save error and continue to next strategy
                last_error = result.error

            except Exception as e:
                print(f"❌ Strategy {strategy} crashed: {e}")
                last_error = str(e)
                continue

        # All strategies failed → Skip paper
        self.stats["skipped"] += 1
        return PDFResult(
            doi=clean_doi,
            success=False,
            error=last_error or "All strategies failed",
            skipped=True,
            attempts=attempts
        )

    def _try_unpaywall(self, doi: str, output_path: Path) -> PDFResult:
        """Try Unpaywall API"""
        result = self.unpaywall_client.fetch(doi, output_path)
        return PDFResult(
            doi=doi,
            success=result.success,
            pdf_url=result.pdf_url,
            pdf_path=str(output_path) if result.success else None,
            source="unpaywall" if result.success else None,
            error=result.error
        )

    def _try_core(self, doi: str, output_path: Path) -> PDFResult:
        """Try CORE API"""
        result = self.core_client.fetch(doi, output_path)
        return PDFResult(
            doi=doi,
            success=result.success,
            pdf_url=result.pdf_url,
            pdf_path=str(output_path) if result.success else None,
            source="core" if result.success else None,
            error=result.error
        )

    def _try_dbis_browser(self, doi: str, output_path: Path) -> PDFResult:
        """Try DBIS Browser"""
        if not self.dbis_browser:
            return PDFResult(
                doi=doi,
                success=False,
                error="DBIS Browser not enabled"
            )

        # DBIS Browser is async, run in sync context
        import asyncio
        result = self.dbis_browser.download_pdf_sync(doi, output_path)

        return PDFResult(
            doi=doi,
            success=result.success,
            pdf_path=result.pdf_path,
            source="dbis_browser" if result.success else None,
            error=result.error
        )

    def fetch_batch(
        self,
        papers: List[Dict[str, Any]],
        session_id: str,
        progress_callback: Optional[callable] = None
    ) -> List[PDFResult]:
        """
        Fetch PDFs for multiple papers

        Args:
            papers: List of paper dicts with 'doi' field
            session_id: Research session ID
            progress_callback: Optional callback(current, total, result)

        Returns:
            List of PDFResults
        """
        results = []
        total = len(papers)
        self.stats["total"] = total

        print(f"\n📄 Fetching PDFs for {total} papers...")
        print(f"   Fallback chain: {' → '.join(self.fallback_chain)}")

        for i, paper in enumerate(papers, 1):
            doi = paper.get("doi")
            if not doi:
                print(f"⚠️ Paper {i}/{total}: No DOI found, skipping")
                results.append(PDFResult(
                    doi="unknown",
                    success=False,
                    error="No DOI",
                    skipped=True
                ))
                continue

            print(f"\n📄 Paper {i}/{total}: {doi[:50]}...")

            # Fetch PDF
            result = self.fetch_single(doi, session_id)

            # Log result
            if result.success:
                print(f"   ✅ Success via {result.source} (attempt {result.attempts})")
            elif result.skipped:
                print(f"   ⏭️ Skipped after {result.attempts} attempts: {result.error}")
            else:
                print(f"   ❌ Failed: {result.error}")

            results.append(result)

            # Progress callback
            if progress_callback:
                progress_callback(i, total, result)

            # Rate limiting (brief pause between papers)
            if i < total:
                time.sleep(0.5)  # 500ms between papers

        # Print summary
        self._print_summary()

        return results

    def _print_summary(self):
        """Print fetch summary statistics"""
        print(f"\n{'='*50}")
        print(f"📊 PDF Fetch Summary")
        print(f"{'='*50}")
        print(f"Total Papers:     {self.stats['total']}")
        print(f"✅ Downloaded:    {self.stats['success']} ({self.stats['success']/self.stats['total']*100:.1f}%)")
        print(f"⏭️ Skipped:        {self.stats['skipped']} ({self.stats['skipped']/self.stats['total']*100:.1f}%)")
        print(f"\nBreakdown by Source:")
        print(f"  Unpaywall:      {self.stats['unpaywall']}")
        print(f"  CORE:           {self.stats['core']}")
        print(f"  DBIS Browser:   {self.stats['dbis_browser']}")
        print(f"{'='*50}\n")

    def _get_output_path(self, doi: str, session_id: str) -> Path:
        """
        Generate output path for PDF

        Args:
            doi: DOI
            session_id: Session ID (unused — PDFs go directly into output_dir)

        Returns:
            Path like: {output_dir}/{sanitized_doi}.pdf

        Note (I-03 fix): PDFs are saved directly into output_dir, NOT a session
        subdirectory. The session is already encoded in the run directory path
        (e.g. runs/2026-03-01_12-00-00/pdfs/), so creating another level breaks
        `ls pdfs/*.pdf` glob patterns used by the Validation Gate.
        """
        # Sanitize DOI for filename (replace special chars with _)
        safe_doi = re.sub(r'[^\w\-.]', '_', doi)

        # Ensure output_dir exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

        return self.output_dir / f"{safe_doi}.pdf"

    def get_stats(self) -> Dict[str, int]:
        """Get current statistics"""
        return self.stats.copy()

    def close(self):
        """Close all clients"""
        self.unpaywall_client.close()
        self.core_client.close()
        if self.dbis_browser:
            import asyncio
            asyncio.run(self.dbis_browser.close())

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# ============================================
# Convenience Functions
# ============================================

def fetch_pdfs(
    papers: List[Dict[str, Any]],
    session_id: str,
    output_dir: Path,
    unpaywall_email: Optional[str] = None,
    core_api_key: Optional[str] = None
) -> List[PDFResult]:
    """
    Simple helper to fetch PDFs for a list of papers

    Args:
        papers: List of paper dicts with 'doi' field
        session_id: Research session ID
        output_dir: Directory to save PDFs (REQUIRED - e.g. Path("runs/2026-01-01/pdfs"))
        unpaywall_email: Optional Unpaywall email
        core_api_key: Optional CORE API key

    Returns:
        List of PDFResults
    """
    with PDFFetcher(
        output_dir=output_dir,
        unpaywall_email=unpaywall_email,
        core_api_key=core_api_key
    ) as fetcher:
        return fetcher.fetch_batch(papers, session_id)


# ============================================
# CLI Interface
# ============================================

def main():
    """
    CLI Interface for PDF Fetcher

    Usage:
        python -m src.pdf.pdf_fetcher --input papers.json --output-dir pdfs/ --session-id abc123
        python -m src.pdf.pdf_fetcher --input papers.json --output-dir pdfs/ --enable-unpaywall --enable-core --results-file results.json
    """
    import argparse
    import json
    import sys
    import uuid

    parser = argparse.ArgumentParser(description="PDF Fetcher - Download PDFs via Unpaywall and CORE")
    parser.add_argument('--input', required=True, help='Input JSON file with papers list')
    parser.add_argument('--output-dir', required=True, help='Output directory for PDFs')
    parser.add_argument('--session-id', help='Session ID (default: auto-generated)')
    parser.add_argument('--max-papers', type=int, help='Maximum papers to process')
    parser.add_argument('--enable-unpaywall', action='store_true', help='Enable Unpaywall API')
    parser.add_argument('--enable-core', action='store_true', help='Enable CORE API')
    parser.add_argument('--unpaywall-email', help='Email for Unpaywall API (polite pool)')
    parser.add_argument('--core-api-key', help='API key for CORE API')
    parser.add_argument('--results-file', help='Output file for download results JSON')
    parser.add_argument('--test', action='store_true', help='Run test with sample DOIs')

    args = parser.parse_args()

    if args.test:
        test_papers = [
            {"doi": "10.1371/journal.pone.0000000"},
            {"doi": "10.1038/nature12345"},
        ]
        output_dir = Path("runs/test_session/pdfs")
        session_id = str(uuid.uuid4())[:8]
        with PDFFetcher(output_dir=output_dir) as fetcher:
            results = fetcher.fetch_batch(test_papers, session_id)
            print(f"✅ Test complete: {sum(1 for r in results if r.success)}/{len(results)} downloaded")
        sys.exit(0)

    try:
        # Load papers
        with open(args.input, 'r') as f:
            data = json.load(f)
        papers = data.get('papers', data) if isinstance(data, dict) else data

        if not papers:
            print("❌ No papers found in input file", file=sys.stderr)
            sys.exit(1)

        # I-18 fix: Sort papers by relevance score (highest first) so that if we
        # run out of API quota or time, the most important papers are downloaded first.
        papers.sort(
            key=lambda p: p.get('final_score', p.get('scores', {}).get('total', p.get('score', 0))),
            reverse=True
        )

        # Apply max-papers limit AFTER sorting so top papers are kept
        if args.max_papers:
            papers = papers[:args.max_papers]

        # Build fallback chain based on flags
        fallback_chain = []
        if args.enable_unpaywall:
            fallback_chain.append("unpaywall")
        if args.enable_core:
            fallback_chain.append("core")
        if not fallback_chain:
            fallback_chain = ["unpaywall", "core"]  # default

        # Session ID
        session_id = args.session_id or str(uuid.uuid4())[:8]
        output_dir = Path(args.output_dir)

        print(f"📄 Processing {len(papers)} papers...")
        print(f"   Output: {output_dir}")
        print(f"   Session: {session_id}")
        print(f"   Chain: {' → '.join(fallback_chain)}")

        with PDFFetcher(
            output_dir=output_dir,
            unpaywall_email=args.unpaywall_email,
            core_api_key=args.core_api_key,
            fallback_chain=fallback_chain
        ) as fetcher:
            results = fetcher.fetch_batch(papers, session_id)

        # Build results dict
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]

        output = {
            "session_id": session_id,
            "total": len(results),
            "downloaded": len(successful),
            "failed_count": len(failed),
            "downloads": {
                "successful": [
                    {"doi": r.doi, "path": r.pdf_path, "source": r.source}
                    for r in successful
                ],
                "failed": [
                    {"doi": r.doi, "error": r.error}
                    for r in failed
                ]
            }
        }

        # Save results file if requested
        if args.results_file:
            Path(args.results_file).parent.mkdir(parents=True, exist_ok=True)
            with open(args.results_file, 'w') as f:
                json.dump(output, f, indent=2)
            print(f"💾 Results saved to: {args.results_file}")

        # Print summary
        print(json.dumps(output, indent=2))

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


# ============================================
# Test Code (backward compat)
# ============================================

if __name__ == "__main__":
    main()
