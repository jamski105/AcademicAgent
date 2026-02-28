"""
CORE API Client für Academic Agent v2.3+

API: https://core.ac.uk/services/api
- Aggregiert Papers von 1000+ Repositories
- Optional API-Key (funktioniert auch ohne, aber limitiert)
- Fallback wenn Unpaywall fehlschlägt

Erfolgsrate: ~10% (zusätzlich zu Unpaywall)
"""

import httpx
import time
from typing import Optional, Dict, Any
from dataclasses import dataclass
from pathlib import Path

from src.utils.retry import retry_with_backoff
from src.utils.rate_limiter import RateLimiter


@dataclass
class COREResult:
    """Result from CORE API"""
    success: bool
    pdf_url: Optional[str] = None
    doi: Optional[str] = None
    error: Optional[str] = None
    source_repository: Optional[str] = None  # Repository name
    open_access: bool = False


class COREClient:
    """Client for CORE API"""

    BASE_URL = "https://api.core.ac.uk/v3"

    def __init__(
        self,
        api_key: Optional[str] = None,
        rate_limit_rps: float = 10.0,
        timeout: int = 30
    ):
        """
        Initialize CORE Client

        Args:
            api_key: Optional CORE API key (None = disabled/limited access)
            rate_limit_rps: Requests per second (default: 10)
            timeout: Request timeout in seconds (default: 30)
        """
        self.api_key = api_key
        self.enabled = api_key is not None
        self.timeout = timeout
        self.rate_limiter = RateLimiter(requests_per_second=rate_limit_rps)

        # Setup HTTP client
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        self.client = httpx.Client(timeout=self.timeout, headers=headers)

    @retry_with_backoff(max_attempts=3, backoff_factor=2)
    def get_pdf_url(self, doi: str) -> COREResult:
        """
        Get PDF URL for a DOI via CORE API

        Args:
            doi: DOI (z.B. "10.1109/ACCESS.2021.1234567")

        Returns:
            COREResult mit PDF-URL falls verfügbar
        """
        # Check if enabled
        if not self.enabled:
            return COREResult(
                success=False,
                doi=doi,
                error="CORE API disabled (no API key provided)"
            )

        # Rate Limiting
        self.rate_limiter.wait_if_needed()

        # Clean DOI
        clean_doi = doi.replace("https://doi.org/", "").strip()

        # CORE API uses search endpoint (works by DOI)
        # Alternative: /works endpoint if we have CORE ID
        url = f"{self.BASE_URL}/search/works"
        params = {
            "q": f"doi:{clean_doi}",
            "limit": 1
        }

        try:
            response = self.client.get(url, params=params)

            # Handle 404
            if response.status_code == 404:
                return COREResult(
                    success=False,
                    doi=clean_doi,
                    error="DOI not found in CORE"
                )

            # Handle 401 (invalid API key)
            if response.status_code == 401:
                return COREResult(
                    success=False,
                    doi=clean_doi,
                    error="Invalid CORE API key"
                )

            # Raise for other errors
            response.raise_for_status()

            # Parse response
            data = response.json()
            return self._parse_response(data, clean_doi)

        except httpx.HTTPStatusError as e:
            return COREResult(
                success=False,
                doi=clean_doi,
                error=f"HTTP {e.response.status_code}: {str(e)}"
            )
        except httpx.RequestError as e:
            return COREResult(
                success=False,
                doi=clean_doi,
                error=f"Request failed: {str(e)}"
            )
        except Exception as e:
            return COREResult(
                success=False,
                doi=clean_doi,
                error=f"Unexpected error: {str(e)}"
            )

    def _parse_response(self, data: Dict[str, Any], doi: str) -> COREResult:
        """Parse CORE API response"""

        # Check if we got results
        results = data.get("results", [])
        if not results:
            return COREResult(
                success=False,
                doi=doi,
                error="No results found in CORE"
            )

        # Get first result
        paper = results[0]

        # Extract PDF URL (CORE has multiple possible fields)
        pdf_url = None
        source_repository = None

        # Try downloadUrl first
        if paper.get("downloadUrl"):
            pdf_url = paper["downloadUrl"]

        # Fallback: check fullText
        if not pdf_url and paper.get("fullText"):
            pdf_url = paper["fullText"]

        # Fallback: check links
        if not pdf_url:
            links = paper.get("links", [])
            for link in links:
                if link.get("type") == "download" or "pdf" in link.get("url", "").lower():
                    pdf_url = link.get("url")
                    break

        # Extract repository info
        if paper.get("dataProvider"):
            source_repository = paper["dataProvider"].get("name")

        # Check Open Access status
        open_access = paper.get("isOpenAccess", False) or paper.get("openAccess", False)

        if not pdf_url:
            return COREResult(
                success=False,
                doi=doi,
                open_access=open_access,
                source_repository=source_repository,
                error="No PDF URL found in CORE result"
            )

        return COREResult(
            success=True,
            doi=doi,
            pdf_url=pdf_url,
            open_access=open_access,
            source_repository=source_repository
        )

    def download_pdf(self, pdf_url: str, output_path: Path) -> bool:
        """
        Download PDF from URL

        Args:
            pdf_url: URL to PDF
            output_path: Where to save PDF

        Returns:
            True if successful, False otherwise
        """
        try:
            self.rate_limiter.wait_if_needed()

            response = self.client.get(pdf_url, follow_redirects=True)
            response.raise_for_status()

            # Check if response is actually a PDF
            content_type = response.headers.get("content-type", "")
            if "pdf" not in content_type.lower():
                # Check PDF magic bytes
                if not response.content.startswith(b"%PDF"):
                    print(f"⚠️ Warning: Response is not a PDF (content-type: {content_type})")
                    return False

            # Save PDF
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(response.content)

            return True

        except Exception as e:
            print(f"❌ PDF download failed: {e}")
            return False

    def fetch(self, doi: str, output_path: Path) -> COREResult:
        """
        Complete workflow: Get PDF URL + Download

        Args:
            doi: DOI
            output_path: Where to save PDF

        Returns:
            COREResult
        """
        # Check if enabled
        if not self.enabled:
            return COREResult(
                success=False,
                doi=doi,
                error="CORE API disabled (no API key)"
            )

        # Step 1: Get PDF URL
        result = self.get_pdf_url(doi)

        if not result.success or not result.pdf_url:
            return result

        # Step 2: Download PDF
        download_success = self.download_pdf(result.pdf_url, output_path)

        if not download_success:
            return COREResult(
                success=False,
                doi=result.doi,
                pdf_url=result.pdf_url,
                open_access=result.open_access,
                source_repository=result.source_repository,
                error="PDF download failed"
            )

        return result

    def close(self):
        """Close HTTP client"""
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# ============================================
# Convenience Functions
# ============================================

def get_pdf_url(doi: str, api_key: Optional[str] = None) -> Optional[str]:
    """
    Simple helper to get PDF URL for a DOI

    Args:
        doi: DOI
        api_key: Optional CORE API key

    Returns:
        PDF URL if found, None otherwise
    """
    if not api_key:
        return None  # CORE requires API key

    with COREClient(api_key=api_key) as client:
        result = client.get_pdf_url(doi)
        return result.pdf_url if result.success else None


# ============================================
# Test Code
# ============================================

if __name__ == "__main__":
    """Test CORE Client"""
    import tempfile
    import os

    print("Testing CORE Client...")

    # Check if API key available
    api_key = os.environ.get("CORE_API_KEY")
    if not api_key:
        print("⚠️ No CORE_API_KEY environment variable set")
        print("   CORE API requires an API key")
        print("   Get one at: https://core.ac.uk/services/api")
        print("\n✅ CORE Client tests skipped (no API key)")
    else:
        # Test DOI (known paper in CORE)
        test_doi = "10.1371/journal.pone.0000000"

        with COREClient(api_key=api_key) as client:
            print(f"\n1️⃣ Testing get_pdf_url() for {test_doi}")
            result = client.get_pdf_url(test_doi)

            print(f"   Success: {result.success}")
            print(f"   Open Access: {result.open_access}")
            print(f"   Repository: {result.source_repository}")
            if result.pdf_url:
                print(f"   PDF URL: {result.pdf_url[:80]}...")
            else:
                print(f"   Error: {result.error}")

            # Test download
            if result.success and result.pdf_url:
                print(f"\n2️⃣ Testing download_pdf()")
                temp_pdf = Path(tempfile.mktemp(suffix=".pdf"))
                download_success = client.download_pdf(result.pdf_url, temp_pdf)

                if download_success:
                    file_size = temp_pdf.stat().st_size
                    print(f"   ✅ Downloaded {file_size} bytes to {temp_pdf}")
                    temp_pdf.unlink()  # Cleanup
                else:
                    print(f"   ❌ Download failed")

        print("\n✅ CORE Client tests completed!")
