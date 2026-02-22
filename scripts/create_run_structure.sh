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
mkdir -p "$BASE_DIR/metadata"
mkdir -p "$BASE_DIR/output"
mkdir -p "$BASE_DIR/logs"
mkdir -p "$BASE_DIR/downloads"

# Pre-create all metadata files (empty JSON arrays/objects)
touch "$BASE_DIR/run_config.json"
echo "[]" > "$BASE_DIR/metadata/databases.json"
echo "[]" > "$BASE_DIR/metadata/search_strings.json"
echo "[]" > "$BASE_DIR/metadata/candidates.json"
echo "[]" > "$BASE_DIR/metadata/ranked_candidates.json"
echo "[]" > "$BASE_DIR/metadata/downloads.json"
echo "[]" > "$BASE_DIR/metadata/quotes.json"
echo '{"phase": "init", "iteration": 0, "total_candidates": 0, "databases_searched": [], "termination_reason": null}' > "$BASE_DIR/metadata/research_state.json"

# Pre-create output files
touch "$BASE_DIR/output/Quote_Library.csv"
touch "$BASE_DIR/output/quote_library.json"
touch "$BASE_DIR/output/bibliography.bib"
touch "$BASE_DIR/output/Annotated_Bibliography.md"
touch "$BASE_DIR/output/search_report.md"

# Pre-create log files for all agents
for agent in orchestrator browser scoring extraction search setup; do
    touch "$BASE_DIR/logs/${agent}_agent.log"
done

echo "✓ Structure created successfully"
echo ""
echo "Created directories:"
echo "  • $BASE_DIR/metadata/"
echo "  • $BASE_DIR/output/"
echo "  • $BASE_DIR/logs/"
echo "  • $BASE_DIR/downloads/"
echo ""
echo "Pre-created files:"
echo "  • run_config.json"
echo "  • metadata/*.json (7 files)"
echo "  • output/*.{csv,json,bib,md} (5 files)"
echo "  • logs/*_agent.log (6 files)"
echo ""
echo "✅ Agents can now write without permission prompts"
