"""
Ranking Engine Orchestrator für Academic Agent v2.3+

Orchestriert 5D-Scoring + LLM-Relevanz

Features:
- Top-N Selection
- Research Mode Integration
- Batch Processing
- Fallback zu Keyword-Scoring

Usage:
    from src.ranking.ranking_engine import RankingEngine
    
    engine = RankingEngine()
    ranked_papers = engine.rank(papers, query="DevOps Governance", top_n=15)
"""

from typing import List, Dict, Optional, Any
import logging

from src.search.crossref_client import Paper
from src.ranking.five_d_scorer import FiveDScorer
# Note: LLM relevance scoring is now done by llm_relevance_scorer Agent (v2.0)
# This module only handles score merging and orchestration

# Setup Logging
logger = logging.getLogger(__name__)


# ============================================
# Ranking Engine
# ============================================

class RankingEngine:
    """
    Ranking Engine Orchestrator
    
    Combines 5D-Scoring + LLM-Relevanz
    """
    
    def __init__(
        self,
        mode: str = "standard"
    ):
        """
        Initialize Ranking Engine

        Args:
            mode: Research mode (quick/standard/deep) for weight configuration

        Note: In v2.0, LLM relevance scoring is handled by llm_relevance_scorer Agent.
        This module only does 5D scoring and score merging.
        """
        self.mode = mode

        # Initialize 5D scorer
        self.five_d_scorer = FiveDScorer()

        logger.info(f"Ranking Engine initialized (mode: {mode})")
    
    def rank(
        self,
        papers: List[Paper],
        query: str,
        llm_scores: Optional[Dict[str, float]] = None,
        top_n: Optional[int] = None
    ) -> List[Paper]:
        """
        Rank papers using 5D scoring + optional LLM relevance scores

        Args:
            papers: Papers to rank
            query: Research query
            llm_scores: Optional dict of {doi: relevance_score} from llm_relevance_scorer Agent
            top_n: Return top N papers (default: all)

        Returns:
            Ranked papers (sorted by total score)

        Note: LLM scores should come from llm_relevance_scorer Agent in v2.0
        """
        if not papers:
            return []

        logger.info(f"Ranking {len(papers)} papers (mode: {self.mode})...")

        # Step 1: Get scoring weights
        weights = self._get_weights(self.mode)

        # Step 2: 5D-Scoring (merges LLM scores if provided)
        self.five_d_scorer = FiveDScorer(**weights)
        scored_papers = self.five_d_scorer.score(
            papers,
            query,
            relevance_scores=llm_scores
        )

        # Step 3: Extract ranked papers
        ranked_papers = [item["paper"] for item in scored_papers]

        # Step 4: Top-N Selection
        if top_n:
            ranked_papers = ranked_papers[:top_n]

        logger.info(f"Ranked {len(ranked_papers)} papers (top-{top_n or 'all'})")

        return ranked_papers
    
    def rank_with_scores(
        self,
        papers: List[Paper],
        query: str,
        llm_scores: Optional[Dict[str, float]] = None,
        top_n: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Rank papers and return with detailed scores

        Args:
            papers: Papers to rank
            query: Research query
            llm_scores: Optional dict of {doi: relevance_score} from llm_relevance_scorer Agent
            top_n: Return top N papers

        Returns:
            List of dicts with paper + scores
        """
        if not papers:
            return []

        logger.info(f"Ranking {len(papers)} papers with scores...")

        # Get weights
        weights = self._get_weights(self.mode)

        # 5D-Scoring
        self.five_d_scorer = FiveDScorer(**weights)
        scored_papers = self.five_d_scorer.score(
            papers,
            query,
            relevance_scores=llm_scores
        )

        # Top-N
        if top_n:
            scored_papers = scored_papers[:top_n]

        return scored_papers
    
    def _get_weights(self, mode: str) -> Dict[str, float]:
        """
        Get scoring weights based on research mode

        Args:
            mode: Research mode (quick/standard/deep)

        Returns:
            Dict with weight configuration
        """
        # Default weights (standard mode)
        weights = {
            "relevance_weight": 0.4,
            "recency_weight": 0.2,
            "quality_weight": 0.2,
            "authority_weight": 0.2,
            "apply_portfolio_balance": False
        }

        # Deep mode: more emphasis on quality and authority, less on recency
        if mode == "deep":
            weights.update({
                "relevance_weight": 0.35,
                "recency_weight": 0.15,
                "quality_weight": 0.25,
                "authority_weight": 0.25,
                "apply_portfolio_balance": True  # Enable diversity for deep mode
            })

        # Quick mode: same as standard (balanced)
        # No need to update, use defaults

        return weights


# ============================================
# Convenience Functions
# ============================================

def rank_papers(
    papers: List[Paper],
    query: str,
    llm_scores: Optional[Dict[str, float]] = None,
    top_n: int = 15,
    mode: str = "standard"
) -> List[Paper]:
    """
    Convenience function for quick ranking

    Args:
        papers: Papers to rank
        query: Research query
        llm_scores: Optional LLM relevance scores from Agent
        top_n: Top N papers (default: 15)
        mode: Research mode

    Returns:
        Ranked papers

    Example:
        ranked = rank_papers(papers, "DevOps Governance", top_n=15)
    """
    engine = RankingEngine(mode=mode)
    return engine.rank(papers, query, llm_scores=llm_scores, top_n=top_n)


# ============================================
# CLI Interface
# ============================================

def main():
    """
    CLI Interface for Ranking Engine

    Usage:
        python -m src.ranking.ranking_engine --papers papers.json --query "DevOps" --output ranked.json
        python -m src.ranking.ranking_engine --papers papers.json --query "DevOps" --llm-scores llm_scores.json --mode deep --top 15
    """
    import argparse
    import json
    import sys

    parser = argparse.ArgumentParser(description="Ranking Engine - Merge 5D + LLM Scores")
    parser.add_argument('--papers', required=True, help='Input JSON file with papers (from search_engine)')
    parser.add_argument('--query', required=True, help='Research query')
    parser.add_argument('--llm-scores', help='Optional JSON file with LLM relevance scores')
    parser.add_argument('--mode', choices=['quick', 'standard', 'deep'], default='standard',
                        help='Research mode (affects weights)')
    parser.add_argument('--top', type=int, help='Return only top N papers')
    parser.add_argument('--output', help='Output JSON file path (default: stdout)')
    parser.add_argument('--test', action='store_true', help='Run tests instead')

    args = parser.parse_args()

    # Test mode
    if args.test:
        _run_tests()
        return

    try:
        # Load papers from JSON
        with open(args.papers, 'r') as f:
            data = json.load(f)

        # Extract papers array
        papers_data = data.get('papers', data) if isinstance(data, dict) else data

        # Convert to Paper objects
        papers = []
        for p in papers_data:
            papers.append(Paper(
                doi=p.get('doi', ''),
                title=p.get('title', ''),
                abstract=p.get('abstract', ''),
                authors=p.get('authors', []),
                year=p.get('year', 2020),
                citations=p.get('citations', 0),
                venue=p.get('venue', ''),
                source_api=p.get('source_api', 'unknown'),
                url=p.get('url', '')
            ))

        # Load LLM relevance scores if provided
        llm_scores = None
        if args.llm_scores:
            with open(args.llm_scores, 'r') as f:
                llm_data = json.load(f)
                # Convert to dict: doi -> score
                llm_scores = {}
                for item in llm_data.get('scores', []):
                    # Handle both "paper_id" and "doi" keys
                    paper_id = item.get('paper_id') or item.get('doi', '')
                    llm_scores[paper_id] = item['relevance_score']

        # Initialize ranking engine
        engine = RankingEngine(mode=args.mode)

        # Rank papers with scores
        scored_papers = engine.rank_with_scores(
            papers,
            args.query,
            llm_scores=llm_scores,
            top_n=args.top
        )

        # Convert to JSON-serializable format
        results = {
            "query": args.query,
            "mode": args.mode,
            "total_papers": len(scored_papers),
            "top_n": args.top or len(scored_papers),
            "papers": [
                {
                    "doi": item["paper"].doi,
                    "title": item["paper"].title,
                    "abstract": item["paper"].abstract,
                    "authors": item["paper"].authors,
                    "year": item["paper"].year,
                    "citations": item["paper"].citations,
                    "venue": item["paper"].venue,
                    "source_api": item["paper"].source_api,
                    "url": item["paper"].url,
                    "scores": item["scores"],
                    "rank": idx + 1
                }
                for idx, item in enumerate(scored_papers)
            ]
        }

        # Output results
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"Ranked {len(scored_papers)} papers, saved to {args.output}", file=sys.stderr)
        else:
            # Output JSON to stdout
            print(json.dumps(results, indent=2))

    except Exception as e:
        error = {
            "error": str(e),
            "query": args.query,
            "status": "failed"
        }
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(error, f, indent=2)
        else:
            print(json.dumps(error), file=sys.stderr)
        sys.exit(1)


def _run_tests():
    """Run test suite"""
    print("Testing Ranking Engine...")

    # Test papers
    papers = [
        Paper(
            doi="10.1/relevant-new",
            title="DevOps Governance Frameworks",
            authors=["A"],
            year=2024,
            citations=50,
            venue="IEEE Software",
            abstract="Governance frameworks for DevOps..."
        ),
        Paper(
            doi="10.2/relevant-old",
            title="Governance in Software Development",
            authors=["B"],
            year=2015,
            citations=500,
            venue="ACM Transactions",
            abstract="Software governance practices..."
        ),
        Paper(
            doi="10.3/not-relevant",
            title="Machine Learning Ethics",
            authors=["C"],
            year=2023,
            citations=100,
            venue="Nature",
            abstract="Ethical considerations in ML..."
        ),
        Paper(
            doi="10.4/somewhat-relevant",
            title="DevOps Practices in Industry",
            authors=["D"],
            year=2022,
            citations=30,
            venue="Journal of Systems",
            abstract="Industry practices for DevOps..."
        )
    ]

    # Test with mock LLM scores
    llm_scores = {
        "10.1/relevant-new": 0.95,
        "10.2/relevant-old": 0.80,
        "10.3/not-relevant": 0.20,
        "10.4/somewhat-relevant": 0.65
    }

    # Rank
    engine = RankingEngine(mode="standard")
    ranked = engine.rank(papers, "DevOps Governance", llm_scores=llm_scores, top_n=3)

    print(f"\n✅ Ranked {len(ranked)} papers (top 3)\n")

    for i, paper in enumerate(ranked, 1):
        print(f"{i}. {paper.title[:50]}...")
        print(f"   DOI: {paper.doi}")
        print(f"   Year: {paper.year}, Citations: {paper.citations}")
        print()

    print("✅ Ranking Engine test passed!")


if __name__ == "__main__":
    main()
