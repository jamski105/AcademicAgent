#!/bin/bash

# 🌐 Starte Chrome mit Remote-Debugging (macOS ONLY)
# Claude Code kann dann via CDP (Chrome DevTools Protocol) auf den Browser zugreifen

set -euo pipefail

# macOS-Only Check
if [[ "$OSTYPE" != "darwin"* ]]; then
  echo "❌ Nicht unterstütztes OS: $OSTYPE"
  echo ""
  echo "⚠️  Dieses Script ist ausschließlich für macOS entwickelt."
  echo "    Grund: Hardcoded Pfad /Applications/Google Chrome.app"
  echo ""
  exit 1
fi

echo "🌐 Starte Chrome mit Remote-Debugging..."
echo ""

# Chrome-Pfad
CHROME_PATH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

# Prüfe ob Chrome installiert ist
if [ ! -f "$CHROME_PATH" ]; then
  echo "❌ Google Chrome nicht gefunden unter: $CHROME_PATH"
  echo ""
  echo "Bitte installiere Google Chrome:"
  echo "  https://www.google.com/chrome/"
  exit 1
fi

# User-Data-Verzeichnis (getrennt vom normalen Chrome-Profil)
USER_DATA_DIR="/tmp/chrome-debug-academic-agent"
mkdir -p "$USER_DATA_DIR"

# Remote-Debugging-Port
DEBUG_PORT=9222

echo "Konfiguration:"
echo "  Chrome: $CHROME_PATH"
echo "  Debug Port: $DEBUG_PORT"
echo "  User Data: $USER_DATA_DIR"
echo ""
echo "⚠️  Diese Chrome-Instanz ist GETRENNT von deinem normalen Chrome."
echo "   Du kannst dein normales Chrome parallel nutzen."
echo ""

# Beende existierendes Chrome auf Port 9222
lsof -ti:$DEBUG_PORT | xargs kill -9 2>/dev/null || true

# Starte Chrome im sichtbaren Modus (macOS-native)
# open -a bringt Chrome automatisch in den Vordergrund
open -a "Google Chrome" --new --args \
  --remote-debugging-port=$DEBUG_PORT \
  --user-data-dir="$USER_DATA_DIR" \
  --no-first-run \
  --no-default-browser-check \
  2>&1

# Warte kurz, damit Chrome starten kann
sleep 2

# Ermittle PID des gestarteten Chrome-Prozesses
CHROME_PID=$(lsof -ti:$DEBUG_PORT 2>/dev/null | head -1)

# Prüfe ob Chrome erfolgreich gestartet ist
RETRY_COUNT=0
MAX_RETRIES=5

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
  if lsof -i:$DEBUG_PORT > /dev/null 2>&1; then
    CHROME_PID=$(lsof -ti:$DEBUG_PORT 2>/dev/null | head -1)
    echo "✅ Chrome gestartet und sichtbar (PID: $CHROME_PID)"
    echo "   Chrome-Fenster sollte jetzt auf deinem Desktop erscheinen!"
    break
  fi

  RETRY_COUNT=$((RETRY_COUNT + 1))
  if [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
    echo "⏳ Warte auf Chrome-Start (Versuch $RETRY_COUNT/$MAX_RETRIES)..."
    sleep 2
  else
    echo "❌ Chrome konnte nicht gestartet werden"
    echo "   Prüfe ob Google Chrome installiert ist unter:"
    echo "   $CHROME_PATH"
    exit 1
  fi
done
echo ""
echo "📋 Verwendung:"
echo ""
echo "  1. Claude Code kann jetzt via CDP verbinden:"
echo "     export PLAYWRIGHT_CDP_URL=http://localhost:$DEBUG_PORT"
echo ""
echo "  2. Verbindung testen:"
echo "     curl http://localhost:$DEBUG_PORT/json/version"
echo ""
echo "  3. Chrome stoppen:"
echo "     kill $CHROME_PID"
echo ""
echo "🌐 Chrome läuft auf: http://localhost:$DEBUG_PORT"
echo ""

# Speichere PID für später
echo $CHROME_PID > /tmp/chrome-debug-pid.txt

# Cleanup-Trap für PID-File
trap 'rm -f /tmp/chrome-debug-pid.txt' EXIT

# Halte Script am Laufen (optional)
# wait $CHROME_PID
