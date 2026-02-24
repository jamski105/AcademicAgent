#!/bin/bash
# Browser-Agent Phase 0 Template: DBIS Navigation
# Version: 1.0.0 (2026-02-23)
# Usage: Wird von browser-agent referenziert, nicht direkt ausgeführt

set -euo pipefail

RUN_ID=${1:-}
MODE=${2:-"standard"}

[ -z "$RUN_ID" ] && { echo "ERROR: RUN_ID required"; exit 1; }

echo "🌐 Phase 0: DBIS Database Discovery"
echo "   Mode: $MODE"
echo "   Run: $RUN_ID"

# Output-File
OUTPUT="runs/$RUN_ID/metadata/databases.json"
mkdir -p "$(dirname "$OUTPUT")"

# DBIS URL
DBIS_URL="https://dbis.ur.de/dbinfo/fachliste.php"

# CDP Connection Check
if ! curl -s http://localhost:9222/json/version &>/dev/null; then
    echo "❌ Chrome CDP nicht erreichbar"
    exit 1
fi

echo "✅ Chrome CDP verbunden"

# Mode-spezifische Targets
case "$MODE" in
    quick)
        TARGET_DBS=5
        ;;
    standard)
        TARGET_DBS=15
        ;;
    deep)
        TARGET_DBS=30
        ;;
    *)
        echo "⚠️  Unbekannter Mode: $MODE, verwende standard"
        TARGET_DBS=15
        ;;
esac

echo "🎯 Target: $TARGET_DBS Datenbanken"

# Navigation Steps (Pseudocode - wird von browser-agent mit CDP umgesetzt)
# 1. Navigate to $DBIS_URL
# 2. Warte auf Page Load
# 3. Filter nach Fachgebiet (aus academic_context.md)
# 4. Sammle Database-Links
# 5. Extrahiere Metadaten (Name, URL, Access-Info)
# 6. Schreibe JSON

echo "📋 Output wird geschrieben: $OUTPUT"

# Validation (nach browser-agent Execution)
validate_output() {
    [ -f "$OUTPUT" ] || { echo "❌ Output fehlt"; return 1; }

    jq empty "$OUTPUT" 2>/dev/null || {
        echo "❌ Invalides JSON"
        return 1
    }

    local count=$(jq 'length' "$OUTPUT")
    [ "$count" -ge 3 ] || {
        echo "⚠️  Nur $count Datenbanken (min 3 empfohlen)"
    }

    echo "✅ $count Datenbanken gefunden"
    return 0
}

# Post-execution validation
# validate_output

echo "✅ Phase 0 Template abgeschlossen"
