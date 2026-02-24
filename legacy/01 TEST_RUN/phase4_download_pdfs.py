#!/usr/bin/env python3
"""
Phase 4: PDF Download using Chrome CDP
Run ID: run_20260223_095905
Date: 2026-02-23
"""

import json
import os
import sys
import time
import re
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

# Configuration
RUN_DIR = Path("/Users/jonas/Desktop/AcademicAgent/runs/run_20260223_095905")
DOWNLOAD_QUEUE = RUN_DIR / "metadata" / "download_queue.json"
PDF_DIR = RUN_DIR / "pdfs"
DOWNLOADS_DIR = RUN_DIR / "downloads"
DOWNLOADS_LOG = DOWNLOADS_DIR / "downloads.json"

CDP_URL = "http://localhost:9222"
MAX_WAIT_PER_PDF = 120  # seconds (2 minutes in quick mode)
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

def attempt_direct_pdf_download(page, url, output_path, paper_id):
    """Attempt to download PDF directly from URL."""
    try:
        print(f"  Navigating to: {url}")
        page.goto(url, timeout=MAX_WAIT_PER_PDF * 1000, wait_until="domcontentloaded")
        page.wait_for_timeout(3000)  # Wait 3s for dynamic content

        # Check if we're on a PDF
        content_type = page.evaluate("""() => {
            return document.contentType || document.querySelector('embed')?.type || 'unknown';
        }""")

        if 'pdf' in content_type.lower():
            print(f"  Direct PDF detected")
            page.wait_for_timeout(5000)
            return True

        # Check if URL ends with .pdf
        if url.lower().endswith('.pdf'):
            print(f"  PDF URL detected")
            page.wait_for_timeout(5000)
            return True

        # Try to find PDF link on page
        pdf_selectors = [
            'a[href*=".pdf"]',
            'a:has-text("PDF")',
            'a:has-text("Download")',
            'button:has-text("Download PDF")',
            '.download-pdf',
            '#download-pdf',
            'a:has-text("Full Text")'
        ]

        for selector in pdf_selectors:
            try:
                elements = page.locator(selector)
                count = elements.count()
                if count > 0:
                    print(f"  Found {count} elements matching: {selector}")
                    element = elements.first
                    if element.is_visible(timeout=2000):
                        print(f"  Clicking on: {selector}")

                        # Get href if it's a link
                        href = element.get_attribute('href')
                        if href and '.pdf' in href:
                            if href.startswith('http'):
                                page.goto(href, timeout=MAX_WAIT_PER_PDF * 1000)
                            else:
                                # Relative URL
                                element.click()
                            page.wait_for_timeout(5000)
                            return True
            except Exception as e:
                continue

        print(f"  No direct PDF link found")
        return False

    except PlaywrightTimeout:
        print(f"  Timeout loading URL")
        return False
    except Exception as e:
        print(f"  Error: {e}")
        return False

def download_pdf(browser, paper):
    """Download PDF for a single paper."""
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
    print(f"Downloading: {paper_id} (Rank {paper['rank']})")
    print(f"Title: {title[:70]}...")
    print(f"URL: {url}")
    print(f"Output: {filename}")

    # Check if already downloaded
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

    # Attempt download
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            print(f"  Attempt {attempt}/{MAX_RETRIES}")

            # Get or create context
            if len(browser.contexts) == 0:
                context = browser.new_context(accept_downloads=True)
            else:
                context = browser.contexts[0]

            # Create new page
            page = context.new_page()

            # Set up download handler
            download_info = {'started': False, 'path': None}

            def on_download(download):
                download_info['started'] = True
                print(f"  Download started: {download.suggested_filename}")
                try:
                    download.save_as(output_path)
                    download_info['path'] = output_path
                    print(f"  Saved to: {output_path}")
                except Exception as e:
                    print(f"  Save error: {e}")

            page.on("download", on_download)

            # Attempt download
            success = attempt_direct_pdf_download(page, url, output_path, paper_id)

            # Wait a bit for download to complete
            if download_info['started']:
                print(f"  Waiting for download to complete...")
                time.sleep(3)

            page.close()

            # Check if file exists and is valid
            if output_path.exists():
                file_size = output_path.stat().st_size
                if file_size > 1000:  # At least 1KB
                    print(f"  SUCCESS: {file_size / 1024:.1f} KB")
                    return {
                        'id': paper_id,
                        'rank': paper['rank'],
                        'title': title,
                        'url': url,
                        'filename': filename,
                        'file_size_kb': round(file_size / 1024, 1),
                        'status': 'success',
                        'attempts': attempt
                    }
                else:
                    print(f"  File too small ({file_size} bytes), removing")
                    output_path.unlink()

            print(f"  No valid PDF downloaded")
            time.sleep(2)

        except Exception as e:
            print(f"  Attempt {attempt} failed: {e}")
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
    print("PHASE 4: PDF DOWNLOAD")
    print("Run ID: run_20260223_095905")
    print("Mode: Quick (6 papers, 2 min timeout)")
    print("="*80)

    # Load papers
    papers = load_download_queue()
    print(f"\nLoaded {len(papers)} papers from download queue")

    # Create directories
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)

    # Connect to CDP Chrome
    print(f"\nConnecting to Chrome CDP: {CDP_URL}")

    downloads = []

    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp(CDP_URL)
            print(f"Connected to Chrome (CDP)")

            # Check if we have contexts
            if len(browser.contexts) > 0:
                print(f"Using existing context with {len(browser.contexts[0].pages)} pages")

            # Process each paper
            for paper in papers:
                result = download_pdf(browser, paper)
                downloads.append(result)

                # Save log after each download
                save_download_log(downloads)

            # Don't close the browser - user might be using it
            print("\nNote: Browser left open for user inspection")

        except Exception as e:
            print(f"\nERROR: Failed to connect to CDP: {e}")
            print("Make sure Chrome is running with --remote-debugging-port=9222")
            return 1

    # Summary
    print("\n" + "="*80)
    print("DOWNLOAD SUMMARY")
    print("="*80)
    successful = sum(1 for d in downloads if d['status'] == 'success')
    failed = sum(1 for d in downloads if d['status'] == 'failed')
    skipped = sum(1 for d in downloads if d['status'] == 'skipped')

    print(f"Total Papers: {len(downloads)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Skipped: {skipped}")

    if successful > 0:
        print(f"\nPDFs saved to: {PDF_DIR}")
        print("Files:")
        for d in downloads:
            if d['status'] == 'success':
                print(f"  - {d['filename']} ({d['file_size_kb']} KB)")

    print(f"\nDownload log: {DOWNLOADS_LOG}")

    return 0 if successful > 0 else 1

if __name__ == "__main__":
    sys.exit(main())
