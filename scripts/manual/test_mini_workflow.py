#!/usr/bin/env python3
"""
Mini Research Test - Academic Agent v2.3
Quick workflow validation test (~5-10 minutes)

Test Configuration:
- Query: "DevOps Governance"
- Mode: quick (15 papers, APIs only, NO DBIS)
- Citation Style: APA 7
- Duration: ~5-10 minutes

Phases:
1. Setup (session ID, run directory, database)
2. API Search (CrossRef only for speed)
3. Ranking (5D Framework - simple version)
4. PDF Download (Unpaywall only)
5. Export (JSON with metadata, citations, statistics)
"""

import sys
import time
import json
from pathlib import Path
from datetime import datetime
import uuid
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Execute mini research test workflow"""

    print("=" * 70)
    print("ACADEMIC AGENT - MINI RESEARCH TEST")
    print("=" * 70)
    print()

    # Test configuration
    query = "DevOps Governance"
    mode = "quick"
    citation_style = "APA 7"
    max_papers = 15

    print(f"Query: {query}")
    print(f"Mode: {mode} ({max_papers} papers, APIs only)")
    print(f"Citation Style: {citation_style}")
    print()

    start_time = time.time()
    results = {
        "test_config": {
            "query": query,
            "mode": mode,
            "citation_style": citation_style,
            "max_papers": max_papers,
            "skip_dbis": True,
            "skip_quotes": True
        },
        "phases": {},
        "errors": []
    }

    try:
        # ============================================
        # PHASE 1: SETUP
        # ============================================
        print("[PHASE 1] Setup...")
        phase_start = time.time()

        # Generate session ID
        session_id = str(uuid.uuid4())
        logger.info(f"Session ID: {session_id}")

        # Create run directory
        from src.state.run_manager import RunManager
        run_manager = RunManager()
        run_dir = run_manager.create_run_directory()
        logger.info(f"Run directory: {run_dir}")

        # Initialize database (create schema only)
        from src.state.database import DatabaseManager
        db_path = run_dir / "session.db"
        db = DatabaseManager(db_path)
        logger.info(f"Database initialized: {db_path}")

        results["session_id"] = session_id
        results["run_directory"] = str(run_dir)
        results["phases"]["setup"] = {
            "status": "success",
            "duration": time.time() - phase_start
        }
        print(f"✓ Setup complete ({time.time() - phase_start:.1f}s)")
        print(f"  Session ID: {session_id}")
        print(f"  Run directory: {run_dir}")
        print()

        # ============================================
        # PHASE 2: API SEARCH (CrossRef only)
        # ============================================
        print("[PHASE 2] API Search (CrossRef only)...")
        phase_start = time.time()

        from src.search.search_engine import SearchEngine

        search_engine = SearchEngine()
        papers = search_engine.search(
            query=query,
            limit=max_papers,
            sources=["crossref"]  # CrossRef only for speed
        )

        logger.info(f"Found {len(papers)} papers from CrossRef")

        # Store in database using ORM (optional for test)
        # Skipping database storage to keep test simple

        results["phases"]["api_search"] = {
            "status": "success",
            "papers_found": len(papers),
            "sources": ["crossref"],
            "duration": time.time() - phase_start
        }
        print(f"✓ API Search complete ({time.time() - phase_start:.1f}s)")
        print(f"  Papers found: {len(papers)}")
        print()

        # ============================================
        # PHASE 3: RANKING (Simple 5D)
        # ============================================
        print("[PHASE 3] Ranking (5D Framework - simple)...")
        phase_start = time.time()

        from src.ranking.five_d_scorer import FiveDScorer

        scorer = FiveDScorer()

        # Score all papers
        scored_results = scorer.score(papers, query=query)

        # Sort by total score
        scored_results.sort(key=lambda x: x["scores"]["total"], reverse=True)

        # Select top papers and attach scores
        top_papers = []
        for result in scored_results[:max_papers]:
            paper = result["paper"]
            paper.score = result["scores"]["total"]
            paper.scores_detail = result["scores"]
            top_papers.append(paper)

        logger.info(f"Ranked {len(scored_results)} papers, selected top {len(top_papers)}")

        results["phases"]["ranking"] = {
            "status": "success",
            "papers_ranked": len(scored_results),
            "papers_selected": len(top_papers),
            "duration": time.time() - phase_start
        }
        print(f"✓ Ranking complete ({time.time() - phase_start:.1f}s)")
        print(f"  Top papers selected: {len(top_papers)}")
        print()

        # ============================================
        # PHASE 4: PDF DOWNLOAD (Unpaywall only)
        # ============================================
        print("[PHASE 4] PDF Download (Unpaywall only)...")
        phase_start = time.time()

        from src.pdf.unpaywall_client import UnpaywallClient

        unpaywall = UnpaywallClient()
        pdfs_downloaded = 0
        pdf_dir = run_dir / "pdfs"
        pdf_dir.mkdir(exist_ok=True)

        for paper in top_papers:
            if not paper.doi:
                continue

            try:
                pdf_url = unpaywall.get_pdf_url(paper.doi)
                if pdf_url:
                    # Download PDF
                    pdf_content = unpaywall.download_pdf(pdf_url)
                    if pdf_content:
                        # Save PDF
                        pdf_filename = f"{paper.doi.replace('/', '_')}.pdf"
                        pdf_path = pdf_dir / pdf_filename
                        pdf_path.write_bytes(pdf_content)
                        pdfs_downloaded += 1
                        logger.info(f"Downloaded PDF: {paper.doi}")
            except Exception as e:
                logger.warning(f"Failed to download PDF for {paper.doi}: {e}")

        results["phases"]["pdf_download"] = {
            "status": "success",
            "pdfs_attempted": len([p for p in top_papers if p.doi]),
            "pdfs_downloaded": pdfs_downloaded,
            "success_rate": f"{pdfs_downloaded / max(len([p for p in top_papers if p.doi]), 1) * 100:.1f}%",
            "duration": time.time() - phase_start
        }
        print(f"✓ PDF Download complete ({time.time() - phase_start:.1f}s)")
        print(f"  PDFs downloaded: {pdfs_downloaded}/{len([p for p in top_papers if p.doi])}")
        print(f"  Success rate: {pdfs_downloaded / max(len([p for p in top_papers if p.doi]), 1) * 100:.1f}%")
        print()

        # ============================================
        # PHASE 5: EXPORT
        # ============================================
        print("[PHASE 5] Export...")
        phase_start = time.time()

        # Generate simple citations for each paper
        papers_with_citations = []
        for paper in top_papers:
            # Simple APA-style citation (without full formatter)
            authors_str = ", ".join(paper.authors[:3]) if paper.authors else "Unknown"
            if len(paper.authors) > 3:
                authors_str += " et al."
            simple_citation = f"{authors_str} ({paper.year}). {paper.title}. {paper.venue or 'Unknown Venue'}."

            papers_with_citations.append({
                "doi": paper.doi,
                "title": paper.title,
                "authors": paper.authors,
                "year": paper.year,
                "abstract": paper.abstract,
                "venue": paper.venue,
                "citations": paper.citations,
                "url": paper.url,
                "score": paper.score,
                "citation": simple_citation
            })

        # Create export JSON
        export_data = {
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "mode": mode,
            "citation_style": citation_style,
            "statistics": {
                "total_papers_found": len(papers),
                "papers_selected": len(top_papers),
                "pdfs_downloaded": pdfs_downloaded,
                "pdf_success_rate": f"{pdfs_downloaded / max(len([p for p in top_papers if p.doi]), 1) * 100:.1f}%"
            },
            "papers": papers_with_citations
        }

        # Save export
        export_path = run_dir / "research_results.json"
        with open(export_path, 'w') as f:
            json.dump(export_data, f, indent=2)

        logger.info(f"Export saved to {export_path}")

        results["phases"]["export"] = {
            "status": "success",
            "export_path": str(export_path),
            "duration": time.time() - phase_start
        }
        print(f"✓ Export complete ({time.time() - phase_start:.1f}s)")
        print(f"  Export saved: {export_path}")
        print()

        # ============================================
        # FINAL SUMMARY
        # ============================================
        total_duration = time.time() - start_time

        print("=" * 70)
        print("TEST COMPLETE!")
        print("=" * 70)
        print()
        print(f"Session ID: {session_id}")
        print(f"Total Duration: {total_duration / 60:.1f} minutes")
        print()
        print("Papers Found:")
        print(f"  - API Search: {len(papers)}")
        print(f"  - Top Selected: {len(top_papers)}")
        print()
        print("PDFs Downloaded:")
        print(f"  - Downloaded: {pdfs_downloaded}/{len([p for p in top_papers if p.doi])}")
        print(f"  - Success Rate: {pdfs_downloaded / max(len([p for p in top_papers if p.doi]), 1) * 100:.1f}%")
        print()
        print("Output Files:")
        print(f"  - Run Directory: {run_dir}")
        print(f"  - Database: {db_path}")
        print(f"  - PDFs: {pdf_dir}")
        print(f"  - Export: {export_path}")
        print()

        # Add summary to results
        results["summary"] = {
            "session_id": session_id,
            "total_duration_seconds": total_duration,
            "total_duration_minutes": total_duration / 60,
            "papers_found": len(papers),
            "papers_selected": len(top_papers),
            "pdfs_downloaded": pdfs_downloaded,
            "pdf_success_rate": f"{pdfs_downloaded / max(len([p for p in top_papers if p.doi]), 1) * 100:.1f}%",
            "run_directory": str(run_dir)
        }

        # Save test report
        report_path = run_dir / "test_report.json"
        with open(report_path, 'w') as f:
            json.dump(results, f, indent=2)

        print(f"Test Report: {report_path}")
        print()

        return 0

    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        results["errors"].append(str(e))
        results["status"] = "failed"

        print()
        print("=" * 70)
        print("TEST FAILED!")
        print("=" * 70)
        print(f"Error: {e}")
        print()

        return 1


if __name__ == "__main__":
    sys.exit(main())
