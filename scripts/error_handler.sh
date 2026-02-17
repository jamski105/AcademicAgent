#!/bin/bash

# 🚨 Error Handler - AcademicAgent
# Zentraler Error Handler für alle Agent-Operationen

set -e

# ============================================
# Color codes
# ============================================
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================
# Error Types
# ============================================

ERROR_TYPE_CDP="CDP_CONNECTION"
ERROR_TYPE_CAPTCHA="CAPTCHA_DETECTED"
ERROR_TYPE_LOGIN="LOGIN_REQUIRED"
ERROR_TYPE_RATE_LIMIT="RATE_LIMIT"
ERROR_TYPE_NETWORK="NETWORK_ERROR"
ERROR_TYPE_FILE="FILE_ERROR"
ERROR_TYPE_UNKNOWN="UNKNOWN"

# ============================================
# Handle CDP Connection Error
# ============================================
handle_cdp_error() {
  local project_dir=$1
  local phase=$2

  echo -e "${RED}❌ CDP Connection Error${NC}"
  echo ""
  echo "Chrome DevTools Protocol (CDP) ist nicht erreichbar."
  echo ""
  echo "Mögliche Ursachen:"
  echo "  1. Chrome ist nicht gestartet"
  echo "  2. Chrome läuft nicht auf Port 9222"
  echo "  3. Chrome wurde geschlossen"
  echo ""
  echo "🔧 Lösungen:"
  echo ""
  echo "  1. Prüfe ob Chrome läuft:"
  echo "     \$ curl http://localhost:9222/json/version"
  echo ""
  echo "  2. Starte Chrome neu:"
  echo "     \$ bash scripts/start_chrome_debug.sh"
  echo ""
  echo "  3. Warte 5 Sekunden und retry"
  echo ""

  # Save error state
  python3 scripts/state_manager.py save "$project_dir" "$phase" "failed" \
    '{"error": "CDP_CONNECTION", "recoverable": true}'

  # Ask user
  echo -e "${YELLOW}Möchtest du Chrome neu starten? (y/n)${NC}"
  read -r response

  if [[ "$response" =~ ^[Yy]$ ]]; then
    echo "Starte Chrome neu..."
    bash scripts/start_chrome_debug.sh &
    sleep 5

    # Test connection
    if curl -s http://localhost:9222/json/version > /dev/null 2>&1; then
      echo -e "${GREEN}✅ Chrome gestartet! Retry...${NC}"
      return 0  # Retry
    else
      echo -e "${RED}❌ Chrome-Start fehlgeschlagen${NC}"
      return 1  # Give up
    fi
  else
    echo "Bitte starte Chrome manuell und drücke ENTER."
    read
    return 0  # Retry
  fi
}

# ============================================
# Handle CAPTCHA
# ============================================
handle_captcha() {
  local project_dir=$1
  local phase=$2
  local screenshot_path=$3

  echo -e "${YELLOW}🚨 CAPTCHA erkannt!${NC}"
  echo ""
  echo "Ein CAPTCHA wurde im Browser-Fenster erkannt."
  echo ""

  # Save state
  python3 scripts/state_manager.py save "$project_dir" "$phase" "paused" \
    '{"error": "CAPTCHA", "screenshot": "'$screenshot_path'"}'

  # Show screenshot path
  if [ -f "$screenshot_path" ]; then
    echo "Screenshot: $screenshot_path"
    echo ""
    # Open screenshot (macOS)
    open "$screenshot_path" 2>/dev/null || true
  fi

  echo "🔧 Lösung:"
  echo "  1. Wechsle zum Chrome-Fenster"
  echo "  2. Löse das CAPTCHA manuell"
  echo "  3. Drücke ENTER zum Fortfahren"
  echo ""

  read

  echo -e "${GREEN}✅ CAPTCHA gelöst! Fortsetzen...${NC}"

  # Resume state
  python3 scripts/state_manager.py save "$project_dir" "$phase" "in_progress" \
    '{"resumed_after": "CAPTCHA"}'

  # Wait before retry
  sleep 5

  return 0  # Retry
}

# ============================================
# Handle Login Required
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

  # Save state
  python3 scripts/state_manager.py save "$project_dir" "$phase" "paused" \
    '{"error": "LOGIN_REQUIRED", "url": "'$url'"}'

  echo "🔧 Lösung:"
  echo "  1. Wechsle zum Chrome-Fenster"
  echo "  2. Logge dich ein (Uni-Account, VPN, etc.)"
  echo "  3. Drücke ENTER zum Fortfahren"
  echo ""

  read

  echo -e "${GREEN}✅ Login abgeschlossen! Fortsetzen...${NC}"

  # Resume state
  python3 scripts/state_manager.py save "$project_dir" "$phase" "in_progress" \
    '{"resumed_after": "LOGIN"}'

  sleep 3

  return 0  # Retry
}

# ============================================
# Handle Rate Limit
# ============================================
handle_rate_limit() {
  local project_dir=$1
  local phase=$2
  local wait_time=${3:-60}

  echo -e "${YELLOW}⏸️  Rate Limit erreicht!${NC}"
  echo ""
  echo "Die Datenbank hat zu viele Anfragen erkannt."
  echo ""

  # Save state
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

  # Resume state
  python3 scripts/state_manager.py save "$project_dir" "$phase" "in_progress" \
    '{"resumed_after": "RATE_LIMIT"}'

  return 0  # Retry
}

# ============================================
# Handle Network Error
# ============================================
handle_network_error() {
  local project_dir=$1
  local phase=$2
  local url=$3

  echo -e "${RED}🌐 Netzwerk-Fehler${NC}"
  echo ""
  echo "Verbindung zu $url fehlgeschlagen."
  echo ""

  # Save state
  python3 scripts/state_manager.py save "$project_dir" "$phase" "paused" \
    '{"error": "NETWORK_ERROR", "url": "'$url'"}'

  echo "Mögliche Ursachen:"
  echo "  - Keine Internetverbindung"
  echo "  - VPN getrennt"
  echo "  - Server nicht erreichbar"
  echo ""
  echo "🔧 Lösung:"
  echo "  1. Prüfe Internetverbindung"
  echo "  2. Prüfe VPN (für Uni-Datenbanken)"
  echo "  3. Drücke ENTER zum Retry"
  echo ""

  read

  echo -e "${BLUE}🔄 Retry...${NC}"

  # Resume state
  python3 scripts/state_manager.py save "$project_dir" "$phase" "in_progress" \
    '{"resumed_after": "NETWORK_ERROR"}'

  sleep 5

  return 0  # Retry
}

# ============================================
# Handle File Error
# ============================================
handle_file_error() {
  local project_dir=$1
  local phase=$2
  local file_path=$3
  local error_type=$4  # missing, corrupt, permission

  echo -e "${RED}📁 File Error${NC}"
  echo ""
  echo "File: $file_path"
  echo "Type: $error_type"
  echo ""

  # Save state
  python3 scripts/state_manager.py save "$project_dir" "$phase" "failed" \
    '{"error": "FILE_ERROR", "file": "'$file_path'", "type": "'$error_type'"}'

  case $error_type in
    missing)
      echo "File fehlt. Wurde eine Phase übersprungen?"
      echo ""
      echo "🔧 Lösung:"
      echo "  - Starte von früherer Phase neu"
      echo "  - Oder erstelle File manuell"
      ;;

    corrupt)
      echo "File ist beschädigt oder leer."
      echo ""
      echo "🔧 Lösung:"
      echo "  - Lösche File und wiederhole Phase"
      echo "  - rm $file_path"
      ;;

    permission)
      echo "Keine Berechtigung für File."
      echo ""
      echo "🔧 Lösung:"
      echo "  - chmod 644 $file_path"
      ;;
  esac

  echo ""
  echo "Drücke ENTER zum Beenden."
  read

  return 1  # Don't retry
}

# ============================================
# Generic Error Handler
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
      echo -e "${RED}❌ Unknown Error: $error_type${NC}"
      python3 scripts/state_manager.py save "$project_dir" "$phase" "failed" \
        '{"error": "UNKNOWN"}'
      return 1
      ;;
  esac
}

# ============================================
# Main (for testing)
# ============================================
if [ "$1" == "test" ]; then
  echo "Testing Error Handler..."
  handle_error "CDP_CONNECTION" "/tmp/test_project" 2
fi
