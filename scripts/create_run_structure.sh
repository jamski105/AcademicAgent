#!/bin/bash

# create_run_structure.sh
# Pre-creates complete run directory structure to avoid permission prompts
# Usage: bash scripts/create_run_structure.sh <run-id>

set -euo pipefail

RUN_ID="${1:-}"

if [[ -z "$RUN_ID" ]]; then
    echo "Error: RUN_ID required"
    echo "Usage: bash scripts/create_run_structure.sh <run-id>"
    exit 1
fi

BASE_DIR="runs/$RUN_ID"

echo "📁 Creating run structure for: $RUN_ID"

# Create main directories
mkdir -p "$BASE_DIR/config"
mkdir -p "$BASE_DIR/metadata"
mkdir -p "$BASE_DIR/outputs"
mkdir -p "$BASE_DIR/logs"
mkdir -p "$BASE_DIR/downloads"

# Pre-create all metadata files (schema-conform JSON objects)
# Note: run_config.json is written by setup-agent in config/
echo '{"databases": [], "timestamp": ""}' > "$BASE_DIR/metadata/databases.json"
echo '{"search_strings": [], "timestamp": ""}' > "$BASE_DIR/metadata/search_strings.json"
echo '{"candidates": [], "timestamp": ""}' > "$BASE_DIR/metadata/candidates.json"
echo '{"ranked_sources": [], "timestamp": ""}' > "$BASE_DIR/metadata/ranked_candidates.json"
echo '{"downloads": [], "timestamp": ""}' > "$BASE_DIR/downloads/downloads.json"
echo '{"quotes": [], "timestamp": ""}' > "$BASE_DIR/outputs/quotes.json"
# Create comprehensive initial research_state.json (status_watcher expects all these fields)
cat > "$BASE_DIR/metadata/research_state.json" <<'EOF'
{
  "run_id": "",
  "status": "initialized",
  "current_phase": -1,
  "last_completed_phase": -1,
  "started_at": "",
  "last_updated": "",
  "phase_outputs": {
    "0": {"status": "pending"},
    "1": {"status": "pending"},
    "2": {"status": "pending"},
    "3": {"status": "pending"},
    "4": {"status": "pending"},
    "5": {"status": "pending"},
    "6": {"status": "pending"}
  },
  "budget_tracking": {
    "total_cost_usd": 0,
    "remaining_usd": 3.0,
    "percent_used": 0
  },
  "phase_2_state": {
    "current_iteration": 0,
    "citations_found": 0,
    "target_citations": 0,
    "consecutive_empty": 0,
    "databases_searched": [],
    "databases_remaining": []
  }
}
EOF

# Pre-create output files
touch "$BASE_DIR/outputs/quote_library.json"
touch "$BASE_DIR/outputs/bibliography.bib"

# Pre-create log files for all agents
for agent in orchestrator browser scoring extraction search setup; do
    touch "$BASE_DIR/logs/${agent}_agent.log"
done

echo "✓ Structure created successfully"
echo ""
echo "Created directories:"
echo "  • $BASE_DIR/config/"
echo "  • $BASE_DIR/metadata/"
echo "  • $BASE_DIR/outputs/"
echo "  • $BASE_DIR/logs/"
echo "  • $BASE_DIR/downloads/"
echo ""
echo "Pre-created files:"
echo "  • metadata/*.json (6 files, schema-conform)"
echo "  • downloads/downloads.json (schema-conform)"
echo "  • outputs/*.json (2 files)"
echo "  • logs/*_agent.log (6 files)"
echo ""
echo "Note: run_config.json will be created by setup-agent in config/"
echo "✅ Agents can now write without permission prompts"
