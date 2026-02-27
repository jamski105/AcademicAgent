"""
PDF Parser für Academic Agent v2.0

Extrahiert Text aus PDFs mit PyMuPDF (fitz)
- Page-by-page Extraction
- Section Detection (wenn möglich)
- Clean Text Normalization
"""

import re
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

try:
    import fitz  # PyMuPDF
except ImportError:
    raise ImportError(
        "PyMuPDF not installed. Install with: pip install pymupdf"
    )


@dataclass
class PDFPage:
    """Single page from PDF"""
    page_number: int
    text: str
    word_count: int


@dataclass
class PDFDocument:
    """Parsed PDF document"""
    file_path: str
    total_pages: int
    pages: List[PDFPage]
    full_text: str
    word_count: int
    metadata: Dict[str, Any]


class PDFParser:
    """Parse PDFs and extract text"""

    def __init__(self, max_pages: Optional[int] = None):
        """
        Initialize PDF Parser

        Args:
            max_pages: Maximum pages to extract (None = all pages)
        """
        self.max_pages = max_pages

    def parse(self, pdf_path: Path) -> PDFDocument:
        """
        Parse PDF and extract text

        Args:
            pdf_path: Path to PDF file

        Returns:
            PDFDocument with extracted text
        """
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        # Open PDF
        doc = fitz.open(str(pdf_path))

        # Extract metadata
        metadata = {
            "title": doc.metadata.get("title", ""),
            "author": doc.metadata.get("author", ""),
            "subject": doc.metadata.get("subject", ""),
            "pages": doc.page_count
        }

        # Extract pages
        pages = []
        max_pages = self.max_pages or doc.page_count

        for page_num in range(min(max_pages, doc.page_count)):
            page = doc[page_num]
            text = page.get_text()

            # Clean text
            text = self._clean_text(text)

            # Count words
            word_count = len(text.split())

            pages.append(PDFPage(
                page_number=page_num + 1,  # 1-indexed
                text=text,
                word_count=word_count
            ))

        # Combine all pages
        full_text = "\n\n".join(p.text for p in pages)
        total_word_count = sum(p.word_count for p in pages)

        doc.close()

        return PDFDocument(
            file_path=str(pdf_path),
            total_pages=len(pages),
            pages=pages,
            full_text=full_text,
            word_count=total_word_count,
            metadata=metadata
        )

    def _clean_text(self, text: str) -> str:
        """
        Clean extracted text

        - Remove excessive whitespace
        - Normalize line breaks
        - Remove page numbers/headers/footers (basic)
        """
        # Remove multiple spaces
        text = re.sub(r' +', ' ', text)

        # Remove multiple line breaks
        text = re.sub(r'\n\n+', '\n\n', text)

        # Remove lines with only numbers (page numbers)
        lines = text.split('\n')
        lines = [line for line in lines if not re.match(r'^\s*\d+\s*$', line)]
        text = '\n'.join(lines)

        # Strip
        text = text.strip()

        return text

    def get_page_text(self, pdf_path: Path, page_number: int) -> Optional[str]:
        """
        Get text from specific page

        Args:
            pdf_path: Path to PDF
            page_number: Page number (1-indexed)

        Returns:
            Page text or None
        """
        doc = self.parse(pdf_path)

        for page in doc.pages:
            if page.page_number == page_number:
                return page.text

        return None

    def search_text(self, pdf_path: Path, query: str) -> List[Dict[str, Any]]:
        """
        Search for text in PDF

        Args:
            pdf_path: Path to PDF
            query: Search query

        Returns:
            List of matches with page numbers
        """
        doc = self.parse(pdf_path)
        matches = []

        query_lower = query.lower()

        for page in doc.pages:
            if query_lower in page.text.lower():
                # Find all occurrences
                text_lower = page.text.lower()
                start = 0

                while True:
                    pos = text_lower.find(query_lower, start)
                    if pos == -1:
                        break

                    # Extract context (50 chars before/after)
                    context_start = max(0, pos - 50)
                    context_end = min(len(page.text), pos + len(query) + 50)
                    context = page.text[context_start:context_end]

                    matches.append({
                        "page": page.page_number,
                        "position": pos,
                        "context": context
                    })

                    start = pos + 1

        return matches


# ============================================
# Convenience Functions
# ============================================

def parse_pdf(pdf_path: Path, max_pages: Optional[int] = None) -> PDFDocument:
    """
    Simple helper to parse PDF

    Args:
        pdf_path: Path to PDF
        max_pages: Maximum pages to extract

    Returns:
        PDFDocument
    """
    parser = PDFParser(max_pages=max_pages)
    return parser.parse(pdf_path)


def extract_text(pdf_path: Path) -> str:
    """
    Extract full text from PDF

    Args:
        pdf_path: Path to PDF

    Returns:
        Full text
    """
    parser = PDFParser()
    doc = parser.parse(pdf_path)
    return doc.full_text


# ============================================
# Test Code
# ============================================

def main():
    """
    CLI Interface for PDFParser

    Usage:
        python -m src.extraction.pdf_parser --pdf paper.pdf --output text.json
        python -m src.extraction.pdf_parser --pdf paper.pdf --max-pages 10
    """
    import argparse
    import json
    import sys

    parser = argparse.ArgumentParser(description="PDF Parser - Extract text from academic PDFs")
    parser.add_argument('--pdf', required=True, help='Path to PDF file')
    parser.add_argument('--output', help='Output JSON file path (default: stdout)')
    parser.add_argument('--max-pages', type=int, help='Maximum pages to parse (default: all)')
    parser.add_argument('--test', action='store_true', help='Run test mode (preview only)')

    args = parser.parse_args()

    pdf_path = Path(args.pdf)

    if not pdf_path.exists():
        error = {
            "error": f"PDF not found: {pdf_path}",
            "status": "failed"
        }
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(error, f, indent=2)
        else:
            print(json.dumps(error), file=sys.stderr)
        sys.exit(1)

    try:
        # Parse PDF
        pdf_parser = PDFParser(max_pages=args.max_pages)
        doc = pdf_parser.parse(pdf_path)

        # Test mode - just show preview
        if args.test:
            print(f"\n📄 PDF Document:")
            print(f"   File: {doc.file_path}")
            print(f"   Pages: {doc.total_pages}")
            print(f"   Words: {doc.word_count}")
            print(f"   Title: {doc.metadata.get('title', 'N/A')}")

            print(f"\n📖 First Page Preview:")
            if doc.pages:
                first_page = doc.pages[0]
                preview = first_page.text[:300] + "..." if len(first_page.text) > 300 else first_page.text
                print(f"   {preview}")

            print("\n✅ PDF Parser test completed!")
            return

        # Convert to JSON-serializable format
        results = {
            "file_path": str(doc.file_path),
            "total_pages": doc.total_pages,
            "word_count": doc.word_count,
            "metadata": doc.metadata,
            "full_text": doc.full_text,
            "pages": [
                {
                    "page_number": page.page_number,
                    "text": page.text,
                    "word_count": page.word_count
                }
                for page in doc.pages
            ],
            "status": "success"
        }

        # Output results
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"Parsed {doc.total_pages} pages, saved to {args.output}", file=sys.stderr)
        else:
            # Output JSON to stdout
            print(json.dumps(results, indent=2))

    except Exception as e:
        error = {
            "error": str(e),
            "pdf_path": str(pdf_path),
            "status": "failed"
        }
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(error, f, indent=2)
        else:
            print(json.dumps(error), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
