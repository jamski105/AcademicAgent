#!/bin/bash
# CDP Health Check Script
# Überwacht Chrome DevTools Protocol Verbindung
# Automatische Wiederherstellung falls Chrome abstürzt

set -euo pipefail

CDP_PORT=9222
CDP_URL="http://localhost:${CDP_PORT}/json/version"
MAX_RETRIES=3
RETRY_DELAY=5

# Farben
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # Keine Farbe

# Prüfe ob Chrome CDP läuft
check_cdp() {
    curl -s --connect-timeout 3 "$CDP_URL" > /dev/null 2>&1
    return $?
}

# Hole Chrome Prozess-Info
get_chrome_pid() {
    # macOS
    pgrep -f "remote-debugging-port=${CDP_PORT}" 2>/dev/null | head -1
}

# Prüfe Chrome Speicherverbrauch
check_chrome_memory() {
    local pid=$(get_chrome_pid)
    if [ -z "$pid" ]; then
        return 1
    fi

    # macOS: Hole Speicher in MB
    local mem_mb=$(ps -o rss= -p "$pid" 2>/dev/null | awk '{print int($1/1024)}')

    if [ -z "$mem_mb" ]; then
        return 1
    fi

    echo "$mem_mb"
    return 0
}

# Starte Chrome mit CDP neu
restart_chrome() {
    echo -e "${YELLOW}🔄 Starte Chrome neu...${NC}"

    # Beende existierendes Chrome
    local pid=$(get_chrome_pid)
    if [ -n "$pid" ]; then
        kill "$pid" 2>/dev/null
        sleep 2
    fi

    # Starte Chrome mit CDP
    bash "$(dirname "$0")/start_chrome_debug.sh" > /dev/null 2>&1 &

    # Warte bis Chrome gestartet ist
    local attempts=0
    while [ $attempts -lt 10 ]; do
        sleep 2
        if check_cdp; then
            echo -e "${GREEN}✅ Chrome erfolgreich neu gestartet${NC}"
            return 0
        fi
        attempts=$((attempts + 1))
    done

    echo -e "${RED}❌ Chrome konnte nicht neu gestartet werden${NC}"
    return 1
}

# Haupt Health Check
health_check() {
    local retry_count=0

    while [ $retry_count -lt $MAX_RETRIES ]; do
        # Prüfe CDP-Verbindung
        if check_cdp; then
            # Prüfe Speicherverbrauch
            local mem_mb=$(check_chrome_memory)
            if [ -n "$mem_mb" ]; then
                # Warne wenn Speicher > 2GB
                if [ "$mem_mb" -gt 2048 ]; then
                    echo -e "${YELLOW}⚠️  Chrome Speicherverbrauch: ${mem_mb}MB (hoch)${NC}"
                fi
            fi

            echo -e "${GREEN}✅ CDP gesund (Port ${CDP_PORT})${NC}"
            return 0
        fi

        # CDP antwortet nicht
        echo -e "${RED}❌ CDP antwortet nicht (Versuch $((retry_count + 1))/${MAX_RETRIES})${NC}"

        # Versuche Neustart
        if restart_chrome; then
            return 0
        fi

        retry_count=$((retry_count + 1))
        if [ $retry_count -lt $MAX_RETRIES ]; then
            echo -e "${YELLOW}Warte ${RETRY_DELAY}s vor erneutem Versuch...${NC}"
            sleep $RETRY_DELAY
        fi
    done

    echo -e "${RED}❌ CDP Health Check fehlgeschlagen nach ${MAX_RETRIES} Versuchen${NC}"
    echo -e "${YELLOW}💡 Manuelle Schritte:${NC}"
    echo "   1. Prüfe ob Chrome läuft: pgrep -f 'remote-debugging-port'"
    echo "   2. Beende Chrome: pkill -f 'remote-debugging-port'"
    echo "   3. Neustart: bash scripts/start_chrome_debug.sh"
    echo "   4. Verifizierung: curl http://localhost:9222/json/version"

    return 1
}

# Überwachungs-Modus (für lang laufende Prozesse)
monitor() {
    local interval=${1:-300} # Standard: 5 Minuten
    local run_dir=${2:-}

    echo -e "${GREEN}🔍 Starte CDP-Überwachung (Intervall: ${interval}s)${NC}"

    # Sanftes Herunterfahren bei SIGINT/SIGTERM
    trap 'echo -e "\n${YELLOW}Beende Überwachung...${NC}"; exit 0' SIGINT SIGTERM

    if [ -n "$run_dir" ]; then
        echo "   Run-Verzeichnis: $run_dir"
        local log_file="${run_dir}/logs/cdp_health.log"
        mkdir -p "$(dirname "$log_file")"
    fi

    while true; do
        local timestamp=$(date '+%Y-%m-%d %H:%M:%S')

        if check_cdp; then
            local mem_mb=$(check_chrome_memory)
            local status="✅ GESUND (${mem_mb}MB)"

            # Speicher-Warnung
            if [ -n "$mem_mb" ] && [ "$mem_mb" -gt 2048 ]; then
                status="⚠️  HOHER_SPEICHER (${mem_mb}MB)"
                echo -e "${YELLOW}[${timestamp}] ${status}${NC}"
            fi

            # Schreibe ins Log
            if [ -n "$run_dir" ]; then
                echo "[${timestamp}] ${status}" >> "$log_file"
            fi
        else
            local status="❌ AUSGEFALLEN - versuche Wiederherstellung"
            echo -e "${RED}[${timestamp}] ${status}${NC}"

            if [ -n "$run_dir" ]; then
                echo "[${timestamp}] ${status}" >> "$log_file"
            fi

            # Versuche Wiederherstellung
            if restart_chrome; then
                echo -e "${GREEN}[${timestamp}] ✅ WIEDERHERGESTELLT${NC}"
                if [ -n "$run_dir" ]; then
                    echo "[${timestamp}] ✅ WIEDERHERGESTELLT" >> "$log_file"
                fi
            else
                echo -e "${RED}[${timestamp}] ❌ WIEDERHERSTELLUNG FEHLGESCHLAGEN${NC}"
                if [ -n "$run_dir" ]; then
                    echo "[${timestamp}] ❌ WIEDERHERSTELLUNG FEHLGESCHLAGEN" >> "$log_file"
                fi
                exit 1
            fi
        fi

        sleep "$interval"
    done
}

# Verwendungsinformationen
usage() {
    echo "Verwendung: cdp_health_check.sh [BEFEHL] [OPTIONEN]"
    echo ""
    echo "Befehle:"
    echo "  check              Einmalige Health-Prüfung (Standard)"
    echo "  monitor [intervall] Kontinuierliche Überwachung (Intervall in Sekunden, Standard: 300)"
    echo "  restart            Chrome-Neustart erzwingen"
    echo ""
    echo "Optionen:"
    echo "  --run-dir <pfad>   Log ins Run-Verzeichnis (für Monitor-Modus)"
    echo ""
    echo "Beispiele:"
    echo "  cdp_health_check.sh check"
    echo "  cdp_health_check.sh monitor 300 --run-dir runs/2026-02-17_14-30-00"
    echo "  cdp_health_check.sh restart"
}

# Hauptprogramm
case "${1:-check}" in
    check)
        health_check
        exit $?
        ;;
    monitor)
        shift
        monitor "$@"
        ;;
    restart)
        restart_chrome
        exit $?
        ;;
    -h|--help)
        usage
        exit 0
        ;;
    *)
        echo "Unbekannter Befehl: $1"
        usage
        exit 1
        ;;
esac
