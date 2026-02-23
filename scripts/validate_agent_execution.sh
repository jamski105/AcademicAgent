#!/bin/bash
# Validation Script - Stellt sicher dass Orchestrator Sub-Agents spawnt
# Prüft auf fake/synthetische Daten

set -euo pipefail

PHASE=$1
RUN_ID=$2

if [ -z "$PHASE" ] || [ -z "$RUN_ID" ]; then
    echo "❌ Fehler: Fehlende Parameter"
    echo "Usage: bash scripts/validate_agent_execution.sh <phase> <run-id>"
    exit 1
fi

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "╭────────────────────────────────────────────────────────────╮"
echo "│ 🔍 Validiere Phase $PHASE Execution                            │"
echo "├────────────────────────────────────────────────────────────┤"
echo "│ Run ID: $RUN_ID                                            │"
echo "╰────────────────────────────────────────────────────────────╯"
echo ""

VALIDATION_FAILED=false

# Phase-spezifische Validierung
case $PHASE in
    0)
        echo "→ Validiere Phase 0: DBIS Navigation"
        echo ""

        # Prüfe ob browser-agent gelaufen ist
        if [ ! -f "runs/$RUN_ID/logs/browser_agent.log" ]; then
            echo -e "${YELLOW}⚠️  WARNUNG: browser_agent.log fehlt${NC}"
            echo "   Phase 0 könnte übersprungen worden sein (OK bei iterative mode)"
        else
            # Prüfe Log-Größe (sollte > 0 sein wenn Agent lief)
            LOG_SIZE=$(stat -f%z "runs/$RUN_ID/logs/browser_agent.log" 2>/dev/null || stat -c%s "runs/$RUN_ID/logs/browser_agent.log" 2>/dev/null || echo "0")
            if [ "$LOG_SIZE" -eq 0 ]; then
                echo -e "${YELLOW}⚠️  WARNUNG: browser_agent.log ist leer${NC}"
                echo "   Agent wurde möglicherweise nicht ausgeführt"
            else
                echo -e "${GREEN}✅ browser_agent.log existiert und ist nicht leer${NC}"
            fi
        fi

        # Prüfe databases.json (nur wenn manual mode)
        SEARCH_MODE=$(jq -r '.search_strategy.mode // "iterative"' "runs/$RUN_ID/run_config.json")
        if [ "$SEARCH_MODE" = "manual" ]; then
            if [ ! -f "runs/$RUN_ID/metadata/databases.json" ]; then
                echo -e "${RED}❌ FEHLER: databases.json fehlt (manual mode)${NC}"
                VALIDATION_FAILED=true
            else
                echo -e "${GREEN}✅ databases.json existiert${NC}"
            fi
        fi
        ;;

    2)
        echo "→ Validiere Phase 2: Database Search"
        echo ""

        # CRITICAL: Prüfe candidates.json auf SYNTHETIC DOIs
        if [ -f "runs/$RUN_ID/metadata/candidates.json" ]; then
            SYNTHETIC_COUNT=$(jq '[.candidates[] | select(.doi | contains("SYNTHETIC"))] | length' "runs/$RUN_ID/metadata/candidates.json" 2>/dev/null || echo "0")

            if [ "$SYNTHETIC_COUNT" -gt 0 ]; then
                echo -e "${RED}╔══════════════════════════════════════════════════════════════╗${NC}"
                echo -e "${RED}║  ❌ KRITISCHER FEHLER: FAKE DATEN ERKANNT                    ║${NC}"
                echo -e "${RED}╠══════════════════════════════════════════════════════════════╣${NC}"
                echo -e "${RED}║  $SYNTHETIC_COUNT Kandidaten mit SYNTHETIC DOIs gefunden!         ║${NC}"
                echo -e "${RED}║                                                              ║${NC}"
                echo -e "${RED}║  Der Orchestrator hat candidates.json NICHT via              ║${NC}"
                echo -e "${RED}║  browser-agent generiert, sondern fake Daten erstellt!      ║${NC}"
                echo -e "${RED}║                                                              ║${NC}"
                echo -e "${RED}║  Dies verstößt gegen die Agent-Contracts!                   ║${NC}"
                echo -e "${RED}╚══════════════════════════════════════════════════════════════╝${NC}"
                echo ""
                echo "Fake DOIs:"
                jq -r '.candidates[] | select(.doi | contains("SYNTHETIC")) | "  • \(.doi) - \(.title)"' "runs/$RUN_ID/metadata/candidates.json"
                echo ""
                VALIDATION_FAILED=true
            else
                echo -e "${GREEN}✅ Keine SYNTHETIC DOIs gefunden${NC}"

                # Prüfe browser-agent.log
                if [ ! -f "runs/$RUN_ID/logs/browser_agent.log" ]; then
                    echo -e "${RED}❌ FEHLER: browser_agent.log fehlt${NC}"
                    echo "   Phase 2 muss via browser-agent ausgeführt werden!"
                    VALIDATION_FAILED=true
                else
                    LOG_SIZE=$(stat -f%z "runs/$RUN_ID/logs/browser_agent.log" 2>/dev/null || stat -c%s "runs/$RUN_ID/logs/browser_agent.log" 2>/dev/null || echo "0")
                    if [ "$LOG_SIZE" -eq 0 ]; then
                        echo -e "${RED}❌ FEHLER: browser_agent.log ist leer${NC}"
                        VALIDATION_FAILED=true
                    else
                        echo -e "${GREEN}✅ browser_agent.log existiert und enthält Daten${NC}"
                    fi
                fi
            fi

            # Prüfe Anzahl Kandidaten
            CANDIDATE_COUNT=$(jq '.candidates | length' "runs/$RUN_ID/metadata/candidates.json")
            echo "→ Gefundene Kandidaten: $CANDIDATE_COUNT"

            if [ "$CANDIDATE_COUNT" -eq 0 ]; then
                echo -e "${YELLOW}⚠️  WARNUNG: Keine Kandidaten gefunden${NC}"
                echo "   Dies kann legitim sein, sollte aber überprüft werden."
            fi
        else
            echo -e "${RED}❌ FEHLER: candidates.json fehlt${NC}"
            VALIDATION_FAILED=true
        fi
        ;;

    4)
        echo "→ Validiere Phase 4: PDF Download"
        echo ""

        # Prüfe downloads.json
        if [ ! -f "runs/$RUN_ID/downloads/downloads.json" ]; then
            echo -e "${RED}❌ FEHLER: downloads.json fehlt${NC}"
            echo "   Phase 4 muss immer downloads.json schreiben (auch bei Fehler)!"
            VALIDATION_FAILED=true
        else
            echo -e "${GREEN}✅ downloads.json existiert${NC}"

            # Validiere JSON-Struktur
            if ! jq empty "runs/$RUN_ID/downloads/downloads.json" 2>/dev/null; then
                echo -e "${RED}❌ FEHLER: downloads.json ist kein valides JSON${NC}"
                VALIDATION_FAILED=true
            else
                # Zähle Erfolge/Fehler
                SUCCESS_COUNT=$(jq '[.downloads[] | select(.status=="success")] | length' "runs/$RUN_ID/downloads/downloads.json" 2>/dev/null || echo "0")
                FAILED_COUNT=$(jq '[.downloads[] | select(.status=="failed")] | length' "runs/$RUN_ID/downloads/downloads.json" 2>/dev/null || echo "0")
                TOTAL_ATTEMPTS=$(jq '.downloads | length' "runs/$RUN_ID/downloads/downloads.json" 2>/dev/null || echo "0")

                echo "→ Download-Statistik:"
                echo "   Versuche:  $TOTAL_ATTEMPTS"
                echo "   Erfolge:   $SUCCESS_COUNT"
                echo "   Fehler:    $FAILED_COUNT"

                # Zähle echte PDFs im Filesystem
                PDF_COUNT=$(find "runs/$RUN_ID/downloads/" -name "*.pdf" 2>/dev/null | wc -l | tr -d ' ')
                echo "   PDFs (FS): $PDF_COUNT"

                # WARNUNG (nicht Fehler) bei 0 PDFs, aber nur wenn auch downloads.json sagt dass 0 erfolgreich
                if [ "$PDF_COUNT" -eq 0 ] && [ "$SUCCESS_COUNT" -eq 0 ] && [ "$TOTAL_ATTEMPTS" -gt 0 ]; then
                    echo -e "${YELLOW}⚠️  WARNUNG: Keine PDFs heruntergeladen${NC}"
                    echo "   Alle $TOTAL_ATTEMPTS Download-Versuche fehlgeschlagen."

                    # Zeige häufigste Fehlertypen
                    echo "   Häufigste Fehler:"
                    jq -r '.downloads[] | select(.status=="failed") | .error_type' "runs/$RUN_ID/downloads/downloads.json" 2>/dev/null | sort | uniq -c | sort -rn | head -3 | sed 's/^/     /'

                    echo ""
                    echo "   Dies ist KEIN Validierungsfehler - downloads.json ist strukturiert."
                    echo "   Phase 5 kann NICHT fortfahren ohne PDFs."
                elif [ "$PDF_COUNT" -ne "$SUCCESS_COUNT" ]; then
                    echo -e "${YELLOW}⚠️  INKONSISTENZ: PDF-Count ($PDF_COUNT) != Success-Count ($SUCCESS_COUNT)${NC}"
                    echo "   Prüfe downloads.json und Filesystem."
                else
                    echo -e "${GREEN}✅ $PDF_COUNT PDFs erfolgreich heruntergeladen${NC}"

                    # Prüfe ob PDFs valide sind (nicht leer)
                    EMPTY_PDFS=0
                    for pdf in runs/$RUN_ID/downloads/*.pdf 2>/dev/null; do
                        if [ -f "$pdf" ]; then
                            SIZE=$(stat -f%z "$pdf" 2>/dev/null || stat -c%s "$pdf" 2>/dev/null || echo "0")
                            if [ "$SIZE" -lt 1024 ]; then
                                echo -e "${YELLOW}⚠️  WARNUNG: $pdf ist sehr klein (<1KB)${NC}"
                                EMPTY_PDFS=$((EMPTY_PDFS + 1))
                            fi
                        fi
                    done

                    if [ "$EMPTY_PDFS" -gt 0 ]; then
                        echo -e "${YELLOW}⚠️  $EMPTY_PDFS PDFs könnten leer/korrupt sein${NC}"
                    fi
                fi
            fi
        fi
        ;;

    5)
        echo "→ Validiere Phase 5: Quote Extraction"
        echo ""

        # Prüfe quotes.json
        if [ ! -f "runs/$RUN_ID/outputs/quotes.json" ]; then
            echo -e "${RED}❌ FEHLER: quotes.json fehlt${NC}"
            VALIDATION_FAILED=true
        else
            echo -e "${GREEN}✅ quotes.json existiert${NC}"

            # Prüfe auf halluzinierte Zitate (keine Seitenzahlen = fake)
            QUOTES_WITHOUT_PAGES=$(jq '[.quotes[] | select(.page_number == null or .page_number == "")] | length' "runs/$RUN_ID/outputs/quotes.json" 2>/dev/null || echo "0")

            if [ "$QUOTES_WITHOUT_PAGES" -gt 0 ]; then
                echo -e "${YELLOW}⚠️  WARNUNG: $QUOTES_WITHOUT_PAGES Zitate ohne Seitenzahl${NC}"
                echo "   Zitate sollten aus echten PDFs mit Seitenzahlen extrahiert werden."
            fi

            # Prüfe extraction-agent.log
            if [ ! -f "runs/$RUN_ID/logs/extraction_agent.log" ]; then
                echo -e "${RED}❌ FEHLER: extraction_agent.log fehlt${NC}"
                VALIDATION_FAILED=true
            else
                echo -e "${GREEN}✅ extraction_agent.log existiert${NC}"
            fi
        fi
        ;;

    *)
        echo "⚠️  Keine Validierung für Phase $PHASE definiert"
        ;;
esac

echo ""
echo "────────────────────────────────────────────────────────────"
echo ""

if [ "$VALIDATION_FAILED" = true ]; then
    echo -e "${RED}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║  ❌ VALIDATION FEHLGESCHLAGEN                                ║${NC}"
    echo -e "${RED}╠══════════════════════════════════════════════════════════════╣${NC}"
    echo -e "${RED}║  Phase $PHASE hat kritische Validierungsfehler!                ║${NC}"
    echo -e "${RED}║                                                              ║${NC}"
    echo -e "${RED}║  Der Orchestrator MUSS Sub-Agents spawnen und darf KEINE    ║${NC}"
    echo -e "${RED}║  synthetischen Daten generieren!                             ║${NC}"
    echo -e "${RED}║                                                              ║${NC}"
    echo -e "${RED}║  Workflow wird abgebrochen.                                  ║${NC}"
    echo -e "${RED}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""

    # Log failure
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Phase $PHASE validation FAILED" >> "runs/$RUN_ID/logs/validation_failures.log"

    exit 1
else
    echo -e "${GREEN}╭────────────────────────────────────────────────────────────╮${NC}"
    echo -e "${GREEN}│ ✅ VALIDATION ERFOLGREICH                                  │${NC}"
    echo -e "${GREEN}├────────────────────────────────────────────────────────────┤${NC}"
    echo -e "${GREEN}│ Phase $PHASE wurde korrekt via Sub-Agent ausgeführt.        │${NC}"
    echo -e "${GREEN}│ Keine synthetischen Daten erkannt.                         │${NC}"
    echo -e "${GREEN}╰────────────────────────────────────────────────────────────╯${NC}"
    echo ""

    exit 0
fi
