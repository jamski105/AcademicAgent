"""
Discipline Classifier für Academic Agent v2.3+

Klassifiziert akademische Queries nach Disziplin für DBIS-Datenbank-Selektion.

UPDATED v2.3: Zwei Modi verfügbar:
1. LLM-basiert (Haiku/Sonnet) - High Accuracy (~80%+)
2. Keyword-basiert - Fallback (~40%)

Usage:
    from src.classification.discipline_classifier import classify_discipline

    # LLM mode (recommended)
    result = classify_discipline(
        user_query="COVID-19 Treatment",
        use_llm=True  # Uses AgentFactory with auto-fallback
    )

    # Keyword mode (fallback)
    result = classify_discipline(
        user_query="Lateinische Metrik",
        expanded_queries=["Latin meter", "Classical prosody"],
        use_llm=False
    )

    # CLI
    python -m src.classification.discipline_classifier \
        --query "DevOps Governance" \
        --llm  # Use LLM mode
"""

import yaml
import json
import re
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class DisciplineResult:
    """Discipline classification result"""
    primary_discipline: str
    secondary_disciplines: List[str]
    dbis_category_id: str
    relevant_databases: List[str]
    confidence: float
    reasoning: str


class DisciplineClassifier:
    """Keyword-based discipline classifier (fallback for Agent)"""

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize classifier

        Args:
            config_path: Path to dbis_disciplines.yaml (default: config/)
        """
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "config" / "dbis_disciplines.yaml"

        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self) -> dict:
        """Load DBIS disciplines configuration"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Config not found: {self.config_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML config: {e}")

    def classify(
        self,
        user_query: str,
        expanded_queries: Optional[List[str]] = None,
        academic_context: Optional[str] = None
    ) -> DisciplineResult:
        """
        Classify query into academic discipline

        Args:
            user_query: Original user query
            expanded_queries: Optional expanded query variations
            academic_context: Optional user-provided academic context

        Returns:
            DisciplineResult with classification
        """
        # Combine all query text
        all_text = user_query.lower()
        if expanded_queries:
            all_text += " " + " ".join([q.lower() for q in expanded_queries])
        if academic_context:
            all_text += " " + academic_context.lower()

        # Score each discipline
        discipline_scores = {}
        disciplines = self.config.get('disciplines', {})

        for discipline_name, discipline_data in disciplines.items():
            keywords = discipline_data.get('keywords', [])
            if not keywords:
                continue

            # Count keyword matches
            matches = 0
            for keyword in keywords:
                if keyword.lower() in all_text:
                    matches += 1

            # Calculate score (normalized by number of keywords)
            score = matches / len(keywords) if keywords else 0
            discipline_scores[discipline_name] = score

        # Find best match
        if not discipline_scores or max(discipline_scores.values()) == 0:
            return self._fallback_result("No keyword matches found")

        # Sort by score
        sorted_disciplines = sorted(
            discipline_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        primary_discipline = sorted_disciplines[0][0]
        primary_score = sorted_disciplines[0][1]

        # Secondary disciplines (score > 0)
        secondary_disciplines = [
            d for d, s in sorted_disciplines[1:4] if s > 0
        ]

        # Get discipline data
        discipline_data = disciplines[primary_discipline]
        dbis_category_id = discipline_data.get('dbis_category_id', '')
        databases = discipline_data.get('databases', [])

        # Extract database names (top 5)
        relevant_databases = [
            db['name'] for db in databases[:5]
        ]

        # Calculate confidence (based on score)
        # 1.0 = all keywords matched, 0.0 = no matches
        confidence = min(primary_score * 2, 1.0)  # Scale to 0-1

        # Reasoning
        reasoning = (
            f"Keyword matching detected '{primary_discipline}' "
            f"with {int(primary_score * 100)}% keyword overlap"
        )

        return DisciplineResult(
            primary_discipline=primary_discipline,
            secondary_disciplines=secondary_disciplines,
            dbis_category_id=dbis_category_id,
            relevant_databases=relevant_databases,
            confidence=round(confidence, 2),
            reasoning=reasoning
        )

    def classify_llm(
        self,
        user_query: str,
        expanded_queries: Optional[List[str]] = None
    ) -> DisciplineResult:
        """
        Classify using LLM-based semantic analysis (Haiku/Sonnet with auto-fallback).

        Args:
            user_query: Original user query
            expanded_queries: Optional expanded query variations

        Returns:
            DisciplineResult with classification
        """
        try:
            # Import AgentFactory here to avoid circular imports
            from src.agents.agent_factory import AgentFactory

            factory = AgentFactory()
            discipline_name = factory.classify_discipline(user_query, expanded_queries)

            # Map discipline to config
            if discipline_name in self.config.get('disciplines', {}):
                discipline_data = self.config['disciplines'][discipline_name]
                dbis_category_id = discipline_data.get('dbis_category_id', '')
                databases = discipline_data.get('databases', [])

                relevant_databases = [
                    db['name'] for db in databases[:5]
                ]

                return DisciplineResult(
                    primary_discipline=discipline_name,
                    secondary_disciplines=[],
                    dbis_category_id=dbis_category_id,
                    relevant_databases=relevant_databases,
                    confidence=0.85,  # High confidence for LLM-based
                    reasoning=f"LLM semantic analysis classified as '{discipline_name}'"
                )
            else:
                # Unknown discipline, use fallback
                return self._fallback_result(
                    f"LLM returned unknown discipline: {discipline_name}"
                )

        except Exception as e:
            # LLM failed, use keyword-based fallback
            import logging
            logging.warning(f"LLM classification failed: {e}, using keyword fallback")
            return self.classify(user_query, expanded_queries)

    def _fallback_result(self, reason: str) -> DisciplineResult:
        """Return fallback result when no discipline detected"""
        # Get fallback databases from config
        fallback_dbs = self.config.get('mapping_rules', {}).get('fallback_databases', [
            "JSTOR",
            "SpringerLink",
            "PubMed"
        ])

        return DisciplineResult(
            primary_discipline="Unknown",
            secondary_disciplines=[],
            dbis_category_id="",
            relevant_databases=fallback_dbs,
            confidence=0.30,
            reasoning=reason
        )


def classify_discipline(
    user_query: str,
    expanded_queries: Optional[List[str]] = None,
    academic_context: Optional[str] = None,
    config_path: Optional[Path] = None,
    use_llm: bool = True
) -> Dict:
    """
    Convenience function for discipline classification

    Args:
        user_query: Original user query
        expanded_queries: Optional expanded queries
        academic_context: Optional user context
        config_path: Optional config file path
        use_llm: Use LLM-based classification (default: True, recommended)

    Returns:
        Dict with classification result
    """
    classifier = DisciplineClassifier(config_path=config_path)

    if use_llm:
        result = classifier.classify_llm(user_query, expanded_queries)
    else:
        result = classifier.classify(user_query, expanded_queries, academic_context)

    return asdict(result)


# ============================================
# CLI
# ============================================

def main():
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description="Discipline Classifier - Maps queries to academic disciplines"
    )
    parser.add_argument(
        '--query',
        required=False,
        help='User query to classify'
    )
    parser.add_argument(
        '--expanded',
        help='Comma-separated expanded queries'
    )
    parser.add_argument(
        '--context',
        help='Optional academic context'
    )
    parser.add_argument(
        '--config',
        help='Path to dbis_disciplines.yaml'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output JSON only'
    )
    parser.add_argument(
        '--llm',
        action='store_true',
        help='Use LLM-based classification (recommended)'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Run tests'
    )

    args = parser.parse_args()

    # Test mode
    if args.test:
        mode_name = "LLM-based" if args.llm else "Keyword-based"
        print(f"Running discipline classifier tests ({mode_name})...")
        test_cases = [
            ("Lateinische Metrik", "Klassische Philologie"),
            ("Machine Learning Optimization", "Informatik"),
            ("COVID-19 Treatment", "Medizin"),
            ("DevOps Governance", "Informatik"),
            ("Social Media Impact", "Psychologie"),
        ]

        classifier = DisciplineClassifier()
        passed = 0
        failed = 0

        for query, expected in test_cases:
            if args.llm:
                result = classifier.classify_llm(query)
            else:
                result = classifier.classify(query)

            if result.primary_discipline == expected:
                print(f"✅ PASS: '{query}' → {expected} (conf: {result.confidence})")
                passed += 1
            else:
                print(f"❌ FAIL: '{query}' → Expected {expected}, got {result.primary_discipline}")
                failed += 1

        print(f"\n📊 Results: {passed} passed, {failed} failed")
        sys.exit(0 if failed == 0 else 1)

    # Normal mode
    try:
        expanded = args.expanded.split(',') if args.expanded else None
        config_path = Path(args.config) if args.config else None

        result = classify_discipline(
            user_query=args.query,
            expanded_queries=expanded,
            academic_context=args.context,
            config_path=config_path,
            use_llm=args.llm
        )

        if args.json:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(f"\n🎓 Discipline Classification")
            print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            print(f"Query: {args.query}")
            print(f"\n📌 Primary Discipline: {result['primary_discipline']}")
            print(f"🔀 Secondary: {', '.join(result['secondary_disciplines']) or 'None'}")
            print(f"📊 DBIS Category: {result['dbis_category_id']}")
            print(f"📚 Databases: {', '.join(result['relevant_databases'])}")
            print(f"✓ Confidence: {result['confidence']}")
            print(f"💡 Reasoning: {result['reasoning']}")

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
