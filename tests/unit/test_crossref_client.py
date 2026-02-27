"""
Unit Tests für CrossRef API Client

Run:
    pytest tests/unit/test_crossref_client.py -v
    pytest tests/unit/test_crossref_client.py -v --cov=src.search.crossref_client
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import httpx

from src.search.crossref_client import CrossRefClient, Paper, search_crossref


# ============================================
# Fixtures
# ============================================

@pytest.fixture
def mock_crossref_response():
    """Mock CrossRef API response"""
    return {
        "status": "ok",
        "message-type": "work-list",
        "message": {
            "items": [
                {
                    "DOI": "10.1109/test.2024.001",
                    "title": ["DevOps Governance Frameworks for Enterprise"],
                    "author": [
                        {"given": "John", "family": "Doe"},
                        {"given": "Jane", "family": "Smith"}
                    ],
                    "published": {"date-parts": [[2024, 3, 15]]},
                    "abstract": "<p>This paper presents governance frameworks...</p>",
                    "container-title": ["IEEE Software"],
                    "URL": "https://doi.org/10.1109/test.2024.001",
                    "is-referenced-by-count": 42
                },
                {
                    "DOI": "10.1145/test.2023.002",
                    "title": ["Compliance Automation in CI/CD Pipelines"],
                    "author": [
                        {"given": "Alice", "family": "Johnson"}
                    ],
                    "published": {"date-parts": [[2023, 6, 20]]},
                    "container-title": ["ACM Computing Surveys"],
                    "URL": "https://doi.org/10.1145/test.2023.002",
                    "is-referenced-by-count": 15
                }
            ]
        }
    }


@pytest.fixture
def mock_single_work():
    """Mock single CrossRef work"""
    return {
        "DOI": "10.1109/test.2024.001",
        "title": ["DevOps Governance Frameworks"],
        "author": [
            {"given": "John", "family": "Doe"}
        ],
        "published": {"date-parts": [[2024, 3, 15]]},
        "container-title": ["IEEE Software"],
        "is-referenced-by-count": 42
    }


# ============================================
# CrossRefClient Tests
# ============================================

class TestCrossRefClient:
    """Test CrossRefClient class"""

    def test_init_anonymous(self):
        """Test initialization without email (anonymous)"""
        client = CrossRefClient()
        assert client.email is None
        assert "AcademicAgentV2" in client.client.headers["User-Agent"]
        assert "mailto:" not in client.client.headers["User-Agent"]

    def test_init_with_email(self):
        """Test initialization with email (polite mode)"""
        client = CrossRefClient(email="test@example.com")
        assert client.email == "test@example.com"
        assert "mailto:test@example.com" in client.client.headers["User-Agent"]

    def test_build_user_agent_anonymous(self):
        """Test User-Agent header without email"""
        client = CrossRefClient()
        ua = client._build_user_agent()
        assert "AcademicAgentV2" in ua
        assert "mailto:" not in ua

    def test_build_user_agent_with_email(self):
        """Test User-Agent header with email"""
        client = CrossRefClient(email="test@example.com")
        ua = client._build_user_agent()
        assert "AcademicAgentV2" in ua
        assert "mailto:test@example.com" in ua

    @patch('src.search.crossref_client.httpx.Client')
    def test_search_success(self, mock_client_class, mock_crossref_response):
        """Test successful search"""
        # Mock HTTP response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_crossref_response

        mock_client_instance = Mock()
        mock_client_instance.get.return_value = mock_response
        mock_client_class.return_value = mock_client_instance

        # Search
        client = CrossRefClient()
        papers = client.search("DevOps Governance", limit=2)

        # Assertions
        assert len(papers) == 2
        assert papers[0].doi == "10.1109/test.2024.001"
        assert papers[0].title == "DevOps Governance Frameworks for Enterprise"
        assert len(papers[0].authors) == 2
        assert papers[0].year == 2024
        assert papers[0].venue == "IEEE Software"
        assert papers[0].citations == 42

    @patch('src.search.crossref_client.httpx.Client')
    def test_search_with_filters(self, mock_client_class, mock_crossref_response):
        """Test search with filters"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_crossref_response

        mock_client_instance = Mock()
        mock_client_instance.get.return_value = mock_response
        mock_client_class.return_value = mock_client_instance

        client = CrossRefClient()
        filters = {"type": "journal-article", "from-pub-date": "2020"}
        papers = client.search("DevOps", limit=5, filters=filters)

        # Check filter params were passed
        call_args = mock_client_instance.get.call_args
        assert "type" in call_args[1]["params"]
        assert "from-pub-date" in call_args[1]["params"]

    @patch('src.search.crossref_client.httpx.Client')
    def test_search_empty_results(self, mock_client_class):
        """Test search with no results"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "message": {"items": []}
        }

        mock_client_instance = Mock()
        mock_client_instance.get.return_value = mock_response
        mock_client_class.return_value = mock_client_instance

        client = CrossRefClient()
        papers = client.search("asdfqwerzxcv12345", limit=10)

        assert len(papers) == 0

    @patch('src.search.crossref_client.httpx.Client')
    def test_search_timeout(self, mock_client_class):
        """Test search timeout handling"""
        mock_client_instance = Mock()
        mock_client_instance.get.side_effect = httpx.TimeoutException("Timeout")
        mock_client_class.return_value = mock_client_instance

        client = CrossRefClient()
        papers = client.search("DevOps", limit=5)

        # Should return empty list on timeout
        assert len(papers) == 0

    @patch('src.search.crossref_client.httpx.Client')
    def test_get_by_doi_success(self, mock_client_class, mock_single_work):
        """Test get_by_doi with valid DOI"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"message": mock_single_work}

        mock_client_instance = Mock()
        mock_client_instance.get.return_value = mock_response
        mock_client_class.return_value = mock_client_instance

        client = CrossRefClient()
        paper = client.get_by_doi("10.1109/test.2024.001")

        assert paper is not None
        assert paper.doi == "10.1109/test.2024.001"
        assert paper.title == "DevOps Governance Frameworks"

    @patch('src.search.crossref_client.httpx.Client')
    def test_get_by_doi_not_found(self, mock_client_class):
        """Test get_by_doi with invalid DOI"""
        mock_response = Mock()
        mock_response.status_code = 404

        mock_client_instance = Mock()
        mock_client_instance.get.return_value = mock_response
        mock_client_class.return_value = mock_client_instance

        client = CrossRefClient()
        paper = client.get_by_doi("10.1109/invalid.doi")

        assert paper is None

    def test_parse_work_complete(self, mock_single_work):
        """Test _parse_work with complete data"""
        client = CrossRefClient()
        paper = client._parse_work(mock_single_work)

        assert paper.doi == "10.1109/test.2024.001"
        assert paper.title == "DevOps Governance Frameworks"
        assert len(paper.authors) == 1
        assert "John Doe" in paper.authors
        assert paper.year == 2024
        assert paper.venue == "IEEE Software"
        assert paper.citations == 42
        assert paper.source_api == "crossref"

    def test_parse_work_minimal(self):
        """Test _parse_work with minimal data"""
        minimal_work = {
            "DOI": "10.1234/minimal",
            "title": ["Minimal Paper"]
        }

        client = CrossRefClient()
        paper = client._parse_work(minimal_work)

        assert paper.doi == "10.1234/minimal"
        assert paper.title == "Minimal Paper"
        assert paper.authors == []
        assert paper.year is None
        assert paper.venue is None

    def test_parse_work_missing_title(self):
        """Test _parse_work with missing title"""
        work = {
            "DOI": "10.1234/notitle",
            "title": []
        }

        client = CrossRefClient()
        paper = client._parse_work(work)

        assert paper.title == "Untitled"

    def test_strip_xml_tags(self):
        """Test XML tag stripping"""
        client = CrossRefClient()

        text = "<p>This is <b>bold</b> text</p>"
        result = client._strip_xml_tags(text)
        assert result == "This is bold text"

        text = "Plain text without tags"
        result = client._strip_xml_tags(text)
        assert result == "Plain text without tags"

    def test_context_manager(self):
        """Test context manager usage"""
        with CrossRefClient() as client:
            assert client is not None
            assert client.client is not None

    @patch('src.search.crossref_client.httpx.Client')
    def test_rate_limiting(self, mock_client_class, mock_crossref_response):
        """Test rate limiting is applied"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_crossref_response

        mock_client_instance = Mock()
        mock_client_instance.get.return_value = mock_response
        mock_client_class.return_value = mock_client_instance

        client = CrossRefClient(rate_limit=50)

        # Make multiple requests
        for _ in range(3):
            client.search("test", limit=1)

        # Rate limiter should have been called
        assert mock_client_instance.get.call_count == 3


# ============================================
# Paper Model Tests
# ============================================

class TestPaper:
    """Test Paper data model"""

    def test_paper_init(self):
        """Test Paper initialization"""
        paper = Paper(
            doi="10.1234/test",
            title="Test Paper",
            authors=["John Doe", "Jane Smith"],
            year=2024,
            venue="Test Journal"
        )

        assert paper.doi == "10.1234/test"
        assert paper.title == "Test Paper"
        assert len(paper.authors) == 2
        assert paper.year == 2024
        assert paper.venue == "Test Journal"
        assert paper.source_api == "crossref"

    def test_paper_repr(self):
        """Test Paper string representation"""
        paper = Paper(
            doi="10.1234/test",
            title="A" * 100,  # Long title
            authors=["John Doe"]
        )

        repr_str = repr(paper)
        assert "10.1234/test" in repr_str
        assert len(repr_str) < 150  # Title should be truncated

    def test_paper_to_dict(self):
        """Test Paper to_dict conversion"""
        paper = Paper(
            doi="10.1234/test",
            title="Test Paper",
            authors=["John Doe"],
            year=2024,
            citations=10
        )

        d = paper.to_dict()
        assert d["doi"] == "10.1234/test"
        assert d["title"] == "Test Paper"
        assert d["authors"] == ["John Doe"]
        assert d["year"] == 2024
        assert d["citations"] == 10


# ============================================
# Convenience Function Tests
# ============================================

@patch('src.search.crossref_client.CrossRefClient')
def test_search_crossref_convenience(mock_client_class, mock_crossref_response):
    """Test search_crossref convenience function"""
    mock_client_instance = Mock()
    mock_client_instance.search.return_value = [
        Paper(doi="10.1234/test", title="Test", authors=["A"])
    ]
    mock_client_instance.__enter__.return_value = mock_client_instance
    mock_client_instance.__exit__.return_value = False
    mock_client_class.return_value = mock_client_instance

    papers = search_crossref("DevOps", limit=5, email="test@example.com")

    assert len(papers) == 1
    mock_client_class.assert_called_once_with(email="test@example.com")
    mock_client_instance.search.assert_called_once_with("DevOps", limit=5)
