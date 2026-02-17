#!/bin/bash

# 🛠️ AcademicAgent - Setup Script
# Installiert alle Dependencies und erstellt Ordnerstruktur

set -e  # Exit bei Fehler

echo "🚀 AcademicAgent Setup gestartet..."
echo ""

# Farben für Output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# ============================================
# 1. Check OS
# ============================================
if [[ "$OSTYPE" != "darwin"* ]]; then
  echo -e "${RED}❌ Fehler: Dieses Script ist nur für macOS!${NC}"
  exit 1
fi

echo -e "${GREEN}✅ macOS erkannt${NC}"
echo ""

# ============================================
# 2. Check Homebrew
# ============================================
echo "📦 Prüfe Homebrew..."
if ! command -v brew &> /dev/null; then
  echo -e "${YELLOW}⚠️  Homebrew nicht gefunden. Installiere Homebrew...${NC}"
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
else
  echo -e "${GREEN}✅ Homebrew installiert${NC}"
fi
echo ""

# ============================================
# 3. Dependencies installieren
# ============================================
echo "📦 Installiere Dependencies..."

# poppler (für pdftotext)
if ! command -v pdftotext &> /dev/null; then
  echo "  Installing poppler (pdftotext)..."
  brew install poppler
else
  echo -e "${GREEN}  ✅ poppler bereits installiert${NC}"
fi

# wget (für Downloads)
if ! command -v wget &> /dev/null; then
  echo "  Installing wget..."
  brew install wget
else
  echo -e "${GREEN}  ✅ wget bereits installiert${NC}"
fi

# Node.js (für Playwright)
if ! command -v node &> /dev/null; then
  echo "  Installing Node.js..."
  brew install node
else
  echo -e "${GREEN}  ✅ Node.js bereits installiert${NC}"
fi

# Python 3 (für CSV-Verarbeitung)
if ! command -v python3 &> /dev/null; then
  echo "  Installing Python 3..."
  brew install python3
else
  echo -e "${GREEN}  ✅ Python 3 bereits installiert${NC}"
fi

echo ""

# ============================================
# 4. Claude Code CLI prüfen
# ============================================
echo "🤖 Prüfe Claude Code CLI..."
if ! command -v claude-code &> /dev/null; then
  echo -e "${YELLOW}⚠️  Claude Code CLI nicht gefunden.${NC}"
  echo ""
  echo "Bitte installiere Claude Code manuell:"
  echo "  1. VS Code öffnen"
  echo "  2. Extension installieren: Anthropic.claude-code"
  echo "  3. Cmd+Shift+P → 'Claude Code: Setup CLI'"
  echo ""
  echo -e "${YELLOW}Setze Setup fort (CLI kann später installiert werden)...${NC}"
else
  echo -e "${GREEN}✅ Claude Code CLI installiert${NC}"
fi
echo ""

# ============================================
# 5. Playwright installieren (für Browser-Automation)
# ============================================
echo "🌐 Installiere Playwright..."
if [ ! -d "node_modules/playwright" ]; then
  npm init -y > /dev/null 2>&1
  npm install playwright > /dev/null 2>&1
  npx playwright install chromium
  echo -e "${GREEN}✅ Playwright installiert${NC}"
else
  echo -e "${GREEN}✅ Playwright bereits installiert${NC}"
fi
echo ""

# ============================================
# 6. Ordnerstruktur erstellen
# ============================================
echo "📁 Erstelle Ordnerstruktur..."

AGENT_DIR="$HOME/AcademicAgent"
mkdir -p "$AGENT_DIR"/{projects,config,logs}
mkdir -p "$AGENT_DIR/scripts"

# Kopiere Dateien aus Repo
cp -r agents "$AGENT_DIR/" 2>/dev/null || mkdir -p "$AGENT_DIR/agents"
cp -r scripts "$AGENT_DIR/" 2>/dev/null || mkdir -p "$AGENT_DIR/scripts"

# Config-Template kopieren
if [ -f "config/Config_Template.md" ]; then
  cp config/Config_Template.md "$AGENT_DIR/config/"
fi

echo -e "${GREEN}✅ Ordnerstruktur erstellt: $AGENT_DIR${NC}"
echo ""
echo "Struktur:"
echo "  $AGENT_DIR/"
echo "    ├── agents/          (Agent-Prompts)"
echo "    ├── config/          (User-Configs)"
echo "    ├── projects/        (Outputs)"
echo "    ├── scripts/         (Helper-Scripts)"
echo "    └── logs/            (Logs)"
echo ""

# ============================================
# 7. Permissions setzen
# ============================================
echo "🔒 Setze Permissions..."
chmod 755 "$AGENT_DIR"
chmod 644 "$AGENT_DIR/config"/*.md 2>/dev/null || true

# Make scripts executable
chmod +x scripts/browser_helper.js 2>/dev/null || true
chmod +x scripts/browser_cdp_helper.js 2>/dev/null || true
chmod +x scripts/start_chrome_debug.sh 2>/dev/null || true
chmod +x scripts/create_quote_library.py 2>/dev/null || true
chmod +x scripts/create_bibliography.py 2>/dev/null || true
chmod +x scripts/validate_config.py 2>/dev/null || true

# Error Recovery Scripts
chmod +x scripts/state_manager.py 2>/dev/null || true
chmod +x scripts/error_handler.sh 2>/dev/null || true
chmod +x scripts/resume_research.sh 2>/dev/null || true

echo -e "${GREEN}✅ Permissions gesetzt${NC}"
echo ""

# ============================================
# 8. Abschluss
# ============================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}✅ Setup abgeschlossen!${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 Nächste Schritte:"
echo ""
echo "  1. Config anpassen:"
echo "     \$ code $AGENT_DIR/config/Config_Template.md"
echo "     (Speichere als: Config_[DeinProjekt].md)"
echo ""
echo "  2. Chrome mit Remote Debugging starten (Terminal 1):"
echo "     \$ bash scripts/start_chrome_debug.sh"
echo "     (Chrome läuft dann auf Port 9222)"
echo ""
echo "  3. VS Code im Repo öffnen (Terminal 2):"
echo "     \$ cd $(pwd)"
echo "     \$ code ."
echo ""
echo "  4. Claude Code Chat starten:"
echo "     Cmd+Shift+P → 'Claude Code: Start Chat'"
echo ""
echo "  5. Agent starten (im Chat):"
echo "     Lies agents/orchestrator.md und starte die Recherche"
echo "     für $AGENT_DIR/config/Config_[DeinProjekt].md"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📁 Working Directory: $AGENT_DIR"
echo ""
echo "🧪 Test Chrome CDP (optional):"
echo "   \$ bash scripts/start_chrome_debug.sh &"
echo "   \$ sleep 3"
echo "   \$ curl http://localhost:9222/json/version"
echo "   (Sollte Chrome-Version anzeigen)"
echo ""
