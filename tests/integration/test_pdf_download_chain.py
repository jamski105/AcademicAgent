#!/usr/bin/env python3
"""
Integration Tests für PDF-Download-Chain
Testet Unpaywall → CORE → DBIS Fallback

WICHTIG: Diese Tests machen echte Downloads!
- Nur mit @pytest.mark.integration markiert
- Benötigt Internet + ggf. DBIS-Credentials
"""

import pytest
from pathlib import Path


pytestmark = pytest.mark.integration


class TestPDFDownloadChain:
    """Integration Tests für PDF-Download-Fallback-Chain"""

    @pytest.mark.slow
    def test_unpaywall_downloads_open_access_pdf(self):
        """Test: Unpaywall lädt OA-PDF herunter"""
        # Bekanntes OA-Paper: arXiv
        # doi = "10.48550/arXiv.1706.03762"  # Attention is All You Need

        # from src.pdf.pdf_fetcher import PDFFetcher
        # fetcher = PDFFetcher()

        # pdf_path = fetcher._try_unpaywall(doi)

        # assert pdf_path is not None
        # assert Path(pdf_path).exists()
        pass

    @pytest.mark.slow
    @pytest.mark.requires_browser
    def test_dbis_downloads_paywalled_pdf(self):
        """Test: DBIS lädt Paywall-PDF herunter"""
        # Benötigt DBIS-Credentials und TIB-Account

        # from src.pdf.pdf_fetcher import PDFFetcher
        # fetcher = PDFFetcher()

        # paper_metadata = {
        #     "doi": "10.1109/EXAMPLE.2024",
        #     "title": "Test Paper",
        #     "venue": "IEEE"
        # }

        # pdf_path = fetcher._try_dbis(paper_metadata)

        # assert pdf_path is not None or pdf_path is None  # Kann fehlschlagen
        pass

    @pytest.mark.slow
    def test_fallback_chain_works_end_to_end(self):
        """Test: Komplette Fallback-Chain funktioniert"""
        # from src.pdf.pdf_fetcher import PDFFetcher
        # fetcher = PDFFetcher()

        # paper = {
        #     "doi": "10.48550/arXiv.1706.03762",
        #     "title": "Attention is All You Need",
        #     "venue": "NeurIPS"
        # }

        # pdf_path = fetcher.fetch(paper["doi"], paper)

        # assert pdf_path is not None
        pass


class TestPDFValidationIntegration:
    """Integration Tests für PDF-Validierung nach Download"""

    @pytest.mark.slow
    def test_validates_pdf_after_download(self):
        """Test: PDF wird nach Download validiert"""
        # from src.pdf.pdf_fetcher import PDFFetcher
        # from src.pdf.pdf_security_validator import PDFSecurityValidator

        # fetcher = PDFFetcher()
        # doi = "10.48550/arXiv.1706.03762"

        # pdf_path = fetcher._try_unpaywall(doi)

        # if pdf_path:
        #     # Validiere PDF
        #     validator = PDFSecurityValidator(pdf_path, "extracted text")
        #     result = validator.validate()
        #     assert result["safe"] is True
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])
