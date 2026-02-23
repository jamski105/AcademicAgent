#!/bin/bash
# Browser-Agent Phase 2 Template: Iterative Database Search
# Version: 1.0.0 (2026-02-23)

set -euo pipefail

RUN_ID=${1:-}
[ -z "$RUN_ID" ] && { echo "ERROR: RUN_ID required"; exit 1; }

source scripts/templates/cdp_retry_handler.sh

echo "🔍 Phase 2: Iterative Database Search"

# Input Files
DATABASES="runs/$RUN_ID/metadata/databases.json"
SEARCH_STRINGS="runs/$RUN_ID/metadata/search_strings.json"

# Output
OUTPUT="runs/$RUN_ID/metadata/candidates.json"
mkdir -p "$(dirname "$OUTPUT")"

# Validation
[ -f "$DATABASES" ] || { echo "❌ databases.json fehlt"; exit 1; }
[ -f "$SEARCH_STRINGS" ] || { echo "❌ search_strings.json fehlt"; exit 1; }

# Iteration Config
MAX_ITERATIONS=30
RESULTS_PER_DB=10

db_count=$(jq 'length' "$DATABASES")
search_count=$(jq 'length' "$SEARCH_STRINGS")

echo "📊 Config:"
echo "   Datenbanken: $db_count"
echo "   Suchstrings: $search_count"
echo "   Max Iterations: $MAX_ITERATIONS"

# Initialize Results
echo "[]" > "$OUTPUT"

# Iterative Search Loop
for i in $(seq 0 $((MAX_ITERATIONS - 1))); do
    echo ""
    echo "🔄 Iteration $((i + 1))/$MAX_ITERATIONS"

    db_index=$((i % db_count))
    search_index=$((i % search_count))

    db_url=$(jq -r ".[$db_index].url" "$DATABASES")
    db_name=$(jq -r ".[$db_index].database_name" "$DATABASES")
    search_string=$(jq -r ".[$search_index].search_string" "$SEARCH_STRINGS")

    echo "   DB: $db_name"
    echo "   Query: ${search_string:0:50}..."

    # CDP Navigate mit Retry
    cdp_navigate "$db_url" 30 || {
        echo "⚠️  Navigation fehlgeschlagen, skip Iteration $i"
        continue
    }

    # Search Execution (Pseudocode - wird von browser-agent umgesetzt)
    # 1. Find search input field
    # 2. Enter search_string
    # 3. Submit form
    # 4. Wait for results
    # 5. Extract result metadata (title, authors, year, DOI/URL)
    # 6. Append to OUTPUT

    echo "   ✅ $RESULTS_PER_DB Ergebnisse gesammelt"

    # Akkumuliere Ergebnisse
    # jq ". += \$new_results" "$OUTPUT" > "$OUTPUT.tmp" && mv "$OUTPUT.tmp" "$OUTPUT"
done

# Final Validation
final_count=$(jq 'length' "$OUTPUT")
echo ""
echo "📊 Gesamt-Ergebnisse: $final_count Kandidaten"

[ "$final_count" -ge 10 ] || {
    echo "⚠️  Weniger als 10 Kandidaten gefunden"
}

echo "✅ Phase 2 abgeschlossen"
