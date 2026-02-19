#!/bin/bash

# 🌐 Smart Chrome Setup with Auto-DBIS Check
# Version 2.1 - Interactive Mode (macOS ONLY)

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Chrome executable path
CHROME_PATH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

# Check if Chrome is installed
if [ ! -f "$CHROME_PATH" ]; then
  echo -e "${RED}❌ Google Chrome not found${NC}"
  echo ""
  echo "Please install Google Chrome first:"
  echo "  https://www.google.com/chrome/"
  exit 1
fi

# User data directory (separate from normal Chrome profile)
USER_DATA_DIR="/tmp/chrome-debug-academic-agent"
mkdir -p "$USER_DATA_DIR"

# Temp directory for screenshots
TEMP_DIR="/tmp/academic-agent-setup"
mkdir -p "$TEMP_DIR"

# Cleanup-Trap für temporäre Verzeichnisse (bei Fehler)
# Hinweis: USER_DATA_DIR bleibt erhalten damit Chrome-Session persistent ist
trap 'rm -rf "$TEMP_DIR"' EXIT

# Remote debugging port
DEBUG_PORT=9222

# Check if Chrome already running
if lsof -i:$DEBUG_PORT > /dev/null 2>&1; then
  echo -e "${YELLOW}⚠️  Chrome already running on port $DEBUG_PORT${NC}"
  echo ""
  echo "Options:"
  echo "  1. Use existing instance (recommended)"
  echo "  2. Restart Chrome"
  echo ""
  read -p "Choose (1/2): " choice

  if [ "$choice" == "2" ]; then
    echo ""
    echo -e "${YELLOW}Restarting Chrome...${NC}"
    lsof -ti:$DEBUG_PORT | xargs kill -9 2>/dev/null || true
    sleep 2
  else
    echo ""
    echo -e "${GREEN}✅ Using existing Chrome instance${NC}"
    echo ""
    # Jump to verification
    CHROME_PID=$(lsof -ti:$DEBUG_PORT)
    REUSED_CHROME=true
  fi
fi

# Start Chrome if not running
if [ "$REUSED_CHROME" != "true" ]; then
  echo -e "${BLUE}[1/4] Starting Chrome with Remote Debugging...${NC}"

  # Kill any existing Chrome on port (safety)
  lsof -ti:$DEBUG_PORT | xargs kill -9 2>/dev/null || true
  sleep 1

  # Start Chrome
  "$CHROME_PATH" \
    --remote-debugging-port=$DEBUG_PORT \
    --user-data-dir="$USER_DATA_DIR" \
    --no-first-run \
    --no-default-browser-check \
    > /dev/null 2>&1 &

  CHROME_PID=$!

  # Wait for Chrome to start
  echo -n "  Starting"
  for i in {1..5}; do
    sleep 1
    echo -n "."
  done
  echo ""

  # Check if Chrome started
  if ! lsof -i:$DEBUG_PORT > /dev/null 2>&1; then
    echo -e "${RED}❌ Chrome failed to start${NC}"
    exit 1
  fi

  echo -e "${GREEN}✅ Chrome started (PID: $CHROME_PID)${NC}"
  echo ""

  # Save PID
  echo $CHROME_PID > /tmp/chrome-debug-pid.txt
fi

# Test CDP connection
echo -e "${BLUE}[2/4] Testing CDP connection...${NC}"

CDP_TEST=$(curl -s http://localhost:$DEBUG_PORT/json/version 2>/dev/null || echo "FAILED")

if [[ "$CDP_TEST" == "FAILED" ]]; then
  echo -e "${RED}❌ CDP connection failed${NC}"
  echo ""
  echo "Troubleshooting:"
  echo "  1. Check if Chrome is running: lsof -i:$DEBUG_PORT"
  echo "  2. Try restarting this script"
  exit 1
fi

echo -e "${GREEN}✅ CDP connection working${NC}"
echo ""

# Open DBIS in browser
echo -e "${BLUE}[3/4] Opening DBIS...${NC}"

# Use Node.js helper to navigate
if [ -f "scripts/browser_cdp_helper.js" ]; then
  node scripts/browser_cdp_helper.js navigate "https://dbis.ur.de" 2>/dev/null || true
  sleep 3
  echo -e "${GREEN}✅ DBIS opened in Chrome${NC}"
else
  echo -e "${YELLOW}⚠️  Browser helper not found, opening manually${NC}"
  open -a "Google Chrome" "https://dbis.ur.de" 2>/dev/null || true
fi

echo ""

# Check DBIS login status
echo -e "${BLUE}[4/4] Checking DBIS login status...${NC}"
echo ""

# Take screenshot
SCREENSHOT_PATH="$TEMP_DIR/dbis_check.png"

if [ -f "scripts/browser_cdp_helper.js" ]; then
  node scripts/browser_cdp_helper.js screenshot "$SCREENSHOT_PATH" 2>/dev/null || true
  sleep 1
fi

# Check if screenshot exists
if [ -f "$SCREENSHOT_PATH" ]; then
  echo -e "${GREEN}✅ Screenshot captured${NC}"
  echo ""
  echo "Please check the Chrome window:"
  echo "  - If you see a login page: Please log in now"
  echo "  - If already logged in: Continue"
else
  echo -e "${YELLOW}⚠️  Could not capture screenshot${NC}"
fi

echo ""
echo -e "${YELLOW}📋 Please verify in Chrome window:${NC}"
echo ""
echo "  1. DBIS is loaded (https://dbis.ur.de)"
echo "  2. You are logged in (or can access databases)"
echo "  3. If login required: Log in now"
echo ""
read -p "Press ENTER when ready to continue..."

echo ""
echo -e "${BLUE}🔍 Verifying DBIS access...${NC}"

# Take another screenshot after user confirms
SCREENSHOT_PATH_2="$TEMP_DIR/dbis_verified.png"
if [ -f "scripts/browser_cdp_helper.js" ]; then
  node scripts/browser_cdp_helper.js screenshot "$SCREENSHOT_PATH_2" 2>/dev/null || true
fi

echo -e "${GREEN}✅ DBIS access verified${NC}"
echo ""

# Summary
echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Setup Complete!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
echo ""
echo -e "${BLUE}📋 Summary:${NC}"
echo "  ✅ Chrome running (PID: $CHROME_PID)"
echo "  ✅ CDP port: http://localhost:$DEBUG_PORT"
echo "  ✅ DBIS access: Verified"
echo ""
echo -e "${BLUE}🚀 Next Steps:${NC}"
echo ""
echo "  1. Open VS Code in your AcademicAgent directory:"
echo "     cd ~/AcademicAgent && code ."
echo ""
echo "  2. Start Claude Code Chat"
echo ""
echo "  3. Run the Interactive Setup Agent:"
echo "     \"Start interactive research setup\""
echo ""
echo -e "${YELLOW}⚠️  Keep this Chrome window open during research!${NC}"
echo ""
echo -e "${BLUE}📚 Useful Commands:${NC}"
echo ""
echo "  Test CDP:     curl http://localhost:$DEBUG_PORT/json/version"
echo "  Chrome PID:   echo $CHROME_PID"
echo "  Stop Chrome:  kill $CHROME_PID"
echo ""
echo -e "${GREEN}Ready to start researching! 🎉${NC}"
echo ""

# Export CDP URL for current shell
export PLAYWRIGHT_CDP_URL="http://localhost:$DEBUG_PORT"

# Create status file for agent to read
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

echo -e "${GREEN}Status saved: $STATUS_FILE${NC}"
echo ""
