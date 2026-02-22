#!/bin/bash
# Status Watcher für Academic Agent Live-Monitoring
# Zeigt Live-Updates von research_state.json an

RUN_ID=$1

if [ -z "$RUN_ID" ]; then
    echo "❌ Fehler: RUN_ID fehlt"
    echo "Usage: bash scripts/status_watcher.sh <run-id>"
    exit 1
fi

STATE_FILE="runs/$RUN_ID/metadata/research_state.json"
LOG_FILE="runs/$RUN_ID/logs/orchestrator.log"

# Phase Namen für bessere Lesbarkeit
declare -A PHASE_NAMES
PHASE_NAMES[0]="DBIS Navigation"
PHASE_NAMES[1]="Suchstring-Generierung"
PHASE_NAMES[2]="Datenbanksuche"
PHASE_NAMES[3]="Screening & Ranking"
PHASE_NAMES[4]="PDF-Download"
PHASE_NAMES[5]="Zitat-Extraktion"
PHASE_NAMES[6]="Finalisierung"

# Farben für bessere Visualisierung (optional, falls Terminal ANSI unterstützt)
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

while true; do
    clear

    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║                                                            ║"
    echo "║       🎓 ACADEMIC AGENT - LIVE STATUS                      ║"
    echo "║                                                            ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""

    if [ -f "$STATE_FILE" ]; then
        # Parse JSON mit jq
        STATUS=$(jq -r '.status // "unknown"' "$STATE_FILE" 2>/dev/null)
        CURRENT_PHASE=$(jq -r '.current_phase // "N/A"' "$STATE_FILE" 2>/dev/null)
        LAST_COMPLETED=$(jq -r '.last_completed_phase // -1' "$STATE_FILE" 2>/dev/null)
        STARTED_AT=$(jq -r '.started_at // "N/A"' "$STATE_FILE" 2>/dev/null)
        LAST_UPDATED=$(jq -r '.last_updated // "N/A"' "$STATE_FILE" 2>/dev/null)

        # Budget Tracking
        TOTAL_COST=$(jq -r '.budget_tracking.total_cost_usd // 0' "$STATE_FILE" 2>/dev/null)
        REMAINING_BUDGET=$(jq -r '.budget_tracking.remaining_usd // 0' "$STATE_FILE" 2>/dev/null)
        PERCENT_USED=$(jq -r '.budget_tracking.percent_used // 0' "$STATE_FILE" 2>/dev/null)

        echo "╭────────────────────────────────────────────────────────────╮"
        echo "│ 📋 Run Information                                         │"
        echo "├────────────────────────────────────────────────────────────┤"
        echo "│ Run ID:        $RUN_ID"
        echo "│ Status:        $STATUS"
        echo "│ Started:       $STARTED_AT"
        echo "│ Last Update:   $LAST_UPDATED"
        echo "╰────────────────────────────────────────────────────────────╯"
        echo ""

        # Phase Status
        PHASE_NAME="${PHASE_NAMES[$CURRENT_PHASE]}"
        if [ -z "$PHASE_NAME" ]; then
            PHASE_NAME="Unknown"
        fi

        echo "╭────────────────────────────────────────────────────────────╮"
        echo "│ 🔄 Phase Status                                            │"
        echo "├────────────────────────────────────────────────────────────┤"
        echo "│ Current Phase: $CURRENT_PHASE/6 - $PHASE_NAME"
        echo "│ Last Completed: $LAST_COMPLETED"
        echo "╰────────────────────────────────────────────────────────────╯"
        echo ""

        # Progress Bar
        if [ "$CURRENT_PHASE" != "N/A" ]; then
            PROGRESS=$((CURRENT_PHASE * 100 / 7))
            FILLED=$((PROGRESS / 2))
            EMPTY=$((50 - FILLED))

            echo "╭────────────────────────────────────────────────────────────╮"
            echo "│ 📈 Overall Progress: ${PROGRESS}%"
            echo "│ [$(printf '█%.0s' $(seq 1 $FILLED))$(printf '░%.0s' $(seq 1 $EMPTY))]"
            echo "╰────────────────────────────────────────────────────────────╯"
            echo ""
        fi

        # Phase 2 Specific (Iterative Search)
        if [ "$CURRENT_PHASE" == "2" ]; then
            ITERATION=$(jq -r '.phase_2_state.current_iteration // 0' "$STATE_FILE" 2>/dev/null)
            CITATIONS_FOUND=$(jq -r '.phase_2_state.citations_found // 0' "$STATE_FILE" 2>/dev/null)
            TARGET_CITATIONS=$(jq -r '.phase_2_state.target_citations // 0' "$STATE_FILE" 2>/dev/null)
            CONSECUTIVE_EMPTY=$(jq -r '.phase_2_state.consecutive_empty // 0' "$STATE_FILE" 2>/dev/null)
            DBS_SEARCHED=$(jq -r '.phase_2_state.databases_searched | length // 0' "$STATE_FILE" 2>/dev/null)
            DBS_REMAINING=$(jq -r '.phase_2_state.databases_remaining | length // 0' "$STATE_FILE" 2>/dev/null)

            echo "╭────────────────────────────────────────────────────────────╮"
            echo "│ 🔍 Iterative Search Details                                │"
            echo "├────────────────────────────────────────────────────────────┤"
            echo "│ Iteration:         $ITERATION"
            echo "│ Citations Found:   $CITATIONS_FOUND / $TARGET_CITATIONS"
            echo "│ Empty Searches:    $CONSECUTIVE_EMPTY"
            echo "│ DBs Searched:      $DBS_SEARCHED"
            echo "│ DBs Remaining:     $DBS_REMAINING"
            echo "╰────────────────────────────────────────────────────────────╯"
            echo ""
        fi

        # Budget Status
        if [ "$TOTAL_COST" != "0" ]; then
            echo "╭────────────────────────────────────────────────────────────╮"
            echo "│ 💰 Budget Status                                           │"
            echo "├────────────────────────────────────────────────────────────┤"
            echo "│ Total Cost:       \$${TOTAL_COST} USD"
            echo "│ Remaining:        \$${REMAINING_BUDGET} USD"
            echo "│ Used:             ${PERCENT_USED}%"
            echo "╰────────────────────────────────────────────────────────────╯"
            echo ""
        fi

        # Phase Outputs Summary
        echo "╭────────────────────────────────────────────────────────────╮"
        echo "│ 📊 Phase Completion Status                                 │"
        echo "├────────────────────────────────────────────────────────────┤"

        for phase in {0..6}; do
            PHASE_STATUS=$(jq -r ".phase_outputs[\"$phase\"].status // \"pending\"" "$STATE_FILE" 2>/dev/null)
            PHASE_NAME="${PHASE_NAMES[$phase]}"

            if [ "$PHASE_STATUS" == "completed" ]; then
                echo "│ [✅] Phase $phase: $PHASE_NAME"
            elif [ "$PHASE_STATUS" == "in_progress" ]; then
                echo "│ [⏳] Phase $phase: $PHASE_NAME"
            else
                echo "│ [⏸️ ] Phase $phase: $PHASE_NAME"
            fi
        done

        echo "╰────────────────────────────────────────────────────────────╯"
        echo ""

    else
        echo "╭────────────────────────────────────────────────────────────╮"
        echo "│ ⏳ Warte auf State-File...                                  │"
        echo "├────────────────────────────────────────────────────────────┤"
        echo "│ Run ID:         $RUN_ID                                    │"
        echo "│ Expected File:  $STATE_FILE"
        echo "│                                                            │"
        echo "│ Der Orchestrator wird den State bald initialisieren.       │"
        echo "╰────────────────────────────────────────────────────────────╯"
        echo ""
    fi

    # Log Tail
    echo "─────────────────────────────────────────────────────────────"
    echo "📋 Letzte Log-Einträge (orchestrator.log):"
    echo ""

    if [ -f "$LOG_FILE" ]; then
        tail -n 5 "$LOG_FILE" | sed 's/^/  /'
    else
        echo "  (Noch keine Logs verfügbar)"
    fi

    echo ""
    echo "─────────────────────────────────────────────────────────────"
    echo "⏰ Aktualisiert: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "🔄 Nächstes Update in 3 Sekunden..."
    echo ""
    echo "Drücke Strg+C zum Beenden"

    sleep 3
done
