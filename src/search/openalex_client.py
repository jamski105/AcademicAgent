"""
OpenAlex API Client für Academic Agent v2.0

OpenAlex API Documentation: https://docs.openalex.org/

Features:
- Anonymous Access (100 req/Tag, KEIN Key nötig!)
- Optional: Email für unbegrenzte Requests (EMPFOHLEN!)
- Rate Limiting: 1 req/s (anonym) oder 10 req/s (mit Email)
- Citation-Counts included (für 5D-Scoring!)
- 250M+ Works verfügbar

Standard-Modus (Anonymous):
    client = OpenAlexClient()  # 100 req/Tag
    papers = client.search("DevOps Governance", limit=20)

Enhanced-Modus (Empfohlen!):
    client = OpenAlexClient(email="your@email.com")  # Unbegrenzt!
    papers = client.search("DevOps Governance", limit=20)
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from src.utils.rate_limiter import RateLimiter
from src.utils.retry import RateLimitError, ServerError, raise_for_status_with_retry
from src.search.crossref_client import Paper  # Reuse Paper model

# Setup Logging
logger = logging.getLogger(__name__)


# ============================================
# OpenAlex API Client
# ============================================

class OpenAlexClient:
    """
    OpenAlex API Client

    Funktioniert OHNE Email (100 req/Tag)
    EMPFOHLEN: Email für unbegrenzte Requests!

    Usage:
        # Standard-Modus (Anonymous - 100 req/Tag)
        client = OpenAlexClient()
        papers = client.search("machine learning ethics", limit=20)

        # Enhanced-Modus (mit Email - UNBEGRENZT!)
        client = OpenAlexClient(email="your@email.com")
        papers = client.search("machine learning ethics", limit=20)
    """

    BASE_URL = "https://api.openalex.org"

    def __init__(
        self,
        email: Optional[str] = None,
        timeout: int = 30
    ):
        """
        Initialize OpenAlex Client

        Args:
            email: Optional email for unlimited requests (EMPFOHLEN!)
            timeout: Request timeout in seconds (default: 30)
        """
        self.email = email
        self.timeout = timeout

        # Rate Limiter
        # Anonymous: 1 req/s + 100 daily limit
        # With Email: 10 req/s, unbegrenzt
        if email:
            self.rate_limiter = RateLimiter(requests_per_second=10)
            logger.info(f"OpenAlex Client: Enhanced Mode (email set, unlimited requests)")
        else:
            self.rate_limiter = RateLimiter(requests_per_second=1, daily_limit=100)
            logger.info(f"OpenAlex Client: Standard Mode (anonymous, 100 req/day)")

        # HTTP Client
        headers = {
            "User-Agent": self._build_user_agent(),
            "Accept": "application/json"
        }
        self.client = httpx.Client(headers=headers, timeout=timeout)

    def _build_user_agent(self) -> str:
        """Build User-Agent header"""
        base = "AcademicAgentV2/1.0"
        if self.email:
            return f"{base} (mailto:{self.email})"
        else:
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
        Search OpenAlex API

        Args:
            query: Search query (supports boolean: AND, OR, NOT)
            limit: Max results (default: 20, max: 200 per page)
            filters: Optional filters (e.g., {"type": "article", "from_publication_date": "2020-01-01"})

        Returns:
            List of Paper objects

        Example:
            papers = client.search("DevOps AND governance", limit=15)
            papers = client.search(
                "machine learning",
                limit=20,
                filters={"type": "article", "from_publication_date": "2020-01-01"}
            )
        """
        # Rate Limiting
        self.rate_limiter.acquire()

        # Build Request
        params = {
            "search": query,
            "per-page": min(limit, 200),  # OpenAlex max: 200
            "select": "id,doi,title,authorships,publication_year,abstract_inverted_index,primary_location,cited_by_count"
        }

        # Apply Filters
        if filters:
            # Convert filters to OpenAlex filter syntax
            filter_parts = []
            for key, value in filters.items():
                filter_parts.append(f"{key}:{value}")
            if filter_parts:
                params["filter"] = ",".join(filter_parts)

        logger.debug(f"OpenAlex search: query='{query}', limit={limit}")

        try:
            # API Call
            response = self.client.get(f"{self.BASE_URL}/works", params=params)
            raise_for_status_with_retry(response)

            data = response.json()

            # Parse Results
            results = data.get("results", [])
            papers = []
            for work in results:
                paper = self._parse_work(work)
                if paper and paper.doi:  # Only include if DOI exists
                    papers.append(paper)

            logger.info(f"OpenAlex found {len(papers)} papers for query: '{query}'")
            return papers[:limit]  # Ensure limit

        except httpx.TimeoutException as e:
            logger.error(f"OpenAlex timeout: {e}")
            return []
        except Exception as e:
            logger.error(f"OpenAlex search failed: {e}")
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
        doi_url = f"https://doi.org/{doi}"

        logger.debug(f"OpenAlex get_by_doi: {doi}")

        try:
            response = self.client.get(f"{self.BASE_URL}/works/{doi_url}")

            if response.status_code == 404:
                logger.warning(f"DOI not found: {doi}")
                return None

            raise_for_status_with_retry(response)

            work = response.json()
            return self._parse_work(work)

        except Exception as e:
            logger.error(f"OpenAlex get_by_doi failed: {e}")
            return None

    def _parse_work(self, work: Dict[str, Any]) -> Optional[Paper]:
        """
        Parse OpenAlex work item to Paper object

        Args:
            work: OpenAlex work JSON object

        Returns:
            Paper object or None if DOI missing
        """
        # DOI (required)
        doi = work.get("doi", "")
        if doi:
            # Remove "https://doi.org/" prefix
            doi = doi.replace("https://doi.org/", "")
        else:
            return None  # Skip papers without DOI

        # Title
        title = work.get("title", "Untitled")
        if not title:
            title = "Untitled"

        # Authors
        authors = []
        for authorship in work.get("authorships", []):
            author_data = authorship.get("author", {})
            display_name = author_data.get("display_name", "")
            if display_name:
                authors.append(display_name)

        # Year
        year = work.get("publication_year", None)

        # Abstract (inverted index format)
        abstract = self._reconstruct_abstract(work.get("abstract_inverted_index", None))

        # Venue (primary_location)
        venue = None
        primary_location = work.get("primary_location", {})
        if primary_location:
            source = primary_location.get("source", {})
            venue = source.get("display_name", None)

        # URL
        url = work.get("id", None)  # OpenAlex ID URL

        # Citations
        citations = work.get("cited_by_count", 0)

        return Paper(
            doi=doi,
            title=title,
            authors=authors,
            year=year,
            abstract=abstract,
            venue=venue,
            source_api="openalex",
            url=url,
            citations=citations,
            raw_data=work
        )

    def _reconstruct_abstract(self, inverted_index: Optional[Dict[str, List[int]]]) -> Optional[str]:
        """
        Reconstruct abstract from inverted index

        OpenAlex stores abstracts as inverted index:
        {"This": [0], "is": [1], "abstract": [2]}
        → "This is abstract"

        Args:
            inverted_index: Dict mapping words to positions

        Returns:
            Reconstructed abstract text or None
        """
        if not inverted_index:
            return None

        try:
            # Create position -> word mapping
            word_positions = []
            for word, positions in inverted_index.items():
                for pos in positions:
                    word_positions.append((pos, word))

            # Sort by position
            word_positions.sort(key=lambda x: x[0])

            # Join words
            abstract = " ".join(word for _, word in word_positions)

            # Truncate if too long
            if len(abstract) > 5000:
                abstract = abstract[:5000] + "..."

            return abstract

        except Exception as e:
            logger.warning(f"Failed to reconstruct abstract: {e}")
            return None

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

def search_openalex(
    query: str,
    limit: int = 20,
    email: Optional[str] = None
) -> List[Paper]:
    """
    Convenience function for quick searches

    Args:
        query: Search query
        limit: Max results
        email: Optional email for unlimited requests

    Returns:
        List of Paper objects

    Example:
        papers = search_openalex("DevOps Governance", limit=15, email="your@email.com")
    """
    with OpenAlexClient(email=email) as client:
        return client.search(query, limit=limit)


# ============================================
# CLI Test
# ============================================

if __name__ == "__main__":
    """
    Test OpenAlex Client

    Run:
        python -m src.search.openalex_client
    """
    print("Testing OpenAlex API Client...")

    # Test 1: Anonymous Access
    print("\n1. Testing Anonymous Access (100 req/day)...")
    client = OpenAlexClient()
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
    with OpenAlexClient() as client:
        papers = client.search("machine learning ethics", limit=3)
        print(f"✅ Found {len(papers)} papers via context manager")

    # Test 4: With Email (Enhanced Mode)
    print("\n4. Testing Enhanced Mode (with email)...")
    print("   (Set email to test unlimited requests)")
    print("   client = OpenAlexClient(email='your@email.com')")

    print("\n✅ All tests passed!")
    print("\n💡 TIP: Set email for unlimited requests!")
    print("   OpenAlexClient(email='your@email.com')")
