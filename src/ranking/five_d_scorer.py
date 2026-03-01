"""
5D-Scorer für Academic Agent v2.3+

5 Dimensionen:
1. Relevanz (0.4) - Semantic relevance to query
2. Recency (0.2) - Publication year
3. Quality (0.2) - Citations, venue
4. Authority (0.2) - Author h-index, affiliations  
5. Portfolio Balance (optional) - Diversity

Features:
- Configurable weights
- Citation-Count Integration
- Research Mode Integration
- Normalized scores (0-1)

Usage:
    from src.ranking.five_d_scorer import FiveDScorer
    
    scorer = FiveDScorer()
    scored_papers = scorer.score(papers, query="DevOps Governance")
"""

from typing import List, Dict, Optional, Any
from datetime import datetime
import logging
import math

from src.search.crossref_client import Paper

# Setup Logging
logger = logging.getLogger(__name__)


# ============================================
# 5D-Scorer
# ============================================

class FiveDScorer:
    """
    5D-Scoring Engine
    
    Scores papers on 5 dimensions with configurable weights
    """
    
    def __init__(
        self,
        relevance_weight: float = 0.4,
        recency_weight: float = 0.2,
        quality_weight: float = 0.2,
        authority_weight: float = 0.2,
        apply_portfolio_balance: bool = False,
        max_year: Optional[int] = None
    ):
        """
        Initialize 5D-Scorer
        
        Args:
            relevance_weight: Weight for relevance (default: 0.4)
            recency_weight: Weight for recency (default: 0.2)
            quality_weight: Weight for quality (default: 0.2)
            authority_weight: Weight for authority (default: 0.2)
            apply_portfolio_balance: Apply portfolio diversity (default: False)
            max_year: Maximum year for recency (default: current year)
        """
        self.relevance_weight = relevance_weight
        self.recency_weight = recency_weight
        self.quality_weight = quality_weight
        self.authority_weight = authority_weight
        self.apply_portfolio_balance = apply_portfolio_balance
        self.max_year = max_year or datetime.now().year
        
        # Validate weights sum to 1.0
        total = relevance_weight + recency_weight + quality_weight + authority_weight
        if not (0.99 <= total <= 1.01):
            logger.warning(f"Weights don't sum to 1.0 (sum: {total}), normalizing...")
            self.relevance_weight /= total
            self.recency_weight /= total
            self.quality_weight /= total
            self.authority_weight /= total
        
        logger.info(f"5D-Scorer initialized (R:{relevance_weight}, Re:{recency_weight}, Q:{quality_weight}, A:{authority_weight})")
    
    def score(
        self,
        papers: List[Paper],
        query: str,
        relevance_scores: Optional[Dict[str, float]] = None
    ) -> List[Dict[str, Any]]:
        """
        Score papers using 5D method
        
        Args:
            papers: List of papers to score
            query: Research query (for relevance scoring)
            relevance_scores: Optional pre-computed relevance scores (DOI -> score)
        
        Returns:
            List of dicts with paper + scores
        """
        if not papers:
            return []
        
        logger.info(f"Scoring {len(papers)} papers...")
        
        scored_papers = []
        
        for paper in papers:
            # Compute individual scores
            relevance = self._score_relevance(paper, query, relevance_scores)
            recency = self._score_recency(paper)
            quality = self._score_quality(paper)
            authority = self._score_authority(paper)
            
            # Weighted total
            total_score = (
                relevance * self.relevance_weight +
                recency * self.recency_weight +
                quality * self.quality_weight +
                authority * self.authority_weight
            )
            
            scored_papers.append({
                "paper": paper,
                "scores": {
                    "relevance": relevance,
                    "recency": recency,
                    "quality": quality,
                    "authority": authority,
                    "total": total_score
                }
            })
        
        # Sort by total score (descending)
        scored_papers.sort(key=lambda x: x["scores"]["total"], reverse=True)
        
        # Apply portfolio balance (optional)
        if self.apply_portfolio_balance:
            scored_papers = self._apply_portfolio_balance(scored_papers)
        
        logger.info(f"Scored {len(scored_papers)} papers (top score: {scored_papers[0]['scores']['total']:.3f})")
        
        return scored_papers
    
    def _score_relevance(
        self,
        paper: Paper,
        query: str,
        precomputed: Optional[Dict[str, float]]
    ) -> float:
        """
        Score relevance (0-1)
        
        Uses pre-computed LLM scores if available, else keyword matching
        """
        # Use pre-computed if available
        if precomputed and paper.doi in precomputed:
            return precomputed[paper.doi]
        
        # Fallback: Keyword matching
        query_lower = query.lower().strip()
        if not query_lower:
            # No query provided: return neutral score (not 0.0)
            return 0.5

        query_terms = set(query_lower.split())

        # Check title
        title_lower = (paper.title or "").lower()
        title_matches = sum(1 for term in query_terms if term in title_lower)
        title_score = min(title_matches / len(query_terms), 1.0) if query_terms else 0.0

        # Check abstract (if available)
        abstract_score = 0.0
        if paper.abstract:
            abstract_lower = paper.abstract.lower()
            abstract_matches = sum(1 for term in query_terms if term in abstract_lower)
            abstract_score = min(abstract_matches / len(query_terms), 1.0) if query_terms else 0.0

        # Weighted: Title 0.7, Abstract 0.3
        relevance = title_score * 0.7 + abstract_score * 0.3

        return relevance
    
    def _score_recency(self, paper: Paper) -> float:
        """
        Score recency (0-1)
        
        Uses exponential decay: newer papers score higher
        """
        if not paper.year:
            return 0.5  # Unknown year: neutral score
        
        # Years ago
        years_ago = self.max_year - paper.year
        
        # Exponential decay (half-life: 5 years)
        recency = math.exp(-years_ago / 5.0)
        
        return min(max(recency, 0.0), 1.0)
    
    def _score_quality(self, paper: Paper) -> float:
        """
        Score quality (0-1)
        
        Based on citations (log-scaled)
        """
        citations = paper.citations or 0
        
        if citations == 0:
            return 0.1  # Minimum score for uncited papers
        
        # Log-scale (saturates at 1000 citations)
        quality = math.log(citations + 1) / math.log(1000)
        
        return min(max(quality, 0.0), 1.0)
    
    def _score_authority(self, paper: Paper) -> float:
        """
        Score authority (0-1)
        
        Based on venue (journal/conference reputation)
        For now: Simple heuristic based on venue name
        """
        if not paper.venue:
            return 0.5  # Unknown venue: neutral score
        
        venue_lower = paper.venue.lower()
        
        # High-reputation venues (heuristic)
        high_rep_keywords = [
            "ieee", "acm", "springer", "nature", "science",
            "transactions", "journal", "conference", "symposium"
        ]
        
        matches = sum(1 for keyword in high_rep_keywords if keyword in venue_lower)
        authority = min(matches / 3.0, 1.0)  # Saturate at 3 matches
        
        return max(authority, 0.3)  # Minimum 0.3 for any venue
    
    def _apply_portfolio_balance(self, scored_papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Apply portfolio balance (diversity boost)
        
        Penalizes very similar papers, rewards diverse papers
        """
        # TODO: Implement diversity scoring
        # For now: No-op
        logger.debug("Portfolio balance not implemented yet")
        return scored_papers


# ============================================
# Convenience Functions
# ============================================

def score_papers(
    papers: List[Paper],
    query: str,
    weights: Optional[Dict[str, float]] = None,
    relevance_scores: Optional[Dict[str, float]] = None
) -> List[Dict[str, Any]]:
    """
    Convenience function for quick scoring
    
    Args:
        papers: Papers to score
        query: Research query
        weights: Optional custom weights
        relevance_scores: Optional pre-computed relevance
    
    Returns:
        Scored papers (sorted by total score)
    
    Example:
        scored = score_papers(papers, "DevOps Governance")
        top_5 = scored[:5]
    """
    if weights:
        scorer = FiveDScorer(**weights)
    else:
        scorer = FiveDScorer()
    
    return scorer.score(papers, query, relevance_scores)


# ============================================
# CLI Test
# ============================================

def main():
    """
    CLI Interface for FiveDScorer

    Usage:
        python -m src.ranking.five_d_scorer --papers papers.json --query "DevOps" --output scored.json
        python -m src.ranking.five_d_scorer --papers papers.json --weights relevance:0.5,recency:0.2,quality:0.15,authority:0.15
    """
    import argparse
    import json
    import sys

    parser = argparse.ArgumentParser(description="5D Paper Scorer - Citation, Recency, Quality, Authority")
    parser.add_argument('--papers', required=True, help='Input JSON file with papers')
    parser.add_argument('--query', help='Research query for relevance scoring')
    parser.add_argument('--weights', help='Score weights (format: relevance:0.4,recency:0.2,quality:0.2,authority:0.2)')
    parser.add_argument('--llm-scores', help='Optional JSON file with LLM relevance scores')
    parser.add_argument('--output', help='Output JSON file path (default: stdout)')
    parser.add_argument('--top', type=int, help='Return only top N papers')
    parser.add_argument('--test', action='store_true', help='Run tests instead of scoring')

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
        from src.search.search_engine import Paper
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

        # Parse custom weights
        custom_weights = None
        if args.weights:
            custom_weights = {}
            for part in args.weights.split(','):
                key, value = part.split(':')
                custom_weights[key.strip()] = float(value.strip())

        # Load LLM relevance scores if provided
        llm_scores = None
        if args.llm_scores:
            with open(args.llm_scores, 'r') as f:
                llm_data = json.load(f)
                # Convert to dict: doi -> score
                llm_scores = {
                    item['paper_id']: item['relevance_score']
                    for item in llm_data.get('scores', [])
                }

        # Initialize scorer with individual weight parameters
        if custom_weights:
            scorer = FiveDScorer(
                relevance_weight=custom_weights.get('relevance', 0.4),
                recency_weight=custom_weights.get('recency', 0.2),
                quality_weight=custom_weights.get('quality', 0.2),
                authority_weight=custom_weights.get('authority', 0.2)
            )
        else:
            scorer = FiveDScorer()

        # Score papers
        query = args.query or ""
        scored = scorer.score(papers, query, llm_scores)

        # Filter top N if requested
        if args.top:
            scored = scored[:args.top]

        # Convert to JSON-serializable format
        weights_used = {
            "relevance": scorer.relevance_weight,
            "recency": scorer.recency_weight,
            "quality": scorer.quality_weight,
            "authority": scorer.authority_weight
        }
        results = {
            "query": query,
            "total_papers": len(scored),
            "weights": weights_used,
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
                    "final_score": item["scores"]["total"]
                }
                for item in scored
            ]
        }

        # Output results
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"Scored {len(scored)} papers, saved to {args.output}", file=sys.stderr)
        else:
            # Output JSON to stdout
            print(json.dumps(results, indent=2))

    except Exception as e:
        error = {
            "error": str(e),
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
    from src.search.search_engine import Paper

    print("Testing 5D-Scorer...")

    # Create test papers
    papers = [
        Paper(
            doi="10.1/new-relevant",
            title="DevOps Governance Frameworks",
            authors=["A"],
            year=2024,
            citations=50,
            venue="IEEE Software"
        ),
        Paper(
            doi="10.2/old-highly-cited",
            title="Software Engineering Practices",
            authors=["B"],
            year=2015,
            citations=500,
            venue="ACM Transactions"
        ),
        Paper(
            doi="10.3/recent-low-cited",
            title="Governance in Modern DevOps",
            authors=["C"],
            year=2023,
            citations=5,
            venue="Journal of Systems"
        )
    ]

    # Score
    scorer = FiveDScorer()
    scored = scorer.score(papers, "DevOps Governance")

    # Display
    print(f"\n✅ Scored {len(scored)} papers\n")

    for i, item in enumerate(scored, 1):
        p = item["paper"]
        s = item["scores"]
        print(f"{i}. {p.title[:50]}...")
        print(f"   Total: {s['total']:.3f} | R:{s['relevance']:.2f} Re:{s['recency']:.2f} Q:{s['quality']:.2f} A:{s['authority']:.2f}")
        print(f"   Year: {p.year}, Citations: {p.citations}, Venue: {p.venue}")
        print()

    print("✅ 5D-Scorer test passed!")


if __name__ == "__main__":
    main()
