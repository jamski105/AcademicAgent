#!/usr/bin/env python3
"""
Unit Tests für Quote Extractor
Tests src/extraction/quote_extractor.py (mit Haiku Mocking)
"""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from src.extraction.quote_extractor import QuoteExtractor, Quote, ExtractionResult, extract_quotes_from_pdf
from src.extraction.pdf_parser import PDFDocument, PDFPage


class TestExtractorInit:
    """Tests für Extractor-Initialisierung"""

    def test_init_without_api_key(self):
        """Test: Init ohne API Key (Fallback)"""
        with patch.dict('os.environ', {}, clear=True):
            extractor = QuoteExtractor(use_llm=False)

            assert extractor.use_llm is False
            assert extractor.anthropic_client is None

    @patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'})
    @patch('src.extraction.quote_extractor.anthropic')
    def test_init_with_api_key(self, mock_anthropic):
        """Test: Init mit API Key"""
        mock_anthropic.Anthropic.return_value = Mock()

        extractor = QuoteExtractor(use_llm=True)

        assert extractor.use_llm is True
        assert extractor.api_key == 'test-key'

    def test_init_custom_params(self):
        """Test: Custom Parameter"""
        extractor = QuoteExtractor(
            use_llm=False,
            max_quotes_per_paper=5,
            max_words_per_quote=30
        )

        assert extractor.max_quotes == 5
        assert extractor.max_words == 30


class TestKeywordExtraction:
    """Tests für Fallback Keyword Extraction"""

    @patch('src.extraction.quote_extractor.PDFParser')
    def test_extract_with_keywords_finds_quotes(self, mock_parser_class):
        """Test: Keyword Extraction findet Quotes"""
        # Mock PDF document
        page = PDFPage(
            page_number=1,
            text="DevOps governance is important. Automation reduces compliance. Policy frameworks ensure audit.",
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

        mock_parser = Mock()
        mock_parser.parse.return_value = pdf_doc
        mock_parser_class.return_value = mock_parser

        extractor = QuoteExtractor(use_llm=False, max_quotes_per_paper=3)

        # Extract quotes
        pdf_path = Path("/tmp/test.pdf")
        with patch.object(Path, 'exists', return_value=True):
            result = extractor.extract_quotes(pdf_path, "DevOps governance")

        assert result.success is True
        assert len(result.quotes) > 0
        assert result.extraction_quality == "medium"

    @patch('src.extraction.quote_extractor.PDFParser')
    def test_extract_respects_max_quotes(self, mock_parser_class):
        """Test: max_quotes wird respektiert"""
        # PDF with many sentences
        sentences = [f"DevOps sentence {i}." for i in range(10)]
        text = " ".join(sentences)

        page = PDFPage(page_number=1, text=text, word_count=30)
        pdf_doc = PDFDocument(
            file_path="test.pdf",
            total_pages=1,
            pages=[page],
            full_text=text,
            word_count=30,
            metadata={}
        )

        mock_parser = Mock()
        mock_parser.parse.return_value = pdf_doc
        mock_parser_class.return_value = mock_parser

        extractor = QuoteExtractor(use_llm=False, max_quotes_per_paper=3)

        pdf_path = Path("/tmp/test.pdf")
        with patch.object(Path, 'exists', return_value=True):
            result = extractor.extract_quotes(pdf_path, "DevOps")

        # Should not exceed max_quotes
        assert len(result.quotes) <= 3


class TestHaikuExtraction:
    """Tests für Haiku-basierte Extraction (mit Mocking)"""

    @patch('src.extraction.quote_extractor.PDFParser')
    @patch('src.extraction.quote_extractor.anthropic')
    def test_extract_with_haiku_success(self, mock_anthropic_module, mock_parser_class):
        """Test: Haiku Extraction erfolgreich"""
        # Mock PDF
        page = PDFPage(
            page_number=1,
            text="DevOps governance frameworks ensure compliance across teams.",
            word_count=8
        )
        pdf_doc = PDFDocument(
            file_path="test.pdf",
            total_pages=1,
            pages=[page],
            full_text=page.text,
            word_count=8,
            metadata={}
        )

        mock_parser = Mock()
        mock_parser.parse.return_value = pdf_doc
        mock_parser_class.return_value = mock_parser

        # Mock Anthropic API response
        mock_client = Mock()
        mock_response = Mock()
        mock_response.content = [Mock(text=json.dumps({
            "quotes": [
                {
                    "text": "DevOps governance frameworks ensure compliance",
                    "page": 1,
                    "section": "Introduction",
                    "word_count": 5,
                    "relevance_score": 0.95,
                    "reasoning": "Directly addresses governance",
                    "context_before": "Large organizations face challenges",
                    "context_after": "across distributed teams"
                }
            ]
        }))]

        mock_client.messages.create.return_value = mock_response
        mock_anthropic_module.Anthropic.return_value = mock_client

        extractor = QuoteExtractor(anthropic_api_key='test-key', use_llm=True)

        pdf_path = Path("/tmp/test.pdf")
        with patch.object(Path, 'exists', return_value=True):
            result = extractor.extract_quotes(pdf_path, "DevOps governance")

        assert result.success is True
        assert len(result.quotes) == 1
        assert result.quotes[0].text == "DevOps governance frameworks ensure compliance"
        assert result.quotes[0].relevance_score == 0.95
        assert result.extraction_quality == "high"

    @patch('src.extraction.quote_extractor.PDFParser')
    @patch('src.extraction.quote_extractor.anthropic')
    def test_extract_handles_haiku_error(self, mock_anthropic_module, mock_parser_class):
        """Test: Haiku-Fehler wird behandelt"""
        # Mock PDF
        page = PDFPage(page_number=1, text="Test", word_count=1)
        pdf_doc = PDFDocument(
            file_path="test.pdf",
            total_pages=1,
            pages=[page],
            full_text="Test",
            word_count=1,
            metadata={}
        )

        mock_parser = Mock()
        mock_parser.parse.return_value = pdf_doc
        mock_parser_class.return_value = mock_parser

        # Mock Anthropic API error
        mock_client = Mock()
        mock_client.messages.create.side_effect = Exception("API Error")
        mock_anthropic_module.Anthropic.return_value = mock_client

        extractor = QuoteExtractor(anthropic_api_key='test-key', use_llm=True)

        pdf_path = Path("/tmp/test.pdf")
        with patch.object(Path, 'exists', return_value=True):
            result = extractor.extract_quotes(pdf_path, "query")

        assert result.success is False
        assert "Extraction failed" in result.error


class TestQuoteValidation:
    """Tests für Quote Validation"""

    @patch('src.extraction.quote_extractor.PDFParser')
    @patch('src.extraction.quote_extractor.QuoteValidator')
    def test_quotes_are_validated(self, mock_validator_class, mock_parser_class):
        """Test: Quotes werden validiert"""
        # Mock PDF
        page = PDFPage(
            page_number=1,
            text="DevOps governance is important",
            word_count=4
        )
        pdf_doc = PDFDocument(
            file_path="test.pdf",
            total_pages=1,
            pages=[page],
            full_text=page.text,
            word_count=4,
            metadata={}
        )

        mock_parser = Mock()
        mock_parser.parse.return_value = pdf_doc
        mock_parser_class.return_value = mock_parser

        # Mock validator
        mock_validator = Mock()
        mock_validation = Mock()
        mock_validation.is_valid = True
        mock_validation.page_number = 1
        mock_validation.context_before = "Test context"
        mock_validation.context_after = "More context"

        mock_validator.validate_quote.return_value = mock_validation
        mock_validator_class.return_value = mock_validator

        extractor = QuoteExtractor(use_llm=False)

        pdf_path = Path("/tmp/test.pdf")
        with patch.object(Path, 'exists', return_value=True):
            result = extractor.extract_quotes(pdf_path, "DevOps governance")

        # Validator should have been called
        assert mock_validator.validate_quote.called


class TestErrorHandling:
    """Tests für Error Handling"""

    def test_extract_pdf_not_found(self):
        """Test: PDF nicht gefunden"""
        extractor = QuoteExtractor(use_llm=False)

        non_existent = Path("/tmp/nonexistent.pdf")
        result = extractor.extract_quotes(non_existent, "query")

        assert result.success is False
        assert "PDF not found" in result.error


class TestPromptBuilding:
    """Tests für Prompt Building"""

    def test_build_haiku_prompt_includes_query(self):
        """Test: Prompt enthält Query"""
        extractor = QuoteExtractor(use_llm=False)

        prompt = extractor._build_haiku_prompt(
            pdf_text="Test PDF text",
            research_query="DevOps Governance",
            paper_title="Test Paper",
            academic_context=None
        )

        assert "DevOps Governance" in prompt
        assert "Test PDF text" in prompt

    def test_build_haiku_prompt_includes_requirements(self):
        """Test: Prompt enthält Requirements"""
        extractor = QuoteExtractor(use_llm=False, max_quotes_per_paper=3, max_words_per_quote=25)

        prompt = extractor._build_haiku_prompt(
            pdf_text="Test",
            research_query="query",
            paper_title="Title",
            academic_context=None
        )

        assert "3" in prompt  # max_quotes
        assert "25" in prompt  # max_words


class TestResponseParsing:
    """Tests für Response Parsing"""

    def test_parse_valid_json_response(self):
        """Test: Valides JSON wird geparst"""
        extractor = QuoteExtractor(use_llm=False)

        response_text = json.dumps({
            "quotes": [
                {
                    "text": "Test quote",
                    "page": 1,
                    "word_count": 2,
                    "relevance_score": 0.9
                }
            ]
        })

        quotes = extractor._parse_haiku_response(response_text)

        assert len(quotes) == 1
        assert quotes[0].text == "Test quote"
        assert quotes[0].page == 1

    def test_parse_invalid_json_returns_empty(self):
        """Test: Invalides JSON gibt leere Liste"""
        extractor = QuoteExtractor(use_llm=False)

        response_text = "This is not JSON"

        quotes = extractor._parse_haiku_response(response_text)

        assert quotes == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
