"""
Extraction Module - Academic Agent v2.0

PDF Text Extraction + Quote Extraction + Validation
"""

from src.extraction.pdf_parser import (
    PDFParser,
    PDFDocument,
    PDFPage,
    parse_pdf,
    extract_text
)

from src.extraction.quote_validator import (
    QuoteValidator,
    ValidationResult,
    validate_quote,
    validate_quotes
)

from src.extraction.quote_extractor import (
    QuoteExtractor,
    Quote,
    ExtractionResult,
    extract_quotes_from_pdf
)

__all__ = [
    # PDF Parser
    "PDFParser",
    "PDFDocument",
    "PDFPage",
    "parse_pdf",
    "extract_text",

    # Quote Validator
    "QuoteValidator",
    "ValidationResult",
    "validate_quote",
    "validate_quotes",

    # Quote Extractor
    "QuoteExtractor",
    "Quote",
    "ExtractionResult",
    "extract_quotes_from_pdf",
]
