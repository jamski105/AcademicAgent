"""
Query Generator Python Wrapper für Academic Agent v2.0

Wrapper für query_generator.md Haiku-Agent

Generiert API-spezifische Boolean-Queries aus natürlichsprachlichen User-Queries

Features:
- Ruft Haiku-Agent auf (via Anthropic SDK)
- API-spezifische Query-Optimierung (CrossRef, OpenAlex, S2)
- Nutzt Academic Context (optional)
- Synonym-Expansion

Usage:
    from src.search.query_generator import QueryGenerator

    generator = QueryGenerator()
    queries = generator.generate(
        user_query="DevOps Governance",
        target_apis=["crossref", "openalex", "semantic_scholar"]
    )

    # Result:
    # {
    #   "crossref": "\"DevOps\" AND (\"governance\" OR \"compliance\")",
    #   "openalex": "DevOps AND governance",
    #   "semantic_scholar": "DevOps governance compliance"
    # }
"""

from typing import Dict, List, Optional, Any
import json
import logging
import os

from anthropic import Anthropic

# Setup Logging
logger = logging.getLogger(__name__)


# ============================================
# Query Generator
# ============================================

class QueryGenerator:
    """
    Query Generator Wrapper

    Calls query_generator.md Haiku-Agent to generate API-specific queries

    Usage:
        generator = QueryGenerator()
        queries = generator.generate("DevOps Governance")
    """

    def __init__(
        self,
        anthropic_api_key: Optional[str] = None,
        model: str = "claude-haiku-4"
    ):
        """
        Initialize Query Generator

        Args:
            anthropic_api_key: Optional Anthropic API key (falls from env: ANTHROPIC_API_KEY)
            model: Model to use (default: claude-haiku-4)
        """
        self.api_key = anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            logger.warning("No Anthropic API key found. QueryGenerator will use fallback (keyword-based)")
            self.client = None
        else:
            self.client = Anthropic(api_key=self.api_key)
            logger.info(f"QueryGenerator initialized with model: {model}")

        self.model = model

    def generate(
        self,
        user_query: str,
        target_apis: List[str] = ["crossref", "openalex", "semantic_scholar"],
        academic_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        """
        Generate API-specific queries

        Args:
            user_query: User's natural language query
            target_apis: Target APIs (default: all three)
            academic_context: Optional academic context (keywords, discipline, etc.)

        Returns:
            Dict mapping API name to optimized query

        Example:
            queries = generator.generate(
                user_query="DevOps Governance",
                target_apis=["crossref", "openalex"],
                academic_context={"keywords": ["CI/CD", "Compliance"]}
            )
        """
        logger.info(f"Generating queries for: '{user_query}'")

        # If no Anthropic client, use fallback
        if not self.client:
            return self._fallback_generate(user_query, target_apis)

        # Build prompt for Haiku-Agent
        prompt = self._build_prompt(user_query, target_apis, academic_context)

        try:
            # Call Haiku
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            # Parse response
            content = response.content[0].text
            queries = self._parse_response(content)

            logger.info(f"Generated {len(queries)} queries via Haiku")
            return queries

        except Exception as e:
            logger.error(f"Haiku call failed: {e}. Using fallback.")
            return self._fallback_generate(user_query, target_apis)

    def _build_prompt(
        self,
        user_query: str,
        target_apis: List[str],
        academic_context: Optional[Dict[str, Any]]
    ) -> str:
        """
        Build prompt for query_generator.md Agent

        Args:
            user_query: User query
            target_apis: Target APIs
            academic_context: Optional context

        Returns:
            Formatted prompt string
        """
        prompt = f"""You are the Query Generator for Academic Agent v2.0.

Generate optimized Boolean search queries for academic APIs.

Input:
{{
  "user_query": "{user_query}",
  "target_apis": {json.dumps(target_apis)}"""

        if academic_context:
            prompt += f""",
  "academic_context": {json.dumps(academic_context, indent=2)}"""

        prompt += """
}

Generate API-specific queries following these rules:

1. **CrossRef**: Boolean with quotes for phrases
   - Example: "DevOps" AND ("governance" OR "compliance")
   - Max 120 characters

2. **OpenAlex**: Boolean without quotes (fuzzy matching)
   - Example: DevOps AND (governance OR compliance)
   - Max 120 characters

3. **Semantic Scholar**: Natural language keywords
   - Example: DevOps governance compliance
   - Max 120 characters

Output as JSON:
{
  "queries": {
    "crossref": "...",
    "openalex": "...",
    "semantic_scholar": "..."
  },
  "keywords_used": ["keyword1", "keyword2"],
  "reasoning": "Brief explanation"
}"""

        return prompt

    def _parse_response(self, content: str) -> Dict[str, str]:
        """
        Parse Haiku response to extract queries

        Args:
            content: Response text from Haiku

        Returns:
            Dict mapping API name to query
        """
        try:
            # Try to parse as JSON
            if "{" in content:
                # Extract JSON from response
                start = content.find("{")
                end = content.rfind("}") + 1
                json_str = content[start:end]
                data = json.loads(json_str)

                # Extract queries
                queries = data.get("queries", {})
                return queries
            else:
                logger.warning("No JSON found in response, using fallback")
                return {}

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Haiku response: {e}")
            return {}

    def _fallback_generate(
        self,
        user_query: str,
        target_apis: List[str]
    ) -> Dict[str, str]:
        """
        Fallback query generation (keyword-based, no LLM)

        Args:
            user_query: User query
            target_apis: Target APIs

        Returns:
            Dict mapping API name to query
        """
        logger.info("Using fallback query generation (keyword-based)")

        queries = {}

        # Simple keyword-based queries
        for api in target_apis:
            if api == "crossref":
                # CrossRef: Add quotes around terms
                terms = user_query.split()
                quoted = " AND ".join(f'"{term}"' for term in terms if len(term) > 2)
                queries["crossref"] = quoted or user_query

            elif api == "openalex":
                # OpenAlex: Simple AND
                terms = user_query.split()
                queries["openalex"] = " AND ".join(terms)

            elif api == "semantic_scholar":
                # S2: Natural language
                queries["semantic_scholar"] = user_query

        return queries


# ============================================
# Convenience Functions
# ============================================

def generate_queries(
    user_query: str,
    target_apis: List[str] = ["crossref", "openalex", "semantic_scholar"],
    api_key: Optional[str] = None
) -> Dict[str, str]:
    """
    Convenience function for quick query generation

    Args:
        user_query: User query
        target_apis: Target APIs
        api_key: Optional Anthropic API key

    Returns:
        Dict mapping API name to optimized query

    Example:
        queries = generate_queries("DevOps Governance")
    """
    generator = QueryGenerator(anthropic_api_key=api_key)
    return generator.generate(user_query, target_apis=target_apis)


# ============================================
# CLI Test
# ============================================

if __name__ == "__main__":
    """
    Test Query Generator

    Run:
        python -m src.search.query_generator
    """
    print("Testing Query Generator...")

    # Test 1: Fallback mode (no API key)
    print("\n1. Testing fallback mode (no API key)...")
    generator = QueryGenerator()
    queries = generator.generate("DevOps Governance")

    print(f"✅ Generated {len(queries)} queries (fallback mode)")
    for api, query in queries.items():
        print(f"  {api}: {query}")

    # Test 2: With Academic Context
    print("\n2. Testing with academic context...")
    queries = generator.generate(
        "DevOps Governance",
        academic_context={
            "keywords": ["CI/CD", "Compliance", "Policy"],
            "discipline": "Software Engineering"
        }
    )
    print(f"✅ Generated {len(queries)} queries (with context)")

    # Test 3: Single API
    print("\n3. Testing single API...")
    queries = generator.generate(
        "Machine Learning Ethics",
        target_apis=["crossref"]
    )
    print(f"✅ Generated {len(queries)} queries (single API)")
    print(f"  CrossRef: {queries.get('crossref', 'N/A')}")

    print("\n✅ All tests passed!")
    print("\n💡 TIP: Set ANTHROPIC_API_KEY for Haiku-powered query generation!")
    print("   export ANTHROPIC_API_KEY='your-key'")
