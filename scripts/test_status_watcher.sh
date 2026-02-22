#!/bin/bash
# Test-Script für Status-Watcher
# Simuliert einen Run mit State-Updates

RUN_ID="test_$(date +%Y%m%d_%H%M%S)"
RUN_DIR="runs/$RUN_ID"

echo "🧪 Test Status-Watcher"
echo "========================"
echo ""
echo "Run ID: $RUN_ID"
echo ""

# Erstelle Run-Struktur
mkdir -p "$RUN_DIR/metadata"
mkdir -p "$RUN_DIR/logs"

# Initialer State
cat > "$RUN_DIR/metadata/research_state.json" <<EOF
{
  "run_id": "$RUN_ID",
  "status": "in_progress",
  "current_phase": 0,
  "last_completed_phase": -1,
  "started_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "last_updated": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "phase_outputs": {},
  "budget_tracking": {
    "total_cost_usd": 0,
    "remaining_usd": 3.0,
    "percent_used": 0
  }
}
EOF

# Initial Log
echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] INFO: Test Run gestartet" > "$RUN_DIR/logs/orchestrator.log"

echo "✅ Test-Run erstellt"
echo ""
echo "Starte Status-Watcher in neuem Terminal-Fenster..."
echo "Führe aus:"
echo ""
echo "  bash scripts/status_watcher.sh $RUN_ID"
echo ""
echo "Drücke Enter wenn Status-Watcher läuft..."
read

# Simuliere Phasen-Durchlauf
for phase in {0..6}; do
    echo "Phase $phase wird simuliert..."

    # Update State
    jq --arg phase "$phase" \
       --arg timestamp "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
       '.current_phase = ($phase | tonumber) |
        .last_updated = $timestamp |
        .phase_outputs["'$phase'"] = {
          status: "in_progress",
          started_at: $timestamp
        }' \
       "$RUN_DIR/metadata/research_state.json" > "$RUN_DIR/metadata/research_state.json.tmp" && \
       mv "$RUN_DIR/metadata/research_state.json.tmp" "$RUN_DIR/metadata/research_state.json"

    # Log
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] INFO: Phase $phase gestartet" >> "$RUN_DIR/logs/orchestrator.log"

    sleep 5

    # Complete Phase
    jq --arg phase "$phase" \
       --arg timestamp "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
       '.last_completed_phase = ($phase | tonumber) |
        .last_updated = $timestamp |
        .phase_outputs["'$phase'"].status = "completed" |
        .phase_outputs["'$phase'"].completed_at = $timestamp' \
       "$RUN_DIR/metadata/research_state.json" > "$RUN_DIR/metadata/research_state.json.tmp" && \
       mv "$RUN_DIR/metadata/research_state.json.tmp" "$RUN_DIR/metadata/research_state.json"

    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] INFO: Phase $phase abgeschlossen" >> "$RUN_DIR/logs/orchestrator.log"
done

# Final State
jq '.status = "completed"' \
   "$RUN_DIR/metadata/research_state.json" > "$RUN_DIR/metadata/research_state.json.tmp" && \
   mv "$RUN_DIR/metadata/research_state.json.tmp" "$RUN_DIR/metadata/research_state.json"

echo ""
echo "✅ Test abgeschlossen"
echo ""
echo "Cleanup? (j/n)"
read cleanup

if [ "$cleanup" = "j" ]; then
    rm -rf "$RUN_DIR"
    echo "🧹 Test-Run gelöscht"
fi
