#!/usr/bin/env python3
"""
Phase 4: Hybrid PDF Download (HTTP + CDP Browser)
Run ID: run_20260223_095905
Date: 2026-02-23
"""

import json
import os
import sys
import time
import re
import requests
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

# Configuration
RUN_DIR = Path("/Users/jonas/Desktop/AcademicAgent/runs/run_20260223_095905")
DOWNLOAD_QUEUE = RUN_DIR / "metadata" / "download_queue.json"
PDF_DIR = RUN_DIR / "pdfs"
DOWNLOADS_DIR = RUN_DIR / "downloads"
DOWNLOADS_LOG = DOWNLOADS_DIR / "downloads.json"

CDP_URL = "http://localhost:9222"
MAX_WAIT_PER_PDF = 120
MAX_RETRIES = 2

def sanitize_filename(text):
    """Create safe filename from text."""
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '_', text)
    return text[:50]

def load_download_queue():
    """Load download queue from JSON."""
    with open(DOWNLOAD_QUEUE, 'r') as f:
        return json.load(f)

def save_download_log(downloads):
    """Save download log to JSON."""
    with open(DOWNLOADS_LOG, 'w') as f:
        json.dump({
            "run_id": "run_20260223_095905",
            "phase": "Phase 4: PDF Download",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "total_attempts": len(downloads),
            "successful_downloads": sum(1 for d in downloads if d['status'] == 'success'),
            "failed_downloads": sum(1 for d in downloads if d['status'] == 'failed'),
            "skipped_downloads": sum(1 for d in downloads if d['status'] == 'skipped'),
            "downloads": downloads
        }, f, indent=2)

def download_via_requests(url, output_path):
    """Download PDF directly via HTTP requests."""
    try:
        print(f"  HTTP GET: {url}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=60, allow_redirects=True)

        if response.status_code == 200:
            content_type = response.headers.get('content-type', '').lower()
            if 'pdf' in content_type or len(response.content) > 1000:
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                print(f"  Downloaded: {len(response.content) / 1024:.1f} KB")
                return True
            else:
                print(f"  Not a PDF (content-type: {content_type})")
                return False
        else:
            print(f"  HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"  HTTP Error: {e}")
        return False

def download_via_browser(browser, url, output_path):
    """Download PDF via browser automation."""
    try:
        print(f"  Browser navigation: {url}")

        # Get or create context with downloads enabled
        if len(browser.contexts) == 0:
            context = browser.new_context(accept_downloads=True)
        else:
            context = browser.contexts[0]

        page = context.new_page()

        # Set up download tracking
        download_completed = {'success': False}

        def handle_download(download):
            try:
                print(f"  Download event: {download.suggested_filename}")
                download.save_as(output_path)
                download_completed['success'] = True
                print(f"  Saved: {output_path}")
            except Exception as e:
                print(f"  Save failed: {e}")

        page.on("download", handle_download)

        # Navigate and wait
        page.goto(url, timeout=MAX_WAIT_PER_PDF * 1000, wait_until="domcontentloaded")
        page.wait_for_timeout(5000)

        # Try to find and click PDF download button
        pdf_selectors = [
            'a[href$=".pdf"]',
            'a:has-text("PDF")',
            'a:has-text("Download")',
            '.download-button',
            '#pdf-download'
        ]

        for selector in pdf_selectors:
            try:
                element = page.locator(selector).first
                if element.is_visible(timeout=2000):
                    print(f"  Clicking: {selector}")
                    element.click()
                    page.wait_for_timeout(3000)
                    break
            except:
                continue

        # Wait for potential download
        page.wait_for_timeout(5000)
        page.close()

        return download_completed['success']

    except Exception as e:
        print(f"  Browser error: {e}")
        try:
            page.close()
        except:
            pass
        return False

def download_pdf(browser, paper):
    """Download PDF for a single paper using hybrid approach."""
    paper_id = paper['id']
    title = paper['title']
    authors = paper.get('authors', ['Unknown'])
    year = paper.get('year', 'NoYear')
    url = paper['url']

    # Generate filename
    author_last = authors[0].split()[-1] if authors and authors[0] else 'Unknown'
    title_short = sanitize_filename(title.split(':')[0])
    filename = f"{sanitize_filename(author_last)}_{year}_{title_short}.pdf"
    output_path = PDF_DIR / filename

    print(f"\n{'='*80}")
    print(f"Paper {paper['rank']}: {paper_id}")
    print(f"Title: {title[:60]}...")
    print(f"URL: {url}")
    print(f"Output: {filename}")

    # Check if already exists
    if output_path.exists():
        print(f"  Already exists, skipping")
        return {
            'id': paper_id,
            'rank': paper['rank'],
            'title': title,
            'url': url,
            'filename': filename,
            'status': 'skipped',
            'reason': 'already_exists'
        }

    # Strategy: Direct PDF URLs try HTTP first, others use browser
    is_direct_pdf = url.lower().endswith('.pdf') or '/download' in url.lower()

    for attempt in range(1, MAX_RETRIES + 1):
        print(f"  Attempt {attempt}/{MAX_RETRIES}")

        success = False

        if is_direct_pdf:
            # Try HTTP download first
            success = download_via_requests(url, output_path)

            # Fallback to browser if HTTP fails
            if not success and browser:
                print(f"  Fallback to browser...")
                success = download_via_browser(browser, url, output_path)
        else:
            # Use browser for article pages
            if browser:
                success = download_via_browser(browser, url, output_path)

        # Check result
        if output_path.exists():
            file_size = output_path.stat().st_size
            if file_size > 1000:
                print(f"  SUCCESS: {file_size / 1024:.1f} KB")
                return {
                    'id': paper_id,
                    'rank': paper['rank'],
                    'title': title,
                    'url': url,
                    'filename': filename,
                    'file_size_kb': round(file_size / 1024, 1),
                    'status': 'success',
                    'attempts': attempt,
                    'method': 'http' if is_direct_pdf else 'browser'
                }
            else:
                print(f"  File too small ({file_size} bytes)")
                output_path.unlink()

        time.sleep(2)

    print(f"  FAILED after {MAX_RETRIES} attempts")
    return {
        'id': paper_id,
        'rank': paper['rank'],
        'title': title,
        'url': url,
        'filename': filename,
        'status': 'failed',
        'reason': 'download_failed',
        'attempts': MAX_RETRIES
    }

def main():
    print("="*80)
    print("PHASE 4: HYBRID PDF DOWNLOAD")
    print("Run ID: run_20260223_095905")
    print("Strategy: HTTP for direct PDFs, Browser for pages")
    print("="*80)

    # Load papers
    papers = load_download_queue()
    print(f"\nLoaded {len(papers)} papers")

    # Create directories
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)

    downloads = []
    browser = None

    # Try to connect to CDP (optional for HTTP downloads)
    try:
        print(f"\nConnecting to Chrome CDP...")
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(CDP_URL)
            print(f"Connected to Chrome")

            # Process each paper
            for paper in papers:
                result = download_pdf(browser, paper)
                downloads.append(result)
                save_download_log(downloads)

            print("\nBrowser left open")
    except Exception as e:
        print(f"CDP not available: {e}")
        print("Falling back to HTTP-only mode")

        # Fallback: HTTP-only mode
        for paper in papers:
            result = download_pdf(None, paper)
            downloads.append(result)
            save_download_log(downloads)

    # Summary
    print("\n" + "="*80)
    print("DOWNLOAD SUMMARY")
    print("="*80)
    successful = sum(1 for d in downloads if d['status'] == 'success')
    failed = sum(1 for d in downloads if d['status'] == 'failed')
    skipped = sum(1 for d in downloads if d['status'] == 'skipped')

    print(f"Total: {len(downloads)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Skipped: {skipped}")

    if successful > 0:
        print(f"\nPDFs in: {PDF_DIR}")
        for d in downloads:
            if d['status'] == 'success':
                print(f"  {d['filename']} ({d['file_size_kb']} KB)")

    print(f"\nLog: {DOWNLOADS_LOG}")
    return 0 if successful > 0 else 1

if __name__ == "__main__":
    sys.exit(main())
