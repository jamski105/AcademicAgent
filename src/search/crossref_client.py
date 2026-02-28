"""
CrossRef API Client für Academic Agent v2.3+

CrossRef API Documentation: https://api.crossref.org/swagger-ui/index.html

Features:
- Anonymous Access (KEIN API-Key nötig!)
- Optional: Email für "polite" Header
- Rate Limiting: 50 req/s
- Retry bei 429/5xx Errors
- 150M+ Papers verfügbar

Standard-Modus:
    client = CrossRefClient()  # Funktioniert ohne Email!
    papers = client.search("DevOps Governance", limit=20)

Enhanced-Modus:
    client = CrossRefClient(email="your@email.com")
    papers = client.search("DevOps Governance", limit=20)
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from src.utils.rate_limiter import RateLimiter
from src.utils.retry import RateLimitError, ServerError, raise_for_status_with_retry

# Setup Logging
logger = logging.getLogger(__name__)


# ============================================
# Data Models
# ============================================

class Paper:
    """Paper Data Model"""

    def __init__(
        self,
        doi: str,
        title: str,
        authors: List[str],
        year: Optional[int] = None,
        abstract: Optional[str] = None,
        venue: Optional[str] = None,
        source_api: str = "crossref",
        url: Optional[str] = None,
        citations: Optional[int] = None,
        raw_data: Optional[Dict[str, Any]] = None
    ):
        self.doi = doi
        self.title = title
        self.authors = authors
        self.year = year
        self.abstract = abstract
        self.venue = venue
        self.source_api = source_api
        self.url = url
        self.citations = citations
        self.raw_data = raw_data or {}

    def __repr__(self):
        return f"Paper(doi='{self.doi}', title='{self.title[:50]}...', year={self.year})"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "doi": self.doi,
            "title": self.title,
            "authors": self.authors,
            "year": self.year,
            "abstract": self.abstract,
            "venue": self.venue,
            "source_api": self.source_api,
            "url": self.url,
            "citations": self.citations
        }


# ============================================
# CrossRef API Client
# ============================================

class CrossRefClient:
    """
    CrossRef API Client

    Funktioniert OHNE API-Key (Anonymous Access)!
    Optional: Email für "polite" User-Agent Header

    Usage:
        # Standard-Modus (Anonymous)
        client = CrossRefClient()
        papers = client.search("machine learning ethics", limit=20)

        # Enhanced-Modus (mit Email)
        client = CrossRefClient(email="your@email.com")
        papers = client.search("machine learning ethics", limit=20)
    """

    BASE_URL = "https://api.crossref.org"

    def __init__(
        self,
        email: Optional[str] = None,
        rate_limit: float = 50.0,  # 50 req/s (Standard + Enhanced gleich)
        timeout: int = 30
    ):
        """
        Initialize CrossRef Client

        Args:
            email: Optional email for polite User-Agent (empfohlen aber nicht erforderlich)
            rate_limit: Requests per second (default: 50)
            timeout: Request timeout in seconds (default: 30)
        """
        self.email = email
        self.timeout = timeout

        # Rate Limiter (50 req/s)
        self.rate_limiter = RateLimiter(requests_per_second=rate_limit)

        # HTTP Client
        headers = {
            "User-Agent": self._build_user_agent(),
            "Accept": "application/json"
        }
        self.client = httpx.Client(headers=headers, timeout=timeout)

        logger.info(f"CrossRef Client initialized (email={'set' if email else 'anonymous'})")

    def _build_user_agent(self) -> str:
        """Build User-Agent header"""
        base = "AcademicAgentV2/1.0"
        if self.email:
            # "Polite" User-Agent mit Email (empfohlen)
            return f"{base} (mailto:{self.email})"
        else:
            # Anonymous User-Agent
            return base

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
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Paper]:
        """
        Search CrossRef API

        Args:
            query: Search query (supports Boolean: AND, OR, NOT)
            limit: Max results (default: 20, max: 1000)
            filters: Optional filters (e.g., {"type": "journal-article", "from-pub-date": "2020"})

        Returns:
            List of Paper objects

        Example:
            papers = client.search("DevOps AND governance", limit=15)
            papers = client.search(
                "machine learning",
                limit=20,
                filters={"type": "journal-article", "from-pub-date": "2020"}
            )
        """
        # Rate Limiting
        self.rate_limiter.acquire()

        # Build Request
        params = {
            "query": query,
            "rows": min(limit, 1000),  # CrossRef max: 1000
            "select": "DOI,title,author,published,abstract,container-title,URL,is-referenced-by-count"
        }

        # Apply Filters
        if filters:
            params.update(filters)

        logger.debug(f"CrossRef search: query='{query}', limit={limit}")

        try:
            # API Call
            response = self.client.get(f"{self.BASE_URL}/works", params=params)
            raise_for_status_with_retry(response)

            data = response.json()

            # Parse Results
            items = data.get("message", {}).get("items", [])
            papers = [self._parse_work(work) for work in items if work.get("DOI")]

            logger.info(f"CrossRef found {len(papers)} papers for query: '{query}'")
            return papers[:limit]  # Ensure limit

        except httpx.TimeoutException as e:
            logger.error(f"CrossRef timeout: {e}")
            return []
        except Exception as e:
            logger.error(f"CrossRef search failed: {e}")
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
        doi = doi.strip().lower()

        logger.debug(f"CrossRef get_by_doi: {doi}")

        try:
            response = self.client.get(f"{self.BASE_URL}/works/{doi}")

            if response.status_code == 404:
                logger.warning(f"DOI not found: {doi}")
                return None

            raise_for_status_with_retry(response)

            work = response.json().get("message", {})
            return self._parse_work(work)

        except Exception as e:
            logger.error(f"CrossRef get_by_doi failed: {e}")
            return None

    def _parse_work(self, work: Dict[str, Any]) -> Paper:
        """
        Parse CrossRef work item to Paper object

        Args:
            work: CrossRef work JSON object

        Returns:
            Paper object
        """
        # DOI (required)
        doi = work.get("DOI", "")

        # Title
        title_list = work.get("title", [])
        title = title_list[0] if title_list else "Untitled"

        # Authors
        authors = []
        for author in work.get("author", []):
            given = author.get("given", "")
            family = author.get("family", "")
            if family:
                authors.append(f"{given} {family}".strip())

        # Year
        year = None
        published = work.get("published", {})
        if "date-parts" in published and published["date-parts"]:
            date_parts = published["date-parts"][0]
            if date_parts:
                year = date_parts[0]

        # Abstract (often missing in CrossRef)
        abstract = work.get("abstract", None)
        if abstract:
            # CrossRef abstracts are often XML-encoded, strip tags
            abstract = self._strip_xml_tags(abstract)

        # Venue (Journal/Conference)
        venue_list = work.get("container-title", [])
        venue = venue_list[0] if venue_list else None

        # URL
        url = work.get("URL", None)

        # Citations (is-referenced-by-count)
        citations = work.get("is-referenced-by-count", 0)

        return Paper(
            doi=doi,
            title=title,
            authors=authors,
            year=year,
            abstract=abstract,
            venue=venue,
            source_api="crossref",
            url=url,
            citations=citations,
            raw_data=work
        )

    def _strip_xml_tags(self, text: str) -> str:
        """Strip XML/HTML tags from text"""
        import re
        return re.sub(r'<[^>]+>', '', text)

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

def search_crossref(
    query: str,
    limit: int = 20,
    email: Optional[str] = None
) -> List[Paper]:
    """
    Convenience function for quick searches

    Args:
        query: Search query
        limit: Max results
        email: Optional email for polite mode

    Returns:
        List of Paper objects

    Example:
        papers = search_crossref("DevOps Governance", limit=15)
    """
    with CrossRefClient(email=email) as client:
        return client.search(query, limit=limit)


# ============================================
# CLI Test
# ============================================

if __name__ == "__main__":
    """
    Test CrossRef Client

    Run:
        python -m src.search.crossref_client
    """
    print("Testing CrossRef API Client...")

    # Test 1: Anonymous Access
    print("\n1. Testing Anonymous Access (no email)...")
    client = CrossRefClient()
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

    # Test 2: Get by DOI
    print("\n2. Testing get_by_doi()...")
    if papers:
        paper = client.get_by_doi(papers[0].doi)
        if paper:
            print(f"✅ Retrieved paper: {paper.title[:50]}...")

    # Test 3: Context Manager
    print("\n3. Testing context manager...")
    with CrossRefClient() as client:
        papers = client.search("machine learning ethics", limit=3)
        print(f"✅ Found {len(papers)} papers via context manager")

    print("\n✅ All tests passed!")
