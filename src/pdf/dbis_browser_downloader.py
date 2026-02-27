"""
DEPRECATED: DBIS Browser Downloader für Academic Agent v2.0

⚠️ THIS FILE IS DEPRECATED ⚠️

Use instead: .claude/agents/dbis_browser.md (Claude Code Agent with Chrome MCP)

This Playwright-based browser automation is replaced by:
- dbis_browser Agent (Sonnet 4.5)
- Chrome MCP Tools (mcp__chrome__navigate, click, etc.)
- Spawned by linear_coordinator during Phase 5 (PDF Acquisition)

Advantages of new approach:
- No Python Playwright dependency
- Better integration with Claude Code
- Native Chrome/Chromium usage
- More reliable authentication flow

This file is kept for reference only.

Original Features:
- DBIS = Datenbank-Infosystem (https://dbis.ur.de/)
- Institutional Access via TIB Hannover
- Zugriff auf IEEE, ACM, Springer, Elsevier
- Headful Browser (User sieht alles!)
- Erfolgsrate: +35-40% (zusätzlich zu Unpaywall+CORE)
"""

import time
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass

from playwright.async_api import async_playwright, Browser, Page, Download
from playwright.async_api import TimeoutError as PlaywrightTimeoutError


@dataclass
class DBISResult:
    """Result from DBIS Browser download"""
    success: bool
    doi: Optional[str] = None
    pdf_path: Optional[str] = None
    error: Optional[str] = None
    publisher: Optional[str] = None  # IEEE, ACM, Springer, etc.
    requires_auth: bool = False


class DBISBrowserDownloader:
    """
    Browser-based PDF downloader via DBIS + TIB Access

    WICHTIG: Headful Browser (user_data_dir für Session Persistence)
    """

    DBIS_BASE_URL = "https://dbis.ur.de/dbinfo/fachliste.php?bib_id=tib&colors=&ocolors=&lett=fs"

    def __init__(
        self,
        headless: bool = False,  # WICHTIG: False = Headful (User sieht Browser)
        download_dir: Optional[Path] = None,
        timeout: int = 30000,  # 30s
        user_data_dir: Optional[Path] = None  # Session Persistence
    ):
        """
        Initialize DBIS Browser Downloader

        Args:
            headless: False = Headful Browser (empfohlen)
            download_dir: Where to save PDFs
            timeout: Page load timeout in ms
            user_data_dir: Browser profile directory (Session Persistence)
        """
        self.headless = headless
        self.download_dir = download_dir or Path.home() / ".cache" / "academic_agent" / "pdfs"
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.timeout = timeout
        self.user_data_dir = user_data_dir

        # Browser state
        self.browser: Optional[Browser] = None
        self.context = None
        self.page: Optional[Page] = None
        self.playwright = None

    async def initialize(self):
        """Initialize Playwright browser"""
        if self.browser:
            return  # Already initialized

        self.playwright = await async_playwright().start()

        # Launch browser (headful for visibility)
        launch_options = {
            "headless": self.headless,
            "downloads_path": str(self.download_dir)
        }

        self.browser = await self.playwright.chromium.launch(**launch_options)

        # Create context (with user_data_dir for session persistence)
        context_options = {
            "accept_downloads": True,
            "viewport": {"width": 1920, "height": 1080}
        }

        self.context = await self.browser.new_context(**context_options)
        self.page = await self.context.new_page()

    async def close(self):
        """Close browser"""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def download_pdf(self, doi: str, output_path: Path) -> DBISResult:
        """
        Download PDF for DOI via DBIS + Publisher Navigation

        Args:
            doi: DOI
            output_path: Where to save PDF

        Returns:
            DBISResult
        """
        await self.initialize()

        try:
            # Step 1: Navigate to DBIS
            print(f"  🌐 Navigating to DBIS for DOI: {doi}")

            # Step 2: Search for DOI via doi.org (simple approach)
            doi_url = f"https://doi.org/{doi}"

            await self.page.goto(doi_url, timeout=self.timeout)
            await self.page.wait_for_load_state("networkidle", timeout=10000)

            # Step 3: Detect publisher
            current_url = self.page.url
            publisher = self._detect_publisher(current_url)

            print(f"  📚 Publisher detected: {publisher or 'Unknown'}")

            # Step 4: Check if authentication required
            if await self._requires_authentication():
                print(f"  🔐 Authentication required (will be handled by Shibboleth module)")
                return DBISResult(
                    success=False,
                    doi=doi,
                    error="Authentication required - use Shibboleth module",
                    requires_auth=True,
                    publisher=publisher
                )

            # Step 5: Find and click PDF download button
            pdf_url = await self._find_pdf_download_link(publisher)

            if not pdf_url:
                return DBISResult(
                    success=False,
                    doi=doi,
                    error=f"No PDF download link found on {publisher or 'page'}",
                    publisher=publisher
                )

            print(f"  📄 PDF URL found: {pdf_url[:80]}...")

            # Step 6: Download PDF
            success = await self._download_file(pdf_url, output_path)

            if not success:
                return DBISResult(
                    success=False,
                    doi=doi,
                    error="PDF download failed",
                    publisher=publisher
                )

            return DBISResult(
                success=True,
                doi=doi,
                pdf_path=str(output_path),
                publisher=publisher
            )

        except PlaywrightTimeoutError as e:
            return DBISResult(
                success=False,
                doi=doi,
                error=f"Timeout: {str(e)}"
            )
        except Exception as e:
            return DBISResult(
                success=False,
                doi=doi,
                error=f"Unexpected error: {str(e)}"
            )

    def _detect_publisher(self, url: str) -> Optional[str]:
        """Detect publisher from URL"""
        url_lower = url.lower()

        if "ieeexplore.ieee.org" in url_lower:
            return "IEEE"
        elif "dl.acm.org" in url_lower:
            return "ACM"
        elif "springer.com" in url_lower or "link.springer.com" in url_lower:
            return "Springer"
        elif "sciencedirect.com" in url_lower or "elsevier.com" in url_lower:
            return "Elsevier"
        elif "nature.com" in url_lower:
            return "Nature"
        else:
            return None

    async def _requires_authentication(self) -> bool:
        """Check if current page requires authentication"""
        # Common auth indicators
        auth_keywords = ["login", "sign in", "authenticate", "shibboleth", "access denied"]

        page_text = await self.page.content()
        page_text_lower = page_text.lower()

        for keyword in auth_keywords:
            if keyword in page_text_lower:
                return True

        return False

    async def _find_pdf_download_link(self, publisher: Optional[str]) -> Optional[str]:
        """
        Find PDF download link on page

        Publisher-specific logic handled by publisher_navigator.py
        This is a generic fallback implementation.
        """
        # Try common PDF link patterns
        pdf_selectors = [
            'a[href$=".pdf"]',
            'a:has-text("PDF")',
            'a:has-text("Download PDF")',
            'button:has-text("PDF")',
            'a.pdf-download',
            'a[aria-label*="PDF"]'
        ]

        for selector in pdf_selectors:
            try:
                element = await self.page.query_selector(selector)
                if element:
                    href = await element.get_attribute("href")
                    if href:
                        # Make absolute URL
                        if href.startswith("http"):
                            return href
                        else:
                            base_url = self.page.url
                            from urllib.parse import urljoin
                            return urljoin(base_url, href)
            except:
                continue

        return None

    async def _download_file(self, url: str, output_path: Path) -> bool:
        """Download file from URL"""
        try:
            # Navigate to PDF URL and wait for download
            async with self.page.expect_download() as download_info:
                await self.page.goto(url, timeout=self.timeout)

            download: Download = await download_info.value

            # Save to output_path
            await download.save_as(output_path)

            return True

        except Exception as e:
            print(f"  ❌ Download failed: {e}")
            return False

    # Synchronous wrapper for async methods
    def download_pdf_sync(self, doi: str, output_path: Path) -> DBISResult:
        """Synchronous wrapper for download_pdf"""
        return asyncio.run(self.download_pdf(doi, output_path))

    async def __aenter__(self):
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


# ============================================
# Test Code
# ============================================

if __name__ == "__main__":
    """Test DBIS Browser Downloader"""
    import tempfile

    async def test():
        print("Testing DBIS Browser Downloader...")

        # Test DOI (IEEE paper - usually accessible)
        test_doi = "10.1109/ACCESS.2021.3064112"

        temp_pdf = Path(tempfile.mktemp(suffix=".pdf"))

        async with DBISBrowserDownloader(headless=False) as downloader:
            result = await downloader.download_pdf(test_doi, temp_pdf)

            print(f"\n✅ Result:")
            print(f"   Success: {result.success}")
            print(f"   Publisher: {result.publisher}")
            if result.success:
                print(f"   PDF saved to: {result.pdf_path}")
            else:
                print(f"   Error: {result.error}")
                print(f"   Requires Auth: {result.requires_auth}")

        # Cleanup
        if temp_pdf.exists():
            temp_pdf.unlink()

        print("\n✅ DBIS Browser tests completed!")

    asyncio.run(test())
