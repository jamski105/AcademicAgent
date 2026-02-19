#!/bin/bash

# 🔄 Resume Research - AcademicAgent
# Setzt unterbrochene Recherche fort

set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# ============================================
# Usage
# ============================================
if [ $# -lt 1 ]; then
  echo "Usage: bash scripts/resume_research.sh <project_name>"
  echo ""
  echo "Example:"
  echo "  bash scripts/resume_research.sh DevOps"
  echo ""
  exit 1
fi

PROJECT_NAME=$1

# Nutze relative Pfade statt hardcoded $HOME/AcademicAgent
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PROJECT_DIR="$ROOT_DIR/projects/$PROJECT_NAME"

# ============================================
# Check if project exists
# ============================================
if [ ! -d "$PROJECT_DIR" ]; then
  echo "❌ Project not found: $PROJECT_DIR"
  echo ""
  echo "Available projects:"
  ls -1 "$ROOT_DIR/projects/" 2>/dev/null || echo "  (none)"
  exit 1
fi

echo "🔍 Checking research state for: $PROJECT_NAME"
echo ""

# ============================================
# Get resume point
# ============================================
RESUME_INFO=$(python3 scripts/state_manager.py resume "$PROJECT_DIR")

if [ $? -ne 0 ]; then
  echo "❌ Error reading state"
  exit 1
fi

SHOULD_RESUME=$(echo "$RESUME_INFO" | jq -r '.should_resume')
MESSAGE=$(echo "$RESUME_INFO" | jq -r '.message')
RESUME_PHASE=$(echo "$RESUME_INFO" | jq -r '.resume_phase // empty')

echo -e "${BLUE}$MESSAGE${NC}"
echo ""

if [ "$SHOULD_RESUME" == "false" ]; then
  if [[ "$MESSAGE" == *"finished"* ]]; then
    echo -e "${GREEN}✅ Research is complete!${NC}"
    echo ""
    echo "Outputs:"
    ls -lh "$PROJECT_DIR/outputs/" 2>/dev/null || echo "  No outputs found"
  else
    echo "Use orchestrator.md to start a new research."
  fi
  exit 0
fi

# ============================================
# Show state summary
# ============================================
echo "📊 State Summary:"
echo ""

STATE=$(python3 scripts/state_manager.py load "$PROJECT_DIR")

echo "$STATE" | jq -r '.phases | to_entries[] |
  "  Phase \(.key | split("_")[1]): \(.value.status) (updated: \(.value.updated_at))"'

echo ""

# ============================================
# Check dependencies
# ============================================
echo "🔍 Checking dependencies..."
echo ""

# Check Chrome CDP
if ! curl -s http://localhost:9222/json/version > /dev/null 2>&1; then
  echo -e "${YELLOW}⚠️  Chrome CDP not running${NC}"
  echo ""
  echo "Starting Chrome..."
  bash scripts/start_chrome_debug.sh &
  sleep 5

  if curl -s http://localhost:9222/json/version > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Chrome started${NC}"
  else
    echo -e "${RED}❌ Failed to start Chrome${NC}"
    echo "Please run: bash scripts/start_chrome_debug.sh"
    exit 1
  fi
else
  echo -e "${GREEN}✅ Chrome CDP running${NC}"
fi

echo ""

# ============================================
# Generate resume instructions
# ============================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}Ready to resume!${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 Next steps:"
echo ""
echo "  1. Open VS Code:"
echo "     cd $ROOT_DIR"
echo "     code ."
echo ""
echo "  2. Start Claude Code Chat:"
echo "     Cmd+Shift+P → 'Claude Code: Start Chat'"
echo ""
echo "  3. Resume with:"
echo "     Lies agents/orchestrator.md und setze die Recherche fort"
echo "     für $PROJECT_DIR/config/Config_${PROJECT_NAME}.md"
echo ""
echo "     WICHTIG: Starte bei Phase $RESUME_PHASE"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ============================================
# Optional: Auto-open VS Code
# ============================================
echo "Soll VS Code automatisch geöffnet werden? (y/n)"
read -r response

if [[ "$response" =~ ^[Yy]$ ]]; then
  code .
  echo ""
  echo "✅ VS Code geöffnet"
  echo ""
  echo "Starte Claude Code Chat mit: Cmd+Shift+P → 'Claude Code: Start Chat'"
fi
