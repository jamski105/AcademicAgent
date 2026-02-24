#!/bin/bash

# 🚨 Error Handler - AcademicAgent
# Zentraler Error Handler für alle Agent-Operationen

set -euo pipefail

# ============================================
# Farbcodes
# ============================================
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # Keine Farbe

# ============================================
# Fehlertypen
# ============================================

ERROR_TYPE_CDP="CDP_CONNECTION"
ERROR_TYPE_CAPTCHA="CAPTCHA_DETECTED"
ERROR_TYPE_LOGIN="LOGIN_REQUIRED"
ERROR_TYPE_RATE_LIMIT="RATE_LIMIT"
ERROR_TYPE_NETWORK="NETWORK_ERROR"
ERROR_TYPE_FILE="FILE_ERROR"
ERROR_TYPE_UNKNOWN="UNKNOWN"

# ============================================
# CDP-Diagnose (detailliert)
# ============================================
diagnose_cdp() {
  echo -e "${BLUE}🔍 Führe CDP-Diagnose durch...${NC}"
  echo ""

  # 1. Prüfe ob Chrome-Prozess läuft
  local chrome_pid=$(pgrep -f "remote-debugging-port=9222" 2>/dev/null | head -1)
  if [ -n "$chrome_pid" ]; then
    echo -e "${GREEN}✅ Chrome-Prozess gefunden (PID: $chrome_pid)${NC}"

    # Prüfe Speicher
    local mem_mb=$(ps -o rss= -p "$chrome_pid" 2>/dev/null | awk '{print int($1/1024)}')
    if [ -n "$mem_mb" ]; then
      if [ "$mem_mb" -gt 2048 ]; then
        echo -e "${YELLOW}⚠️  Hoher Speicherverbrauch: ${mem_mb}MB (möglicherweise Neustart nötig)${NC}"
      else
        echo "   Speicher: ${mem_mb}MB"
      fi
    fi
  else
    echo -e "${RED}❌ Chrome-Prozess läuft NICHT${NC}"
  fi

  # 2. Prüfe Port-Verfügbarkeit
  if lsof -i :9222 > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Port 9222 ist in Verwendung${NC}"
  else
    echo -e "${RED}❌ Port 9222 ist NICHT in Verwendung (Chrome hört nicht zu)${NC}"
  fi

  # 3. Teste CDP-Endpunkt
  if curl -s --connect-timeout 2 http://localhost:9222/json/version > /dev/null 2>&1; then
    echo -e "${GREEN}✅ CDP-Endpunkt antwortet${NC}"
    local version=$(curl -s http://localhost:9222/json/version | jq -r '.Browser' 2>/dev/null)
    if [ -n "$version" ]; then
      echo "   Version: $version"
    fi
  else
    echo -e "${RED}❌ CDP-Endpunkt antwortet NICHT${NC}"
  fi

  echo ""
}

# ============================================
# Behandle CDP-Verbindungsfehler (erweitert)
# ============================================
handle_cdp_error() {
  local project_dir=$1
  local phase=$2

  echo -e "${RED}❌ CDP-Verbindungsfehler${NC}"
  echo ""
  echo "Chrome DevTools Protocol (CDP) ist nicht erreichbar."
  echo ""

  # Führe Diagnose durch
  diagnose_cdp

  echo -e "${YELLOW}🔧 Empfohlene Lösungen (in dieser Reihenfolge):${NC}"
  echo ""
  echo "1️⃣  Auto-Restart via Health Check:"
  echo "   \$ bash scripts/cdp_health_check.sh restart"
  echo ""
  echo "2️⃣  Manueller Chrome-Neustart:"
  echo "   \$ bash scripts/start_chrome_debug.sh"
  echo ""
  echo "3️⃣  Port-Konflikt prüfen (wenn Port belegt):"
  echo "   \$ lsof -i :9222"
  echo "   \$ kill <PID>  # Falls anderer Prozess Port nutzt"
  echo ""
  echo "4️⃣  Chrome komplett beenden und neu starten:"
  echo "   \$ pkill -f 'remote-debugging-port'"
  echo "   \$ bash scripts/start_chrome_debug.sh"
  echo ""

  # Speichere Fehlerstatus
  python3 scripts/state_manager.py save "$project_dir" "$phase" "failed" \
    '{"error": "CDP_CONNECTION", "recoverable": true}'

  # Automatischer Wiederherstellungsversuch
  echo -e "${YELLOW}Möchtest du Auto-Recovery versuchen? (y/n)${NC}"

  # TTY-Check für non-interactive Umgebungen
  if [ -t 0 ]; then
    read -t 60 -r response || response="n"
  else
    echo "Non-interactive Modus - Auto-Recovery wird nicht versucht"
    response="n"
  fi

  if [[ "$response" =~ ^[Yy]$ ]]; then
    echo "Versuche automatische Wiederherstellung..."

    if bash scripts/cdp_health_check.sh restart; then
      echo -e "${GREEN}✅ Chrome erfolgreich neu gestartet!${NC}"
      sleep 3
      return 0  # Retry
    else
      echo -e "${RED}❌ Auto-Recovery fehlgeschlagen${NC}"
      echo ""
      echo "Bitte führe manuellen Neustart durch und drücke ENTER."
      read
      return 0  # Retry
    fi
  else
    echo "Bitte starte Chrome manuell und drücke ENTER."
    read
    return 0  # Retry
  fi
}

# ============================================
# Behandle CAPTCHA
# ============================================
handle_captcha() {
  local project_dir=$1
  local phase=$2
  local screenshot_path=$3

  echo -e "${YELLOW}🚨 CAPTCHA erkannt!${NC}"
  echo ""
  echo "Ein CAPTCHA wurde im Browser-Fenster erkannt."
  echo ""

  # Speichere Status
  python3 scripts/state_manager.py save "$project_dir" "$phase" "paused" \
    '{"error": "CAPTCHA", "screenshot": "'$screenshot_path'"}'

  # Zeige Screenshot-Pfad
  if [ -f "$screenshot_path" ]; then
    echo "Screenshot: $screenshot_path"
    echo ""
    # Öffne Screenshot (macOS)
    open "$screenshot_path" 2>/dev/null || true
  fi

  echo "🔧 Lösung:"
  echo "  1. Wechsle zum Chrome-Fenster"
  echo "  2. Löse das CAPTCHA manuell"
  echo "  3. Drücke ENTER zum Fortfahren"
  echo ""

  # TTY-Check für non-interactive Umgebungen
  if [ -t 0 ]; then
    read -t 300 -r || echo "Timeout nach 5 Minuten"
  else
    echo "Non-interactive Modus - Warte 60 Sekunden..."
    sleep 60
  fi

  echo -e "${GREEN}✅ CAPTCHA gelöst! Fortsetzen...${NC}"

  # Setze Status fort
  python3 scripts/state_manager.py save "$project_dir" "$phase" "in_progress" \
    '{"resumed_after": "CAPTCHA"}'

  # Warte vor erneutem Versuch
  sleep 5

  return 0  # Retry
}

# ============================================
# Behandle Login erforderlich
# ============================================
handle_login() {
  local project_dir=$1
  local phase=$2
  local url=$3

  echo -e "${YELLOW}🔐 Login erforderlich!${NC}"
  echo ""
  echo "Die Datenbank erfordert einen Login."
  echo "URL: $url"
  echo ""

  # Speichere Status
  python3 scripts/state_manager.py save "$project_dir" "$phase" "paused" \
    '{"error": "LOGIN_REQUIRED", "url": "'$url'"}'

  echo "🔧 Lösung:"
  echo "  1. Wechsle zum Chrome-Fenster"
  echo "  2. Logge dich ein (Uni-Account, VPN, etc.)"
  echo "  3. Drücke ENTER zum Fortfahren"
  echo ""

  # TTY-Check für non-interactive Umgebungen
  if [ -t 0 ]; then
    read -t 600 -r || echo "Timeout nach 10 Minuten"
  else
    echo "Non-interactive Modus - Warte 120 Sekunden..."
    sleep 120
  fi

  echo -e "${GREEN}✅ Login abgeschlossen! Fortsetzen...${NC}"

  # Setze Status fort
  python3 scripts/state_manager.py save "$project_dir" "$phase" "in_progress" \
    '{"resumed_after": "LOGIN"}'

  sleep 3

  return 0  # Retry
}

# ============================================
# Behandle Rate Limit
# ============================================
handle_rate_limit() {
  local project_dir=$1
  local phase=$2
  local wait_time=${3:-60}

  echo -e "${YELLOW}⏸️  Rate Limit erreicht!${NC}"
  echo ""
  echo "Die Datenbank hat zu viele Anfragen erkannt."
  echo ""

  # Speichere Status
  python3 scripts/state_manager.py save "$project_dir" "$phase" "paused" \
    '{"error": "RATE_LIMIT", "wait_time": '$wait_time'}'

  echo "🔧 Automatische Wartezeit: ${wait_time} Sekunden"
  echo ""

  for ((i=wait_time; i>0; i--)); do
    echo -ne "\rWarten: ${i}s...   "
    sleep 1
  done

  echo ""
  echo -e "${GREEN}✅ Wartezeit vorbei! Fortsetzen...${NC}"

  # Setze Status fort
  python3 scripts/state_manager.py save "$project_dir" "$phase" "in_progress" \
    '{"resumed_after": "RATE_LIMIT"}'

  return 0  # Retry
}

# ============================================
# Behandle Netzwerk-Fehler (erweitert)
# ============================================
handle_network_error() {
  local project_dir=$1
  local phase=$2
  local url=$3

  echo -e "${RED}🌐 Netzwerk-Fehler${NC}"
  echo ""
  echo "Verbindung zu $url fehlgeschlagen."
  echo ""

  # Diagnose
  echo -e "${BLUE}🔍 Netzwerk-Diagnose:${NC}"

  # 1. Teste Internet-Verbindung
  if ping -c 1 -W 2 8.8.8.8 > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Internet-Verbindung OK${NC}"
  else
    echo -e "${RED}❌ Keine Internet-Verbindung${NC}"
  fi

  # 2. Teste DNS
  if nslookup google.com > /dev/null 2>&1; then
    echo -e "${GREEN}✅ DNS-Auflösung OK${NC}"
  else
    echo -e "${RED}❌ DNS-Auflösung fehlgeschlagen${NC}"
  fi

  # 3. Extrahiere Domain aus URL und teste
  local domain=$(echo "$url" | sed -E 's|https?://([^/]+).*|\1|')
  if [ -n "$domain" ]; then
    if curl -s --connect-timeout 5 --head "$url" > /dev/null 2>&1; then
      echo -e "${GREEN}✅ Zielserver erreichbar${NC}"
    else
      echo -e "${RED}❌ Kann $domain nicht erreichen${NC}"

      # Prüfe ob es eine Uni-Domain ist (möglicherweise VPN nötig)
      if [[ "$domain" =~ \.(edu|ac\.|uni-) ]]; then
        echo -e "${YELLOW}⚠️  Uni-Domain erkannt - VPN wahrscheinlich erforderlich!${NC}"
      fi
    fi
  fi

  echo ""

  # Speichere Status
  python3 scripts/state_manager.py save "$project_dir" "$phase" "paused" \
    '{"error": "NETWORK_ERROR", "url": "'$url'"}'

  echo -e "${YELLOW}🔧 Lösungsschritte:${NC}"
  echo ""
  echo "1️⃣  Für Uni-Datenbanken:"
  echo "   - Verbinde mit Uni-VPN"
  echo "   - Prüfe VPN-Verbindung: https://vpn.uni-xyz.de"
  echo ""
  echo "2️⃣  Allgemeine Netzwerk-Probleme:"
  echo "   - Prüfe WLAN/Ethernet-Verbindung"
  echo "   - Deaktiviere temporär Firewall/Proxy"
  echo "   - Teste: curl -I $url"
  echo ""
  echo "3️⃣  Server-seitige Probleme:"
  echo "   - Server könnte ausgefallen sein"
  echo "   - Warte 1-2 Minuten und versuche erneut"
  echo ""
  echo "Drücke ENTER wenn Netzwerk-Problem behoben ist..."

  # TTY-Check für non-interactive Umgebungen
  if [ -t 0 ]; then
    read -t 300 -r || echo "Timeout nach 5 Minuten"
  else
    echo "Non-interactive Modus - Warte 60 Sekunden..."
    sleep 60
  fi

  echo -e "${BLUE}🔄 Erneuter Versuch...${NC}"

  # Setze Status fort
  python3 scripts/state_manager.py save "$project_dir" "$phase" "in_progress" \
    '{"resumed_after": "NETWORK_ERROR"}'

  sleep 5

  return 0  # Retry
}

# ============================================
# Behandle Datei-Fehler
# ============================================
handle_file_error() {
  local project_dir=$1
  local phase=$2
  local file_path=$3
  local error_type=$4  # missing, corrupt, permission

  echo -e "${RED}📁 Datei-Fehler${NC}"
  echo ""
  echo "Datei: $file_path"
  echo "Typ: $error_type"
  echo ""

  # Speichere Status
  python3 scripts/state_manager.py save "$project_dir" "$phase" "failed" \
    '{"error": "FILE_ERROR", "file": "'$file_path'", "type": "'$error_type'"}'

  case $error_type in
    missing)
      echo "Datei fehlt. Wurde eine Phase übersprungen?"
      echo ""
      echo "🔧 Lösung:"
      echo "  - Starte von früherer Phase neu"
      echo "  - Oder erstelle Datei manuell"
      ;;

    corrupt)
      echo "Datei ist beschädigt oder leer."
      echo ""
      echo "🔧 Lösung:"
      echo "  - Lösche Datei und wiederhole Phase"
      echo "  - rm $file_path"
      ;;

    permission)
      echo "Keine Berechtigung für Datei."
      echo ""
      echo "🔧 Lösung:"
      echo "  - chmod 644 $file_path"
      ;;
  esac

  echo ""

  # TTY-Check für non-interactive Umgebungen
  if [ -t 0 ]; then
    echo "Drücke ENTER zum Beenden."
    read -t 30 -r || true
  else
    echo "Beende in 5 Sekunden..."
    sleep 5
  fi

  return 1  # Don't retry
}

# ============================================
# Generischer Fehler-Handler
# ============================================
handle_error() {
  local error_type=$1
  local project_dir=$2
  local phase=$3
  shift 3
  local args=("$@")

  case $error_type in
    $ERROR_TYPE_CDP)
      handle_cdp_error "$project_dir" "$phase"
      return $?
      ;;

    $ERROR_TYPE_CAPTCHA)
      handle_captcha "$project_dir" "$phase" "${args[0]}"
      return $?
      ;;

    $ERROR_TYPE_LOGIN)
      handle_login "$project_dir" "$phase" "${args[0]}"
      return $?
      ;;

    $ERROR_TYPE_RATE_LIMIT)
      handle_rate_limit "$project_dir" "$phase" "${args[0]:-60}"
      return $?
      ;;

    $ERROR_TYPE_NETWORK)
      handle_network_error "$project_dir" "$phase" "${args[0]}"
      return $?
      ;;

    $ERROR_TYPE_FILE)
      handle_file_error "$project_dir" "$phase" "${args[0]}" "${args[1]}"
      return $?
      ;;

    *)
      echo -e "${RED}❌ Unbekannter Fehler: $error_type${NC}"
      python3 scripts/state_manager.py save "$project_dir" "$phase" "failed" \
        '{"error": "UNKNOWN"}'
      return 1
      ;;
  esac
}

# ============================================
# Hauptprogramm (für Tests)
# ============================================
if [ "$1" == "test" ]; then
  echo "Teste Error Handler..."
  handle_error "CDP_CONNECTION" "/tmp/test_project" 2
fi
