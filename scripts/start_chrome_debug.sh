#!/bin/bash

# 🌐 Starte Chrome mit Remote-Debugging
# Claude Code kann dann via CDP (Chrome DevTools Protocol) auf den Browser zugreifen

set -e

echo "🌐 Starte Chrome mit Remote-Debugging..."
echo ""

# Chrome-Pfad
CHROME_PATH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

# Prüfe ob Chrome installiert ist
if [ ! -f "$CHROME_PATH" ]; then
  echo "❌ Google Chrome nicht gefunden unter: $CHROME_PATH"
  echo ""
  echo "Alternativen:"
  echo "  - Installiere Google Chrome"
  echo "  - Oder nutze Chromium: brew install chromium"
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

# Starte Chrome
"$CHROME_PATH" \
  --remote-debugging-port=$DEBUG_PORT \
  --user-data-dir="$USER_DATA_DIR" \
  --no-first-run \
  --no-default-browser-check \
  > /dev/null 2>&1 &

CHROME_PID=$!

# Warte bis Chrome gestartet ist
sleep 3

# Prüfe ob Chrome gestartet ist
if ! lsof -i:$DEBUG_PORT > /dev/null 2>&1; then
  echo "❌ Chrome konnte nicht gestartet werden"
  exit 1
fi

echo "✅ Chrome gestartet (PID: $CHROME_PID)"
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

# Halte Script am Laufen (optional)
# wait $CHROME_PID
