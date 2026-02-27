#!/usr/bin/env python3
"""
Unit Tests für Quote Validator
Tests src/extraction/quote_validator.py
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from src.extraction.quote_validator import QuoteValidator, ValidationResult, validate_quote
from src.extraction.pdf_parser import PDFDocument, PDFPage


class TestValidatorInit:
    """Tests für Validator-Initialisierung"""

    def test_init_default(self):
        """Test: Default Initialisierung"""
        validator = QuoteValidator()

        assert validator.max_word_count == 25
        assert validator.context_words == 50

    def test_init_custom_params(self):
        """Test: Custom Parameter"""
        validator = QuoteValidator(max_word_count=30, context_words=40)

        assert validator.max_word_count == 30
        assert validator.context_words == 40


class TestWordCountValidation:
    """Tests für Word Count Validation"""

    def test_quote_within_word_limit(self):
        """Test: Quote innerhalb Word Limit"""
        validator = QuoteValidator(max_word_count=25)

        # Mock PDF document
        page = PDFPage(
            page_number=1,
            text="DevOps governance frameworks ensure compliance",
            word_count=6
        )
        pdf_doc = PDFDocument(
            file_path="test.pdf",
            total_pages=1,
            pages=[page],
            full_text=page.text,
            word_count=6,
            metadata={}
        )

        quote = "DevOps governance frameworks ensure compliance"
        result = validator.validate_quote(quote, pdf_doc)

        assert result.word_count == 5
        assert result.complies_with_word_limit is True

    def test_quote_exceeds_word_limit(self):
        """Test: Quote überschreitet Word Limit"""
        validator = QuoteValidator(max_word_count=5)

        page = PDFPage(
            page_number=1,
            text="This is a very long quote that exceeds the word limit",
            word_count=11
        )
        pdf_doc = PDFDocument(
            file_path="test.pdf",
            total_pages=1,
            pages=[page],
            full_text=page.text,
            word_count=11,
            metadata={}
        )

        quote = "This is a very long quote that exceeds the word limit"
        result = validator.validate_quote(quote, pdf_doc)

        assert result.word_count == 11
        assert result.complies_with_word_limit is False


class TestQuoteValidation:
    """Tests für Quote Validation gegen PDF"""

    def test_validate_quote_found_in_pdf(self):
        """Test: Quote gefunden in PDF"""
        validator = QuoteValidator()

        page = PDFPage(
            page_number=3,
            text="Governance frameworks ensure DevOps compliance across distributed teams.",
            word_count=9
        )
        pdf_doc = PDFDocument(
            file_path="test.pdf",
            total_pages=5,
            pages=[page],
            full_text=page.text,
            word_count=9,
            metadata={}
        )

        quote = "Governance frameworks ensure DevOps compliance"
        result = validator.validate_quote(quote, pdf_doc)

        assert result.is_valid is True
        assert result.found_in_pdf is True
        assert result.page_number == 3

    def test_validate_quote_not_found_in_pdf(self):
        """Test: Quote NICHT in PDF gefunden"""
        validator = QuoteValidator()

        page = PDFPage(
            page_number=1,
            text="This paper discusses software engineering practices.",
            word_count=6
        )
        pdf_doc = PDFDocument(
            file_path="test.pdf",
            total_pages=1,
            pages=[page],
            full_text=page.text,
            word_count=6,
            metadata={}
        )

        quote = "DevOps governance frameworks"
        result = validator.validate_quote(quote, pdf_doc)

        assert result.is_valid is False
        assert result.found_in_pdf is False
        assert result.error == "Quote not found in PDF text"

    def test_validate_quote_case_insensitive(self):
        """Test: Validation ist case-insensitive"""
        validator = QuoteValidator()

        page = PDFPage(
            page_number=1,
            text="DevOps Governance Frameworks",
            word_count=3
        )
        pdf_doc = PDFDocument(
            file_path="test.pdf",
            total_pages=1,
            pages=[page],
            full_text=page.text,
            word_count=3,
            metadata={}
        )

        # Different case
        quote = "devops governance frameworks"
        result = validator.validate_quote(quote, pdf_doc)

        assert result.is_valid is True
        assert result.found_in_pdf is True


class TestContextExtraction:
    """Tests für Context Extraction"""

    def test_context_extraction(self):
        """Test: Context wird extrahiert"""
        validator = QuoteValidator(context_words=10)

        page = PDFPage(
            page_number=1,
            text="Large organizations face challenges in standardizing practices. Governance frameworks ensure DevOps compliance across distributed teams. This requires clear policy definition.",
            word_count=21
        )
        pdf_doc = PDFDocument(
            file_path="test.pdf",
            total_pages=1,
            pages=[page],
            full_text=page.text,
            word_count=21,
            metadata={}
        )

        quote = "Governance frameworks ensure DevOps compliance"
        result = validator.validate_quote(quote, pdf_doc)

        assert result.is_valid is True
        assert result.context_before is not None
        assert result.context_after is not None

        # Context should contain surrounding words
        assert "challenges" in result.context_before.lower() or "standardizing" in result.context_before.lower()
        assert "teams" in result.context_after.lower() or "requires" in result.context_after.lower()


class TestBatchValidation:
    """Tests für Batch Validation"""

    def test_validate_multiple_quotes(self):
        """Test: Multiple Quotes validieren"""
        validator = QuoteValidator()

        page = PDFPage(
            page_number=1,
            text="DevOps governance is important. Automation reduces compliance checks. Policy frameworks ensure audit readiness.",
            word_count=13
        )
        pdf_doc = PDFDocument(
            file_path="test.pdf",
            total_pages=1,
            pages=[page],
            full_text=page.text,
            word_count=13,
            metadata={}
        )

        quotes = [
            "DevOps governance is important",
            "Automation reduces compliance checks",
            "This quote does not exist"
        ]

        results = validator.validate_quotes(quotes, pdf_doc)

        assert len(results) == 3
        assert results[0].is_valid is True
        assert results[1].is_valid is True
        assert results[2].is_valid is False


class TestConvenienceFunctions:
    """Tests für Convenience Functions"""

    @patch('src.extraction.quote_validator.parse_pdf')
    def test_validate_quote_convenience(self, mock_parse_pdf):
        """Test: validate_quote() convenience function"""
        # Mock PDF document
        page = PDFPage(
            page_number=1,
            text="Test quote here",
            word_count=3
        )
        mock_parse_pdf.return_value = PDFDocument(
            file_path="test.pdf",
            total_pages=1,
            pages=[page],
            full_text=page.text,
            word_count=3,
            metadata={}
        )

        pdf_path = Path("/tmp/test.pdf")
        quote = "Test quote here"

        result = validate_quote(quote, pdf_path)

        assert result.is_valid is True
        mock_parse_pdf.assert_called_once_with(pdf_path)


class TestTextNormalization:
    """Tests für Text Normalization"""

    def test_normalize_removes_extra_whitespace(self):
        """Test: Normalisierung entfernt extra Whitespace"""
        validator = QuoteValidator()

        text = "This   has    extra     spaces"
        normalized = validator._normalize_text(text)

        assert "  " not in normalized

    def test_normalize_lowercases_text(self):
        """Test: Normalisierung macht lowercase"""
        validator = QuoteValidator()

        text = "THIS IS UPPERCASE"
        normalized = validator._normalize_text(text)

        assert normalized == "this is uppercase"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
