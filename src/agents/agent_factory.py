"""
Agent Factory with Automatic Model Fallback
Academic Agent v2.3+

Provides high-level functions to spawn agents with automatic
Haiku → Sonnet fallback when Haiku is unavailable.

Usage in Python CLIs and Coordinators:
    from src.agents.agent_factory import AgentFactory

    factory = AgentFactory()
    queries = factory.generate_queries("DevOps Governance", mode="quick")
    discipline = factory.classify_discipline("COVID-19 Treatment")
    scores = factory.score_relevance("DevOps", papers_list)
"""

import json
import subprocess
import logging
from typing import Any, Dict, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class AgentFactory:
    """Factory for spawning agents with automatic fallback"""

    def __init__(
        self,
        preferred_model: str = "haiku",
        fallback_model: str = "sonnet"
    ):
        """
        Initialize Agent Factory.

        Args:
            preferred_model: Model to try first (default: haiku)
            fallback_model: Model to use if preferred fails (default: sonnet)
        """
        self.preferred_model = preferred_model
        self.fallback_model = fallback_model
        self.project_root = Path(__file__).parent.parent.parent

    def generate_queries(
        self,
        user_query: str,
        research_mode: str = "quick",
        num_queries: int = 5
    ) -> Dict[str, Any]:
        """
        Generate alternative search queries using query_generator agent.

        Args:
            user_query: Original user query
            research_mode: Research mode (quick/standard/deep)
            num_queries: Number of alternative queries to generate

        Returns:
            Dict with:
                - expanded_queries: List of alternative queries
                - keywords: List of extracted keywords
                - reasoning: Explanation of query expansion strategy
        """
        prompt = f"""Generate {num_queries} alternative search queries for academic research.

**User Query:** "{user_query}"
**Research Mode:** {research_mode}

**Your Task:**
Generate {num_queries} alternative queries that:
- Expand acronyms (e.g., DevOps → Development Operations)
- Add related terms and synonyms
- Include domain-specific variations
- Maintain academic focus

**Return JSON:**
```json
{{
  "expanded_queries": [
    "query 1",
    "query 2",
    ...
  ],
  "keywords": ["keyword1", "keyword2", ...],
  "reasoning": "Brief explanation of expansion strategy"
}}
```

Return ONLY valid JSON, no additional text."""

        logger.info(f"Generating queries for: '{user_query}' (mode: {research_mode})")

        result = self._spawn_agent(
            agent_type="general-purpose",  # Using general-purpose as query_generator might not exist
            prompt=prompt,
            description="Generate search queries"
        )

        # Parse result
        try:
            if isinstance(result, str):
                # Try to extract JSON from result
                import re
                json_match = re.search(r'\{.*\}', result, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                else:
                    # Fallback: simple query expansion
                    logger.warning("Could not parse agent result, using simple expansion")
                    result = self._simple_query_expansion(user_query)

            return result

        except Exception as e:
            logger.warning(f"Error parsing query generator result: {e}, using simple expansion")
            return self._simple_query_expansion(user_query)

    def classify_discipline(
        self,
        user_query: str,
        expanded_queries: Optional[List[str]] = None
    ) -> str:
        """
        Classify the academic discipline for the research query.

        Args:
            user_query: Original user query
            expanded_queries: Optional list of expanded queries for context

        Returns:
            Discipline name (e.g., "Informatik", "Medizin", "Rechtswissenschaft")
        """
        queries_context = ""
        if expanded_queries:
            queries_context = "\n**Expanded Queries:**\n" + "\n".join(f"- {q}" for q in expanded_queries)

        prompt = f"""Classify the academic discipline for this research query.

**User Query:** "{user_query}"
{queries_context}

**Available Disciplines:**
- Informatik (Computer Science, IT, Software, DevOps, AI, Machine Learning)
- Rechtswissenschaft (Law, Legal, Juristisch, Mietrecht, Vertragsrecht)
- Medizin (Medicine, Health, Clinical, COVID, Treatment, Disease)
- Klassische Philologie (Latin, Greek, Ancient Languages, Metrik)
- Psychologie (Psychology, Social Science, Mental Health, Behavior)
- Wirtschaftswissenschaften (Business, Economics, Management, Finance)
- Naturwissenschaften (Physics, Chemistry, Biology, Environment)
- Ingenieurwissenschaften (Engineering, Technical Sciences, Construction)
- Sozialwissenschaften (Sociology, Anthropology, Social Studies)
- Geschichtswissenschaft (History, Historical Studies)

**Your Task:**
Analyze the query and determine the primary academic discipline.

**Return ONLY the discipline name** (e.g., "Informatik" or "Medizin").
No additional explanation needed."""

        logger.info(f"Classifying discipline for: '{user_query}'")

        result = self._spawn_agent(
            agent_type="general-purpose",
            prompt=prompt,
            description="Classify discipline"
        )

        # Extract discipline from result
        if isinstance(result, str):
            result = result.strip()
            # Check if it's a known discipline
            known_disciplines = [
                "Informatik", "Rechtswissenschaft", "Medizin",
                "Klassische Philologie", "Psychologie", "Wirtschaftswissenschaften",
                "Naturwissenschaften", "Ingenieurwissenschaften",
                "Sozialwissenschaften", "Geschichtswissenschaft"
            ]
            for disc in known_disciplines:
                if disc.lower() in result.lower():
                    logger.info(f"✅ Classified as: {disc}")
                    return disc

        logger.warning(f"Could not classify discipline, defaulting to 'Unknown'")
        return "Unknown"

    def score_relevance(
        self,
        user_query: str,
        papers: List[Dict[str, Any]],
        max_papers: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Score paper relevance using LLM-based semantic analysis.

        Args:
            user_query: Research query
            papers: List of paper dicts with title, abstract, etc.
            max_papers: Maximum number of papers to score (to avoid token limits)

        Returns:
            List of dicts with:
                - paper_index: Index in original list
                - relevance_score: 0.0-1.0
                - reasoning: Brief explanation
        """
        # Limit papers to avoid token limits
        papers_to_score = papers[:max_papers]

        # Prepare papers for LLM
        papers_json = []
        for i, paper in enumerate(papers_to_score):
            papers_json.append({
                "index": i,
                "title": paper.get("title", "")[:200],  # Limit title
                "abstract": paper.get("abstract", "")[:400],  # Limit abstract
                "year": paper.get("year"),
                "authors": paper.get("authors", [])[:3]  # Limit authors
            })

        papers_str = json.dumps(papers_json, indent=2)

        prompt = f"""Score the relevance of these academic papers to the research query.

**Query:** "{user_query}"

**Papers:**
{papers_str}

**Your Task:**
Score each paper's relevance (0.0-1.0) based on:
- Title alignment with query
- Abstract content match
- Semantic similarity
- Topical relevance

**Scoring Guidelines:**
- 0.9-1.0: Highly relevant, directly addresses query
- 0.7-0.8: Relevant, related but not perfect match
- 0.5-0.6: Somewhat relevant, tangentially related
- 0.3-0.4: Loosely related
- 0.0-0.2: Not relevant

**Return JSON:**
```json
{{
  "scores": [
    {{
      "paper_index": 0,
      "relevance_score": 0.95,
      "reasoning": "Brief reason"
    }},
    ...
  ]
}}
```

Return ONLY valid JSON."""

        logger.info(f"Scoring relevance for {len(papers_to_score)} papers")

        result = self._spawn_agent(
            agent_type="general-purpose",
            prompt=prompt,
            description="Score paper relevance"
        )

        # Parse result
        try:
            if isinstance(result, str):
                import re
                json_match = re.search(r'\{.*\}', result, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())

            scores = result.get("scores", [])
            logger.info(f"✅ Scored {len(scores)} papers")
            return scores

        except Exception as e:
            logger.warning(f"Error parsing relevance scores: {e}, using fallback scoring")
            # Fallback: simple keyword-based scoring
            return self._simple_relevance_scoring(user_query, papers_to_score)

    def _spawn_agent(
        self,
        agent_type: str,
        prompt: str,
        description: str
    ) -> Any:
        """
        Internal method to spawn agent with fallback.

        Uses AWS Bedrock (when in Claude Code) or Anthropic API.

        Args:
            agent_type: Agent type
            prompt: Agent prompt
            description: Short description

        Returns:
            Agent result (raw text response)
        """
        import os

        # Check if running in Claude Code (Bedrock)
        use_bedrock = os.environ.get("CLAUDE_CODE_USE_BEDROCK") == "1"

        if use_bedrock:
            return self._spawn_agent_bedrock(agent_type, prompt, description)
        else:
            return self._spawn_agent_anthropic(agent_type, prompt, description)

    def _spawn_agent_bedrock(
        self,
        agent_type: str,
        prompt: str,
        description: str
    ) -> Any:
        """Spawn agent using AWS Bedrock"""
        import os

        try:
            from anthropic import AnthropicBedrock
        except ImportError:
            logger.error("Anthropic SDK not installed. Install with: pip install anthropic")
            raise

        # Map model names to Bedrock model IDs
        model_map = {
            "haiku": "us.anthropic.claude-3-5-haiku-20241022-v1:0",
            "sonnet": "eu.anthropic.claude-sonnet-4-5-20250929-v1:0"
        }

        # Use default Sonnet model if set
        default_sonnet = os.environ.get("ANTHROPIC_DEFAULT_SONNET_MODEL")
        if default_sonnet and self.preferred_model == "sonnet":
            model_map["sonnet"] = default_sonnet

        client = AnthropicBedrock()

        # Try preferred model first
        preferred_model_id = model_map.get(self.preferred_model, model_map["haiku"])

        try:
            logger.info(f"Calling {preferred_model_id} (Bedrock) for {agent_type}...")

            response = client.messages.create(
                model=preferred_model_id,
                max_tokens=1024,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            result = response.content[0].text.strip()
            logger.info(f"✅ {agent_type} completed with {self.preferred_model}")
            return result

        except Exception as e:
            error_msg = str(e)

            # Check if it's a model access error
            if "403" in error_msg or "access" in error_msg.lower() or "denied" in error_msg.lower():
                logger.warning(f"⚠️  {self.preferred_model} access denied, trying {self.fallback_model}...")

                # Try fallback model
                fallback_model_id = model_map.get(self.fallback_model, model_map["sonnet"])

                try:
                    response = client.messages.create(
                        model=fallback_model_id,
                        max_tokens=1024,
                        messages=[
                            {"role": "user", "content": prompt}
                        ]
                    )

                    result = response.content[0].text.strip()
                    logger.info(f"✅ {agent_type} completed with {self.fallback_model}")
                    return result

                except Exception as fallback_error:
                    logger.error(f"❌ Both models failed for {agent_type}")
                    raise Exception(
                        f"Both {self.preferred_model} and {self.fallback_model} failed. "
                        f"Preferred error: {error_msg}. Fallback error: {str(fallback_error)}"
                    )
            else:
                # Not an access error, re-raise
                logger.error(f"❌ {agent_type} failed: {error_msg}")
                raise

    def _spawn_agent_anthropic(
        self,
        agent_type: str,
        prompt: str,
        description: str
    ) -> Any:
        """Spawn agent using Anthropic API (non-Bedrock)"""
        import os

        try:
            from anthropic import Anthropic
        except ImportError:
            logger.error("Anthropic SDK not installed. Install with: pip install anthropic")
            raise

        # Get API key from environment
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            logger.warning("ANTHROPIC_API_KEY not set, agent will fail")
            raise Exception("ANTHROPIC_API_KEY environment variable not set")

        # Map model names
        model_map = {
            "haiku": "claude-3-5-haiku-20241022",
            "sonnet": "claude-3-5-sonnet-20241022"
        }

        client = Anthropic(api_key=api_key)

        # Try preferred model first
        preferred_model_id = model_map.get(self.preferred_model, "claude-3-5-haiku-20241022")

        try:
            logger.info(f"Calling {preferred_model_id} for {agent_type}...")

            response = client.messages.create(
                model=preferred_model_id,
                max_tokens=1024,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            result = response.content[0].text.strip()
            logger.info(f"✅ {agent_type} completed with {self.preferred_model}")
            return result

        except Exception as e:
            error_msg = str(e)

            # Check if it's a model access error
            if "403" in error_msg or "access" in error_msg.lower():
                logger.warning(f"⚠️  {self.preferred_model} access denied, trying {self.fallback_model}...")

                # Try fallback model
                fallback_model_id = model_map.get(self.fallback_model, "claude-3-5-sonnet-20241022")

                try:
                    response = client.messages.create(
                        model=fallback_model_id,
                        max_tokens=1024,
                        messages=[
                            {"role": "user", "content": prompt}
                        ]
                    )

                    result = response.content[0].text.strip()
                    logger.info(f"✅ {agent_type} completed with {self.fallback_model}")
                    return result

                except Exception as fallback_error:
                    logger.error(f"❌ Both models failed for {agent_type}")
                    raise Exception(
                        f"Both {self.preferred_model} and {self.fallback_model} failed. "
                        f"Preferred error: {error_msg}. Fallback error: {str(fallback_error)}"
                    )
            else:
                # Not an access error, re-raise
                logger.error(f"❌ {agent_type} failed: {error_msg}")
                raise

    def _simple_query_expansion(self, query: str) -> Dict[str, Any]:
        """Fallback: Simple keyword-based query expansion"""
        words = query.split()
        return {
            "expanded_queries": [
                query,
                f"{query} framework",
                f"{query} best practices",
                f"{query} methodology",
                f"{query} case study"
            ],
            "keywords": words,
            "reasoning": "Simple keyword expansion (LLM unavailable)"
        }

    def _simple_relevance_scoring(
        self,
        query: str,
        papers: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Fallback: Simple keyword-based relevance scoring"""
        query_words = set(query.lower().split())
        scores = []

        for i, paper in enumerate(papers):
            title = paper.get("title", "").lower()
            abstract = paper.get("abstract", "").lower()

            # Count keyword matches
            title_matches = sum(1 for word in query_words if word in title)
            abstract_matches = sum(1 for word in query_words if word in abstract)

            # Simple scoring
            score = (title_matches * 0.4 + abstract_matches * 0.2) / len(query_words)
            score = min(score, 1.0)

            scores.append({
                "paper_index": i,
                "relevance_score": round(score, 2),
                "reasoning": f"Keyword match: {title_matches} in title, {abstract_matches} in abstract"
            })

        return scores


# Testing
if __name__ == "__main__":
    print("🧪 Testing Agent Factory\n")

    factory = AgentFactory()

    # Test 1: Query generation
    print("Test 1: Query Generation")
    result = factory.generate_queries("DevOps Governance", research_mode="quick")
    print(f"✅ Generated {len(result.get('expanded_queries', []))} queries")
    print(f"   Example: {result.get('expanded_queries', [''])[0]}\n")

    # Test 2: Discipline classification
    print("Test 2: Discipline Classification")
    disciplines_to_test = [
        "COVID-19 Treatment",
        "DevOps Governance",
        "Lateinische Metrik"
    ]
    for query in disciplines_to_test:
        disc = factory.classify_discipline(query)
        print(f"   '{query}' → {disc}")

    print("\n✅ Agent Factory tests completed")
    print("⚠️  Note: Actual agent spawning requires Claude Code context")
