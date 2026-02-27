"""
Unit Tests für PDF Fetcher Modul

Tests:
- Unpaywall success (mocked API)
- CORE fallback (Unpaywall fails → CORE success)
- Fallback chain (alle 3 Steps)
- Skip after failures (alle Strategien failed)
- Rate limiting

Nutzt pytest + responses für HTTP Mocking
"""

import pytest
import tempfile
import uuid
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from src.pdf.pdf_fetcher import PDFFetcher, PDFResult
from src.pdf.unpaywall_client import UnpaywallClient, UnpaywallResult
from src.pdf.core_client import COREClient, COREResult


# ============================================
# Fixtures
# ============================================

@pytest.fixture
def temp_output_dir():
    """Temporary output directory for tests"""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def session_id():
    """Test session ID"""
    return str(uuid.uuid4())[:8]


@pytest.fixture
def test_papers():
    """Test paper list"""
    return [
        {"doi": "10.1371/journal.pone.0000001", "title": "Paper 1"},
        {"doi": "10.1371/journal.pone.0000002", "title": "Paper 2"},
        {"doi": "10.1371/journal.pone.0000003", "title": "Paper 3"},
    ]


# ============================================
# Test Unpaywall Client
# ============================================

def test_unpaywall_success_mocked(temp_output_dir, session_id):
    """Test successful Unpaywall download (mocked)"""

    # Mock UnpaywallClient.fetch()
    with patch.object(UnpaywallClient, 'fetch') as mock_fetch:
        # Setup mock
        mock_fetch.return_value = UnpaywallResult(
            success=True,
            doi="10.1371/journal.pone.0000001",
            pdf_url="https://example.com/paper.pdf",
            is_oa=True,
            oa_status="gold"
        )

        # Create fetcher
        fetcher = PDFFetcher(output_dir=temp_output_dir)

        # Fetch single paper
        result = fetcher.fetch_single("10.1371/journal.pone.0000001", session_id)

        # Assertions
        assert result.success == True
        assert result.source == "unpaywall"
        assert result.attempts == 1
        assert mock_fetch.called


def test_unpaywall_not_found(temp_output_dir, session_id):
    """Test Unpaywall returns 404 (paper not OA)"""

    with patch.object(UnpaywallClient, 'fetch') as mock_fetch:
        mock_fetch.return_value = UnpaywallResult(
            success=False,
            doi="10.1109/CLOSED.2024.123",
            error="DOI not found in Unpaywall (likely not Open Access)"
        )

        fetcher = PDFFetcher(output_dir=temp_output_dir, fallback_chain=["unpaywall"])
        result = fetcher.fetch_single("10.1109/CLOSED.2024.123", session_id)

        # Should fail and be skipped (no fallback)
        assert result.success == False
        assert result.skipped == True
        assert result.attempts == 1


# ============================================
# Test CORE Client
# ============================================

def test_core_success_mocked(temp_output_dir, session_id):
    """Test successful CORE download (mocked)"""

    with patch.object(COREClient, 'fetch') as mock_fetch:
        mock_fetch.return_value = COREResult(
            success=True,
            doi="10.1371/journal.pone.0000002",
            pdf_url="https://core.ac.uk/download/12345.pdf",
            open_access=True
        )

        # Force CORE only
        fetcher = PDFFetcher(
            output_dir=temp_output_dir,
            fallback_chain=["core"],
            core_api_key="test_key"
        )

        result = fetcher.fetch_single("10.1371/journal.pone.0000002", session_id)

        assert result.success == True
        assert result.source == "core"
        assert result.attempts == 1


def test_core_disabled_without_key(temp_output_dir, session_id):
    """Test CORE is skipped if no API key"""

    fetcher = PDFFetcher(
        output_dir=temp_output_dir,
        fallback_chain=["core"],
        core_api_key=None  # No key
    )

    result = fetcher.fetch_single("10.1371/journal.pone.0000003", session_id)

    # Should skip because CORE requires key
    assert result.success == False
    assert result.skipped == True


# ============================================
# Test Fallback Chain
# ============================================

def test_fallback_unpaywall_fails_core_succeeds(temp_output_dir, session_id):
    """Test fallback: Unpaywall fails → CORE succeeds"""

    with patch.object(UnpaywallClient, 'fetch') as mock_unpaywall, \
         patch.object(COREClient, 'fetch') as mock_core:

        # Unpaywall fails
        mock_unpaywall.return_value = UnpaywallResult(
            success=False,
            doi="10.1109/TEST.2024",
            error="Not Open Access"
        )

        # CORE succeeds
        mock_core.return_value = COREResult(
            success=True,
            doi="10.1109/TEST.2024",
            pdf_url="https://core.ac.uk/download/test.pdf"
        )

        fetcher = PDFFetcher(
            output_dir=temp_output_dir,
            fallback_chain=["unpaywall", "core"],
            core_api_key="test_key"
        )

        result = fetcher.fetch_single("10.1109/TEST.2024", session_id)

        # Should succeed via CORE (2nd attempt)
        assert result.success == True
        assert result.source == "core"
        assert result.attempts == 2
        assert mock_unpaywall.called
        assert mock_core.called


def test_all_strategies_fail_skip(temp_output_dir, session_id):
    """Test all strategies fail → paper is skipped"""

    with patch.object(UnpaywallClient, 'fetch') as mock_unpaywall, \
         patch.object(COREClient, 'fetch') as mock_core:

        # Both fail
        mock_unpaywall.return_value = UnpaywallResult(
            success=False, doi="10.1109/FAIL.2024", error="Not OA"
        )
        mock_core.return_value = COREResult(
            success=False, doi="10.1109/FAIL.2024", error="Not found"
        )

        fetcher = PDFFetcher(
            output_dir=temp_output_dir,
            fallback_chain=["unpaywall", "core"],
            core_api_key="test_key"
        )

        result = fetcher.fetch_single("10.1109/FAIL.2024", session_id)

        # Should be skipped
        assert result.success == False
        assert result.skipped == True
        assert result.attempts == 2
        assert mock_unpaywall.called
        assert mock_core.called


# ============================================
# Test Batch Processing
# ============================================

def test_fetch_batch(temp_output_dir, session_id, test_papers):
    """Test batch processing of multiple papers"""

    with patch.object(UnpaywallClient, 'fetch') as mock_fetch:
        # Mock: First 2 succeed, 3rd fails
        mock_fetch.side_effect = [
            UnpaywallResult(success=True, doi=test_papers[0]["doi"], pdf_url="url1"),
            UnpaywallResult(success=True, doi=test_papers[1]["doi"], pdf_url="url2"),
            UnpaywallResult(success=False, doi=test_papers[2]["doi"], error="Not found"),
        ]

        fetcher = PDFFetcher(
            output_dir=temp_output_dir,
            fallback_chain=["unpaywall"]
        )

        results = fetcher.fetch_batch(test_papers, session_id)

        # Assertions
        assert len(results) == 3
        assert results[0].success == True
        assert results[1].success == True
        assert results[2].success == False
        assert results[2].skipped == True

        # Check stats
        stats = fetcher.get_stats()
        assert stats["total"] == 3
        assert stats["success"] == 2
        assert stats["skipped"] == 1
        assert stats["unpaywall"] == 2


def test_fetch_batch_with_progress_callback(temp_output_dir, session_id, test_papers):
    """Test batch processing with progress callback"""

    progress_calls = []

    def progress_callback(current, total, result):
        progress_calls.append((current, total, result.success))

    with patch.object(UnpaywallClient, 'fetch') as mock_fetch:
        mock_fetch.return_value = UnpaywallResult(
            success=True, doi="test", pdf_url="url"
        )

        fetcher = PDFFetcher(output_dir=temp_output_dir)
        fetcher.fetch_batch(test_papers, session_id, progress_callback=progress_callback)

        # Check callback was called
        assert len(progress_calls) == 3
        assert progress_calls[0] == (1, 3, True)
        assert progress_calls[1] == (2, 3, True)
        assert progress_calls[2] == (3, 3, True)


# ============================================
# Test Edge Cases
# ============================================

def test_paper_without_doi(temp_output_dir, session_id):
    """Test paper without DOI is skipped"""

    fetcher = PDFFetcher(output_dir=temp_output_dir)
    papers = [{"title": "Paper without DOI"}]

    results = fetcher.fetch_batch(papers, session_id)

    assert len(results) == 1
    assert results[0].success == False
    assert results[0].skipped == True
    assert "No DOI" in results[0].error


def test_cached_pdf_not_redownloaded(temp_output_dir, session_id):
    """Test that already downloaded PDF is not re-downloaded"""

    # Create fake cached PDF
    doi = "10.1371/journal.pone.0000001"
    safe_doi = doi.replace("/", "_").replace(".", "_")
    session_dir = temp_output_dir / session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    cached_pdf = session_dir / f"{safe_doi}.pdf"
    cached_pdf.write_bytes(b"fake pdf content")

    fetcher = PDFFetcher(output_dir=temp_output_dir)
    result = fetcher.fetch_single(doi, session_id)

    # Should return cached result without calling APIs
    assert result.success == True
    assert result.source == "cached"
    assert result.attempts == 0


# ============================================
# Test Rate Limiting
# ============================================

def test_rate_limiting_between_papers(temp_output_dir, session_id, test_papers):
    """Test that rate limiting happens between papers"""

    import time

    with patch.object(UnpaywallClient, 'fetch') as mock_fetch:
        mock_fetch.return_value = UnpaywallResult(
            success=True, doi="test", pdf_url="url"
        )

        with patch('time.sleep') as mock_sleep:
            fetcher = PDFFetcher(output_dir=temp_output_dir)
            fetcher.fetch_batch(test_papers, session_id)

            # Should have 2 sleep calls (between 3 papers: 0.5s each)
            assert mock_sleep.call_count == 2
            mock_sleep.assert_called_with(0.5)


# ============================================
# Test Output Path Generation
# ============================================

def test_output_path_sanitization(temp_output_dir, session_id):
    """Test that DOI is properly sanitized for filename"""

    fetcher = PDFFetcher(output_dir=temp_output_dir)

    # DOI with special chars
    doi = "10.1109/ACCESS.2021.1234567"
    output_path = fetcher._get_output_path(doi, session_id)

    # Should replace special chars with _
    assert "10_1109_ACCESS_2021_1234567" in str(output_path)
    assert output_path.suffix == ".pdf"
    assert session_id in str(output_path.parent)


# ============================================
# Run Tests
# ============================================

if __name__ == "__main__":
    """Run tests with pytest"""
    pytest.main([__file__, "-v", "--tb=short"])
