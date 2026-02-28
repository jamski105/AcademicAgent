"""
Quote Validator für Academic Agent v2.3+

Validiert extrahierte Zitate gegen PDF-Text:
- Prüft ob Zitat wirklich im PDF existiert
- Findet Seiten-Nummer
- Extrahiert Context (50 Wörter vor/nach)
- Word Count Compliance (≤25 Wörter)
"""

import re
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from pathlib import Path

from src.extraction.pdf_parser import PDFDocument, parse_pdf


@dataclass
class ValidationResult:
    """Result of quote validation"""
    is_valid: bool
    quote: str
    found_in_pdf: bool
    page_number: Optional[int] = None
    context_before: Optional[str] = None
    context_after: Optional[str] = None
    word_count: int = 0
    complies_with_word_limit: bool = True
    error: Optional[str] = None


class QuoteValidator:
    """Validate quotes against PDF text"""

    def __init__(self, max_word_count: int = 25, context_words: int = 50):
        """
        Initialize Quote Validator

        Args:
            max_word_count: Maximum words per quote (default: 25)
            context_words: Words to extract before/after quote (default: 50)
        """
        self.max_word_count = max_word_count
        self.context_words = context_words

    def validate_quote(
        self,
        quote: str,
        pdf_document: PDFDocument
    ) -> ValidationResult:
        """
        Validate single quote against PDF

        Args:
            quote: Quote text to validate
            pdf_document: Parsed PDF document

        Returns:
            ValidationResult
        """
        # Check word count
        word_count = len(quote.split())
        complies_with_word_limit = word_count <= self.max_word_count

        # Search for quote in PDF
        quote_normalized = self._normalize_text(quote)

        for page in pdf_document.pages:
            page_text_normalized = self._normalize_text(page.text)

            if quote_normalized in page_text_normalized:
                # Found! Extract context
                context_before, context_after = self._extract_context(
                    quote_normalized,
                    page_text_normalized,
                    page.text  # Original text for context
                )

                return ValidationResult(
                    is_valid=True,
                    quote=quote,
                    found_in_pdf=True,
                    page_number=page.page_number,
                    context_before=context_before,
                    context_after=context_after,
                    word_count=word_count,
                    complies_with_word_limit=complies_with_word_limit
                )

        # Not found
        return ValidationResult(
            is_valid=False,
            quote=quote,
            found_in_pdf=False,
            word_count=word_count,
            complies_with_word_limit=complies_with_word_limit,
            error="Quote not found in PDF text"
        )

    def validate_quotes(
        self,
        quotes: List[str],
        pdf_document: PDFDocument
    ) -> List[ValidationResult]:
        """
        Validate multiple quotes

        Args:
            quotes: List of quote texts
            pdf_document: Parsed PDF document

        Returns:
            List of ValidationResults
        """
        results = []

        for quote in quotes:
            result = self.validate_quote(quote, pdf_document)
            results.append(result)

        return results

    def validate_quote_from_pdf_path(
        self,
        quote: str,
        pdf_path: Path
    ) -> ValidationResult:
        """
        Validate quote against PDF file

        Args:
            quote: Quote text
            pdf_path: Path to PDF

        Returns:
            ValidationResult
        """
        # Parse PDF
        pdf_doc = parse_pdf(pdf_path)

        # Validate
        return self.validate_quote(quote, pdf_doc)

    def _normalize_text(self, text: str) -> str:
        """
        Normalize text for comparison

        - Lowercase
        - Remove extra whitespace
        - Remove punctuation (optional)
        """
        # Lowercase
        text = text.lower()

        # Remove multiple spaces
        text = re.sub(r'\s+', ' ', text)

        # Strip
        text = text.strip()

        return text

    def _extract_context(
        self,
        quote_normalized: str,
        page_text_normalized: str,
        page_text_original: str
    ) -> tuple[Optional[str], Optional[str]]:
        """
        Extract context before and after quote

        Args:
            quote_normalized: Normalized quote
            page_text_normalized: Normalized page text
            page_text_original: Original page text (for context)

        Returns:
            (context_before, context_after)
        """
        # Find position in normalized text
        pos = page_text_normalized.find(quote_normalized)
        if pos == -1:
            return None, None

        # Map back to original text (approximate)
        # This is tricky because normalization changes length
        # Simplified approach: find similar position in original

        # Split original text into words
        words = page_text_original.split()

        # Find quote in original text (fuzzy)
        quote_words = quote_normalized.split()
        quote_start_idx = None

        for i in range(len(words) - len(quote_words) + 1):
            window = " ".join(words[i:i+len(quote_words)])
            window_normalized = self._normalize_text(window)

            if quote_normalized in window_normalized:
                quote_start_idx = i
                break

        if quote_start_idx is None:
            return None, None

        # Extract context
        context_before_words = words[max(0, quote_start_idx - self.context_words):quote_start_idx]
        context_after_words = words[quote_start_idx + len(quote_words):quote_start_idx + len(quote_words) + self.context_words]

        context_before = " ".join(context_before_words) if context_before_words else None
        context_after = " ".join(context_after_words) if context_after_words else None

        return context_before, context_after


# ============================================
# Convenience Functions
# ============================================

def validate_quote(
    quote: str,
    pdf_path: Path,
    max_word_count: int = 25
) -> ValidationResult:
    """
    Simple helper to validate quote

    Args:
        quote: Quote text
        pdf_path: Path to PDF
        max_word_count: Maximum words

    Returns:
        ValidationResult
    """
    validator = QuoteValidator(max_word_count=max_word_count)
    return validator.validate_quote_from_pdf_path(quote, pdf_path)


def validate_quotes(
    quotes: List[str],
    pdf_path: Path,
    max_word_count: int = 25
) -> List[ValidationResult]:
    """
    Validate multiple quotes

    Args:
        quotes: List of quote texts
        pdf_path: Path to PDF
        max_word_count: Maximum words

    Returns:
        List of ValidationResults
    """
    validator = QuoteValidator(max_word_count=max_word_count)
    pdf_doc = parse_pdf(pdf_path)
    return validator.validate_quotes(quotes, pdf_doc)


# ============================================
# Test Code
# ============================================

if __name__ == "__main__":
    """Test Quote Validator"""
    import sys

    if len(sys.argv) < 3:
        print("Usage: python quote_validator.py <pdf-path> <quote>")
        sys.exit(1)

    pdf_path = Path(sys.argv[1])
    quote = sys.argv[2]

    if not pdf_path.exists():
        print(f"Error: PDF not found: {pdf_path}")
        sys.exit(1)

    print("Testing Quote Validator...")

    result = validate_quote(quote, pdf_path)

    print(f"\n✂️ Quote Validation:")
    print(f"   Quote: '{quote}'")
    print(f"   Valid: {result.is_valid}")
    print(f"   Found in PDF: {result.found_in_pdf}")
    print(f"   Page: {result.page_number}")
    print(f"   Word Count: {result.word_count} (max: 25)")
    print(f"   Complies: {result.complies_with_word_limit}")

    if result.context_before:
        print(f"\n   Context Before: ...{result.context_before[-100:]}...")

    if result.context_after:
        print(f"   Context After: ...{result.context_after[:100]}...")

    if result.error:
        print(f"   Error: {result.error}")

    print("\n✅ Quote Validator test completed!")
