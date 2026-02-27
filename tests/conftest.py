#!/usr/bin/env python3
"""
Pytest Configuration & Fixtures für AcademicAgent v2.0 Tests

Provides:
- Shared fixtures for all test types
- Mock objects for APIs, Browser, Database
- Test data generators
- Cleanup utilities
"""

import pytest
import tempfile
import json
import sqlite3
from pathlib import Path
from unittest.mock import Mock, MagicMock
from typing import Dict, Any, List


# ============================================================
# Path Fixtures
# ============================================================

@pytest.fixture
def project_root() -> Path:
    """Returns project root directory"""
    return Path(__file__).parent.parent


@pytest.fixture
def src_path(project_root) -> Path:
    """Returns src/ directory"""
    return project_root / "src"


@pytest.fixture
def temp_dir():
    """Creates temporary directory for test files"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_db(temp_dir):
    """Creates temporary SQLite database"""
    db_path = temp_dir / "test.db"
    conn = sqlite3.connect(str(db_path))
    yield conn
    conn.close()


# ============================================================
# Mock API Responses
# ============================================================

@pytest.fixture
def mock_crossref_response() -> Dict[str, Any]:
    """Mock CrossRef API response"""
    return {
        "status": "ok",
        "message-type": "work-list",
        "message": {
            "items": [
                {
                    "DOI": "10.1109/example.2024.001",
                    "title": ["Example Paper on Machine Learning"],
                    "author": [
                        {"given": "John", "family": "Doe"},
                        {"given": "Jane", "family": "Smith"}
                    ],
                    "published": {"date-parts": [[2024, 1, 15]]},
                    "container-title": ["IEEE Transactions"],
                    "abstract": "This paper explores machine learning techniques...",
                    "is-referenced-by-count": 42
                }
            ],
            "total-results": 1
        }
    }


@pytest.fixture
def mock_openalex_response() -> Dict[str, Any]:
    """Mock OpenAlex API response"""
    return {
        "results": [
            {
                "id": "https://openalex.org/W123456789",
                "doi": "https://doi.org/10.1109/example.2024.001",
                "title": "Example Paper on Machine Learning",
                "publication_date": "2024-01-15",
                "cited_by_count": 42,
                "authorships": [
                    {"author": {"display_name": "John Doe"}},
                    {"author": {"display_name": "Jane Smith"}}
                ],
                "primary_location": {
                    "source": {"display_name": "IEEE Transactions"}
                },
                "abstract_inverted_index": {
                    "This": [0],
                    "paper": [1],
                    "explores": [2]
                }
            }
        ]
    }


@pytest.fixture
def mock_semantic_scholar_response() -> Dict[str, Any]:
    """Mock Semantic Scholar API response"""
    return {
        "data": [
            {
                "paperId": "abc123",
                "externalIds": {"DOI": "10.1109/example.2024.001"},
                "title": "Example Paper on Machine Learning",
                "authors": [
                    {"name": "John Doe"},
                    {"name": "Jane Smith"}
                ],
                "year": 2024,
                "citationCount": 42,
                "abstract": "This paper explores machine learning techniques...",
                "venue": "IEEE Transactions"
            }
        ]
    }


@pytest.fixture
def mock_unpaywall_response() -> Dict[str, Any]:
    """Mock Unpaywall API response"""
    return {
        "doi": "10.1109/example.2024.001",
        "is_oa": True,
        "best_oa_location": {
            "url_for_pdf": "https://arxiv.org/pdf/2024.00001.pdf",
            "version": "submittedVersion",
            "license": "cc-by"
        }
    }


# ============================================================
# Test Data Fixtures
# ============================================================

@pytest.fixture
def sample_paper() -> Dict[str, Any]:
    """Sample paper metadata for testing"""
    return {
        "doi": "10.1109/example.2024.001",
        "title": "Example Paper on Machine Learning",
        "authors": ["John Doe", "Jane Smith"],
        "year": 2024,
        "venue": "IEEE Transactions",
        "abstract": "This paper explores machine learning techniques for natural language processing.",
        "citation_count": 42,
        "url": "https://doi.org/10.1109/example.2024.001"
    }


@pytest.fixture
def sample_papers() -> List[Dict[str, Any]]:
    """List of sample papers for testing"""
    return [
        {
            "doi": "10.1109/paper1.2024",
            "title": "Deep Learning for NLP",
            "authors": ["Alice Brown"],
            "year": 2024,
            "citation_count": 100
        },
        {
            "doi": "10.1145/paper2.2023",
            "title": "Transformers in Computer Vision",
            "authors": ["Bob White"],
            "year": 2023,
            "citation_count": 75
        },
        {
            "doi": "10.1007/paper3.2022",
            "title": "Reinforcement Learning Advances",
            "authors": ["Charlie Green"],
            "year": 2022,
            "citation_count": 50
        }
    ]


@pytest.fixture
def sample_query() -> str:
    """Sample research query"""
    return "machine learning transformers natural language processing"


@pytest.fixture
def sample_pdf_text() -> str:
    """Sample PDF text content"""
    return """
    Abstract

    This paper investigates the application of transformer models in natural language processing.
    We propose a novel architecture that improves upon existing methods.

    Introduction

    Machine learning has revolutionized the field of artificial intelligence.
    Recent advances in deep learning have enabled significant progress in NLP tasks.

    Methods

    We trained our model on a large corpus of text data using supervised learning.
    The architecture consists of multiple attention layers with residual connections.

    Results

    Our experiments show a 15% improvement over the baseline on benchmark datasets.
    Statistical significance was confirmed using paired t-tests (p < 0.01).

    Conclusion

    We demonstrated that our approach achieves state-of-the-art performance.
    Future work will explore applications to other domains.
    """


# ============================================================
# Mock Objects
# ============================================================

@pytest.fixture
def mock_api_client():
    """Mock API client with common methods"""
    client = Mock()
    client.search = Mock(return_value=[])
    client.get_by_doi = Mock(return_value=None)
    client.rate_limiter = Mock()
    return client


@pytest.fixture
def mock_browser():
    """Mock Playwright browser for testing"""
    browser = MagicMock()
    page = MagicMock()

    # Setup common browser methods
    browser.new_page = Mock(return_value=page)
    page.goto = Mock()
    page.wait_for_selector = Mock()
    page.click = Mock()
    page.fill = Mock()
    page.download = Mock()
    page.content = Mock(return_value="<html></html>")

    return browser


@pytest.fixture
def mock_state_manager():
    """Mock state manager for testing"""
    manager = Mock()
    manager.save_state = Mock()
    manager.load_state = Mock(return_value={})
    manager.get_checkpoint = Mock(return_value=None)
    manager.create_checkpoint = Mock()
    return manager


# ============================================================
# Test Configuration
# ============================================================

@pytest.fixture
def test_config() -> Dict[str, Any]:
    """Test configuration for v2.0"""
    return {
        "api_keys": {
            "anthropic": "test-key-123",
            "crossref_email": "test@example.com"
        },
        "search": {
            "max_results_per_source": 50,
            "deduplicate": True
        },
        "pdf": {
            "download_timeout": 30,
            "max_retries": 3,
            "fallback_chain": ["unpaywall", "core", "dbis"]
        },
        "scoring": {
            "weights": {
                "relevance": 0.35,
                "recency": 0.25,
                "authority": 0.20,
                "depth": 0.10,
                "diversity": 0.10
            }
        },
        "browser": {
            "headless": True,
            "timeout": 30000
        },
        "domain_validation": {
            "blocked_domains": [
                "sci-hub.*",
                "libgen.*",
                "z-library.*"
            ],
            "allowed_publishers": [
                "ieeexplore.ieee.org",
                "dl.acm.org",
                "link.springer.com",
                "arxiv.org"
            ]
        }
    }


# ============================================================
# Pytest Configuration
# ============================================================

def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "unit: Unit tests (fast, isolated)"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests (slower, uses real APIs)"
    )
    config.addinivalue_line(
        "markers", "e2e: End-to-end tests (slowest, full workflow)"
    )
    config.addinivalue_line(
        "markers", "slow: Slow tests (> 1 second)"
    )
    config.addinivalue_line(
        "markers", "requires_browser: Tests that require Playwright browser"
    )
    config.addinivalue_line(
        "markers", "requires_api_key: Tests that require real API keys"
    )


# ============================================================
# Cleanup Helpers
# ============================================================

@pytest.fixture(autouse=True)
def cleanup_test_files(temp_dir):
    """Automatically cleanup test files after each test"""
    yield
    # Cleanup is handled by temp_dir fixture
