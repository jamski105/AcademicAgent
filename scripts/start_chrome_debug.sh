#!/bin/bash

# 🌐 Start Chrome with Remote Debugging
# Claude Code kann dann via CDP (Chrome DevTools Protocol) auf den Browser zugreifen

set -e

echo "🌐 Starting Chrome with Remote Debugging..."
echo ""

# Chrome executable path
CHROME_PATH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

# Check if Chrome is installed
if [ ! -f "$CHROME_PATH" ]; then
  echo "❌ Google Chrome not found at: $CHROME_PATH"
  echo ""
  echo "Alternatives:"
  echo "  - Install Google Chrome"
  echo "  - Or use Chromium: brew install chromium"
  exit 1
fi

# User data directory (separate from normal Chrome profile)
USER_DATA_DIR="/tmp/chrome-debug-academic-agent"
mkdir -p "$USER_DATA_DIR"

# Remote debugging port
DEBUG_PORT=9222

echo "Configuration:"
echo "  Chrome: $CHROME_PATH"
echo "  Debug Port: $DEBUG_PORT"
echo "  User Data: $USER_DATA_DIR"
echo ""
echo "⚠️  This Chrome instance is SEPARATE from your normal Chrome."
echo "   You can still use your normal Chrome in parallel."
echo ""

# Kill existing Chrome on port 9222
lsof -ti:$DEBUG_PORT | xargs kill -9 2>/dev/null || true

# Start Chrome
"$CHROME_PATH" \
  --remote-debugging-port=$DEBUG_PORT \
  --user-data-dir="$USER_DATA_DIR" \
  --no-first-run \
  --no-default-browser-check \
  > /dev/null 2>&1 &

CHROME_PID=$!

# Wait for Chrome to start
sleep 3

# Check if Chrome started
if ! lsof -i:$DEBUG_PORT > /dev/null 2>&1; then
  echo "❌ Chrome failed to start"
  exit 1
fi

echo "✅ Chrome started (PID: $CHROME_PID)"
echo ""
echo "📋 Usage:"
echo ""
echo "  1. Claude Code can now connect via CDP:"
echo "     export PLAYWRIGHT_CDP_URL=http://localhost:$DEBUG_PORT"
echo ""
echo "  2. Test connection:"
echo "     curl http://localhost:$DEBUG_PORT/json/version"
echo ""
echo "  3. Stop Chrome:"
echo "     kill $CHROME_PID"
echo ""
echo "🌐 Chrome is running on: http://localhost:$DEBUG_PORT"
echo ""

# Save PID for later
echo $CHROME_PID > /tmp/chrome-debug-pid.txt

# Keep script running (optional)
# wait $CHROME_PID
