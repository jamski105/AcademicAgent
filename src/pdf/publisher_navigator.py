"""
Publisher-Specific Navigation für PDF Downloads

Unterstützte Publisher:
- IEEE Xplore
- ACM Digital Library
- Springer
- Elsevier/ScienceDirect
- Generic Fallback
"""

from typing import Optional
from playwright.async_api import Page


class PublisherNavigator:
    """Navigate different publisher websites to find PDF downloads"""

    @staticmethod
    async def find_pdf_link(page: Page, publisher: Optional[str]) -> Optional[str]:
        """
        Find PDF download link based on publisher

        Args:
            page: Playwright page
            publisher: Publisher name (IEEE, ACM, Springer, Elsevier)

        Returns:
            PDF URL if found, None otherwise
        """
        if publisher == "IEEE":
            return await PublisherNavigator._ieee_pdf_link(page)
        elif publisher == "ACM":
            return await PublisherNavigator._acm_pdf_link(page)
        elif publisher == "Springer":
            return await PublisherNavigator._springer_pdf_link(page)
        elif publisher == "Elsevier":
            return await PublisherNavigator._elsevier_pdf_link(page)
        else:
            return await PublisherNavigator._generic_pdf_link(page)

    @staticmethod
    async def _ieee_pdf_link(page: Page) -> Optional[str]:
        """Find PDF link on IEEE Xplore"""
        selectors = [
            'a:has-text("Download PDF")',
            'a.pdf-download',
            'a[href*=".pdf"]'
        ]

        for selector in selectors:
            try:
                elem = await page.query_selector(selector)
                if elem:
                    return await elem.get_attribute("href")
            except:
                continue
        return None

    @staticmethod
    async def _acm_pdf_link(page: Page) -> Optional[str]:
        """Find PDF link on ACM Digital Library"""
        selectors = [
            'a:has-text("PDF")',
            'a.pdf-link',
            'a[title*="PDF"]'
        ]

        for selector in selectors:
            try:
                elem = await page.query_selector(selector)
                if elem:
                    return await elem.get_attribute("href")
            except:
                continue
        return None

    @staticmethod
    async def _springer_pdf_link(page: Page) -> Optional[str]:
        """Find PDF link on Springer"""
        selectors = [
            'a:has-text("Download PDF")',
            'a.pdf-download',
            'a[data-track-action="download pdf"]'
        ]

        for selector in selectors:
            try:
                elem = await page.query_selector(selector)
                if elem:
                    return await elem.get_attribute("href")
            except:
                continue
        return None

    @staticmethod
    async def _elsevier_pdf_link(page: Page) -> Optional[str]:
        """Find PDF link on Elsevier/ScienceDirect"""
        selectors = [
            'a:has-text("Download PDF")',
            'a.pdf-download',
            'a[href*="pdfft"]'
        ]

        for selector in selectors:
            try:
                elem = await page.query_selector(selector)
                if elem:
                    return await elem.get_attribute("href")
            except:
                continue
        return None

    @staticmethod
    async def _generic_pdf_link(page: Page) -> Optional[str]:
        """Generic PDF link finder (fallback)"""
        selectors = [
            'a[href$=".pdf"]',
            'a:has-text("PDF")',
            'a:has-text("Download")',
            'button:has-text("PDF")'
        ]

        for selector in selectors:
            try:
                elem = await page.query_selector(selector)
                if elem:
                    href = await elem.get_attribute("href")
                    if href:
                        return href
            except:
                continue
        return None
