#!/usr/bin/env python3
"""
Unit Tests für src/ranking/five_d_scorer.py
Tests against real production code
"""

import pytest
from datetime import datetime
from src.ranking.five_d_scorer import FiveDScorer, score_papers
from src.search.crossref_client import Paper


class TestFiveDScorerInitialization:
    """Tests für Scorer-Initialisierung"""

    def test_default_weights(self):
        """Test: Default Weights sind korrekt"""
        scorer = FiveDScorer()

        assert scorer.relevance_weight == 0.4
        assert scorer.recency_weight == 0.2
        assert scorer.quality_weight == 0.2
        assert scorer.authority_weight == 0.2
        assert scorer.apply_portfolio_balance == False

    def test_custom_weights(self):
        """Test: Custom Weights werden akzeptiert"""
        scorer = FiveDScorer(
            relevance_weight=0.5,
            recency_weight=0.3,
            quality_weight=0.1,
            authority_weight=0.1
        )

        assert scorer.relevance_weight == 0.5
        assert scorer.recency_weight == 0.3

    def test_weights_normalize_if_not_sum_to_one(self):
        """Test: Weights werden normalisiert wenn Summe != 1.0"""
        scorer = FiveDScorer(
            relevance_weight=0.5,
            recency_weight=0.5,
            quality_weight=0.5,
            authority_weight=0.5
        )

        # Sollten normalisiert werden (Summe war 2.0)
        total = (scorer.relevance_weight + scorer.recency_weight +
                 scorer.quality_weight + scorer.authority_weight)
        assert 0.99 <= total <= 1.01


class TestRecencyScoring:
    """Tests für Recency Score"""

    def test_current_year_paper_gets_full_score(self):
        """Test: Aktuelles Paper bekommt Score 1.0"""
        scorer = FiveDScorer()
        paper = Paper(doi="10.1", title="Test", authors=["A"], year=datetime.now().year)

        score = scorer._score_recency(paper)

        assert score == 1.0

    def test_five_year_old_paper(self):
        """Test: 5 Jahre altes Paper hat mittleren Score"""
        scorer = FiveDScorer()
        paper = Paper(doi="10.1", title="Test", authors=["A"],
                     year=datetime.now().year - 5)

        score = scorer._score_recency(paper)

        # Exponential decay: exp(-5/5) = exp(-1) ≈ 0.368
        assert 0.3 < score < 0.4

    def test_ten_year_old_paper(self):
        """Test: 10 Jahre altes Paper hat niedrigen Score"""
        scorer = FiveDScorer()
        paper = Paper(doi="10.1", title="Test", authors=["A"],
                     year=datetime.now().year - 10)

        score = scorer._score_recency(paper)

        # exp(-10/5) = exp(-2) ≈ 0.135
        assert 0.1 < score < 0.2

    def test_missing_year_returns_neutral_score(self):
        """Test: Fehlendes Jahr gibt 0.5"""
        scorer = FiveDScorer()
        paper = Paper(doi="10.1", title="Test", authors=["A"], year=None)

        score = scorer._score_recency(paper)

        assert score == 0.5


class TestQualityScoring:
    """Tests für Quality Score (Citations)"""

    def test_zero_citations_gets_minimum_score(self):
        """Test: 0 Citations gibt 0.1"""
        scorer = FiveDScorer()
        paper = Paper(doi="10.1", title="Test", authors=["A"], citations=0)

        score = scorer._score_quality(paper)

        assert score == 0.1

    def test_hundred_citations(self):
        """Test: 100 Citations gibt mittleren Score"""
        scorer = FiveDScorer()
        paper = Paper(doi="10.1", title="Test", authors=["A"], citations=100)

        score = scorer._score_quality(paper)

        # log(101) / log(1000) ≈ 0.67
        assert 0.6 < score < 0.7

    def test_thousand_citations_saturates_at_one(self):
        """Test: 1000+ Citations gibt 1.0"""
        scorer = FiveDScorer()
        paper = Paper(doi="10.1", title="Test", authors=["A"], citations=1000)

        score = scorer._score_quality(paper)

        assert score >= 0.99

    def test_none_citations_treated_as_zero(self):
        """Test: None Citations = 0"""
        scorer = FiveDScorer()
        paper = Paper(doi="10.1", title="Test", authors=["A"], citations=None)

        score = scorer._score_quality(paper)

        assert score == 0.1


class TestAuthorityScoring:
    """Tests für Authority Score (Venue)"""

    def test_ieee_venue_gets_high_score(self):
        """Test: IEEE Venue bekommt hohen Score"""
        scorer = FiveDScorer()
        paper = Paper(doi="10.1", title="Test", authors=["A"],
                     venue="IEEE Transactions on Software Engineering")

        score = scorer._score_authority(paper)

        assert score >= 0.5

    def test_acm_venue_gets_high_score(self):
        """Test: ACM Venue bekommt hohen Score"""
        scorer = FiveDScorer()
        paper = Paper(doi="10.1", title="Test", authors=["A"],
                     venue="ACM Conference on Computer Science")

        score = scorer._score_authority(paper)

        assert score >= 0.5

    def test_unknown_venue_gets_neutral_score(self):
        """Test: Unbekanntes Venue bekommt Minimum 0.3"""
        scorer = FiveDScorer()
        paper = Paper(doi="10.1", title="Test", authors=["A"],
                     venue="Unknown Journal")

        score = scorer._score_authority(paper)

        assert score >= 0.3

    def test_none_venue_returns_neutral(self):
        """Test: Kein Venue gibt 0.5"""
        scorer = FiveDScorer()
        paper = Paper(doi="10.1", title="Test", authors=["A"], venue=None)

        score = scorer._score_authority(paper)

        assert score == 0.5


class TestRelevanceScoring:
    """Tests für Relevance Score (Keyword Fallback)"""

    def test_perfect_title_match(self):
        """Test: Alle Keywords im Title = hoher Score"""
        scorer = FiveDScorer()
        paper = Paper(doi="10.1",
                     title="DevOps Governance Frameworks",
                     authors=["A"])

        score = scorer._score_relevance(paper, "DevOps Governance", None)

        # Title: 2/2 = 1.0, Abstract: 0, Weighted: 1.0*0.7 + 0*0.3 = 0.7
        assert score >= 0.7

    def test_title_and_abstract_match(self):
        """Test: Keywords in Title + Abstract"""
        scorer = FiveDScorer()
        paper = Paper(doi="10.1",
                     title="DevOps Best Practices",
                     authors=["A"],
                     abstract="This paper discusses governance in DevOps environments")

        score = scorer._score_relevance(paper, "DevOps Governance", None)

        # Beide Keywords in Title oder Abstract
        assert score > 0.5

    def test_no_match_gives_low_score(self):
        """Test: Keine Matches = niedriger Score"""
        scorer = FiveDScorer()
        paper = Paper(doi="10.1",
                     title="Machine Learning for Images",
                     authors=["A"],
                     abstract="Deep learning computer vision")

        score = scorer._score_relevance(paper, "DevOps Governance", None)

        assert score == 0.0

    def test_precomputed_relevance_is_used(self):
        """Test: Pre-computed Scores haben Vorrang"""
        scorer = FiveDScorer()
        paper = Paper(doi="10.1", title="Test", authors=["A"])

        precomputed = {"10.1": 0.95}
        score = scorer._score_relevance(paper, "query", precomputed)

        assert score == 0.95


class TestFullScoring:
    """Tests für komplettes Scoring"""

    def test_scores_single_paper(self):
        """Test: Einzelnes Paper wird gescoret"""
        scorer = FiveDScorer()
        papers = [
            Paper(doi="10.1",
                  title="DevOps Governance",
                  authors=["A"],
                  year=2024,
                  citations=100,
                  venue="IEEE Software")
        ]

        result = scorer.score(papers, "DevOps Governance")

        assert len(result) == 1
        assert "paper" in result[0]
        assert "scores" in result[0]
        assert 0.0 <= result[0]["scores"]["total"] <= 1.0

    def test_sorts_by_total_score(self):
        """Test: Papers werden nach Total-Score sortiert"""
        scorer = FiveDScorer()
        papers = [
            Paper(doi="10.1", title="Old Paper", authors=["A"],
                  year=2010, citations=5),
            Paper(doi="10.2", title="DevOps Governance", authors=["B"],
                  year=2024, citations=100, venue="IEEE")
        ]

        result = scorer.score(papers, "DevOps Governance")

        # Zweites Paper sollte höher ranken
        assert result[0]["paper"].doi == "10.2"
        assert result[1]["paper"].doi == "10.1"

    def test_empty_papers_returns_empty(self):
        """Test: Leere Liste gibt leere Liste zurück"""
        scorer = FiveDScorer()

        result = scorer.score([], "query")

        assert result == []


class TestConvenienceFunction:
    """Tests für score_papers() Convenience Function"""

    def test_score_papers_works(self):
        """Test: score_papers() funktioniert"""
        papers = [
            Paper(doi="10.1", title="Test", authors=["A"],
                  year=2024, citations=50)
        ]

        result = score_papers(papers, "test")

        assert len(result) == 1
        assert result[0]["scores"]["total"] > 0

    def test_score_papers_with_custom_weights(self):
        """Test: Custom Weights funktionieren"""
        papers = [Paper(doi="10.1", title="Test", authors=["A"])]

        weights = {
            "relevance_weight": 0.6,
            "recency_weight": 0.1,
            "quality_weight": 0.1,
            "authority_weight": 0.2
        }

        result = score_papers(papers, "test", weights=weights)

        assert len(result) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
