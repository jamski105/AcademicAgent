#!/usr/bin/env python3
"""
Integration Tests für Ranking Pipeline
Tests Phase 2 (Search) → Phase 3 (Ranking) Workflow
"""

import pytest
from src.ranking.ranking_engine import RankingEngine
from src.search.crossref_client import Paper


class TestSearchToRankingPipeline:
    """Integration Tests für Search → Ranking Pipeline"""

    def test_complete_pipeline_without_llm(self):
        """Test: Kompletter Pipeline ohne LLM (Fallback)"""
        # Simuliere Search-Results
        papers = [
            Paper(
                doi="10.1109/MS.2024.001",
                title="DevOps Governance Frameworks for Enterprise",
                authors=["Smith, J.", "Doe, A."],
                year=2024,
                citations=50,
                venue="IEEE Software",
                abstract="This paper presents governance frameworks for DevOps in large enterprises."
            ),
            Paper(
                doi="10.1145/ACM.2023.456",
                title="Compliance Automation in CI/CD Pipelines",
                authors=["Johnson, B."],
                year=2023,
                citations=30,
                venue="ACM Digital Library",
                abstract="We propose automated compliance checking for continuous integration."
            ),
            Paper(
                doi="10.1007/Springer.2015.789",
                title="Software Engineering Best Practices",
                authors=["Brown, C."],
                year=2015,
                citations=500,
                venue="Springer Lecture Notes",
                abstract="A comprehensive guide to software engineering practices."
            ),
            Paper(
                doi="10.1016/Nature.2023.123",
                title="Machine Learning Ethics",
                authors=["Green, D."],
                year=2023,
                citations=100,
                venue="Nature",
                abstract="Ethical considerations in machine learning systems."
            )
        ]

        # Ranking durchführen
        engine = RankingEngine(use_llm_relevance=False)
        ranked = engine.rank(papers, "DevOps Governance", top_n=3)

        # Validierung
        assert len(ranked) == 3

        # Erstes Paper sollte am relevantesten sein (DevOps Governance im Titel)
        assert "DevOps" in ranked[0].title or "Governance" in ranked[0].title

        # ML Ethics Paper sollte nicht in Top 3 sein (irrelevant)
        dois_in_top3 = [p.doi for p in ranked[:3]]
        assert "10.1016/Nature.2023.123" not in dois_in_top3

    def test_pipeline_with_scores(self):
        """Test: Pipeline gibt Scores zurück"""
        papers = [
            Paper(
                doi="10.1",
                title="Relevant Recent Paper",
                authors=["A"],
                year=2024,
                citations=100,
                venue="IEEE Transactions"
            )
        ]

        engine = RankingEngine(use_llm_relevance=False)
        result = engine.rank_with_scores(papers, "Relevant Paper", top_n=1)

        assert len(result) == 1
        assert "paper" in result[0]
        assert "scores" in result[0]

        scores = result[0]["scores"]
        assert 0.0 <= scores["total"] <= 1.0
        assert 0.0 <= scores["relevance"] <= 1.0
        assert 0.0 <= scores["recency"] <= 1.0
        assert 0.0 <= scores["quality"] <= 1.0
        assert 0.0 <= scores["authority"] <= 1.0

    def test_pipeline_handles_large_candidate_set(self):
        """Test: Pipeline handhabt große Paper-Menge"""
        # 50 Papers
        papers = [
            Paper(
                doi=f"10.{i}",
                title=f"Paper {i}" + (" DevOps" if i < 5 else ""),
                authors=["Author"],
                year=2024 - (i % 10),
                citations=i * 10
            )
            for i in range(50)
        ]

        engine = RankingEngine(use_llm_relevance=False)
        ranked = engine.rank(papers, "DevOps", top_n=15)

        # Top-15 Selection sollte funktionieren
        assert len(ranked) == 15

        # Papers mit "DevOps" im Titel sollten höher ranken
        devops_count_in_top5 = sum(1 for p in ranked[:5] if "DevOps" in p.title)
        assert devops_count_in_top5 >= 3

    def test_pipeline_with_mixed_quality_papers(self):
        """Test: Pipeline rankt gemischte Qualität korrekt"""
        papers = [
            # High relevance, recent, low citations
            Paper(doi="10.1", title="DevOps Governance Today",
                  authors=["A"], year=2024, citations=5),

            # Low relevance, old, high citations
            Paper(doi="10.2", title="Software Testing Methods",
                  authors=["B"], year=2010, citations=1000),

            # Medium relevance, medium recency, medium citations
            Paper(doi="10.3", title="Agile DevOps Practices",
                  authors=["C"], year=2020, citations=100, venue="IEEE"),
        ]

        engine = RankingEngine(use_llm_relevance=False)
        ranked = engine.rank(papers, "DevOps Governance")

        # Erstes Paper sollte höchste Relevanz haben
        assert ranked[0].doi == "10.1"  # DevOps Governance

        # Zweites könnte 10.3 sein (guter Mix)
        # Drittes sollte 10.2 sein (irrelevant trotz Citations)
        assert ranked[2].doi == "10.2"

    def test_pipeline_respects_different_modes(self):
        """Test: Pipeline respektiert Research Modes"""
        papers = [
            Paper(doi="10.1", title="Recent Paper", authors=["A"],
                  year=2024, citations=10),
            Paper(doi="10.2", title="Old High-Impact Paper", authors=["B"],
                  year=2010, citations=1000, venue="Nature"),
        ]

        engine = RankingEngine(use_llm_relevance=False)

        # Quick Mode (default weights)
        quick_result = engine.rank(papers, "Paper", mode="quick")
        assert len(quick_result) == 2

        # Standard Mode
        standard_result = engine.rank(papers, "Paper", mode="standard")
        assert len(standard_result) == 2

        # Deep Mode
        deep_result = engine.rank(papers, "Paper", mode="deep")
        assert len(deep_result) == 2


class TestEdgeCasesInPipeline:
    """Edge-Cases im Pipeline"""

    def test_pipeline_with_papers_missing_metadata(self):
        """Test: Pipeline handhabt fehlende Metadaten"""
        papers = [
            Paper(doi="10.1", title="Complete Paper", authors=["A"],
                  year=2024, citations=100, venue="IEEE",
                  abstract="Full abstract here"),
            Paper(doi="10.2", title="Minimal Paper", authors=["B"]),
            # Kein year, citations, venue, abstract
        ]

        engine = RankingEngine(use_llm_relevance=False)
        ranked = engine.rank(papers, "Paper")

        # Beide Papers sollten gerankt werden
        assert len(ranked) == 2

        # Complete Paper sollte höher ranken (mehr Metadaten)
        assert ranked[0].doi == "10.1"

    def test_pipeline_with_identical_papers(self):
        """Test: Pipeline handhabt identische Papers"""
        paper = Paper(doi="10.1", title="Same", authors=["A"],
                     year=2024, citations=50)

        papers = [paper, paper, paper]  # 3x dasselbe Paper

        engine = RankingEngine(use_llm_relevance=False)
        ranked = engine.rank(papers, "Same")

        # Alle sollten denselben Score haben
        result = engine.rank_with_scores(papers, "Same")
        scores = [r["scores"]["total"] for r in result]

        assert scores[0] == scores[1] == scores[2]

    def test_pipeline_with_empty_query(self):
        """Test: Pipeline handhabt leere Query"""
        papers = [
            Paper(doi="10.1", title="Paper", authors=["A"], year=2024)
        ]

        engine = RankingEngine(use_llm_relevance=False)

        # Sollte nicht crashen
        ranked = engine.rank(papers, "")

        assert len(ranked) == 1


class TestPerformance:
    """Performance Tests"""

    def test_pipeline_performance_with_100_papers(self):
        """Test: Pipeline ist schnell genug für 100 Papers"""
        import time

        papers = [
            Paper(
                doi=f"10.{i}",
                title=f"Paper {i}",
                authors=["Author"],
                year=2024 - (i % 10),
                citations=i * 10,
                venue="IEEE"
            )
            for i in range(100)
        ]

        engine = RankingEngine(use_llm_relevance=False)

        start = time.time()
        ranked = engine.rank(papers, "query", top_n=15)
        duration = time.time() - start

        assert len(ranked) == 15
        # Sollte in unter 1 Sekunde laufen (ohne LLM)
        assert duration < 1.0


class TestRankingQuality:
    """Tests für Ranking-Qualität"""

    def test_highly_relevant_paper_ranks_first(self):
        """Test: Hoch relevantes Paper rankt #1"""
        papers = [
            Paper(doi="10.1", title="Machine Learning", authors=["A"],
                  year=2024, citations=100),
            Paper(doi="10.2", title="DevOps Governance Framework", authors=["B"],
                  year=2024, citations=100),
            Paper(doi="10.3", title="Database Systems", authors=["C"],
                  year=2024, citations=100),
        ]

        engine = RankingEngine(use_llm_relevance=False)
        ranked = engine.rank(papers, "DevOps Governance")

        # 10.2 sollte #1 sein (perfekter Title-Match)
        assert ranked[0].doi == "10.2"

    def test_recent_paper_beats_old_paper_with_same_relevance(self):
        """Test: Neueres Paper schlägt älteres bei gleicher Relevanz"""
        papers = [
            Paper(doi="10.1", title="DevOps", authors=["A"],
                  year=2010, citations=100),
            Paper(doi="10.2", title="DevOps", authors=["B"],
                  year=2024, citations=100),
        ]

        engine = RankingEngine(use_llm_relevance=False)
        ranked = engine.rank(papers, "DevOps")

        # 2024 Paper sollte höher ranken (gleiche Relevanz, aber neuer)
        assert ranked[0].doi == "10.2"

    def test_highly_cited_paper_gets_boost(self):
        """Test: Hoch-zitiertes Paper bekommt Boost"""
        papers = [
            Paper(doi="10.1", title="Software", authors=["A"],
                  year=2024, citations=10),
            Paper(doi="10.2", title="Software", authors=["B"],
                  year=2024, citations=1000),
        ]

        engine = RankingEngine(use_llm_relevance=False)
        ranked = engine.rank(papers, "Software")

        # 1000 Citations Paper sollte höher ranken
        assert ranked[0].doi == "10.2"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
