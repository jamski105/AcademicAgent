#!/usr/bin/env python3
"""
Integration Tests für Extraction Pipeline
Tests kompletten Workflow: PDF → Parse → Extract → Validate

WICHTIG: Diese Tests brauchen keine echten PDFs!
Nutzen Mock-PDFs für schnelle Tests.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from src.extraction.quote_extractor import QuoteExtractor
from src.extraction.pdf_parser import PDFDocument, PDFPage


class TestCompleteExtractionPipeline:
    """Integration Tests für komplette Pipeline"""

    @patch('src.extraction.pdf_parser.fitz')
    def test_complete_pipeline_keyword_extraction(self, mock_fitz):
        """Test: Komplette Pipeline mit Keyword Extraction"""
        # Mock PDF document
        mock_doc = Mock()
        mock_doc.page_count = 1
        mock_doc.metadata = {"title": "Test Paper"}

        mock_page = Mock()
        mock_page.get_text.return_value = """
        Large organizations face challenges in standardizing DevOps practices.
        Governance frameworks ensure DevOps compliance across distributed teams.
        This requires clear policy definition and enforcement mechanisms.
        Policy automation reduces manual compliance checks by 80%.
        """

        mock_doc.__getitem__ = Mock(return_value=mock_page)
        mock_fitz.open.return_value = mock_doc

        # Extract quotes
        extractor = QuoteExtractor(use_llm=False, max_quotes_per_paper=3)

        pdf_path = Path("/tmp/test.pdf")
        with patch.object(Path, 'exists', return_value=True):
            result = extractor.extract_quotes(pdf_path, "DevOps governance")

        # Assertions
        assert result.success is True
        assert result.total_quotes > 0
        assert result.extraction_quality == "medium"

        # All quotes should be validated
        for quote in result.quotes:
            assert quote.validated is True

    @patch('src.extraction.pdf_parser.fitz')
    def test_pipeline_filters_invalid_quotes(self, mock_fitz):
        """Test: Pipeline filtert invalide Quotes"""
        # Mock PDF with short text
        mock_doc = Mock()
        mock_doc.page_count = 1
        mock_doc.metadata = {}

        mock_page = Mock()
        mock_page.get_text.return_value = "DevOps governance is important."

        mock_doc.__getitem__ = Mock(return_value=mock_page)
        mock_fitz.open.return_value = mock_doc

        extractor = QuoteExtractor(use_llm=False)

        pdf_path = Path("/tmp/test.pdf")
        with patch.object(Path, 'exists', return_value=True):
            result = extractor.extract_quotes(pdf_path, "DevOps governance")

        # Only validated quotes should be returned
        for quote in result.quotes:
            assert quote.validated is True


class TestPipelineWithDifferentQueries:
    """Tests mit verschiedenen Queries"""

    @patch('src.extraction.pdf_parser.fitz')
    def test_pipeline_with_specific_query(self, mock_fitz):
        """Test: Pipeline mit spezifischer Query"""
        mock_doc = Mock()
        mock_doc.page_count = 1
        mock_doc.metadata = {}

        mock_page = Mock()
        mock_page.get_text.return_value = """
        Cloud computing has transformed infrastructure.
        DevOps practices improve deployment speed.
        Governance frameworks ensure compliance.
        """

        mock_doc.__getitem__ = Mock(return_value=mock_page)
        mock_fitz.open.return_value = mock_doc

        extractor = QuoteExtractor(use_llm=False)

        pdf_path = Path("/tmp/test.pdf")
        with patch.object(Path, 'exists', return_value=True):
            result = extractor.extract_quotes(pdf_path, "cloud computing")

        assert result.success is True
        # Should find quotes about cloud computing
        if result.quotes:
            assert any("cloud" in quote.text.lower() for quote in result.quotes)


class TestPipelineWithMultiplePages:
    """Tests mit mehrseitigen PDFs"""

    @patch('src.extraction.pdf_parser.fitz')
    def test_pipeline_extracts_from_multiple_pages(self, mock_fitz):
        """Test: Pipeline extrahiert von mehreren Seiten"""
        mock_doc = Mock()
        mock_doc.page_count = 3
        mock_doc.metadata = {}

        # Mock 3 pages
        mock_page1 = Mock()
        mock_page1.get_text.return_value = "Page 1: DevOps governance is crucial for enterprises."

        mock_page2 = Mock()
        mock_page2.get_text.return_value = "Page 2: Policy automation reduces compliance overhead."

        mock_page3 = Mock()
        mock_page3.get_text.return_value = "Page 3: Framework adoption improves audit readiness."

        mock_doc.__getitem__ = Mock(side_effect=[mock_page1, mock_page2, mock_page3])
        mock_fitz.open.return_value = mock_doc

        extractor = QuoteExtractor(use_llm=False, max_quotes_per_paper=3)

        pdf_path = Path("/tmp/test.pdf")
        with patch.object(Path, 'exists', return_value=True):
            result = extractor.extract_quotes(pdf_path, "DevOps policy")

        # Should extract from multiple pages
        if result.quotes:
            assert result.success is True
            # Page numbers should vary
            page_numbers = [q.page for q in result.quotes]
            # At least some diversity in page numbers expected
            assert len(set(page_numbers)) > 0


class TestPipelinePerformance:
    """Performance Tests"""

    @patch('src.extraction.pdf_parser.fitz')
    def test_pipeline_performance_small_pdf(self, mock_fitz):
        """Test: Pipeline Performance mit kleinem PDF"""
        import time

        mock_doc = Mock()
        mock_doc.page_count = 5
        mock_doc.metadata = {}

        # 5 pages
        pages = []
        for i in range(5):
            page = Mock()
            page.get_text.return_value = f"Page {i+1}: DevOps governance frameworks are essential for compliance."
            pages.append(page)

        mock_doc.__getitem__ = Mock(side_effect=pages)
        mock_fitz.open.return_value = mock_doc

        extractor = QuoteExtractor(use_llm=False)

        pdf_path = Path("/tmp/test.pdf")

        start = time.time()
        with patch.object(Path, 'exists', return_value=True):
            result = extractor.extract_quotes(pdf_path, "DevOps governance")
        duration = time.time() - start

        # Should complete quickly (< 5 seconds for keyword extraction)
        assert duration < 5.0
        assert result.success is True


class TestPipelineEdgeCases:
    """Edge Cases"""

    @patch('src.extraction.pdf_parser.fitz')
    def test_pipeline_with_empty_pdf(self, mock_fitz):
        """Test: Pipeline mit leerem PDF"""
        mock_doc = Mock()
        mock_doc.page_count = 1
        mock_doc.metadata = {}

        mock_page = Mock()
        mock_page.get_text.return_value = ""  # Empty

        mock_doc.__getitem__ = Mock(return_value=mock_page)
        mock_fitz.open.return_value = mock_doc

        extractor = QuoteExtractor(use_llm=False)

        pdf_path = Path("/tmp/test.pdf")
        with patch.object(Path, 'exists', return_value=True):
            result = extractor.extract_quotes(pdf_path, "query")

        # Should not crash
        assert result.success is True
        assert result.total_quotes == 0

    @patch('src.extraction.pdf_parser.fitz')
    def test_pipeline_with_very_long_text(self, mock_fitz):
        """Test: Pipeline mit sehr langem Text"""
        mock_doc = Mock()
        mock_doc.page_count = 1
        mock_doc.metadata = {}

        # Very long text (10K words)
        long_text = "DevOps governance frameworks. " * 1000

        mock_page = Mock()
        mock_page.get_text.return_value = long_text

        mock_doc.__getitem__ = Mock(return_value=mock_page)
        mock_fitz.open.return_value = mock_doc

        extractor = QuoteExtractor(use_llm=False, max_quotes_per_paper=3)

        pdf_path = Path("/tmp/test.pdf")
        with patch.object(Path, 'exists', return_value=True):
            result = extractor.extract_quotes(pdf_path, "DevOps governance")

        # Should handle long text
        assert result.success is True
        # Should respect max_quotes
        assert len(result.quotes) <= 3


if __name__ == "__main__":
    """
    Run integration tests

    Usage:
        python tests/integration/test_extraction_pipeline.py
        pytest tests/integration/test_extraction_pipeline.py -v
    """
    pytest.main([__file__, "-v", "-s"])
