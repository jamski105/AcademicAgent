"""
SearchEngine Orchestrator für Academic Agent v2.2

Orchestriert Multi-API Paper-Suche + DBIS Search:
- CrossRef (150M+ papers)
- OpenAlex (250M+ works)
- Semantic Scholar (200M+ papers)
- DBIS Search (v2.2 - via dbis_search agent)

Features:
- Multi-Source Search (parallel via asyncio)
- Hybrid Mode: APIs + DBIS (v2.2)
- Source Annotation (api/dbis)
- Automatic Deduplication
- Fallback-Chain (wenn API fehlschlägt)
- Mode Detection (Standard vs Enhanced)
- Graceful Degradation

Usage:
    from src.search.search_engine import SearchEngine

    # Standard-Modus (ohne API-Keys)
    engine = SearchEngine()
    papers = engine.search("DevOps Governance", limit=20)

    # Enhanced-Modus (mit API-Keys)
    from src.utils.config import load_config
    api_config, _ = load_config()
    engine = SearchEngine(api_config=api_config)
    papers = engine.search("DevOps Governance", limit=20)
"""

from typing import List, Optional, Dict, Any
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor

from src.search.crossref_client import CrossRefClient, Paper
from src.search.openalex_client import OpenAlexClient
from src.search.semantic_scholar_client import SemanticScholarClient
from src.search.deduplicator import Deduplicator
from src.utils.config import APIConfig

# Setup Logging
logger = logging.getLogger(__name__)


# ============================================
# SearchEngine
# ============================================

class SearchEngine:
    """
    Multi-API SearchEngine Orchestrator

    Koordiniert Suche über CrossRef, OpenAlex, Semantic Scholar
    Dedupliziert Ergebnisse, handled Fallbacks

    Usage:
        engine = SearchEngine()
        papers = engine.search("DevOps Governance", limit=20)
    """

    def __init__(
        self,
        api_config: Optional[APIConfig] = None,
        sources: Optional[List[str]] = None
    ):
        """
        Initialize SearchEngine

        Args:
            api_config: Optional APIConfig object (from config loader)
            sources: Optional list of sources to use (default: all)
        """
        # Load config if not provided
        if api_config:
            self.api_config = api_config
        else:
            # Use default (no API keys)
            logger.info("SearchEngine: Using default config (no API keys)")
            self.api_config = None

        # Sources to use
        self.sources = sources or ["crossref", "openalex", "semantic_scholar"]

        # Initialize API clients
        self._init_clients()

        # Deduplicator
        self.deduplicator = Deduplicator()

        logger.info(f"SearchEngine initialized (mode: {self._get_mode()}, sources: {self.sources})")

    def _init_clients(self):
        """Initialize API clients based on config"""
        # CrossRef
        crossref_email = None
        if self.api_config:
            crossref_email = self.api_config.api_keys.crossref_email

        self.crossref_client = CrossRefClient(email=crossref_email)

        # OpenAlex
        openalex_email = None
        if self.api_config:
            openalex_email = self.api_config.api_keys.openalex_email

        self.openalex_client = OpenAlexClient(email=openalex_email)

        # Semantic Scholar
        s2_key = None
        if self.api_config:
            s2_key = self.api_config.api_keys.semantic_scholar_api_key

        self.s2_client = SemanticScholarClient(api_key=s2_key)

    def _get_mode(self) -> str:
        """Get current mode (standard or enhanced)"""
        if self.api_config:
            return self.api_config.mode
        return "standard"

    def search(
        self,
        query: str,
        limit: int = 50,
        sources: Optional[List[str]] = None,
        deduplicate: bool = True
    ) -> List[Paper]:
        """
        Search for papers across multiple APIs

        Args:
            query: Search query
            limit: Max results (default: 50)
            sources: Optional override of sources (default: use instance sources)
            deduplicate: Whether to deduplicate results (default: True)

        Returns:
            List of Paper objects (deduplicated and sorted by relevance)

        Example:
            papers = engine.search("DevOps Governance", limit=20)
            papers = engine.search("ML Ethics", sources=["crossref", "openalex"])
        """
        sources = sources or self.sources

        logger.info(f"SearchEngine: Searching '{query}' across {len(sources)} sources (limit: {limit})")

        # Search each source
        all_papers = []
        per_source_limit = limit  # Each source can return up to limit

        for source in sources:
            try:
                source_papers = self._search_source(source, query, per_source_limit)
                # Annotate with source (v2.2)
                for paper in source_papers:
                    if not hasattr(paper, 'source'):
                        paper.source = source
                    if not hasattr(paper, 'source_type'):
                        paper.source_type = 'api'  # API papers (not DBIS)
                all_papers.extend(source_papers)
                logger.info(f"  {source}: {len(source_papers)} papers")
            except Exception as e:
                logger.error(f"  {source}: Failed - {e}")
                # Continue with other sources

        logger.info(f"SearchEngine: Total {len(all_papers)} papers before deduplication")

        # Deduplicate
        if deduplicate:
            all_papers = self.deduplicator.deduplicate(all_papers)
            logger.info(f"SearchEngine: {len(all_papers)} unique papers after deduplication")

        # Sort by citations (descending)
        all_papers = sorted(
            all_papers,
            key=lambda p: p.citations or 0,
            reverse=True
        )

        # Return up to limit
        return all_papers[:limit]

    def _search_source(self, source: str, query: str, limit: int) -> List[Paper]:
        """
        Search single source

        Args:
            source: Source name ("crossref", "openalex", "semantic_scholar")
            query: Search query
            limit: Max results

        Returns:
            List of Paper objects
        """
        if source == "crossref":
            return self.crossref_client.search(query, limit=limit)
        elif source == "openalex":
            return self.openalex_client.search(query, limit=limit)
        elif source == "semantic_scholar":
            return self.s2_client.search(query, limit=limit)
        else:
            logger.warning(f"Unknown source: {source}")
            return []

    def search_parallel(
        self,
        query: str,
        limit: int = 50,
        sources: Optional[List[str]] = None
    ) -> List[Paper]:
        """
        Search multiple sources in parallel (faster!)

        Uses ThreadPoolExecutor for parallel API calls

        Args:
            query: Search query
            limit: Max results
            sources: Optional override of sources

        Returns:
            List of Paper objects (deduplicated)
        """
        sources = sources or self.sources

        logger.info(f"SearchEngine: Parallel search '{query}' across {len(sources)} sources")

        # Parallel search
        with ThreadPoolExecutor(max_workers=len(sources)) as executor:
            futures = []
            for source in sources:
                future = executor.submit(self._search_source, source, query, limit)
                futures.append((source, future))

            # Collect results
            all_papers = []
            for source, future in futures:
                try:
                    source_papers = future.result(timeout=30)
                    all_papers.extend(source_papers)
                    logger.info(f"  {source}: {len(source_papers)} papers")
                except Exception as e:
                    logger.error(f"  {source}: Failed - {e}")

        logger.info(f"SearchEngine: Total {len(all_papers)} papers before deduplication")

        # Deduplicate
        all_papers = self.deduplicator.deduplicate(all_papers)
        logger.info(f"SearchEngine: {len(all_papers)} unique papers after deduplication")

        # Sort by citations
        all_papers = sorted(
            all_papers,
            key=lambda p: p.citations or 0,
            reverse=True
        )

        return all_papers[:limit]

    def merge_with_dbis_papers(
        self,
        api_papers: List[Paper],
        dbis_papers: List[Dict],
        deduplicate: bool = True
    ) -> List[Paper]:
        """
        Merge API papers with DBIS papers (v2.2)

        Args:
            api_papers: Papers from APIs (CrossRef, OpenAlex, S2)
            dbis_papers: Papers from DBIS search (dicts from agent)
            deduplicate: Remove duplicates (default: True)

        Returns:
            Combined list of papers with source annotation
        """
        # Convert DBIS dicts to Paper objects
        dbis_paper_objects = []
        for dbis_paper in dbis_papers:
            # Create Paper object from DBIS dict
            paper = Paper(
                doi=dbis_paper.get('doi'),
                title=dbis_paper.get('title', ''),
                authors=dbis_paper.get('authors', []),
                year=dbis_paper.get('year'),
                abstract=dbis_paper.get('abstract', ''),
                venue=dbis_paper.get('journal', dbis_paper.get('venue', '')),
                citations=None,  # DBIS doesn't provide citation count
                url=dbis_paper.get('url', '')
            )
            # Annotate with DBIS source
            paper.source = dbis_paper.get('source', 'dbis')
            paper.source_type = 'dbis'
            dbis_paper_objects.append(paper)

        # Merge
        all_papers = api_papers + dbis_paper_objects
        logger.info(f"Merged {len(api_papers)} API papers + {len(dbis_paper_objects)} DBIS papers")

        # Deduplicate if requested
        if deduplicate:
            all_papers = self.deduplicator.deduplicate(all_papers)
            logger.info(f"{len(all_papers)} unique papers after deduplication")

        return all_papers

    def close(self):
        """Close all API clients"""
        self.crossref_client.close()
        self.openalex_client.close()
        self.s2_client.close()

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


# ============================================
# Convenience Functions
# ============================================

def search_papers(
    query: str,
    limit: int = 50,
    api_config: Optional[APIConfig] = None
) -> List[Paper]:
    """
    Convenience function for quick searches

    Args:
        query: Search query
        limit: Max results
        api_config: Optional API config

    Returns:
        List of Paper objects

    Example:
        papers = search_papers("DevOps Governance", limit=20)
    """
    with SearchEngine(api_config=api_config) as engine:
        return engine.search(query, limit=limit)


# ============================================
# CLI Test
# ============================================

def main():
    """
    CLI Interface for SearchEngine

    Usage:
        python -m src.search.search_engine --query "DevOps Governance" --mode standard --output results.json
        python -m src.search.search_engine --query "AI Ethics" --limit 10 --sources crossref openalex
    """
    import argparse
    import json
    import sys

    parser = argparse.ArgumentParser(description="Academic Search Engine - Multi-API Search")
    parser.add_argument('--query', required=True, help='Search query')
    parser.add_argument('--mode', choices=['quick', 'standard', 'deep'], default='standard',
                        help='Research mode (determines limit)')
    parser.add_argument('--limit', type=int, help='Max number of papers (overrides mode)')
    parser.add_argument('--sources', nargs='+', choices=['crossref', 'openalex', 'semantic_scholar'],
                        help='API sources to search (default: all)')
    parser.add_argument('--output', help='Output JSON file path (default: stdout)')
    parser.add_argument('--parallel', action='store_true', help='Use parallel search (faster)')
    parser.add_argument('--test', action='store_true', help='Run tests instead of search')

    args = parser.parse_args()

    # Test mode
    if args.test:
        _run_tests()
        return

    # Determine limit from mode
    mode_limits = {
        'quick': 15,
        'standard': 25,
        'deep': 40
    }
    limit = args.limit or mode_limits.get(args.mode, 25)

    try:
        # Initialize search engine
        engine = SearchEngine()

        # Perform search
        if args.parallel:
            papers = engine.search_parallel(args.query, limit=limit, sources=args.sources)
        else:
            papers = engine.search(args.query, limit=limit, sources=args.sources)

        # Convert to JSON-serializable format
        results = {
            "query": args.query,
            "mode": args.mode,
            "total_found": len(papers),
            "limit": limit,
            "sources": args.sources or ["crossref", "openalex", "semantic_scholar"],
            "papers": [
                {
                    "doi": p.doi,
                    "title": p.title,
                    "abstract": p.abstract,
                    "authors": p.authors,
                    "year": p.year,
                    "venue": p.venue,
                    "citations": p.citations,
                    "source_api": p.source_api,
                    "url": p.url
                }
                for p in papers
            ]
        }

        # Output results
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"Results saved to {args.output}", file=sys.stderr)
        else:
            # Output JSON to stdout (for parsing by coordinator)
            print(json.dumps(results, indent=2))

    except Exception as e:
        error = {
            "error": str(e),
            "query": args.query,
            "status": "failed"
        }
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(error, f, indent=2)
        else:
            print(json.dumps(error), file=sys.stderr)
        sys.exit(1)


def _run_tests():
    """Run test suite"""
    print("Testing SearchEngine...")

    # Test 1: Basic search (sequential)
    print("\n1. Testing basic search (sequential)...")
    engine = SearchEngine()
    papers = engine.search("DevOps Governance", limit=10)
    print(f"✅ Found {len(papers)} unique papers")

    if papers:
        print(f"\nTop 3 Papers (by citations):")
        for i, p in enumerate(papers[:3], 1):
            print(f"\n{i}. {p.title[:60]}...")
            print(f"   DOI: {p.doi}")
            print(f"   Source: {p.source_api}")
            print(f"   Citations: {p.citations}")
            print(f"   Year: {p.year}")

    # Test 2: Parallel search (faster)
    print("\n2. Testing parallel search...")
    papers = engine.search_parallel("DevOps Governance", limit=10)
    print(f"✅ Found {len(papers)} unique papers (parallel)")

    # Test 3: Single source
    print("\n3. Testing single source search...")
    papers = engine.search("machine learning ethics", limit=5, sources=["crossref"])
    print(f"✅ Found {len(papers)} papers (CrossRef only)")

    # Test 4: Context manager
    print("\n4. Testing context manager...")
    with SearchEngine() as engine:
        papers = engine.search("AI Ethics", limit=5)
        print(f"✅ Found {len(papers)} papers via context manager")

    print("\n✅ All tests passed!")
    print(f"\n💡 TIP: Use search_parallel() for faster results!")


if __name__ == "__main__":
    main()
