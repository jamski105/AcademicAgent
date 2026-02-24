#!/usr/bin/env python3
"""
Phase 4: Manual retry for failed downloads with PDF URL extraction
"""

import json
import time
import requests
from pathlib import Path
from playwright.sync_api import sync_playwright

RUN_DIR = Path("/Users/jonas/Desktop/AcademicAgent/runs/run_20260223_095905")
PDF_DIR = RUN_DIR / "pdfs"
DOWNLOADS_LOG = RUN_DIR / "downloads" / "downloads.json"
CDP_URL = "http://localhost:9222"

# Failed papers to retry
FAILED_PAPERS = [
    {
        "id": "C001",
        "url": "https://oscarpubhouse.com/index.php/sdlijmef/article/view/637",
        "filename": "Whitcombe_2026_Data_Driven_Change_Control.pdf",
        "strategy": "Extract PDF link from article page"
    },
    {
        "id": "C004",
        "url": "https://ijite.jredu.id/index.php/ijite/article/view/260",
        "filename": "Batmetan_2025_Agile_IT_Governance_for_Sustainable_Digital_Transf.pdf",
        "strategy": "Extract PDF link from article page"
    }
]

def try_extract_pdf_url(page, article_url):
    """Navigate to article and extract actual PDF URL."""
    try:
        print(f"  Loading article page...")
        page.goto(article_url, timeout=60000, wait_until="domcontentloaded")
        page.wait_for_timeout(3000)

        # Look for PDF links
        pdf_links = page.evaluate("""() => {
            const links = [];
            document.querySelectorAll('a').forEach(a => {
                const href = a.getAttribute('href');
                const text = a.textContent.toLowerCase();
                if (href && (href.includes('.pdf') || text.includes('pdf') || text.includes('download'))) {
                    links.push({
                        href: href,
                        text: a.textContent.trim()
                    });
                }
            });
            return links;
        }""")

        print(f"  Found {len(pdf_links)} potential PDF links:")
        for i, link in enumerate(pdf_links[:5]):  # Show first 5
            print(f"    {i+1}. {link['text'][:40]} -> {link['href'][:60]}")

        # Try to find the most likely PDF link
        for link in pdf_links:
            href = link['href']
            # Make absolute URL if relative
            if href.startswith('/'):
                from urllib.parse import urljoin
                href = urljoin(article_url, href)
            elif not href.startswith('http'):
                continue

            if '.pdf' in href or '/pdf' in href.lower():
                print(f"  Candidate PDF URL: {href}")
                return href

        return None

    except Exception as e:
        print(f"  Error: {e}")
        return None

def download_with_pdf_url(pdf_url, output_path):
    """Download PDF from extracted URL."""
    try:
        print(f"  Downloading: {pdf_url}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Referer': pdf_url.rsplit('/', 2)[0]  # Use domain as referer
        }
        response = requests.get(pdf_url, headers=headers, timeout=60, allow_redirects=True)

        if response.status_code == 200 and len(response.content) > 1000:
            with open(output_path, 'wb') as f:
                f.write(response.content)
            print(f"  SUCCESS: {len(response.content) / 1024:.1f} KB")
            return True
        else:
            print(f"  Failed: HTTP {response.status_code}")
            return False

    except Exception as e:
        print(f"  Error: {e}")
        return False

def main():
    print("="*80)
    print("RETRY FAILED DOWNLOADS")
    print("="*80)

    successful = 0

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(CDP_URL)
        context = browser.contexts[0] if browser.contexts else browser.new_context()
        page = context.new_page()

        for paper in FAILED_PAPERS:
            print(f"\n{paper['id']}: {paper['url'][:60]}...")
            output_path = PDF_DIR / paper['filename']

            # Skip if already downloaded
            if output_path.exists():
                print("  Already exists, skipping")
                continue

            # Try to extract PDF URL
            pdf_url = try_extract_pdf_url(page, paper['url'])

            if pdf_url:
                if download_with_pdf_url(pdf_url, output_path):
                    successful += 1
            else:
                print("  No PDF URL found")

            time.sleep(2)

        page.close()

    print(f"\n{'='*80}")
    print(f"Retry complete: {successful} additional PDFs downloaded")
    print(f"{'='*80}")

if __name__ == "__main__":
    main()
