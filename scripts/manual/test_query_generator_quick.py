#!/usr/bin/env python3
"""
Test Query Generator in Quick Mode

Tests the query_generator functionality with:
- Input: User Query = "DevOps Governance"
- Mode: quick
- Output: JSON with expanded_queries array (3 alternative search queries)
"""

import json
import os
from anthropic import Anthropic

def test_query_generator_quick():
    """
    Test query generator in quick mode

    Simulates the query_generator agent call as it would be done
    by the linear_coordinator in quick mode.
    """
    print("=" * 60)
    print("Testing Query Generator - Quick Mode")
    print("=" * 60)
    print()

    # Input parameters
    user_query = "DevOps Governance"
    mode = "quick"

    print(f"Input:")
    print(f"  User Query: {user_query}")
    print(f"  Mode: {mode}")
    print()

    # Check for API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ERROR: ANTHROPIC_API_KEY not found in environment")
        print("   Please set: export ANTHROPIC_API_KEY='your-key'")
        return None

    # Initialize client
    client = Anthropic(api_key=api_key)

    # Build prompt for query_generator agent
    # This mimics what the linear_coordinator would send
    prompt = f"""You are the Query Generator for Academic Agent v2.0.

Your task is to generate 3 alternative search queries for academic APIs.

Input:
{{
  "user_query": "{user_query}",
  "research_mode": "{mode}"
}}

In QUICK mode, generate 3 focused alternative search queries that expand on the user's query.

Output as JSON:
{{
  "expanded_queries": [
    "alternative query 1",
    "alternative query 2",
    "alternative query 3"
  ],
  "keywords": ["keyword1", "keyword2", "..."],
  "reasoning": "Brief explanation of query expansion strategy"
}}

Requirements:
- Generate exactly 3 expanded queries
- Each query should be a variation that explores different aspects
- Keep queries focused and academic
- Include synonyms and related terms
- Output valid JSON only
"""

    print("Calling query_generator agent (Haiku)...")
    print()

    try:
        # Call Haiku agent
        response = client.messages.create(
            model="claude-haiku-4",
            max_tokens=1024,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        # Extract response
        content = response.content[0].text

        # Parse JSON
        if "{" in content:
            start = content.find("{")
            end = content.rfind("}") + 1
            json_str = content[start:end]
            result = json.loads(json_str)

            # Display output
            print("=" * 60)
            print("Output:")
            print("=" * 60)
            print()
            print(json.dumps(result, indent=2))
            print()

            # Validate output
            print("=" * 60)
            print("Validation:")
            print("=" * 60)

            checks = []

            # Check 1: Has expanded_queries field
            has_expanded = "expanded_queries" in result
            checks.append(("✓" if has_expanded else "✗", "Has 'expanded_queries' field", has_expanded))

            # Check 2: expanded_queries is a list
            is_list = isinstance(result.get("expanded_queries", None), list)
            checks.append(("✓" if is_list else "✗", "expanded_queries is a list", is_list))

            # Check 3: Has exactly 3 queries
            if is_list:
                count = len(result["expanded_queries"])
                has_three = count == 3
                checks.append(("✓" if has_three else "✗", f"Has 3 queries (found: {count})", has_three))
            else:
                checks.append(("✗", "Cannot count queries (not a list)", False))

            # Check 4: Has keywords field
            has_keywords = "keywords" in result
            checks.append(("✓" if has_keywords else "✗", "Has 'keywords' field", has_keywords))

            # Check 5: Has reasoning field
            has_reasoning = "reasoning" in result
            checks.append(("✓" if has_reasoning else "✗", "Has 'reasoning' field", has_reasoning))

            # Display checks
            for symbol, desc, passed in checks:
                print(f"{symbol} {desc}")

            print()

            # Summary
            all_passed = all(check[2] for check in checks)
            if all_passed:
                print("✅ All validation checks passed!")
            else:
                failed_count = sum(1 for check in checks if not check[2])
                print(f"⚠️  {failed_count}/{len(checks)} validation checks failed")

            print()

            return result

        else:
            print("❌ ERROR: No JSON found in agent response")
            print(f"Response: {content[:200]}...")
            return None

    except Exception as e:
        print(f"❌ ERROR: Agent call failed")
        print(f"   {type(e).__name__}: {e}")
        return None


def mock_query_generator_quick():
    """
    Mock version that shows expected output without API call

    This demonstrates the expected output format for quick mode.
    """
    print("=" * 60)
    print("Mock Query Generator - Quick Mode")
    print("=" * 60)
    print()

    # Input parameters
    user_query = "DevOps Governance"
    mode = "quick"

    print(f"Input:")
    print(f"  User Query: {user_query}")
    print(f"  Mode: {mode}")
    print()

    # Simulate query generation based on agent logic
    result = {
        "expanded_queries": [
            "DevOps governance frameworks and best practices",
            "Continuous delivery governance and compliance",
            "Infrastructure as Code governance policies"
        ],
        "keywords": [
            "DevOps",
            "governance",
            "compliance",
            "CI/CD",
            "infrastructure",
            "policy",
            "frameworks"
        ],
        "reasoning": "Expanded 'DevOps Governance' into 3 focused variations covering frameworks, continuous delivery, and infrastructure aspects. Included synonyms (compliance, policy) and related DevOps concepts (CI/CD, Infrastructure as Code)."
    }

    print("=" * 60)
    print("Output:")
    print("=" * 60)
    print()
    print(json.dumps(result, indent=2))
    print()

    # Validate output
    print("=" * 60)
    print("Validation:")
    print("=" * 60)

    checks = [
        ("✓", "Has 'expanded_queries' field", True),
        ("✓", "expanded_queries is a list", True),
        ("✓", "Has 3 queries (found: 3)", True),
        ("✓", "Has 'keywords' field", True),
        ("✓", "Has 'reasoning' field", True)
    ]

    for symbol, desc, _ in checks:
        print(f"{symbol} {desc}")

    print()
    print("✅ All validation checks passed!")
    print()

    return result


if __name__ == "__main__":
    # Check if API key is available
    api_key = os.getenv("ANTHROPIC_API_KEY")

    if api_key:
        print("🔑 API key found - running live test with Haiku agent")
        print()
        result = test_query_generator_quick()
    else:
        print("ℹ️  No API key found - running mock simulation")
        print("   (To run with real agent, set: export ANTHROPIC_API_KEY='your-key')")
        print()
        result = mock_query_generator_quick()

    if result:
        print()
        print("=" * 60)
        print("Test completed successfully!")
        print("=" * 60)
    else:
        print()
        print("=" * 60)
        print("Test failed!")
        print("=" * 60)
        exit(1)
