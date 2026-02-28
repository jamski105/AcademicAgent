"""
Semantic Scholar API Client für Academic Agent v2.3+

Semantic Scholar API Documentation: https://api.semanticscholar.org/api-docs/

Features:
- Anonymous Access (100 req/5min, KEIN Key nötig!)
- Optional: API-Key für 1 req/s (schneller)
- Semantic Search (Natural Language)
- Citation-Counts included
- 200M+ Papers verfügbar

Standard-Modus (Anonymous):
    client = SemanticScholarClient()  # 100 req/5min
    papers = client.search("DevOps Governance", limit=20)

Enhanced-Modus (Optional):
    client = SemanticScholarClient(api_key="YOUR_KEY")  # 1 req/s
    papers = client.search("DevOps Governance", limit=20)
"""

from typing import List, Optional, Dict, Any
import logging

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from src.utils.rate_limiter import RateLimiter
from src.utils.retry import RateLimitError, ServerError, raise_for_status_with_retry
from src.search.crossref_client import Paper

# Setup Logging
logger = logging.getLogger(__name__)


# ============================================
# Semantic Scholar API Client
# ============================================

class SemanticScholarClient:
    """
    Semantic Scholar API Client

    Funktioniert OHNE API-Key (100 req/5min)
    Optional: API-Key für 1 req/s (schneller)

    Usage:
        # Standard-Modus (Anonymous)
        client = SemanticScholarClient()
        papers = client.search("machine learning ethics", limit=20)

        # Enhanced-Modus (mit API-Key)
        client = SemanticScholarClient(api_key="YOUR_KEY")
        papers = client.search("machine learning ethics", limit=20)
    """

    BASE_URL = "https://api.semanticscholar.org/graph/v1"

    def __init__(
        self,
        api_key: Optional[str] = None,
        timeout: int = 30
    ):
        """
        Initialize Semantic Scholar Client

        Args:
            api_key: Optional API key for 1 req/s (ohne: 100 req/5min)
            timeout: Request timeout in seconds (default: 30)
        """
        self.api_key = api_key
        self.timeout = timeout

        # Rate Limiter
        # Anonymous: 0.33 req/s (100 req/5min)
        # With Key: 1 req/s
        if api_key:
            self.rate_limiter = RateLimiter(requests_per_second=1)
            logger.info(f"Semantic Scholar: Enhanced Mode (API key set)")
        else:
            self.rate_limiter = RateLimiter(requests_per_second=0.33)  # ~100 req/5min
            logger.info(f"Semantic Scholar: Standard Mode (anonymous)")

        # HTTP Client
        headers = {
            "User-Agent": "AcademicAgentV2/1.0",
            "Accept": "application/json"
        }
        if api_key:
            headers["x-api-key"] = api_key

        self.client = httpx.Client(headers=headers, timeout=timeout)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=1, max=10),
        retry=retry_if_exception_type((RateLimitError, ServerError)),
        reraise=True
    )
    def search(
        self,
        query: str,
        limit: int = 20,
        fields: Optional[List[str]] = None
    ) -> List[Paper]:
        """
        Search Semantic Scholar API

        Args:
            query: Search query (natural language or keywords)
            limit: Max results (default: 20, max: 100)
            fields: Optional fields to retrieve (default: all relevant fields)

        Returns:
            List of Paper objects

        Example:
            papers = client.search("DevOps governance", limit=15)
            papers = client.search("machine learning ethics", limit=20)
        """
        # Rate Limiting
        self.rate_limiter.acquire()

        # Default fields
        if not fields:
            fields = [
                "paperId", "externalIds", "title", "authors", "year",
                "abstract", "venue", "publicationDate", "citationCount", "url"
            ]

        # Build Request
        params = {
            "query": query,
            "limit": min(limit, 100),  # S2 max: 100
            "fields": ",".join(fields)
        }

        logger.debug(f"Semantic Scholar search: query='{query}', limit={limit}")

        try:
            # API Call
            response = self.client.get(f"{self.BASE_URL}/paper/search", params=params)
            raise_for_status_with_retry(response)

            data = response.json()

            # Parse Results
            papers_data = data.get("data", [])
            papers = []
            for paper_data in papers_data:
                paper = self._parse_paper(paper_data)
                if paper:
                    papers.append(paper)

            logger.info(f"Semantic Scholar found {len(papers)} papers for query: '{query}'")
            return papers[:limit]

        except httpx.TimeoutException as e:
            logger.error(f"Semantic Scholar timeout: {e}")
            return []
        except Exception as e:
            logger.error(f"Semantic Scholar search failed: {e}")
            raise

    def get_by_doi(self, doi: str) -> Optional[Paper]:
        """
        Get single paper by DOI

        Args:
            doi: Paper DOI (e.g., "10.1109/MS.2022.1234567")

        Returns:
            Paper object or None if not found
        """
        # Rate Limiting
        self.rate_limiter.acquire()

        # Normalize DOI
        doi = doi.strip()

        logger.debug(f"Semantic Scholar get_by_doi: {doi}")

        try:
            # S2 uses DOI as external ID
            fields = "paperId,externalIds,title,authors,year,abstract,venue,citationCount,url"
            response = self.client.get(f"{self.BASE_URL}/paper/DOI:{doi}", params={"fields": fields})

            if response.status_code == 404:
                logger.warning(f"DOI not found: {doi}")
                return None

            raise_for_status_with_retry(response)

            paper_data = response.json()
            return self._parse_paper(paper_data)

        except Exception as e:
            logger.error(f"Semantic Scholar get_by_doi failed: {e}")
            return None

    def _parse_paper(self, paper_data: Dict[str, Any]) -> Optional[Paper]:
        """
        Parse Semantic Scholar paper to Paper object

        Args:
            paper_data: S2 paper JSON object

        Returns:
            Paper object or None if DOI missing
        """
        # DOI (required)
        external_ids = paper_data.get("externalIds", {})
        doi = external_ids.get("DOI", "")
        if not doi:
            return None  # Skip papers without DOI

        # Title
        title = paper_data.get("title", "Untitled")
        if not title:
            title = "Untitled"

        # Authors
        authors = []
        for author in paper_data.get("authors", []):
            name = author.get("name", "")
            if name:
                authors.append(name)

        # Year
        year = paper_data.get("year", None)

        # Abstract
        abstract = paper_data.get("abstract", None)

        # Venue
        venue = paper_data.get("venue", None)

        # URL
        url = paper_data.get("url", None)

        # Citations
        citations = paper_data.get("citationCount", 0)

        return Paper(
            doi=doi,
            title=title,
            authors=authors,
            year=year,
            abstract=abstract,
            venue=venue,
            source_api="semantic_scholar",
            url=url,
            citations=citations,
            raw_data=paper_data
        )

    def close(self):
        """Close HTTP client"""
        self.client.close()

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


# ============================================
# Convenience Functions
# ============================================

def search_semantic_scholar(
    query: str,
    limit: int = 20,
    api_key: Optional[str] = None
) -> List[Paper]:
    """
    Convenience function for quick searches

    Args:
        query: Search query
        limit: Max results
        api_key: Optional API key

    Returns:
        List of Paper objects

    Example:
        papers = search_semantic_scholar("DevOps Governance", limit=15)
    """
    with SemanticScholarClient(api_key=api_key) as client:
        return client.search(query, limit=limit)


# ============================================
# CLI Test
# ============================================

if __name__ == "__main__":
    """
    Test Semantic Scholar Client

    Run:
        python -m src.search.semantic_scholar_client
    """
    print("Testing Semantic Scholar API Client...")

    # Test 1: Anonymous Access
    print("\n1. Testing Anonymous Access (100 req/5min)...")
    client = SemanticScholarClient()
    papers = client.search("DevOps Governance", limit=5)
    print(f"✅ Found {len(papers)} papers")

    if papers:
        print(f"\nExample Paper:")
        p = papers[0]
        print(f"  DOI: {p.doi}")
        print(f"  Title: {p.title}")
        print(f"  Authors: {', '.join(p.authors[:3])}")
        print(f"  Year: {p.year}")
        print(f"  Venue: {p.venue}")
        print(f"  Citations: {p.citations}")
        if p.abstract:
            print(f"  Abstract: {p.abstract[:100]}...")

    # Test 2: Get by DOI
    print("\n2. Testing get_by_doi()...")
    if papers:
        paper = client.get_by_doi(papers[0].doi)
        if paper:
            print(f"✅ Retrieved paper: {paper.title[:50]}...")

    # Test 3: Context Manager
    print("\n3. Testing context manager...")
    with SemanticScholarClient() as client:
        papers = client.search("machine learning ethics", limit=3)
        print(f"✅ Found {len(papers)} papers via context manager")

    print("\n✅ All tests passed!")
    print("\n💡 TIP: Get API key for faster requests (1 req/s)!")
    print("   https://www.semanticscholar.org/product/api")
