#!/usr/bin/env python3
"""
Unit Tests für src/ranking/ranking_engine.py
Tests RankingEngine Orchestrator
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from src.ranking.ranking_engine import RankingEngine, rank_papers
from src.search.crossref_client import Paper


class TestInitialization:
    """Tests für Engine-Initialisierung"""

    def test_init_without_config(self):
        """Test: Init ohne Config funktioniert"""
        engine = RankingEngine()

        assert engine.five_d_scorer is not None
        assert engine.research_config is None

    def test_init_with_llm_disabled(self):
        """Test: Init mit LLM deaktiviert"""
        engine = RankingEngine(use_llm_relevance=False)

        assert engine.llm_scorer is None

    @patch('src.ranking.ranking_engine.LLMRelevanceScorer')
    def test_init_with_api_key(self, mock_llm_class):
        """Test: Init mit API Key"""
        mock_llm_class.return_value = Mock()

        engine = RankingEngine(anthropic_api_key='test-key')

        mock_llm_class.assert_called_once()

    @patch('src.ranking.ranking_engine.LLMRelevanceScorer')
    def test_init_handles_llm_scorer_failure(self, mock_llm_class):
        """Test: LLM-Scorer Fehler wird behandelt"""
        mock_llm_class.side_effect = Exception("Init failed")

        engine = RankingEngine(use_llm_relevance=True)

        # Sollte nicht crashen, llm_scorer sollte None sein
        assert engine.llm_scorer is None


class TestRankMethod:
    """Tests für rank() Method"""

    def test_rank_empty_papers_returns_empty(self):
        """Test: Leere Liste gibt leere Liste"""
        engine = RankingEngine(use_llm_relevance=False)

        result = engine.rank([], "query")

        assert result == []

    def test_rank_returns_papers_in_order(self):
        """Test: Papers werden sortiert zurückgegeben"""
        engine = RankingEngine(use_llm_relevance=False)

        papers = [
            Paper(doi="10.1", title="Old", authors=["A"],
                  year=2010, citations=5),
            Paper(doi="10.2", title="Relevant Query", authors=["B"],
                  year=2024, citations=100, venue="IEEE")
        ]

        result = engine.rank(papers, "Relevant Query")

        assert len(result) == 2
        # Zweites Paper sollte höher ranken (relevant + recent + citations)
        assert result[0].doi == "10.2"

    def test_rank_respects_top_n(self):
        """Test: top_n limitiert Ergebnis"""
        engine = RankingEngine(use_llm_relevance=False)

        papers = [
            Paper(doi=f"10.{i}", title="Test", authors=["A"])
            for i in range(10)
        ]

        result = engine.rank(papers, "query", top_n=5)

        assert len(result) == 5

    def test_rank_without_top_n_returns_all(self):
        """Test: Ohne top_n werden alle Papers zurückgegeben"""
        engine = RankingEngine(use_llm_relevance=False)

        papers = [Paper(doi=f"10.{i}", title="Test", authors=["A"])
                  for i in range(10)]

        result = engine.rank(papers, "query", top_n=None)

        assert len(result) == 10

    @patch('src.ranking.ranking_engine.LLMRelevanceScorer')
    def test_rank_uses_llm_scores_if_available(self, mock_llm_class):
        """Test: LLM-Scores werden genutzt wenn verfügbar"""
        mock_llm = Mock()
        mock_llm.score_batch.return_value = {"10.1": 0.95, "10.2": 0.5}
        mock_llm_class.return_value = mock_llm

        engine = RankingEngine(anthropic_api_key='test-key')

        papers = [
            Paper(doi="10.1", title="Test1", authors=["A"]),
            Paper(doi="10.2", title="Test2", authors=["B"])
        ]

        result = engine.rank(papers, "query")

        # LLM-Scorer sollte aufgerufen worden sein
        mock_llm.score_batch.assert_called_once()

    @patch('src.ranking.ranking_engine.LLMRelevanceScorer')
    def test_rank_handles_llm_scoring_failure(self, mock_llm_class):
        """Test: LLM-Fehler wird behandelt"""
        mock_llm = Mock()
        mock_llm.score_batch.side_effect = Exception("API Error")
        mock_llm_class.return_value = mock_llm

        engine = RankingEngine(anthropic_api_key='test-key')

        papers = [Paper(doi="10.1", title="Test", authors=["A"])]

        # Sollte nicht crashen, sondern mit Fallback weitermachen
        result = engine.rank(papers, "query")

        assert len(result) == 1


class TestRankWithScoresMethod:
    """Tests für rank_with_scores() Method"""

    def test_rank_with_scores_returns_scores(self):
        """Test: rank_with_scores() gibt Scores zurück"""
        engine = RankingEngine(use_llm_relevance=False)

        papers = [Paper(doi="10.1", title="Test", authors=["A"], year=2024)]

        result = engine.rank_with_scores(papers, "query")

        assert len(result) == 1
        assert "paper" in result[0]
        assert "scores" in result[0]
        assert "total" in result[0]["scores"]
        assert "relevance" in result[0]["scores"]
        assert "recency" in result[0]["scores"]

    def test_rank_with_scores_respects_top_n(self):
        """Test: top_n wird respektiert"""
        engine = RankingEngine(use_llm_relevance=False)

        papers = [Paper(doi=f"10.{i}", title="Test", authors=["A"])
                  for i in range(10)]

        result = engine.rank_with_scores(papers, "query", top_n=3)

        assert len(result) == 3


class TestWeightLoading:
    """Tests für Weight-Loading aus Config"""

    def test_get_weights_without_config_returns_defaults(self):
        """Test: Ohne Config werden Defaults genutzt"""
        engine = RankingEngine()

        weights = engine._get_weights("standard")

        assert weights["relevance_weight"] == 0.4
        assert weights["recency_weight"] == 0.2
        assert weights["quality_weight"] == 0.2
        assert weights["authority_weight"] == 0.2

    def test_get_weights_with_invalid_mode_falls_back_to_standard(self):
        """Test: Invalider Mode fällt zurück auf 'standard'"""
        mock_config = Mock()
        mock_config.modes = {
            "standard": Mock(
                scoring=Mock(
                    relevance_weight=0.4,
                    recency_weight=0.2,
                    quality_weight=0.2,
                    authority_weight=0.2,
                    apply_portfolio_balance=False
                )
            )
        }

        engine = RankingEngine(research_config=mock_config)

        weights = engine._get_weights("invalid_mode")

        # Sollte Standard-Weights nutzen
        assert weights["relevance_weight"] == 0.4

    def test_get_weights_with_config_error_uses_defaults(self):
        """Test: Config-Fehler führt zu Defaults"""
        mock_config = Mock()
        mock_config.modes.get.side_effect = Exception("Config error")

        engine = RankingEngine(research_config=mock_config)

        weights = engine._get_weights("standard")

        # Sollte Defaults nutzen
        assert weights["relevance_weight"] == 0.4


class TestModeParameter:
    """Tests für Research Mode Parameter"""

    def test_rank_accepts_quick_mode(self):
        """Test: Quick Mode wird akzeptiert"""
        engine = RankingEngine(use_llm_relevance=False)

        papers = [Paper(doi="10.1", title="Test", authors=["A"])]

        result = engine.rank(papers, "query", mode="quick")

        assert len(result) == 1

    def test_rank_accepts_standard_mode(self):
        """Test: Standard Mode wird akzeptiert"""
        engine = RankingEngine(use_llm_relevance=False)

        papers = [Paper(doi="10.1", title="Test", authors=["A"])]

        result = engine.rank(papers, "query", mode="standard")

        assert len(result) == 1

    def test_rank_accepts_deep_mode(self):
        """Test: Deep Mode wird akzeptiert"""
        engine = RankingEngine(use_llm_relevance=False)

        papers = [Paper(doi="10.1", title="Test", authors=["A"])]

        result = engine.rank(papers, "query", mode="deep")

        assert len(result) == 1


class TestConvenienceFunction:
    """Tests für rank_papers() Convenience Function"""

    def test_rank_papers_works(self):
        """Test: rank_papers() funktioniert"""
        papers = [Paper(doi="10.1", title="Test", authors=["A"], year=2024)]

        result = rank_papers(papers, "query", top_n=10, use_llm=False)

        assert len(result) == 1
        assert isinstance(result[0], Paper)

    def test_rank_papers_with_llm_disabled(self):
        """Test: LLM kann deaktiviert werden"""
        papers = [Paper(doi="10.1", title="Test", authors=["A"])]

        result = rank_papers(papers, "query", use_llm=False)

        assert len(result) == 1

    def test_rank_papers_respects_mode(self):
        """Test: Mode-Parameter wird respektiert"""
        papers = [Paper(doi="10.1", title="Test", authors=["A"])]

        result = rank_papers(papers, "query", mode="quick", use_llm=False)

        assert len(result) == 1


class TestEdgeCases:
    """Tests für Edge-Cases"""

    def test_rank_with_papers_missing_all_metadata(self):
        """Test: Papers ohne Metadaten werden behandelt"""
        engine = RankingEngine(use_llm_relevance=False)

        papers = [
            Paper(doi="10.1", title="Minimal", authors=["A"])
            # Kein year, citations, venue, abstract
        ]

        result = engine.rank(papers, "query")

        assert len(result) == 1

    def test_rank_with_duplicate_dois(self):
        """Test: Duplikate DOIs werden behandelt"""
        engine = RankingEngine(use_llm_relevance=False)

        papers = [
            Paper(doi="10.1", title="Paper1", authors=["A"]),
            Paper(doi="10.1", title="Paper2", authors=["B"])  # Duplikat DOI
        ]

        # Sollte nicht crashen
        result = engine.rank(papers, "query")

        assert len(result) == 2

    def test_rank_with_very_long_query(self):
        """Test: Sehr lange Query wird behandelt"""
        engine = RankingEngine(use_llm_relevance=False)

        papers = [Paper(doi="10.1", title="Test", authors=["A"])]

        long_query = " ".join(["word"] * 500)

        result = engine.rank(papers, long_query)

        assert len(result) == 1


class TestIntegrationWithFiveDScorer:
    """Integration Tests mit FiveDScorer"""

    def test_ranking_uses_five_d_scorer(self):
        """Test: Ranking nutzt FiveDScorer"""
        engine = RankingEngine(use_llm_relevance=False)

        papers = [
            Paper(doi="10.1", title="Old Low Citations", authors=["A"],
                  year=2010, citations=5),
            Paper(doi="10.2", title="Recent High Citations", authors=["B"],
                  year=2024, citations=500, venue="IEEE Transactions")
        ]

        result = engine.rank(papers, "query")

        # Zweites Paper sollte höher ranken (recent + high citations + good venue)
        assert result[0].doi == "10.2"
        assert result[1].doi == "10.1"

    def test_ranking_considers_all_dimensions(self):
        """Test: Alle 5 Dimensionen werden berücksichtigt"""
        engine = RankingEngine(use_llm_relevance=False)

        papers = [
            Paper(doi="10.1", title="Test", authors=["A"],
                  year=2024, citations=100, venue="IEEE")
        ]

        result = engine.rank_with_scores(papers, "Test")

        scores = result[0]["scores"]

        # Alle Scores sollten berechnet worden sein
        assert "relevance" in scores
        assert "recency" in scores
        assert "quality" in scores
        assert "authority" in scores
        assert "total" in scores

        # Alle Scores sollten im validen Bereich sein
        for key, value in scores.items():
            assert 0.0 <= value <= 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
