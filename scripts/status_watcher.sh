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

        # Phase-Specific Details
        case "$CURRENT_PHASE" in
            2)
                # Phase 2: Iterative Search
                ITERATION=$(jq -r '.phase_2_state.current_iteration // 0' "$STATE_FILE" 2>/dev/null)
                CITATIONS_FOUND=$(jq -r '.phase_2_state.citations_found // 0' "$STATE_FILE" 2>/dev/null)
                TARGET_CITATIONS=$(jq -r '.phase_2_state.target_citations // 0' "$STATE_FILE" 2>/dev/null)
                CONSECUTIVE_EMPTY=$(jq -r '.phase_2_state.consecutive_empty // 0' "$STATE_FILE" 2>/dev/null)
                DBS_SEARCHED=$(jq -r '.phase_2_state.databases_searched | length // 0' "$STATE_FILE" 2>/dev/null)
                DBS_REMAINING=$(jq -r '.phase_2_state.databases_remaining | length // 0' "$STATE_FILE" 2>/dev/null)

                echo "╭────────────────────────────────────────────────────────────╮"
                echo "│ 🔍 Iterative Search Details (Phase 2)                     │"
                echo "├────────────────────────────────────────────────────────────┤"
                echo "│ Iteration:         $ITERATION"
                echo "│ Citations Found:   $CITATIONS_FOUND / $TARGET_CITATIONS"
                echo "│ Empty Searches:    $CONSECUTIVE_EMPTY"
                echo "│ DBs Searched:      $DBS_SEARCHED"
                echo "│ DBs Remaining:     $DBS_REMAINING"
                echo "╰────────────────────────────────────────────────────────────╯"
                echo ""
                ;;
            4)
                # Phase 4: PDF Downloads
                TOTAL_ATTEMPTS=$(jq '.downloads | length // 0' "runs/$RUN_ID/downloads/downloads.json" 2>/dev/null || echo "0")
                SUCCESS_DL=$(jq '[.downloads[] | select(.status=="success")] | length // 0' "runs/$RUN_ID/downloads/downloads.json" 2>/dev/null || echo "0")
                FAILED_DL=$(jq '[.downloads[] | select(.status=="failed")] | length // 0' "runs/$RUN_ID/downloads/downloads.json" 2>/dev/null || echo "0")

                echo "╭────────────────────────────────────────────────────────────╮"
                echo "│ 📥 PDF Download Details (Phase 4)                         │"
                echo "├────────────────────────────────────────────────────────────┤"
                echo "│ Total Attempts:    $TOTAL_ATTEMPTS"
                echo "│ Successful:        $SUCCESS_DL"
                echo "│ Failed:            $FAILED_DL"
                if [ "$TOTAL_ATTEMPTS" -gt 0 ]; then
                    SUCCESS_RATE=$((SUCCESS_DL * 100 / TOTAL_ATTEMPTS))
                    echo "│ Success Rate:      ${SUCCESS_RATE}%"
                fi
                echo "╰────────────────────────────────────────────────────────────╯"
                echo ""
                ;;
            5)
                # Phase 5: Quote Extraction
                TOTAL_QUOTES=$(jq '.quotes | length // 0' "runs/$RUN_ID/outputs/quotes.json" 2>/dev/null || echo "0")
                PDF_FILES=$(find "runs/$RUN_ID/downloads/" -name "*.pdf" 2>/dev/null | wc -l | tr -d ' ')

                echo "╭────────────────────────────────────────────────────────────╮"
                echo "│ 📝 Quote Extraction Details (Phase 5)                     │"
                echo "├────────────────────────────────────────────────────────────┤"
                echo "│ PDFs Available:    $PDF_FILES"
                echo "│ Quotes Extracted:  $TOTAL_QUOTES"
                if [ "$PDF_FILES" -gt 0 ] && [ "$TOTAL_QUOTES" -gt 0 ]; then
                    AVG_QUOTES=$((TOTAL_QUOTES / PDF_FILES))
                    echo "│ Avg per PDF:       $AVG_QUOTES"
                fi
                echo "╰────────────────────────────────────────────────────────────╯"
                echo ""
                ;;
        esac

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

        # Artifact Status (File Counts)
        echo "╭────────────────────────────────────────────────────────────╮"
        echo "│ 📦 Artifacts Status                                        │"
        echo "├────────────────────────────────────────────────────────────┤"

        # Count databases
        DB_COUNT=$(jq '.databases | length // 0' "runs/$RUN_ID/metadata/databases.json" 2>/dev/null || echo "0")
        echo "│ Databases:        $DB_COUNT selected"

        # Count search strings
        SS_COUNT=$(jq '.search_strings | length // 0' "runs/$RUN_ID/metadata/search_strings.json" 2>/dev/null || echo "0")
        echo "│ Search Strings:   $SS_COUNT generated"

        # Count candidates
        CAND_COUNT=$(jq '.candidates | length // 0' "runs/$RUN_ID/metadata/candidates.json" 2>/dev/null || echo "0")
        echo "│ Candidates:       $CAND_COUNT found"

        # Count ranked candidates
        RANKED_COUNT=$(jq '.ranked_sources | length // 0' "runs/$RUN_ID/metadata/ranked_candidates.json" 2>/dev/null || echo "0")
        echo "│ Ranked:           $RANKED_COUNT scored"

        # Count PDFs
        PDF_COUNT=$(find "runs/$RUN_ID/downloads/" -name "*.pdf" 2>/dev/null | wc -l | tr -d ' ')
        PDF_SUCCESS=$(jq '[.downloads[] | select(.status=="success")] | length // 0' "runs/$RUN_ID/downloads/downloads.json" 2>/dev/null || echo "0")
        echo "│ PDFs:             $PDF_COUNT downloaded ($PDF_SUCCESS successful)"

        # Count quotes
        QUOTE_COUNT=$(jq '.quotes | length // 0' "runs/$RUN_ID/outputs/quotes.json" 2>/dev/null || echo "0")
        echo "│ Quotes:           $QUOTE_COUNT extracted"

        echo "╰────────────────────────────────────────────────────────────╯"
        echo ""

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
            elif [ "$PHASE_STATUS" == "failed" ]; then
                echo -e "│ [${RED}❌${NC}] Phase $phase: $PHASE_NAME"
            else
                echo "│ [⏸️ ] Phase $phase: $PHASE_NAME"
            fi
        done

        echo "╰────────────────────────────────────────────────────────────╯"
        echo ""

        # Errors & Warnings (with Next Actions)
        HAS_ERRORS=false
        HAS_WARNINGS=false
        ERROR_MSG=""
        WARNING_MSG=""

        # Check for failed phases
        for phase in {0..6}; do
            PHASE_STATUS=$(jq -r ".phase_outputs[\"$phase\"].status // \"pending\"" "$STATE_FILE" 2>/dev/null)
            if [ "$PHASE_STATUS" == "failed" ]; then
                HAS_ERRORS=true
                ERROR_MSG="Phase $phase (${PHASE_NAMES[$phase]}) failed"
                break
            fi
        done

        # Check for stuck state (no update in >10 minutes)
        if [ -n "$LAST_UPDATED" ] && [ "$LAST_UPDATED" != "N/A" ]; then
            LAST_TS=$(date -j -f "%Y-%m-%dT%H:%M:%S" "$(echo $LAST_UPDATED | cut -d'.' -f1)" +%s 2>/dev/null || echo "0")
            NOW_TS=$(date +%s)
            DIFF_SECONDS=$((NOW_TS - LAST_TS))
            if [ "$DIFF_SECONDS" -gt 600 ] && [ "$STATUS" == "in_progress" ]; then
                HAS_WARNINGS=true
                WARNING_MSG="No state updates for >10 minutes. Agent might be stuck."
            fi
        fi

        # Check for Phase 4 with 0 PDFs
        if [ "$CURRENT_PHASE" == "4" ] || [ "$LAST_COMPLETED_PHASE" == "4" ]; then
            if [ "$PDF_COUNT" -eq 0 ]; then
                HAS_WARNINGS=true
                WARNING_MSG="Phase 4 completed but 0 PDFs downloaded. Check download logs."
            fi
        fi

        if [ "$HAS_ERRORS" = true ] || [ "$HAS_WARNINGS" = true ]; then
            echo "╭────────────────────────────────────────────────────────────╮"
            if [ "$HAS_ERRORS" = true ]; then
                echo -e "│ ${RED}❌ ERROR${NC}                                                   │"
            else
                echo -e "│ ${YELLOW}⚠️  WARNING${NC}                                                │"
            fi
            echo "├────────────────────────────────────────────────────────────┤"

            if [ -n "$ERROR_MSG" ]; then
                echo "│ $ERROR_MSG"
            fi
            if [ -n "$WARNING_MSG" ]; then
                echo "│ $WARNING_MSG"
            fi

            echo "│                                                            │"
            echo "│ 📋 Next Actions:                                           │"

            if [ "$HAS_ERRORS" = true ]; then
                echo "│  1. Check logs: runs/$RUN_ID/logs/*.log"
                echo "│  2. Validate: bash scripts/validate_agent_execution.sh"
                echo "│  3. Review failed phase output artifacts"
            else
                echo "│  1. Check orchestrator logs for blocking issues"
                echo "│  2. Verify Chrome CDP connection (Phase 0/2/4)"
                echo "│  3. If stuck >15min, consider manual resume"
            fi

            echo "╰────────────────────────────────────────────────────────────╯"
            echo ""
        fi

        # Current Agent Activity (from JSONL logs)
        echo "╭────────────────────────────────────────────────────────────╮"
        echo "│ 🤖 Current Agent Activity                                  │"
        echo "├────────────────────────────────────────────────────────────┤"

        # Check latest orchestrator JSONL events
        if [ -f "runs/$RUN_ID/logs/orchestrator_agent.jsonl" ]; then
            LAST_EVENT=$(tail -n 1 "runs/$RUN_ID/logs/orchestrator_agent.jsonl" 2>/dev/null)
            if [ -n "$LAST_EVENT" ]; then
                EVENT_TYPE=$(echo "$LAST_EVENT" | jq -r '.event // "unknown"')
                EVENT_PHASE=$(echo "$LAST_EVENT" | jq -r '.phase // ""')
                EVENT_AGENT=$(echo "$LAST_EVENT" | jq -r '.agent // ""')
                EVENT_TIME=$(echo "$LAST_EVENT" | jq -r '.timestamp // ""' | cut -d'T' -f2 | cut -d'.' -f1)

                case "$EVENT_TYPE" in
                    "agent_spawn")
                        echo "│ Spawning:         $EVENT_AGENT (Phase $EVENT_PHASE)"
                        echo "│ Started:          $EVENT_TIME UTC"
                        ;;
                    "agent_complete")
                        echo "│ Completed:        $EVENT_AGENT (Phase $EVENT_PHASE)"
                        echo "│ Finished:         $EVENT_TIME UTC"
                        ;;
                    "phase_start")
                        echo "│ Phase:            $EVENT_PHASE started"
                        echo "│ Time:             $EVENT_TIME UTC"
                        ;;
                    *)
                        echo "│ Last Event:       $EVENT_TYPE"
                        ;;
                esac
            else
                echo "│ No agent activity logged yet"
            fi
        else
            echo "│ No orchestrator logs found"
        fi

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
