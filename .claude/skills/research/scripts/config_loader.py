#!/usr/bin/env python3
"""
Config Loader Script für Research Skill

Lädt und validiert Konfiguration bevor Linear Coordinator gestartet wird.

Usage:
    python config_loader.py --mode standard --query "DevOps Governance"
    python config_loader.py --mode quick --query "AI Ethics" --academic-context config/academic_context.md

Exit Codes:
    0: Config valid
    1: Config invalid
"""

import argparse
import json
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

try:
    from src.utils.config import load_config, get_mode_info
except ImportError as e:
    print(f"❌ Error: Cannot import config module. Did you install dependencies?", file=sys.stderr)
    print(f"   Run: pip install -r requirements-v2.txt", file=sys.stderr)
    print(f"   Details: {e}", file=sys.stderr)
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Load and validate research config")
    parser.add_argument("--mode", required=True, choices=["quick", "standard", "deep", "custom"],
                        help="Research mode")
    parser.add_argument("--query", required=True, help="Research query")
    parser.add_argument("--academic-context", help="Path to academic context file (optional)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    try:
        # Load Config
        api_config, research_config = load_config()

        # Get Mode Info
        mode_info = get_mode_info()

        # Get Selected Research Mode
        selected_mode = research_config.get_mode(args.mode)

        # Load Academic Context (optional)
        academic_context = None
        if args.academic_context:
            context_path = Path(args.academic_context)
            if context_path.exists():
                with open(context_path) as f:
                    academic_context = f.read()
            else:
                print(f"⚠️ Warning: Academic context file not found: {context_path}", file=sys.stderr)

        # Build Result
        result = {
            "valid": True,
            "mode": args.mode,
            "query": args.query,
            "api_mode": mode_info["mode"],
            "is_enhanced": mode_info["is_enhanced"],
            "api_keys": {
                "crossref": mode_info["has_crossref"],
                "openalex": mode_info["has_openalex"],
                "semantic_scholar": mode_info["has_s2"],
                "core": mode_info["has_core"]
            },
            "research_config": {
                "max_papers": selected_mode.max_papers,
                "estimated_duration_min": selected_mode.estimated_duration_min,
                "api_sources": selected_mode.api_sources,
                "scoring_weights": {
                    "relevance": selected_mode.scoring.relevance_weight,
                    "recency": selected_mode.scoring.recency_weight,
                    "quality": selected_mode.scoring.quality_weight,
                    "authority": selected_mode.scoring.authority_weight
                },
                "pdf_fetcher": {
                    "fallback_chain": selected_mode.pdf_fetcher.fallback_chain,
                    "max_parallel": selected_mode.pdf_fetcher.max_parallel
                }
            },
            "global_settings": {
                "use_llm_relevance": research_config.global_settings.use_llm_relevance,
                "checkpoint_interval_min": research_config.global_settings.checkpoint_interval_minutes,
                "auto_resume": research_config.global_settings.auto_resume_on_error
            },
            "academic_context": academic_context
        }

        # Output
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            # Human-readable output
            print("✅ Config loaded successfully!\n")
            print(f"📊 Research Mode: {args.mode}")
            print(f"📝 Query: {args.query}")
            print(f"🔧 API Mode: {mode_info['mode']}")
            print(f"📄 Max Papers: {selected_mode.max_papers}")
            print(f"⏱️  Estimated Duration: ~{selected_mode.estimated_duration_min} minutes")
            print(f"\n🔑 API Keys Status:")
            print(f"   CrossRef: {'✅' if mode_info['has_crossref'] else '⚠️ Anonymous'}")
            print(f"   OpenAlex: {'✅' if mode_info['has_openalex'] else '⚠️ Anonymous (~100 req/day limit)'}")
            print(f"   Semantic Scholar: {'✅' if mode_info['has_s2'] else '⚠️ Anonymous (slower)'}")
            print(f"   CORE: {'✅' if mode_info['has_core'] else '❌ Disabled (needs key)'}")
            print(f"\n💡 Mode: {'Enhanced (with keys)' if mode_info['is_enhanced'] else 'Standard (plug & play)'}")

            if academic_context:
                print(f"\n📚 Academic Context: Loaded ({len(academic_context)} chars)")

        sys.exit(0)

    except FileNotFoundError as e:
        error = {
            "valid": False,
            "error": "config_not_found",
            "message": str(e),
            "hint": "Check if config/api_config.yaml and config/research_modes.yaml exist"
        }

        if args.json:
            print(json.dumps(error, indent=2))
        else:
            print(f"❌ Error: Config file not found", file=sys.stderr)
            print(f"   {e}", file=sys.stderr)
            print(f"\n💡 Hint: {error['hint']}", file=sys.stderr)

        sys.exit(1)

    except ValueError as e:
        error = {
            "valid": False,
            "error": "invalid_mode",
            "message": str(e)
        }

        if args.json:
            print(json.dumps(error, indent=2))
        else:
            print(f"❌ Error: Invalid mode", file=sys.stderr)
            print(f"   {e}", file=sys.stderr)

        sys.exit(1)

    except Exception as e:
        error = {
            "valid": False,
            "error": "unknown",
            "message": str(e)
        }

        if args.json:
            print(json.dumps(error, indent=2))
        else:
            print(f"❌ Unexpected error:", file=sys.stderr)
            print(f"   {e}", file=sys.stderr)

        sys.exit(1)


if __name__ == "__main__":
    main()
