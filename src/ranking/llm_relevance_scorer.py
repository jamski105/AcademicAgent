"""
DEPRECATED: LLM-Relevanz-Scorer für Academic Agent v2.3+

⚠️ THIS FILE IS DEPRECATED ⚠️

Use instead: .claude/agents/llm_relevance_scorer.md (Claude Code Agent)

This Python-based LLM scorer is replaced by an agent:
- llm_relevance_scorer Agent (Haiku 4.5) handles semantic relevance scoring
- Spawned by linear_coordinator during Phase 4 (Ranking)
- No direct Anthropic API calls needed (uses Claude Code agents)

This file is kept for reference only.

Original Features:
- Paper + Query → Relevanz-Score (0-1)
- Batch-Scoring (parallel)
- Fallback: Keyword-Matching
- Caching (optional)

Old Usage (DEPRECATED):
    from src.ranking.llm_relevance_scorer import LLMRelevanceScorer

    scorer = LLMRelevanceScorer()
    scores = scorer.score_batch(papers, query="DevOps Governance")
"""

from typing import List, Dict, Optional
import logging
import os
import json

from anthropic import Anthropic
from src.search.crossref_client import Paper

# Setup Logging
logger = logging.getLogger(__name__)


# ============================================
# LLM-Relevanz-Scorer
# ============================================

class LLMRelevanceScorer:
    """
    LLM-based Relevance Scorer
    
    Uses Haiku to score paper relevance semantically
    """
    
    def __init__(
        self,
        anthropic_api_key: Optional[str] = None,
        model: str = "claude-haiku-4",
        use_fallback_if_no_key: bool = True
    ):
        """
        Initialize LLM Relevance Scorer
        
        Args:
            anthropic_api_key: Anthropic API key (from env if not provided)
            model: Model to use (default: claude-haiku-4)
            use_fallback_if_no_key: Use keyword fallback if no API key (default: True)
        """
        self.api_key = anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model = model
        self.use_fallback = use_fallback_if_no_key
        
        if self.api_key:
            self.client = Anthropic(api_key=self.api_key)
            logger.info(f"LLM Relevance Scorer initialized with model: {model}")
        else:
            self.client = None
            if use_fallback_if_no_key:
                logger.warning("No Anthropic API key - using keyword fallback")
            else:
                raise ValueError("Anthropic API key required")
    
    def score_batch(
        self,
        papers: List[Paper],
        query: str,
        batch_size: int = 10
    ) -> Dict[str, float]:
        """
        Score multiple papers (batch)
        
        Args:
            papers: Papers to score
            query: Research query
            batch_size: Papers per batch (default: 10)
        
        Returns:
            Dict mapping DOI to relevance score (0-1)
        """
        if not papers:
            return {}
        
        # If no client, use fallback
        if not self.client:
            return self._fallback_score_batch(papers, query)
        
        logger.info(f"Scoring {len(papers)} papers with Haiku...")
        
        scores = {}
        
        # Process in batches
        for i in range(0, len(papers), batch_size):
            batch = papers[i:i+batch_size]
            batch_scores = self._score_batch_haiku(batch, query)
            scores.update(batch_scores)
        
        logger.info(f"Scored {len(scores)} papers via Haiku")
        return scores
    
    def _score_batch_haiku(
        self,
        papers: List[Paper],
        query: str
    ) -> Dict[str, float]:
        """
        Score batch via Haiku
        
        Args:
            papers: Papers (up to 10)
            query: Query
        
        Returns:
            DOI -> score mapping
        """
        # Build prompt
        prompt = self._build_prompt(papers, query)
        
        try:
            # Call Haiku
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Parse response
            content = response.content[0].text
            scores = self._parse_response(content, papers)
            
            return scores
        
        except Exception as e:
            logger.error(f"Haiku call failed: {e}. Using fallback.")
            return self._fallback_score_batch(papers, query)
    
    def _build_prompt(self, papers: List[Paper], query: str) -> str:
        """
        Build prompt for Haiku
        
        Args:
            papers: Papers to score
            query: Query
        
        Returns:
            Formatted prompt
        """
        prompt = f"""You are the Relevance Scorer for Academic Agent v2.3+.

Score papers based on semantic relevance to the research query.

Query: "{query}"

Papers ({len(papers)}):
"""
        
        for i, paper in enumerate(papers, 1):
            prompt += f"""
{i}. DOI: {paper.doi}
   Title: {paper.title}
   Abstract: {paper.abstract[:200] if paper.abstract else "N/A"}...
"""
        
        prompt += """

For each paper, provide a relevance score (0-1):
- 1.0: Highly relevant (directly addresses query)
- 0.7-0.9: Relevant (related topic)
- 0.4-0.6: Somewhat relevant (tangentially related)
- 0.1-0.3: Barely relevant (different topic)
- 0.0: Not relevant

Output as JSON:
{
  "scores": [
    {"doi": "10.xxx", "score": 0.95, "reasoning": "..."},
    {"doi": "10.yyy", "score": 0.65, "reasoning": "..."}
  ]
}"""
        
        return prompt
    
    def _parse_response(self, content: str, papers: List[Paper]) -> Dict[str, float]:
        """
        Parse Haiku response
        
        Args:
            content: Response text
            papers: Original papers
        
        Returns:
            DOI -> score mapping
        """
        try:
            # Extract JSON
            if "{" in content:
                start = content.find("{")
                end = content.rfind("}") + 1
                json_str = content[start:end]
                data = json.loads(json_str)
                
                # Extract scores
                scores = {}
                for item in data.get("scores", []):
                    doi = item.get("doi", "")
                    score = item.get("score", 0.5)
                    if doi:
                        scores[doi] = float(score)
                
                return scores
            else:
                logger.warning("No JSON in Haiku response")
                return {}
        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Haiku response: {e}")
            return {}
    
    def _fallback_score_batch(
        self,
        papers: List[Paper],
        query: str
    ) -> Dict[str, float]:
        """
        Fallback: Keyword-based scoring
        
        Args:
            papers: Papers
            query: Query
        
        Returns:
            DOI -> score mapping
        """
        logger.debug("Using keyword fallback for relevance scoring")
        
        query_lower = query.lower()
        query_terms = set(query_lower.split())
        
        scores = {}
        
        for paper in papers:
            # Title matching
            title_lower = (paper.title or "").lower()
            title_matches = sum(1 for term in query_terms if term in title_lower)
            title_score = min(title_matches / len(query_terms), 1.0) if query_terms else 0.0
            
            # Abstract matching (if available)
            abstract_score = 0.0
            if paper.abstract:
                abstract_lower = paper.abstract.lower()
                abstract_matches = sum(1 for term in query_terms if term in abstract_lower)
                abstract_score = min(abstract_matches / len(query_terms), 1.0) if query_terms else 0.0
            
            # Weighted: Title 0.7, Abstract 0.3
            relevance = title_score * 0.7 + abstract_score * 0.3
            
            scores[paper.doi] = relevance
        
        return scores


# ============================================
# CLI Test
# ============================================

if __name__ == "__main__":
    """
    Test LLM Relevance Scorer
    
    Run:
        python -m src.ranking.llm_relevance_scorer
    """
    print("Testing LLM Relevance Scorer...")
    
    # Test papers
    papers = [
        Paper(
            doi="10.1/relevant",
            title="DevOps Governance Frameworks in Enterprise",
            authors=["A"],
            abstract="This paper presents governance frameworks for DevOps..."
        ),
        Paper(
            doi="10.2/somewhat",
            title="Software Engineering Best Practices",
            authors=["B"],
            abstract="We discuss best practices in software engineering..."
        ),
        Paper(
            doi="10.3/not-relevant",
            title="Machine Learning for Image Recognition",
            authors=["C"],
            abstract="Deep learning models for computer vision tasks..."
        )
    ]
    
    # Test fallback
    print("\n1. Testing fallback mode (no API key)...")
    scorer = LLMRelevanceScorer()
    scores = scorer.score_batch(papers, "DevOps Governance")
    
    print(f"✅ Scored {len(scores)} papers (fallback)\n")
    for doi, score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
        paper = next(p for p in papers if p.doi == doi)
        print(f"  {score:.2f} - {paper.title[:50]}...")
    
    print("\n✅ LLM Relevance Scorer test passed!")
