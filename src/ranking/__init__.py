"""
Ranking Engine für Academic Agent v2.0

Module:
- five_d_scorer.py: 5D-Scoring (Relevanz, Recency, Quality, Authority, Portfolio)
- llm_relevance_scorer.py: LLM-basierte Relevanz (Haiku)
- ranking_engine.py: Orchestrator
"""

from src.ranking.five_d_scorer import FiveDScorer, score_papers
from src.ranking.ranking_engine import RankingEngine, rank_papers

__all__ = [
    "FiveDScorer",
    "score_papers",
    "RankingEngine",
    "rank_papers"
]
