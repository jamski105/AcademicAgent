"""
DBIS Search Orchestrator v2.3

Prepares DBIS search configuration for dbis_search agent.
Supports Discovery Mode (v2.3) and Config Mode (v2.2).

WICHTIG: Dies ist ein ORCHESTRATOR-Modul, KEIN eigenständiger Searcher!
Die eigentliche DBIS-Suche wird vom dbis_search Agent (Sonnet + Chrome MCP) durchgeführt.

Dieses Modul:
- Bereitet DBIS-Suche vor (lädt Config, formatiert Query)
- Entscheidet: Discovery Mode oder Config Mode
- Wird vom linear_coordinator aufgerufen
- Coordinator spawnt dann dbis_search Agent mit vorbereiteten Daten

Architecture:
    linear_coordinator.md
        → calls: python -m src.search.dbis_search_orchestrator (prep)
        → spawns: Task(subagent_type="dbis_search") (actual search)

Usage:
    # Discovery Mode (v2.3)
    python -m src.search.dbis_search_orchestrator \
        --query "Mietrecht Kündigungsfristen" \
        --discipline "Rechtswissenschaft" \
        --max-databases 5 \
        --output /tmp/dbis_config.json

    # Output: Agent-ready JSON config with discovery settings
"""

import yaml
import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import date


def load_dbis_config() -> dict:
    """Load DBIS disciplines configuration"""
    config_path = Path(__file__).parent.parent.parent / "config" / "dbis_disciplines.yaml"
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def load_dbis_selectors() -> dict:
    """Load DBIS HTML selectors (v2.3)"""
    selectors_path = Path(__file__).parent.parent.parent / "config" / "dbis_selectors.yaml"
    if selectors_path.exists():
        with open(selectors_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    else:
        # Fallback selectors
        return {
            "database_entry": {"primary": "tr[id^='db_']"},
            "database_name": {"primary": "td.td2 a"},
            "traffic_light": {"primary": "img[src*='dbis_']"},
            "database_link": {"primary": "a[title='Zum Angebot']"}
        }


def prepare_dbis_search(
    user_query: str,
    discipline: str,
    max_databases: int = 3,
    mode: str = "auto"  # auto, discovery, config
) -> Dict:
    """
    Prepare DBIS search configuration for agent (v2.3 with Discovery)

    Args:
        user_query: User's research query
        discipline: Detected discipline (from discipline_classifier)
        max_databases: Max databases to search/discover
        mode: "auto" (check config), "discovery" (force), "config" (force)

    Returns:
        Dict with agent-ready configuration including discovery settings
    """
    config = load_dbis_config()
    selectors = load_dbis_selectors()
    disciplines = config.get('disciplines', {})

    # Get discipline data
    if discipline not in disciplines:
        # Fallback to general databases
        return {
            "user_query": user_query,
            "discipline": "Unknown",
            "mode": "config",
            "databases": config.get('general_fallback_databases', [])[:max_databases],
            "dbis_category_id": "",
            "limit": max_databases * 20
        }

    discipline_data = disciplines[discipline]

    # Determine mode: Discovery vs Config
    if mode == "auto":
        discovery_enabled = discipline_data.get('discovery_enabled', False)
    elif mode == "discovery":
        discovery_enabled = True
    else:  # mode == "config"
        discovery_enabled = False

    # Prepare base config
    base_config = {
        "user_query": user_query,
        "discipline": discipline,
        "dbis_category_id": discipline_data.get('dbis_category_id', ''),
        "dbis_url": discipline_data.get('dbis_url', ''),
        "limit": max_databases * 20  # Papers per database
    }

    if discovery_enabled:
        # ========================================
        # DISCOVERY MODE (v2.3)
        # ========================================

        # Get discovery defaults from config
        discovery_defaults = config.get('discovery_defaults', {})
        discovery_blacklist = config.get('discovery_blacklist', [])

        # Build discovery config
        discovery_config = {
            "enabled": True,
            "dbis_url": discipline_data.get('dbis_url', ''),
            "max_databases": discipline_data.get('discovery_max_databases', max_databases),
            "timeout_seconds": discovery_defaults.get('timeout_seconds', 30),

            # Preferred databases (prioritized if found)
            "preferred_databases": discipline_data.get('preferred_databases', []),

            # HTML Selectors
            "selectors": {
                "database_entry": selectors.get('database_entry', {}).get('primary', ''),
                "database_name": selectors.get('database_name', {}).get('primary', ''),
                "traffic_light": selectors.get('traffic_light', {}).get('primary', ''),
                "access_link": selectors.get('database_link', {}).get('primary', ''),

                # Traffic light indicators
                "green_indicator": selectors.get('traffic_light', {}).get('green', ['dbis_gr_']),
                "yellow_indicator": selectors.get('traffic_light', {}).get('yellow', ['dbis_ge_']),
                "red_indicator": selectors.get('traffic_light', {}).get('red', ['dbis_ro_'])
            },

            # Blacklist
            "blacklist": discovery_blacklist,

            # Caching
            "cache_key": f"dbis_discovery_{discipline}_{date.today().isoformat()}",
            "cache_ttl_hours": discovery_defaults.get('cache_ttl_hours', 24)
        }

        # Fallback databases (if discovery fails)
        fallback_dbs = discipline_data.get('fallback_databases', [])
        fallback_db_list = []
        for db in fallback_dbs[:max_databases]:
            if isinstance(db, dict):
                fallback_db_list.append(db)
            else:
                fallback_db_list.append({"name": db, "priority": 99})

        base_config.update({
            "mode": "discovery",
            "discovery": discovery_config,
            "fallback_databases": fallback_db_list
        })

    else:
        # ========================================
        # CONFIG MODE (v2.2 - Predefined)
        # ========================================

        databases = discipline_data.get('databases', [])

        # Sort by priority and take top N
        sorted_dbs = sorted(databases, key=lambda x: x.get('priority', 999))
        top_databases = sorted_dbs[:max_databases]

        # Prepare database info with selectors
        db_info = {}
        for db in top_databases:
            db_info[db['name']] = {
                'search_selector': db.get('search_selector', '#search'),
                'result_selector': db.get('result_selector', '.result'),
                'search_type': db.get('search_type', 'basic'),
                'pagination': db.get('pagination', False),
                'max_pages': db.get('max_pages', 1)
            }

        base_config.update({
            "mode": "config",
            "databases": [db['name'] for db in top_databases],
            "selectors": db_info
        })

    return base_config


def main():
    """CLI for DBIS search preparation"""
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="DBIS Search Orchestrator v2.3")
    parser.add_argument('--query', required=True, help='User query')
    parser.add_argument('--discipline', required=True, help='Academic discipline')
    parser.add_argument('--max-databases', type=int, default=5, help='Max databases (default: 5)')
    parser.add_argument('--mode', choices=['auto', 'discovery', 'config'], default='auto',
                        help='Mode: auto (check config), discovery (force), config (force)')
    parser.add_argument('--output', help='Output JSON file')
    parser.add_argument('--test', action='store_true', help='Run test with sample data')

    args = parser.parse_args()

    if args.test:
        # Test with Rechtswissenschaft (has discovery enabled)
        print("🧪 Testing DBIS Orchestrator v2.3...")
        print()

        test_config = prepare_dbis_search(
            user_query="Mietrecht Kündigungsfristen",
            discipline="Rechtswissenschaft",
            max_databases=5,
            mode="auto"
        )

        print("✅ Test Config Generated:")
        print(json.dumps(test_config, indent=2, ensure_ascii=False))
        print()
        print(f"Mode: {test_config['mode']}")
        print(f"Discovery Enabled: {test_config.get('discovery', {}).get('enabled', False)}")
        sys.exit(0)

    try:
        config = prepare_dbis_search(
            user_query=args.query,
            discipline=args.discipline,
            max_databases=args.max_databases,
            mode=args.mode
        )

        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            print(f"✅ DBIS config saved: {args.output}")
            print(f"   Mode: {config['mode']}")
        else:
            print(json.dumps(config, indent=2, ensure_ascii=False))

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
