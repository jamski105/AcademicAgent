#!/bin/bash

# 🔄 Resume Research - AcademicAgent
# Setzt unterbrochene Recherche fort

set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# ============================================
# Verwendung
# ============================================
if [ $# -lt 1 ]; then
  echo "Verwendung: bash scripts/resume_research.sh <projekt_name>"
  echo ""
  echo "Beispiel:"
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
# Prüfe ob Projekt existiert
# ============================================
if [ ! -d "$PROJECT_DIR" ]; then
  echo "❌ Projekt nicht gefunden: $PROJECT_DIR"
  echo ""
  echo "Verfügbare Projekte:"
  ls -1 "$ROOT_DIR/projects/" 2>/dev/null || echo "  (keine)"
  exit 1
fi

echo "🔍 Prüfe Recherche-Status für: $PROJECT_NAME"
echo ""

# ============================================
# Hole Fortsetzungspunkt
# ============================================
RESUME_INFO=$(python3 scripts/state_manager.py resume "$PROJECT_DIR")

if [ $? -ne 0 ]; then
  echo "❌ Fehler beim Lesen des Status"
  exit 1
fi

SHOULD_RESUME=$(echo "$RESUME_INFO" | jq -r '.should_resume')
MESSAGE=$(echo "$RESUME_INFO" | jq -r '.message')
RESUME_PHASE=$(echo "$RESUME_INFO" | jq -r '.resume_phase // empty')

echo -e "${BLUE}$MESSAGE${NC}"
echo ""

if [ "$SHOULD_RESUME" == "false" ]; then
  if [[ "$MESSAGE" == *"finished"* ]]; then
    echo -e "${GREEN}✅ Recherche ist abgeschlossen!${NC}"
    echo ""
    echo "Ausgaben:"
    ls -lh "$PROJECT_DIR/outputs/" 2>/dev/null || echo "  Keine Ausgaben gefunden"
  else
    echo "Nutze orchestrator.md um eine neue Recherche zu starten."
  fi
  exit 0
fi

# ============================================
# Zeige Status-Zusammenfassung
# ============================================
echo "📊 Status-Zusammenfassung:"
echo ""

STATE=$(python3 scripts/state_manager.py load "$PROJECT_DIR")

echo "$STATE" | jq -r '.phases | to_entries[] |
  "  Phase \(.key | split("_")[1]): \(.value.status) (aktualisiert: \(.value.updated_at))"'

echo ""

# ============================================
# Prüfe Abhängigkeiten
# ============================================
echo "🔍 Prüfe Abhängigkeiten..."
echo ""

# Prüfe Chrome CDP
if ! curl -s http://localhost:9222/json/version > /dev/null 2>&1; then
  echo -e "${YELLOW}⚠️  Chrome CDP läuft nicht${NC}"
  echo ""
  echo "Starte Chrome..."
  bash scripts/start_chrome_debug.sh &
  sleep 5

  if curl -s http://localhost:9222/json/version > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Chrome gestartet${NC}"
  else
    echo -e "${RED}❌ Chrome konnte nicht gestartet werden${NC}"
    echo "Bitte führe aus: bash scripts/start_chrome_debug.sh"
    exit 1
  fi
else
  echo -e "${GREEN}✅ Chrome CDP läuft${NC}"
fi

echo ""

# ============================================
# Generiere Fortsetzungs-Anweisungen
# ============================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}Bereit zum Fortsetzen!${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 Nächste Schritte:"
echo ""
echo "  1. Öffne VS Code:"
echo "     cd $ROOT_DIR"
echo "     code ."
echo ""
echo "  2. Starte Claude Code Chat:"
echo "     Cmd+Shift+P → 'Claude Code: Start Chat'"
echo ""
echo "  3. Setze fort mit:"
echo "     Lies agents/orchestrator.md und setze die Recherche fort"
echo "     für $PROJECT_DIR/config/Config_${PROJECT_NAME}.md"
echo ""
echo "     WICHTIG: Starte bei Phase $RESUME_PHASE"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ============================================
# Optional: VS Code automatisch öffnen
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
