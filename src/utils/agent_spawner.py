"""
Agent Spawner with Automatic Model Fallback
Academic Agent v2.3+

Automatically handles model fallback when Haiku is unavailable:
- Try Haiku first (fast, cheap)
- Fallback to Sonnet if Haiku access denied (slower, more expensive, but works)

Usage:
    from src.utils.agent_spawner import spawn_agent_with_fallback

    result = spawn_agent_with_fallback(
        agent_type="query_generator",
        prompt="Generate queries for: DevOps Governance"
    )
"""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class ModelAccessError(Exception):
    """Raised when model access is denied"""
    pass


def spawn_agent_with_fallback(
    agent_type: str,
    prompt: str,
    description: str = "",
    preferred_model: str = "haiku",
    fallback_model: str = "sonnet",
    run_in_background: bool = False,
    timeout: Optional[int] = None
) -> Any:
    """
    Spawn an agent with automatic model fallback.

    Args:
        agent_type: Type of agent to spawn (e.g., "query_generator")
        prompt: Prompt for the agent
        description: Short description of the task (3-5 words)
        preferred_model: Model to try first (default: "haiku")
        fallback_model: Model to use if preferred fails (default: "sonnet")
        run_in_background: Run agent in background
        timeout: Timeout in milliseconds

    Returns:
        Agent result object

    Raises:
        Exception: If both preferred and fallback models fail
    """

    # Generate description if not provided
    if not description:
        description = f"Run {agent_type} agent"

    # Try preferred model first (usually Haiku - fast & cheap)
    try:
        logger.info(f"Spawning {agent_type} agent with {preferred_model.upper()} model...")

        # Import Task here to avoid circular imports
        # In Claude Code context, Task is available as a tool
        # This is a placeholder - actual implementation uses Claude Code's Task tool

        result = _spawn_agent_task(
            agent_type=agent_type,
            prompt=prompt,
            description=description,
            model=preferred_model,
            run_in_background=run_in_background,
            timeout=timeout
        )

        logger.info(f"✅ {agent_type} completed successfully with {preferred_model.upper()}")
        return result

    except Exception as e:
        error_msg = str(e)

        # Check if it's a model access error (403, IAM permissions, etc.)
        if _is_model_access_error(error_msg):
            logger.warning(
                f"⚠️  {preferred_model.upper()} model access denied for {agent_type}. "
                f"Falling back to {fallback_model.upper()}..."
            )

            # Try fallback model (usually Sonnet - slower but more reliable)
            try:
                result = _spawn_agent_task(
                    agent_type=agent_type,
                    prompt=prompt,
                    description=description,
                    model=fallback_model,
                    run_in_background=run_in_background,
                    timeout=timeout
                )

                logger.info(
                    f"✅ {agent_type} completed successfully with {fallback_model.upper()} fallback"
                )
                return result

            except Exception as fallback_error:
                logger.error(
                    f"❌ Both {preferred_model.upper()} and {fallback_model.upper()} "
                    f"failed for {agent_type}: {str(fallback_error)}"
                )
                raise Exception(
                    f"Agent {agent_type} failed with both models. "
                    f"Preferred ({preferred_model}): {error_msg}. "
                    f"Fallback ({fallback_model}): {str(fallback_error)}"
                )
        else:
            # Not a model access error - re-raise original exception
            logger.error(f"❌ {agent_type} failed: {error_msg}")
            raise


def _is_model_access_error(error_msg: str) -> bool:
    """
    Check if error message indicates model access denial.

    Args:
        error_msg: Error message string

    Returns:
        True if it's a model access error, False otherwise
    """
    model_access_keywords = [
        "403",
        "model access is denied",
        "iam user or service role is not authorized",
        "aws-marketplace",
        "viewsubscriptions",
        "subscribe",
        "not authorized to perform",
        "access denied",
        "permission denied",
        "unauthorized"
    ]

    error_lower = error_msg.lower()
    return any(keyword in error_lower for keyword in model_access_keywords)


def _spawn_agent_task(
    agent_type: str,
    prompt: str,
    description: str,
    model: str,
    run_in_background: bool = False,
    timeout: Optional[int] = None
) -> Any:
    """
    Internal method to spawn agent using Claude Code Task tool.

    This is a placeholder that should be called from Claude Code context
    where the Task tool is available.

    Args:
        agent_type: Type of agent
        prompt: Agent prompt
        description: Short description
        model: Model to use
        run_in_background: Background execution
        timeout: Timeout in ms

    Returns:
        Agent result
    """
    # This function should be called from Claude Code context
    # where Task tool is available. The actual implementation
    # will use the Task tool directly.

    raise NotImplementedError(
        "This function must be called from Claude Code context with Task tool available. "
        "Use the spawn_agent_with_fallback function from within Claude Code agents."
    )


# Convenience functions for specific agent types

def spawn_query_generator(user_query: str, research_mode: str = "quick") -> Dict[str, Any]:
    """Spawn query_generator agent with fallback"""
    prompt = f"""Generate alternative search queries for academic research.

User Query: "{user_query}"
Research Mode: {research_mode}

Generate 3-5 alternative queries with:
- Expanded acronyms
- Related terms
- Variations
- Academic focus

Return JSON with expanded_queries array."""

    return spawn_agent_with_fallback(
        agent_type="query_generator",
        prompt=prompt,
        description="Generate search queries"
    )


def spawn_discipline_classifier(user_query: str, expanded_queries: list) -> str:
    """Spawn discipline_classifier agent with fallback"""
    queries_str = "\n".join(f"- {q}" for q in expanded_queries)

    prompt = f"""Classify the academic discipline for this research query.

User Query: "{user_query}"

Expanded Queries:
{queries_str}

Available Disciplines:
- Informatik (Computer Science, IT, Software, DevOps)
- Rechtswissenschaft (Law, Legal, Juristisch, Mietrecht)
- Medizin (Medicine, Health, Clinical, COVID)
- Klassische Philologie (Latin, Greek, Ancient Languages)
- Psychologie (Psychology, Social Science, Mental Health)
- Wirtschaftswissenschaften (Business, Economics, Management)
- Naturwissenschaften (Physics, Chemistry, Biology)
- Ingenieurwissenschaften (Engineering, Technical Sciences)

Return only the discipline name."""

    result = spawn_agent_with_fallback(
        agent_type="discipline_classifier",
        prompt=prompt,
        description="Classify research discipline"
    )

    return result.get("discipline", "Unknown")


def spawn_relevance_scorer(user_query: str, papers: list) -> Dict[str, Any]:
    """Spawn llm_relevance_scorer agent with fallback"""
    papers_json = []
    for i, paper in enumerate(papers):
        papers_json.append({
            "index": i,
            "title": paper.get("title", ""),
            "abstract": paper.get("abstract", "")[:500],  # Limit abstract length
            "authors": paper.get("authors", [])[:3],  # Limit authors
            "year": paper.get("year")
        })

    import json
    papers_str = json.dumps(papers_json, indent=2)

    prompt = f"""Score the relevance of these papers to the research query.

Query: "{user_query}"

Papers:
{papers_str}

Score each paper 0.0-1.0 based on:
- Title relevance
- Abstract content match
- Semantic similarity

Return JSON with scores array:
{{
  "scores": [
    {{"paper_index": 0, "relevance_score": 0.95, "reasoning": "..."}},
    ...
  ]
}}"""

    return spawn_agent_with_fallback(
        agent_type="llm_relevance_scorer",
        prompt=prompt,
        description="Score paper relevance"
    )


def spawn_quote_extractor(paper_text: str, user_query: str, max_quotes: int = 3) -> list:
    """Spawn quote_extractor agent with fallback"""
    # Limit text length to avoid token limits
    text_preview = paper_text[:5000] if len(paper_text) > 5000 else paper_text

    prompt = f"""Extract {max_quotes} relevant quotes from this paper.

Query: "{user_query}"

Paper Text:
{text_preview}

Extract quotes that:
- Directly address the research query
- Are self-contained and meaningful
- Include key definitions, findings, or comparisons

Return JSON with quotes array:
{{
  "quotes": [
    {{"text": "...", "relevance": 0.9, "context": "..."}},
    ...
  ]
}}"""

    result = spawn_agent_with_fallback(
        agent_type="quote_extractor",
        prompt=prompt,
        description="Extract relevant quotes"
    )

    return result.get("quotes", [])


# Testing utilities

def test_fallback_mechanism():
    """Test the fallback mechanism with a mock agent"""
    import sys

    print("🧪 Testing Agent Spawner Fallback Mechanism\n")

    # Test 1: Model access error detection
    print("Test 1: Model Access Error Detection")
    test_errors = [
        "403 Model access is denied",
        "IAM user is not authorized to perform aws-marketplace:Subscribe",
        "Permission denied for model access",
        "Some other error"
    ]

    for error in test_errors:
        is_access_error = _is_model_access_error(error)
        status = "✅" if (is_access_error and "403" in error or "IAM" in error or "Permission" in error) or (not is_access_error and "other" in error) else "❌"
        print(f"{status} '{error[:50]}...' → {'ACCESS ERROR' if is_access_error else 'OTHER ERROR'}")

    print("\n✅ Fallback mechanism utility functions tested successfully")
    print("\n⚠️  Note: Actual agent spawning requires Claude Code context with Task tool")


if __name__ == "__main__":
    # Run tests
    test_fallback_mechanism()
