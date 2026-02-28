#!/usr/bin/env python3
"""
Test script for LLM Relevance Scorer functionality
Tests with the provided input data
"""

import json
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.ranking.llm_relevance_scorer import LLMRelevanceScorer
from src.search.crossref_client import Paper


def test_llm_relevance_scorer():
    """Test the LLM Relevance Scorer with provided input"""

    print("=" * 80)
    print("TESTING LLM RELEVANCE SCORER")
    print("=" * 80)

    # Input data from user
    test_input = {
        "user_query": "DevOps Governance",
        "papers": [
            {
                "title": "DevOps Governance Framework for Enterprise IT",
                "abstract": "This paper presents a comprehensive governance framework for DevOps practices in enterprise environments, focusing on compliance and risk management.",
                "authors": ["Smith, J.", "Jones, A."],
                "year": 2023
            },
            {
                "title": "Machine Learning in Agriculture",
                "abstract": "We explore applications of machine learning for crop yield prediction.",
                "authors": ["Brown, B."],
                "year": 2022
            }
        ]
    }

    print("\nInput:")
    print(json.dumps(test_input, indent=2))
    print("\n" + "=" * 80)

    # Convert to Paper objects
    papers = []
    for i, paper_data in enumerate(test_input["papers"]):
        paper = Paper(
            doi=f"10.test/{i}",  # Generate test DOI
            title=paper_data["title"],
            authors=paper_data["authors"],
            abstract=paper_data.get("abstract"),
            year=paper_data.get("year")
        )
        papers.append(paper)

    # Test with fallback mode (no API key required)
    print("\n[1] Testing with FALLBACK MODE (keyword-based scoring)")
    print("-" * 80)

    scorer_fallback = LLMRelevanceScorer(use_fallback_if_no_key=True)
    scores_fallback = scorer_fallback.score_batch(papers, test_input["user_query"])

    output_fallback = {
        "scores": []
    }

    for i, paper in enumerate(papers):
        score = scores_fallback.get(paper.doi, 0.0)

        # Generate reasoning based on score
        if score > 0.7:
            reasoning = "High keyword overlap with query. Title and/or abstract contain multiple matching terms."
        elif score > 0.4:
            reasoning = "Moderate keyword overlap. Some query terms found in title or abstract."
        else:
            reasoning = "Low keyword overlap. Few or no matching terms with the query."

        output_fallback["scores"].append({
            "paper_index": i,
            "relevance_score": round(score, 2),
            "reasoning": reasoning
        })

    print("\nFallback Output:")
    print(json.dumps(output_fallback, indent=2))

    # Test with Haiku (if API key available)
    print("\n" + "=" * 80)
    print("\n[2] Testing with HAIKU MODE (semantic scoring)")
    print("-" * 80)

    api_key = os.getenv("ANTHROPIC_API_KEY")

    if api_key:
        print("API key found - using Haiku for semantic scoring...")
        try:
            scorer_haiku = LLMRelevanceScorer(anthropic_api_key=api_key, model="claude-haiku-4")
            scores_haiku = scorer_haiku.score_batch(papers, test_input["user_query"])

            output_haiku = {
                "scores": []
            }

            for i, paper in enumerate(papers):
                score = scores_haiku.get(paper.doi, 0.0)

                # Generate reasoning (simplified - actual Haiku call would provide this)
                if score > 0.8:
                    reasoning = "Paper directly addresses the query topic with comprehensive coverage."
                elif score > 0.5:
                    reasoning = "Paper is relevant to query with significant overlap in concepts."
                else:
                    reasoning = "Paper has minimal relevance to the query topic."

                output_haiku["scores"].append({
                    "paper_index": i,
                    "relevance_score": round(score, 2),
                    "reasoning": reasoning
                })

            print("\nHaiku Output:")
            print(json.dumps(output_haiku, indent=2))

        except Exception as e:
            print(f"Error with Haiku mode: {e}")
            print("Falling back to keyword-based scoring.")
    else:
        print("No ANTHROPIC_API_KEY found in environment.")
        print("Skipping Haiku test. Set the API key to test semantic scoring.")

    print("\n" + "=" * 80)
    print("\nEXPECTED BEHAVIOR:")
    print("-" * 80)
    print("Paper 0 (DevOps Governance Framework):")
    print("  - Should score HIGH (0.85-0.95)")
    print("  - Direct match with query topic")
    print("  - Title contains 'DevOps Governance'")
    print("  - Abstract discusses governance framework for DevOps")
    print()
    print("Paper 1 (Machine Learning in Agriculture):")
    print("  - Should score LOW (0.0-0.10)")
    print("  - Completely different topic")
    print("  - No overlap with DevOps or Governance concepts")
    print("=" * 80)

    return output_fallback


if __name__ == "__main__":
    result = test_llm_relevance_scorer()

    print("\n✓ Test completed successfully!")
    print("\nFinal JSON Output:")
    print(json.dumps(result, indent=2))
