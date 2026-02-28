"""
Unpaywall API Client für Academic Agent v2.3+

API: https://unpaywall.org/products/api
- Kostenlos, kein API-Key nötig (nur Email)
- Gibt PDF-URLs für Open Access Papers
- Response: {"oa_locations": [{"url_for_pdf": "..."}]}

Erfolgsrate: ~40% (Open Access Papers)
"""

import httpx
import time
from typing import Optional, Dict, Any
from dataclasses import dataclass
from pathlib import Path

from src.utils.retry import retry_with_backoff
from src.utils.rate_limiter import RateLimiter


@dataclass
class UnpaywallResult:
    """Result from Unpaywall API"""
    success: bool
    pdf_url: Optional[str] = None
    doi: Optional[str] = None
    error: Optional[str] = None
    is_oa: bool = False  # Is Open Access?
    oa_status: Optional[str] = None  # gold, green, hybrid, bronze, closed


class UnpaywallClient:
    """Client for Unpaywall API"""

    BASE_URL = "https://api.unpaywall.org/v2"
    DEFAULT_EMAIL = "research@academic-agent.org"  # Generic Email für Standard-Modus (polite pool)

    def __init__(
        self,
        email: Optional[str] = None,
        rate_limit_rps: float = 10.0,
        timeout: int = 30
    ):
        """
        Initialize Unpaywall Client

        Args:
            email: Optional email (für "polite" requests). None = Generic Email
            rate_limit_rps: Requests per second (default: 10)
            timeout: Request timeout in seconds (default: 30)
        """
        self.email = email or self.DEFAULT_EMAIL
        self.timeout = timeout
        self.rate_limiter = RateLimiter(requests_per_second=rate_limit_rps)
        self.client = httpx.Client(timeout=self.timeout)

    @retry_with_backoff(max_attempts=3, backoff_factor=2)
    def get_pdf_url(self, doi: str) -> UnpaywallResult:
        """
        Get PDF URL for a DOI via Unpaywall API

        Args:
            doi: DOI (z.B. "10.1109/ACCESS.2021.1234567")

        Returns:
            UnpaywallResult mit PDF-URL falls verfügbar
        """
        # Rate Limiting
        self.rate_limiter.wait_if_needed()

        # Clean DOI - strip whitespace and URL-decode first
        from urllib.parse import unquote
        clean_doi = unquote(doi.strip())

        # Handle doi: / DOI: prefix (common in bibliographic software)
        for prefix in ("DOI:", "doi:", "DOI: ", "doi: "):
            if clean_doi.startswith(prefix):
                clean_doi = clean_doi[len(prefix):].strip()
                break

        # Remove doi.org URL prefixes
        for prefix in ("https://doi.org/", "http://doi.org/", "doi.org/"):
            if clean_doi.startswith(prefix):
                clean_doi = clean_doi[len(prefix):]
                break

        # Strip URL query params (?key=val) and fragments (#section) — both cause HTTP 422
        for delimiter in ("?", "#"):
            if delimiter in clean_doi:
                clean_doi = clean_doi.split(delimiter)[0]

        clean_doi = clean_doi.strip()

        # Validate DOI format (must start with "10.")
        if not clean_doi or not clean_doi.startswith("10."):
            return UnpaywallResult(
                success=False,
                doi=clean_doi,
                error=f"Invalid DOI format: '{clean_doi}' (must start with '10.')"
            )

        # Build URL
        url = f"{self.BASE_URL}/{clean_doi}"
        params = {"email": self.email}

        try:
            response = self.client.get(url, params=params)

            # Handle 404 (DOI not found in Unpaywall)
            if response.status_code == 404:
                return UnpaywallResult(
                    success=False,
                    doi=clean_doi,
                    error="DOI not found in Unpaywall (likely not Open Access)"
                )

            # Handle 422 (invalid DOI format - Unprocessable Entity)
            if response.status_code == 422:
                return UnpaywallResult(
                    success=False,
                    doi=clean_doi,
                    error=f"Unpaywall rejected DOI (HTTP 422 - invalid format): '{clean_doi}'"
                )

            # Raise for other errors
            response.raise_for_status()

            # Parse response
            data = response.json()
            return self._parse_response(data, clean_doi)

        except httpx.HTTPStatusError as e:
            return UnpaywallResult(
                success=False,
                doi=clean_doi,
                error=f"HTTP {e.response.status_code}: {str(e)}"
            )
        except httpx.RequestError as e:
            return UnpaywallResult(
                success=False,
                doi=clean_doi,
                error=f"Request failed: {str(e)}"
            )
        except Exception as e:
            return UnpaywallResult(
                success=False,
                doi=clean_doi,
                error=f"Unexpected error: {str(e)}"
            )

    def _parse_response(self, data: Dict[str, Any], doi: str) -> UnpaywallResult:
        """Parse Unpaywall API response"""

        # Check if Open Access
        is_oa = data.get("is_oa", False)
        oa_status = data.get("oa_status", "closed")

        if not is_oa:
            return UnpaywallResult(
                success=False,
                doi=doi,
                is_oa=False,
                oa_status=oa_status,
                error=f"Paper is not Open Access (status: {oa_status})"
            )

        # Get best OA location (prioritize published version)
        best_location = data.get("best_oa_location")
        if not best_location:
            # Fallback: check oa_locations array
            oa_locations = data.get("oa_locations", [])
            if oa_locations:
                best_location = oa_locations[0]

        if not best_location:
            return UnpaywallResult(
                success=False,
                doi=doi,
                is_oa=True,
                oa_status=oa_status,
                error="No OA location found despite is_oa=True"
            )

        # Extract PDF URL
        pdf_url = best_location.get("url_for_pdf")
        if not pdf_url:
            # Try url_for_landing_page as fallback
            pdf_url = best_location.get("url")

        if not pdf_url:
            return UnpaywallResult(
                success=False,
                doi=doi,
                is_oa=True,
                oa_status=oa_status,
                error="No PDF URL in OA location"
            )

        return UnpaywallResult(
            success=True,
            doi=doi,
            pdf_url=pdf_url,
            is_oa=True,
            oa_status=oa_status
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
                # Sometimes servers don't set content-type correctly
                # Check if content starts with PDF magic bytes
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

    def fetch(self, doi: str, output_path: Path) -> UnpaywallResult:
        """
        Complete workflow: Get PDF URL + Download

        Args:
            doi: DOI
            output_path: Where to save PDF

        Returns:
            UnpaywallResult
        """
        # Step 1: Get PDF URL
        result = self.get_pdf_url(doi)

        if not result.success or not result.pdf_url:
            return result

        # Step 2: Download PDF
        download_success = self.download_pdf(result.pdf_url, output_path)

        if not download_success:
            return UnpaywallResult(
                success=False,
                doi=result.doi,
                pdf_url=result.pdf_url,
                is_oa=result.is_oa,
                oa_status=result.oa_status,
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

def get_pdf_url(doi: str, email: Optional[str] = None) -> Optional[str]:
    """
    Simple helper to get PDF URL for a DOI

    Args:
        doi: DOI
        email: Optional email

    Returns:
        PDF URL if found, None otherwise
    """
    with UnpaywallClient(email=email) as client:
        result = client.get_pdf_url(doi)
        return result.pdf_url if result.success else None


# ============================================
# Test Code
# ============================================

if __name__ == "__main__":
    """Test Unpaywall Client"""
    import tempfile

    print("Testing Unpaywall Client...")

    # Test DOI (known Open Access paper)
    test_doi = "10.1371/journal.pone.0000000"  # PLoS ONE (always OA)

    with UnpaywallClient() as client:
        print(f"\n1️⃣ Testing get_pdf_url() for {test_doi}")
        result = client.get_pdf_url(test_doi)

        print(f"   Success: {result.success}")
        print(f"   Is OA: {result.is_oa}")
        print(f"   OA Status: {result.oa_status}")
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

    print("\n✅ Unpaywall Client tests completed!")
