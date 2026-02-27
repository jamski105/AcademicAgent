#!/usr/bin/env python3
"""
Unit Tests für src/ranking/llm_relevance_scorer.py
Tests with mocked Anthropic API
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json

from src.ranking.llm_relevance_scorer import LLMRelevanceScorer
from src.search.crossref_client import Paper


class TestInitialization:
    """Tests für Initialisierung"""

    @patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'})
    def test_init_with_api_key_from_env(self):
        """Test: API Key aus Environment Variable"""
        scorer = LLMRelevanceScorer()

        assert scorer.api_key == 'test-key'
        assert scorer.client is not None

    def test_init_with_explicit_api_key(self):
        """Test: Expliziter API Key"""
        scorer = LLMRelevanceScorer(anthropic_api_key='my-key')

        assert scorer.api_key == 'my-key'

    @patch.dict('os.environ', {}, clear=True)
    def test_init_without_key_uses_fallback(self):
        """Test: Ohne Key wird Fallback aktiviert"""
        scorer = LLMRelevanceScorer(use_fallback_if_no_key=True)

        assert scorer.client is None
        assert scorer.use_fallback is True

    @patch.dict('os.environ', {}, clear=True)
    def test_init_without_key_raises_error_if_no_fallback(self):
        """Test: Ohne Key und ohne Fallback gibt Fehler"""
        with pytest.raises(ValueError, match="API key required"):
            LLMRelevanceScorer(use_fallback_if_no_key=False)


class TestFallbackScoring:
    """Tests für Fallback Keyword-Scoring"""

    @patch.dict('os.environ', {}, clear=True)
    def test_fallback_scores_relevant_paper_high(self):
        """Test: Fallback gibt relevantem Paper hohen Score"""
        scorer = LLMRelevanceScorer(use_fallback_if_no_key=True)

        papers = [
            Paper(doi="10.1",
                  title="DevOps Governance Frameworks",
                  authors=["A"],
                  abstract="This paper discusses governance in DevOps")
        ]

        scores = scorer.score_batch(papers, "DevOps Governance")

        assert "10.1" in scores
        assert scores["10.1"] > 0.7

    @patch.dict('os.environ', {}, clear=True)
    def test_fallback_scores_irrelevant_paper_low(self):
        """Test: Fallback gibt irrelevantem Paper niedrigen Score"""
        scorer = LLMRelevanceScorer(use_fallback_if_no_key=True)

        papers = [
            Paper(doi="10.1",
                  title="Machine Learning Ethics",
                  authors=["A"],
                  abstract="Deep learning fairness")
        ]

        scores = scorer.score_batch(papers, "DevOps Governance")

        assert scores["10.1"] < 0.3

    @patch.dict('os.environ', {}, clear=True)
    def test_fallback_title_weighted_more_than_abstract(self):
        """Test: Title hat höheres Gewicht (0.7) als Abstract (0.3)"""
        scorer = LLMRelevanceScorer(use_fallback_if_no_key=True)

        # Paper mit Match nur in Title
        paper1 = Paper(doi="10.1",
                       title="DevOps Governance",
                       authors=["A"],
                       abstract="Some other topic here")

        # Paper mit Match nur in Abstract
        paper2 = Paper(doi="10.2",
                       title="Software Engineering",
                       authors=["B"],
                       abstract="DevOps Governance is important")

        scores = scorer.score_batch([paper1, paper2], "DevOps Governance")

        # Title-Match sollte höher gewichtet sein
        assert scores["10.1"] > scores["10.2"]


class TestHaikuScoring:
    """Tests für Haiku-basiertes Scoring"""

    @patch('anthropic.Anthropic')
    def test_haiku_call_returns_scores(self, mock_anthropic_class):
        """Test: Haiku gibt Scores zurück"""
        # Mock Anthropic Client
        mock_client = Mock()
        mock_response = Mock()
        mock_response.content = [Mock(text=json.dumps({
            "scores": [
                {"doi": "10.1", "score": 0.95, "reasoning": "Highly relevant"}
            ]
        }))]
        mock_client.messages.create.return_value = mock_response
        mock_anthropic_class.return_value = mock_client

        scorer = LLMRelevanceScorer(anthropic_api_key='test-key')
        papers = [Paper(doi="10.1", title="Test", authors=["A"])]

        scores = scorer.score_batch(papers, "test query")

        assert "10.1" in scores
        assert scores["10.1"] == 0.95

    @patch('anthropic.Anthropic')
    def test_haiku_call_with_multiple_papers(self, mock_anthropic_class):
        """Test: Batch mit mehreren Papers"""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.content = [Mock(text=json.dumps({
            "scores": [
                {"doi": "10.1", "score": 0.9},
                {"doi": "10.2", "score": 0.6},
                {"doi": "10.3", "score": 0.3}
            ]
        }))]
        mock_client.messages.create.return_value = mock_response
        mock_anthropic_class.return_value = mock_client

        scorer = LLMRelevanceScorer(anthropic_api_key='test-key')
        papers = [
            Paper(doi="10.1", title="A", authors=["A"]),
            Paper(doi="10.2", title="B", authors=["B"]),
            Paper(doi="10.3", title="C", authors=["C"])
        ]

        scores = scorer.score_batch(papers, "query")

        assert len(scores) == 3
        assert scores["10.1"] == 0.9
        assert scores["10.2"] == 0.6
        assert scores["10.3"] == 0.3

    @patch('anthropic.Anthropic')
    def test_haiku_fallback_on_error(self, mock_anthropic_class):
        """Test: Bei Haiku-Fehler wird Fallback genutzt"""
        mock_client = Mock()
        mock_client.messages.create.side_effect = Exception("API Error")
        mock_anthropic_class.return_value = mock_client

        scorer = LLMRelevanceScorer(anthropic_api_key='test-key')
        papers = [Paper(doi="10.1", title="DevOps", authors=["A"])]

        # Sollte nicht crashen, sondern Fallback nutzen
        scores = scorer.score_batch(papers, "DevOps")

        assert "10.1" in scores
        assert 0.0 <= scores["10.1"] <= 1.0


class TestPromptBuilding:
    """Tests für Prompt-Erstellung"""

    def test_prompt_contains_query(self):
        """Test: Prompt enthält Query"""
        scorer = LLMRelevanceScorer(anthropic_api_key='test-key')
        papers = [Paper(doi="10.1", title="Test", authors=["A"])]

        prompt = scorer._build_prompt(papers, "DevOps Governance")

        assert "DevOps Governance" in prompt

    def test_prompt_contains_paper_title(self):
        """Test: Prompt enthält Paper-Title"""
        scorer = LLMRelevanceScorer(anthropic_api_key='test-key')
        papers = [Paper(doi="10.1", title="My Paper Title", authors=["A"])]

        prompt = scorer._build_prompt(papers, "query")

        assert "My Paper Title" in prompt

    def test_prompt_contains_abstract(self):
        """Test: Prompt enthält Abstract (truncated)"""
        scorer = LLMRelevanceScorer(anthropic_api_key='test-key')
        papers = [Paper(doi="10.1", title="Test", authors=["A"],
                       abstract="Long abstract here" * 50)]

        prompt = scorer._build_prompt(papers, "query")

        assert "abstract" in prompt.lower()


class TestResponseParsing:
    """Tests für Response-Parsing"""

    def test_parse_valid_json_response(self):
        """Test: Valides JSON wird geparst"""
        scorer = LLMRelevanceScorer(anthropic_api_key='test-key')
        papers = [Paper(doi="10.1", title="Test", authors=["A"])]

        content = json.dumps({
            "scores": [
                {"doi": "10.1", "score": 0.85, "reasoning": "Good match"}
            ]
        })

        scores = scorer._parse_response(content, papers)

        assert scores["10.1"] == 0.85

    def test_parse_json_with_extra_text(self):
        """Test: JSON mit Extra-Text wird extrahiert"""
        scorer = LLMRelevanceScorer(anthropic_api_key='test-key')
        papers = [Paper(doi="10.1", title="Test", authors=["A"])]

        content = 'Here is my analysis:\n' + json.dumps({
            "scores": [{"doi": "10.1", "score": 0.9}]
        }) + '\nThat is all.'

        scores = scorer._parse_response(content, papers)

        assert scores["10.1"] == 0.9

    def test_parse_invalid_json_returns_empty(self):
        """Test: Invalides JSON gibt leeres Dict zurück"""
        scorer = LLMRelevanceScorer(anthropic_api_key='test-key')
        papers = [Paper(doi="10.1", title="Test", authors=["A"])]

        content = "This is not JSON at all"

        scores = scorer._parse_response(content, papers)

        assert scores == {}

    def test_parse_missing_scores_key(self):
        """Test: Fehlendes 'scores' Key"""
        scorer = LLMRelevanceScorer(anthropic_api_key='test-key')
        papers = [Paper(doi="10.1", title="Test", authors=["A"])]

        content = json.dumps({"other_key": "value"})

        scores = scorer._parse_response(content, papers)

        assert scores == {}


class TestBatchProcessing:
    """Tests für Batch-Processing"""

    @patch('anthropic.Anthropic')
    def test_batch_size_respected(self, mock_anthropic_class):
        """Test: Batch-Size wird respektiert"""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.content = [Mock(text=json.dumps({"scores": []}))]
        mock_client.messages.create.return_value = mock_response
        mock_anthropic_class.return_value = mock_client

        scorer = LLMRelevanceScorer(anthropic_api_key='test-key')

        # 15 papers mit batch_size=10 → 2 Batches
        papers = [Paper(doi=f"10.{i}", title="Test", authors=["A"])
                  for i in range(15)]

        scorer.score_batch(papers, "query", batch_size=10)

        # Sollte 2x aufgerufen werden
        assert mock_client.messages.create.call_count == 2

    @patch.dict('os.environ', {}, clear=True)
    def test_empty_papers_returns_empty_dict(self):
        """Test: Leere Liste gibt leeres Dict"""
        scorer = LLMRelevanceScorer(use_fallback_if_no_key=True)

        scores = scorer.score_batch([], "query")

        assert scores == {}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
