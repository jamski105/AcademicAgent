#!/usr/bin/env python3
"""
Unit Tests für PDF Parser
Tests src/extraction/pdf_parser.py
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from src.extraction.pdf_parser import PDFParser, PDFDocument, PDFPage, parse_pdf, extract_text


class TestPDFParserInit:
    """Tests für Parser-Initialisierung"""

    def test_init_default(self):
        """Test: Default Initialisierung"""
        parser = PDFParser()

        assert parser.max_pages is None

    def test_init_with_max_pages(self):
        """Test: Init mit max_pages"""
        parser = PDFParser(max_pages=10)

        assert parser.max_pages == 10


class TestTextCleaning:
    """Tests für Text-Cleaning"""

    def test_clean_text_removes_multiple_spaces(self):
        """Test: Multiple spaces werden entfernt"""
        parser = PDFParser()

        text = "This   has    multiple     spaces"
        cleaned = parser._clean_text(text)

        assert "  " not in cleaned
        assert cleaned == "This has multiple spaces"

    def test_clean_text_removes_page_numbers(self):
        """Test: Standalone Zahlen (Page Numbers) werden entfernt"""
        parser = PDFParser()

        text = "Some text\n42\nMore text"
        cleaned = parser._clean_text(text)

        # Page number line should be removed
        assert "42" not in cleaned.split('\n')

    def test_clean_text_removes_multiple_linebreaks(self):
        """Test: Multiple Linebreaks werden normalisiert"""
        parser = PDFParser()

        text = "Text\n\n\n\nMore text"
        cleaned = parser._clean_text(text)

        assert "\n\n\n" not in cleaned


class TestPDFParsingMocked:
    """Tests mit gemocktem PyMuPDF"""

    @patch('src.extraction.pdf_parser.fitz')
    def test_parse_pdf_success(self, mock_fitz):
        """Test: PDF Parsing erfolgreich"""
        # Mock PDF document
        mock_doc = Mock()
        mock_doc.page_count = 2
        mock_doc.metadata = {
            "title": "Test Paper",
            "author": "Test Author"
        }

        # Mock pages
        mock_page1 = Mock()
        mock_page1.get_text.return_value = "Page 1 text content"

        mock_page2 = Mock()
        mock_page2.get_text.return_value = "Page 2 text content"

        mock_doc.__getitem__ = Mock(side_effect=[mock_page1, mock_page2])

        mock_fitz.open.return_value = mock_doc

        # Parse
        parser = PDFParser()
        temp_pdf = Path("/tmp/test.pdf")

        with patch.object(Path, 'exists', return_value=True):
            doc = parser.parse(temp_pdf)

        # Assertions
        assert isinstance(doc, PDFDocument)
        assert doc.total_pages == 2
        assert len(doc.pages) == 2
        assert doc.metadata["title"] == "Test Paper"
        assert "Page 1" in doc.full_text
        assert "Page 2" in doc.full_text

    @patch('src.extraction.pdf_parser.fitz')
    def test_parse_pdf_with_max_pages(self, mock_fitz):
        """Test: Parse nur erste N Seiten"""
        mock_doc = Mock()
        mock_doc.page_count = 10

        mock_doc.metadata = {}

        # Mock pages
        mock_pages = [Mock() for _ in range(10)]
        for i, page in enumerate(mock_pages):
            page.get_text.return_value = f"Page {i+1}"

        mock_doc.__getitem__ = Mock(side_effect=mock_pages)
        mock_fitz.open.return_value = mock_doc

        # Parse with max_pages=3
        parser = PDFParser(max_pages=3)
        temp_pdf = Path("/tmp/test.pdf")

        with patch.object(Path, 'exists', return_value=True):
            doc = parser.parse(temp_pdf)

        # Should only parse first 3 pages
        assert doc.total_pages == 3
        assert len(doc.pages) == 3

    def test_parse_pdf_file_not_found(self):
        """Test: FileNotFoundError wenn PDF nicht existiert"""
        parser = PDFParser()
        non_existent = Path("/tmp/nonexistent.pdf")

        with pytest.raises(FileNotFoundError):
            parser.parse(non_existent)


class TestConvenienceFunctions:
    """Tests für Convenience Functions"""

    @patch('src.extraction.pdf_parser.fitz')
    def test_parse_pdf_convenience(self, mock_fitz):
        """Test: parse_pdf() convenience function"""
        mock_doc = Mock()
        mock_doc.page_count = 1
        mock_doc.metadata = {}

        mock_page = Mock()
        mock_page.get_text.return_value = "Test content"
        mock_doc.__getitem__ = Mock(return_value=mock_page)

        mock_fitz.open.return_value = mock_doc

        temp_pdf = Path("/tmp/test.pdf")

        with patch.object(Path, 'exists', return_value=True):
            doc = parse_pdf(temp_pdf)

        assert isinstance(doc, PDFDocument)
        assert doc.total_pages == 1

    @patch('src.extraction.pdf_parser.fitz')
    def test_extract_text_convenience(self, mock_fitz):
        """Test: extract_text() convenience function"""
        mock_doc = Mock()
        mock_doc.page_count = 1
        mock_doc.metadata = {}

        mock_page = Mock()
        mock_page.get_text.return_value = "Test text content"
        mock_doc.__getitem__ = Mock(return_value=mock_page)

        mock_fitz.open.return_value = mock_doc

        temp_pdf = Path("/tmp/test.pdf")

        with patch.object(Path, 'exists', return_value=True):
            text = extract_text(temp_pdf)

        assert "Test text content" in text


class TestSearchText:
    """Tests für Text-Search"""

    @patch('src.extraction.pdf_parser.fitz')
    def test_search_text_finds_matches(self, mock_fitz):
        """Test: Text-Suche findet Matches"""
        mock_doc = Mock()
        mock_doc.page_count = 2
        mock_doc.metadata = {}

        mock_page1 = Mock()
        mock_page1.get_text.return_value = "This paper discusses DevOps governance frameworks"

        mock_page2 = Mock()
        mock_page2.get_text.return_value = "The conclusion discusses DevOps best practices"

        mock_doc.__getitem__ = Mock(side_effect=[mock_page1, mock_page2])
        mock_fitz.open.return_value = mock_doc

        parser = PDFParser()
        temp_pdf = Path("/tmp/test.pdf")

        with patch.object(Path, 'exists', return_value=True):
            matches = parser.search_text(temp_pdf, "DevOps")

        # Should find 2 matches (one per page)
        assert len(matches) == 2
        assert matches[0]["page"] == 1
        assert matches[1]["page"] == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
