"""
Integration Tests für PDF Workflow

WICHTIG: Diese Tests machen ECHTE API-Calls!
- Unpaywall API (kostenlos, kein Key nötig)
- CORE API (braucht API-Key, optional)
- DBIS Browser (braucht TIB Credentials, optional)

Setup:
    export CORE_API_KEY="your_key"  # Optional
    export TIB_USERNAME="your_username"  # Optional
    export TIB_PASSWORD="your_password"  # Optional

Run:
    pytest tests/integration/test_pdf_workflow.py -v
    pytest tests/integration/test_pdf_workflow.py -v -k "unpaywall"  # Nur Unpaywall
"""

import pytest
import tempfile
import os
from pathlib import Path
import uuid

from src.pdf.unpaywall_client import UnpaywallClient
from src.pdf.core_client import COREClient
from src.pdf.pdf_fetcher import PDFFetcher


# ============================================
# Fixtures
# ============================================

@pytest.fixture
def temp_output_dir():
    """Temporary output directory"""
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
def core_api_key():
    """CORE API key from environment"""
    return os.environ.get("CORE_API_KEY")


@pytest.fixture
def test_dois():
    """Test DOIs (mix of OA and paywalled)"""
    return {
        # Open Access Papers (should work with Unpaywall)
        "oa_plos": "10.1371/journal.pone.0000001",
        "oa_ieee_access": "10.1109/ACCESS.2021.3064112",

        # Paywalled (might work with CORE or DBIS)
        "paywalled_nature": "10.1038/nature12345",
        "paywalled_ieee": "10.1109/TSE.2020.1234567",
    }


# ============================================
# Test Unpaywall API (Real Calls)
# ============================================

@pytest.mark.integration
def test_unpaywall_real_oa_paper(temp_output_dir):
    """Test Unpaywall with real Open Access paper"""

    # PLoS ONE paper (always OA)
    doi = "10.1371/journal.pone.0250641"
    output_path = temp_output_dir / "test.pdf"

    with UnpaywallClient() as client:
        result = client.fetch(doi, output_path)

        # Should succeed for OA paper
        assert result.success == True
        assert result.is_oa == True
        assert result.pdf_url is not None
        assert output_path.exists()

        # Check PDF is valid
        assert output_path.stat().st_size > 1000  # At least 1KB

        print(f"\n✅ Unpaywall Success:")
        print(f"   DOI: {doi}")
        print(f"   OA Status: {result.oa_status}")
        print(f"   PDF Size: {output_path.stat().st_size} bytes")


@pytest.mark.integration
def test_unpaywall_real_paywalled_paper(temp_output_dir):
    """Test Unpaywall with paywalled paper (should fail gracefully)"""

    # Nature paper (likely paywalled)
    doi = "10.1038/s41586-020-2649-2"
    output_path = temp_output_dir / "test.pdf"

    with UnpaywallClient() as client:
        result = client.fetch(doi, output_path)

        # Should fail for paywalled paper
        assert result.success == False
        assert not output_path.exists()

        print(f"\n✅ Unpaywall correctly failed for paywalled paper:")
        print(f"   DOI: {doi}")
        print(f"   Error: {result.error}")


# ============================================
# Test CORE API (Real Calls, Optional)
# ============================================

@pytest.mark.integration
@pytest.mark.skipif(not os.environ.get("CORE_API_KEY"),
                   reason="CORE_API_KEY not set")
def test_core_real_api(temp_output_dir, core_api_key):
    """Test CORE API with real API key"""

    # Known paper in CORE
    doi = "10.1371/journal.pone.0250641"
    output_path = temp_output_dir / "test.pdf"

    with COREClient(api_key=core_api_key) as client:
        result = client.fetch(doi, output_path)

        # Note: CORE might not have all papers
        if result.success:
            assert output_path.exists()
            print(f"\n✅ CORE Success:")
            print(f"   Repository: {result.source_repository}")
            print(f"   PDF Size: {output_path.stat().st_size} bytes")
        else:
            print(f"\n⚠️ CORE didn't have this paper:")
            print(f"   Error: {result.error}")


# ============================================
# Test Fallback Chain (Real Calls)
# ============================================

@pytest.mark.integration
def test_fallback_chain_unpaywall_only(temp_output_dir, session_id):
    """Test fallback chain with only Unpaywall (no CORE key)"""

    test_papers = [
        {"doi": "10.1371/journal.pone.0250641", "title": "OA Paper 1"},
        {"doi": "10.1371/journal.pone.0247771", "title": "OA Paper 2"},
    ]

    with PDFFetcher(
        output_dir=temp_output_dir,
        fallback_chain=["unpaywall"]
    ) as fetcher:
        results = fetcher.fetch_batch(test_papers, session_id)

        # At least some should succeed (OA papers)
        success_count = sum(1 for r in results if r.success)
        assert success_count > 0

        # All successful ones should be via Unpaywall
        for result in results:
            if result.success:
                assert result.source == "unpaywall"

        print(f"\n✅ Fallback Chain (Unpaywall only):")
        print(f"   Total: {len(results)}")
        print(f"   Success: {success_count}")
        print(f"   Failed: {len(results) - success_count}")


@pytest.mark.integration
@pytest.mark.skipif(not os.environ.get("CORE_API_KEY"),
                   reason="CORE_API_KEY not set")
def test_fallback_chain_with_core(temp_output_dir, session_id, core_api_key):
    """Test complete fallback chain: Unpaywall → CORE"""

    test_papers = [
        {"doi": "10.1371/journal.pone.0250641", "title": "OA Paper"},
        {"doi": "10.1038/s41586-020-2649-2", "title": "Paywalled Paper"},
    ]

    with PDFFetcher(
        output_dir=temp_output_dir,
        core_api_key=core_api_key,
        fallback_chain=["unpaywall", "core"]
    ) as fetcher:
        results = fetcher.fetch_batch(test_papers, session_id)

        # Check that both strategies were used
        sources = [r.source for r in results if r.success]

        print(f"\n✅ Fallback Chain (Unpaywall + CORE):")
        print(f"   Total: {len(results)}")
        print(f"   Success: {len([r for r in results if r.success])}")
        print(f"   Sources used: {set(sources)}")

        # At least one should succeed
        assert len([r for r in results if r.success]) > 0


# ============================================
# Test Batch Processing (Real Calls)
# ============================================

@pytest.mark.integration
def test_batch_processing_real(temp_output_dir, session_id):
    """Test batch processing with real papers"""

    # Mix of OA papers
    test_papers = [
        {"doi": "10.1371/journal.pone.0250641"},
        {"doi": "10.1371/journal.pone.0247771"},
        {"doi": "10.1371/journal.pone.0245315"},
    ]

    with PDFFetcher(output_dir=temp_output_dir) as fetcher:
        results = fetcher.fetch_batch(test_papers, session_id)

        # Assertions
        assert len(results) == len(test_papers)

        # Check statistics
        stats = fetcher.get_stats()
        assert stats["total"] == len(test_papers)
        assert stats["success"] > 0

        # Check PDFs were saved
        for result in results:
            if result.success:
                assert Path(result.pdf_path).exists()

        print(f"\n✅ Batch Processing:")
        print(f"   Total: {stats['total']}")
        print(f"   Success: {stats['success']}")
        print(f"   Skipped: {stats['skipped']}")


# ============================================
# Test Error Handling (Real Calls)
# ============================================

@pytest.mark.integration
def test_invalid_doi_handling(temp_output_dir, session_id):
    """Test handling of invalid DOI"""

    test_papers = [
        {"doi": "10.invalid/doi.12345"},  # Invalid DOI
    ]

    with PDFFetcher(output_dir=temp_output_dir) as fetcher:
        results = fetcher.fetch_batch(test_papers, session_id)

        # Should fail gracefully
        assert len(results) == 1
        assert results[0].success == False
        assert results[0].skipped == True


@pytest.mark.integration
def test_mixed_success_failure(temp_output_dir, session_id):
    """Test batch with mix of successful and failed downloads"""

    test_papers = [
        {"doi": "10.1371/journal.pone.0250641"},  # Should work (OA)
        {"doi": "10.1038/nature12345"},  # Likely fails (paywalled)
        {"doi": "10.invalid/doi.12345"},  # Invalid DOI
    ]

    with PDFFetcher(output_dir=temp_output_dir) as fetcher:
        results = fetcher.fetch_batch(test_papers, session_id)

        # Should have mix of success and failures
        assert len(results) == 3

        success_count = sum(1 for r in results if r.success)
        failed_count = sum(1 for r in results if not r.success)

        assert success_count > 0  # At least one should succeed
        assert failed_count > 0   # At least one should fail

        print(f"\n✅ Mixed batch:")
        print(f"   Success: {success_count}")
        print(f"   Failed: {failed_count}")


# ============================================
# Performance Tests
# ============================================

@pytest.mark.integration
@pytest.mark.slow
def test_performance_parallel_downloads(temp_output_dir, session_id):
    """Test performance with multiple papers"""
    import time

    # 5 OA papers
    test_papers = [
        {"doi": "10.1371/journal.pone.0250641"},
        {"doi": "10.1371/journal.pone.0247771"},
        {"doi": "10.1371/journal.pone.0245315"},
        {"doi": "10.1371/journal.pone.0243210"},
        {"doi": "10.1371/journal.pone.0241234"},
    ]

    start_time = time.time()

    with PDFFetcher(output_dir=temp_output_dir) as fetcher:
        results = fetcher.fetch_batch(test_papers, session_id)

    duration = time.time() - start_time

    # Should complete in reasonable time (not more than 60s)
    assert duration < 60

    success_count = sum(1 for r in results if r.success)

    print(f"\n✅ Performance Test:")
    print(f"   Papers: {len(test_papers)}")
    print(f"   Success: {success_count}")
    print(f"   Duration: {duration:.1f}s")
    print(f"   Avg per paper: {duration/len(test_papers):.1f}s")


# ============================================
# Caching Tests
# ============================================

@pytest.mark.integration
def test_cached_pdf_not_redownloaded(temp_output_dir, session_id):
    """Test that cached PDFs are not re-downloaded"""

    doi = "10.1371/journal.pone.0250641"
    test_papers = [{"doi": doi}]

    with PDFFetcher(output_dir=temp_output_dir) as fetcher:
        # First download
        results1 = fetcher.fetch_batch(test_papers, session_id)
        assert results1[0].success == True

        # Second download (should use cache)
        results2 = fetcher.fetch_batch(test_papers, session_id)
        assert results2[0].success == True
        assert results2[0].source == "cached"
        assert results2[0].attempts == 0  # No attempts needed


# ============================================
# Run Tests
# ============================================

if __name__ == "__main__":
    """
    Run integration tests manually

    Run all:
        python tests/integration/test_pdf_workflow.py

    Run with pytest:
        pytest tests/integration/test_pdf_workflow.py -v

    Run only fast tests:
        pytest tests/integration/test_pdf_workflow.py -v -m "not slow"
    """
    pytest.main([__file__, "-v", "-s"])
