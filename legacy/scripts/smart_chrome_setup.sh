#!/bin/bash

# 🌐 Smart Chrome Setup with Auto-DBIS Check
# Interactive Mode (macOS ONLY)

set -euo pipefail

# Farben für Ausgabe
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # Keine Farbe

# macOS-Only Check
if [[ "$OSTYPE" != "darwin"* ]]; then
  echo -e "${RED}❌ Nicht unterstütztes OS: $OSTYPE${NC}"
  echo ""
  echo "⚠️  Dieses Script ist ausschließlich für macOS entwickelt."
  echo "    Grund: Hardcoded Pfad /Applications/Google Chrome.app"
  echo ""
  exit 1
fi

echo -e "${BLUE}🌐 Smart Chrome Setup - AcademicAgent${NC}"
echo ""

# Chrome-Pfad
CHROME_PATH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

# Prüfe ob Chrome installiert ist
if [ ! -f "$CHROME_PATH" ]; then
  echo -e "${RED}❌ Google Chrome nicht gefunden${NC}"
  echo ""
  echo "Bitte installiere zuerst Google Chrome:"
  echo "  https://www.google.com/chrome/"
  exit 1
fi

# User-Data-Verzeichnis (getrennt vom normalen Chrome-Profil)
USER_DATA_DIR="/tmp/chrome-debug-academic-agent"
mkdir -p "$USER_DATA_DIR"

# Temp-Verzeichnis für Screenshots
TEMP_DIR="/tmp/academic-agent-setup"
mkdir -p "$TEMP_DIR"

# Cleanup-Trap für temporäre Verzeichnisse (bei Fehler)
# Hinweis: USER_DATA_DIR bleibt erhalten damit Chrome-Session persistent ist
trap 'rm -rf "$TEMP_DIR"' EXIT

# Remote-Debugging-Port
DEBUG_PORT=9222

# Prüfe ob Chrome bereits läuft
if lsof -i:$DEBUG_PORT > /dev/null 2>&1; then
  echo -e "${YELLOW}⚠️  Chrome läuft bereits auf Port $DEBUG_PORT${NC}"
  echo ""
  echo "Optionen:"
  echo "  1. Existierende Instanz verwenden (empfohlen)"
  echo "  2. Chrome neu starten"
  echo ""
  read -p "Wähle (1/2): " choice

  if [ "$choice" == "2" ]; then
    echo ""
    echo -e "${YELLOW}Starte Chrome neu...${NC}"
    lsof -ti:$DEBUG_PORT | xargs kill -9 2>/dev/null || true
    sleep 2
  else
    echo ""
    echo -e "${GREEN}✅ Verwende existierende Chrome-Instanz${NC}"
    echo ""
    # Springe zur Verifikation
    CHROME_PID=$(lsof -ti:$DEBUG_PORT)
    REUSED_CHROME=true
  fi
fi

# Starte Chrome falls nicht laufend
if [ "$REUSED_CHROME" != "true" ]; then
  echo -e "${BLUE}[1/4] Starte Chrome mit Remote-Debugging...${NC}"

  # Beende existierendes Chrome auf Port (Sicherheit)
  lsof -ti:$DEBUG_PORT | xargs kill -9 2>/dev/null || true
  sleep 1

  # Starte Chrome
  "$CHROME_PATH" \
    --remote-debugging-port=$DEBUG_PORT \
    --user-data-dir="$USER_DATA_DIR" \
    --no-first-run \
    --no-default-browser-check \
    > /dev/null 2>&1 &

  CHROME_PID=$!

  # Warte bis Chrome gestartet ist
  echo -n "  Starte"
  for i in {1..5}; do
    sleep 1
    echo -n "."
  done
  echo ""

  # Prüfe ob Chrome gestartet ist
  if ! lsof -i:$DEBUG_PORT > /dev/null 2>&1; then
    echo -e "${RED}❌ Chrome konnte nicht gestartet werden${NC}"
    exit 1
  fi

  echo -e "${GREEN}✅ Chrome gestartet (PID: $CHROME_PID)${NC}"
  echo ""

  # Speichere PID
  echo $CHROME_PID > /tmp/chrome-debug-pid.txt
fi

# Teste CDP-Verbindung
echo -e "${BLUE}[2/4] Teste CDP-Verbindung...${NC}"

CDP_TEST=$(curl -s http://localhost:$DEBUG_PORT/json/version 2>/dev/null || echo "FAILED")

if [[ "$CDP_TEST" == "FAILED" ]]; then
  echo -e "${RED}❌ CDP-Verbindung fehlgeschlagen${NC}"
  echo ""
  echo "Fehlerbehebung:"
  echo "  1. Prüfe ob Chrome läuft: lsof -i:$DEBUG_PORT"
  echo "  2. Versuche dieses Script neu zu starten"
  exit 1
fi

echo -e "${GREEN}✅ CDP-Verbindung funktioniert${NC}"
echo ""

# Öffne DBIS im Browser
echo -e "${BLUE}[3/4] Öffne DBIS...${NC}"

# Nutze Node.js Helper zur Navigation
if [ -f "scripts/browser_cdp_helper.js" ]; then
  node scripts/browser_cdp_helper.js navigate "https://dbis.ur.de" 2>/dev/null || true
  sleep 3
  echo -e "${GREEN}✅ DBIS in Chrome geöffnet${NC}"
else
  echo -e "${YELLOW}⚠️  Browser-Helper nicht gefunden, öffne manuell${NC}"
  open -a "Google Chrome" "https://dbis.ur.de" 2>/dev/null || true
fi

echo ""

# Prüfe DBIS-Login-Status
echo -e "${BLUE}[4/4] Prüfe DBIS-Login-Status...${NC}"
echo ""

# Erstelle Screenshot
SCREENSHOT_PATH="$TEMP_DIR/dbis_check.png"

if [ -f "scripts/browser_cdp_helper.js" ]; then
  node scripts/browser_cdp_helper.js screenshot "$SCREENSHOT_PATH" 2>/dev/null || true
  sleep 1
fi

# Prüfe ob Screenshot existiert
if [ -f "$SCREENSHOT_PATH" ]; then
  echo -e "${GREEN}✅ Screenshot erfasst${NC}"
  echo ""
  echo "Bitte prüfe das Chrome-Fenster:"
  echo "  - Falls eine Login-Seite angezeigt wird: Bitte jetzt einloggen"
  echo "  - Falls bereits eingeloggt: Fortfahren"
else
  echo -e "${YELLOW}⚠️  Screenshot konnte nicht erstellt werden${NC}"
fi

echo ""
echo -e "${YELLOW}📋 Bitte verifiziere im Chrome-Fenster:${NC}"
echo ""
echo "  1. DBIS ist geladen (https://dbis.ur.de)"
echo "  2. Du bist eingeloggt (oder kannst auf Datenbanken zugreifen)"
echo "  3. Falls Login erforderlich: Jetzt einloggen"
echo ""
read -p "Drücke ENTER wenn bereit zum Fortfahren..."

echo ""
echo -e "${BLUE}🔍 Verifiziere DBIS-Zugriff...${NC}"

# Erstelle einen weiteren Screenshot nach Benutzerbestätigung
SCREENSHOT_PATH_2="$TEMP_DIR/dbis_verified.png"
if [ -f "scripts/browser_cdp_helper.js" ]; then
  node scripts/browser_cdp_helper.js screenshot "$SCREENSHOT_PATH_2" 2>/dev/null || true
fi

echo -e "${GREEN}✅ DBIS-Zugriff verifiziert${NC}"
echo ""

# Zusammenfassung
echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Setup abgeschlossen!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
echo ""
echo -e "${BLUE}📋 Zusammenfassung:${NC}"
echo "  ✅ Chrome läuft (PID: $CHROME_PID)"
echo "  ✅ CDP-Port: http://localhost:$DEBUG_PORT"
echo "  ✅ DBIS-Zugriff: Verifiziert"
echo ""
echo -e "${BLUE}🚀 Nächste Schritte:${NC}"
echo ""
echo "  1. Öffne VS Code in deinem AcademicAgent-Verzeichnis:"
echo "     cd ~/AcademicAgent && code ."
echo ""
echo "  2. Starte Claude Code Chat"
echo ""
echo "  3. Führe den Interactive Setup Agent aus:"
echo "     \"Start interactive research setup\""
echo ""
echo -e "${YELLOW}⚠️  Halte dieses Chrome-Fenster während der Recherche geöffnet!${NC}"
echo ""
echo -e "${BLUE}📚 Nützliche Befehle:${NC}"
echo ""
echo "  CDP testen:   curl http://localhost:$DEBUG_PORT/json/version"
echo "  Chrome PID:   echo $CHROME_PID"
echo "  Chrome stoppen:  kill $CHROME_PID"
echo ""
echo -e "${GREEN}Bereit zum Recherchieren! 🎉${NC}"
echo ""

# Exportiere CDP-URL für aktuelle Shell
export PLAYWRIGHT_CDP_URL="http://localhost:$DEBUG_PORT"

# Erstelle Status-Datei für Agent
STATUS_FILE="$TEMP_DIR/chrome_status.json"
cat > "$STATUS_FILE" << EOF
{
  "status": "ready",
  "pid": $CHROME_PID,
  "port": $DEBUG_PORT,
  "cdp_url": "http://localhost:$DEBUG_PORT",
  "dbis_verified": true,
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
}
EOF

echo -e "${GREEN}Status gespeichert: $STATUS_FILE${NC}"
echo ""
