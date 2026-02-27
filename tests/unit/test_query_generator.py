"""
Unit Tests für Query Generator

Run:
    pytest tests/unit/test_query_generator.py -v
    pytest tests/unit/test_query_generator.py -v --cov=src.search.query_generator
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json

from src.search.query_generator import QueryGenerator, generate_queries


# ============================================
# Fixtures
# ============================================

@pytest.fixture
def mock_anthropic_response():
    """Mock Anthropic API response"""
    return {
        "queries": {
            "crossref": '"DevOps" AND ("governance" OR "compliance")',
            "openalex": "DevOps AND governance",
            "semantic_scholar": "DevOps governance compliance"
        },
        "keywords_used": ["DevOps", "governance", "compliance"],
        "reasoning": "Expanded governance to include compliance"
    }


# ============================================
# QueryGenerator Tests
# ============================================

class TestQueryGenerator:
    """Test QueryGenerator class"""

    def test_init_without_api_key(self):
        """Test initialization without Anthropic API key"""
        generator = QueryGenerator()
        assert generator.client is None
        assert generator.model == "claude-haiku-4"

    def test_init_with_api_key(self):
        """Test initialization with Anthropic API key"""
        generator = QueryGenerator(anthropic_api_key="test-key")
        assert generator.client is not None
        assert generator.api_key == "test-key"

    def test_fallback_generate_crossref(self):
        """Test fallback query generation for CrossRef"""
        generator = QueryGenerator()  # No API key
        queries = generator._fallback_generate("DevOps Governance", ["crossref"])

        assert "crossref" in queries
        assert '"DevOps"' in queries["crossref"]
        assert '"Governance"' in queries["crossref"]
        assert "AND" in queries["crossref"]

    def test_fallback_generate_openalex(self):
        """Test fallback query generation for OpenAlex"""
        generator = QueryGenerator()
        queries = generator._fallback_generate("Machine Learning", ["openalex"])

        assert "openalex" in queries
        assert "Machine" in queries["openalex"]
        assert "Learning" in queries["openalex"]
        assert "AND" in queries["openalex"]

    def test_fallback_generate_semantic_scholar(self):
        """Test fallback query generation for Semantic Scholar"""
        generator = QueryGenerator()
        queries = generator._fallback_generate("AI Ethics", ["semantic_scholar"])

        assert "semantic_scholar" in queries
        assert queries["semantic_scholar"] == "AI Ethics"  # Natural language

    def test_fallback_generate_all_apis(self):
        """Test fallback generation for all APIs"""
        generator = QueryGenerator()
        queries = generator._fallback_generate(
            "DevOps Governance",
            ["crossref", "openalex", "semantic_scholar"]
        )

        assert len(queries) == 3
        assert "crossref" in queries
        assert "openalex" in queries
        assert "semantic_scholar" in queries

    @patch('src.search.query_generator.Anthropic')
    def test_generate_with_haiku(self, mock_anthropic_class, mock_anthropic_response):
        """Test query generation with Haiku"""
        # Mock Anthropic client
        mock_client = Mock()
        mock_response = Mock()
        mock_response.content = [Mock(text=json.dumps(mock_anthropic_response))]
        mock_client.messages.create.return_value = mock_response
        mock_anthropic_class.return_value = mock_client

        # Generate
        generator = QueryGenerator(anthropic_api_key="test-key")
        queries = generator.generate("DevOps Governance")

        # Assertions
        assert len(queries) == 3
        assert queries["crossref"] == '"DevOps" AND ("governance" OR "compliance")'
        assert queries["openalex"] == "DevOps AND governance"
        assert queries["semantic_scholar"] == "DevOps governance compliance"

    @patch('src.search.query_generator.Anthropic')
    def test_generate_with_haiku_failure_uses_fallback(self, mock_anthropic_class):
        """Test that fallback is used when Haiku fails"""
        # Mock Anthropic client to raise exception
        mock_client = Mock()
        mock_client.messages.create.side_effect = Exception("API Error")
        mock_anthropic_class.return_value = mock_client

        # Generate
        generator = QueryGenerator(anthropic_api_key="test-key")
        queries = generator.generate("DevOps Governance")

        # Should use fallback
        assert len(queries) == 3
        assert "crossref" in queries
        assert "DevOps" in queries["crossref"]

    def test_generate_without_api_key_uses_fallback(self):
        """Test that fallback is used when no API key"""
        generator = QueryGenerator()  # No API key
        queries = generator.generate("Machine Learning Ethics")

        assert len(queries) == 3
        assert "crossref" in queries
        assert "openalex" in queries
        assert "semantic_scholar" in queries

    def test_generate_with_academic_context(self):
        """Test generation with academic context"""
        generator = QueryGenerator()
        queries = generator.generate(
            "DevOps Governance",
            academic_context={"keywords": ["CI/CD", "Compliance"]}
        )

        # Fallback should still work with context
        assert len(queries) == 3

    def test_generate_single_api(self):
        """Test generation for single API"""
        generator = QueryGenerator()
        queries = generator.generate("AI Ethics", target_apis=["crossref"])

        assert len(queries) == 1
        assert "crossref" in queries

    def test_build_prompt(self):
        """Test prompt building"""
        generator = QueryGenerator()
        prompt = generator._build_prompt(
            "DevOps Governance",
            ["crossref", "openalex"],
            None
        )

        assert "DevOps Governance" in prompt
        assert "crossref" in prompt
        assert "openalex" in prompt
        assert "CrossRef" in prompt  # Should contain API-specific rules
        assert "Boolean" in prompt

    def test_build_prompt_with_context(self):
        """Test prompt building with academic context"""
        generator = QueryGenerator()
        prompt = generator._build_prompt(
            "DevOps",
            ["crossref"],
            {"keywords": ["CI/CD", "Compliance"]}
        )

        assert "DevOps" in prompt
        assert "CI/CD" in prompt
        assert "Compliance" in prompt
        assert "academic_context" in prompt

    def test_parse_response_valid_json(self, mock_anthropic_response):
        """Test parsing valid JSON response"""
        generator = QueryGenerator()
        content = json.dumps(mock_anthropic_response)

        queries = generator._parse_response(content)

        assert len(queries) == 3
        assert queries["crossref"] == '"DevOps" AND ("governance" OR "compliance")'

    def test_parse_response_json_in_markdown(self, mock_anthropic_response):
        """Test parsing JSON embedded in markdown"""
        generator = QueryGenerator()
        content = f"Here are the queries:\n```json\n{json.dumps(mock_anthropic_response)}\n```"

        queries = generator._parse_response(content)

        assert len(queries) == 3

    def test_parse_response_invalid_json(self):
        """Test parsing invalid JSON returns empty dict"""
        generator = QueryGenerator()
        content = "This is not JSON at all"

        queries = generator._parse_response(content)

        assert queries == {}

    def test_parse_response_no_queries_key(self):
        """Test parsing JSON without queries key"""
        generator = QueryGenerator()
        content = json.dumps({"other_key": "value"})

        queries = generator._parse_response(content)

        assert queries == {}


# ============================================
# Convenience Function Tests
# ============================================

def test_generate_queries_convenience():
    """Test generate_queries convenience function"""
    queries = generate_queries("DevOps Governance")

    assert len(queries) == 3
    assert "crossref" in queries
    assert "openalex" in queries
    assert "semantic_scholar" in queries

def test_generate_queries_with_api_key():
    """Test convenience function with API key"""
    queries = generate_queries(
        "AI Ethics",
        api_key=None  # Will use fallback
    )

    assert len(queries) == 3


# ============================================
# Integration Test (Optional - requires API key)
# ============================================

@pytest.mark.skipif(
    not pytest.config.getoption("--run-integration"),
    reason="Integration tests require --run-integration flag"
)
def test_haiku_integration_real():
    """
    Integration test with real Haiku API

    Run with:
        pytest tests/unit/test_query_generator.py -v --run-integration

    Requires:
        export ANTHROPIC_API_KEY="your-key"
    """
    import os

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        pytest.skip("ANTHROPIC_API_KEY not set")

    generator = QueryGenerator(anthropic_api_key=api_key)
    queries = generator.generate("DevOps Governance")

    # Real Haiku should return queries
    assert len(queries) > 0
    assert "crossref" in queries or "openalex" in queries
    print(f"\n✅ Real Haiku Integration Test:")
    print(f"   Queries: {queries}")


# ============================================
# Pytest Configuration
# ============================================

def pytest_addoption(parser):
    """Add custom pytest options"""
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="Run integration tests (requires API keys)"
    )
