#!/bin/bash

# 🛠️ AcademicAgent - Vollständiges Setup-Script
# Version: 3.1 (Enhanced Security Edition)
# Letztes Update: 2026-02-18
# Zweck: Frische Installation auf neuer VM mit allen Abhängigkeiten

set -euo pipefail  # Bei Fehler abbrechen, uninitialisierte Variablen erkennen, Pipe-Fehler nicht ignorieren

# Farben
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # Keine Farbe

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${BLUE}🤖 AcademicAgent Setup v3.0${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ============================================
# 1. Betriebssystem-Erkennung (macOS ONLY)
# ============================================
echo -e "${BLUE}📋 Erkenne Betriebssystem...${NC}"

if [[ "$OSTYPE" != "darwin"* ]]; then
  echo -e "${RED}❌ Nicht unterstütztes OS: $OSTYPE${NC}"
  echo ""
  echo "⚠️  AcademicAgent ist ausschließlich für macOS entwickelt."
  echo ""
  echo "Grund:"
  echo "  - macOS-spezifische Pfade (/Applications/Google Chrome.app)"
  echo "  - macOS-spezifische Befehle (stat -f, lsof, open)"
  echo "  - Homebrew als Paketmanager"
  echo ""
  echo "Linux/Windows werden nicht unterstützt."
  exit 1
fi

OS="macos"
echo -e "${GREEN}✅ macOS erkannt${NC}"

echo ""

# ============================================
# 2. Paketmanager-Erkennung & Installation
# ============================================
echo -e "${BLUE}📦 Prüfe Paketmanager...${NC}"

# macOS: Prüfe auf Homebrew
if ! command -v brew &> /dev/null; then
  echo -e "${YELLOW}⚠️  Homebrew nicht gefunden.${NC}"
  echo ""
  echo "⚠️  SICHERHEITSHINWEIS:"
  echo "    Homebrew wird von einem öffentlichen GitHub-Repository installiert."
  echo "    Bitte prüfe den Installationsbefehl vorher auf https://brew.sh"
  echo ""
  echo "Möchtest du Homebrew jetzt installieren? (y/n)"
  read -r INSTALL_BREW

  if [[ "$INSTALL_BREW" =~ ^[Yy]$ ]]; then
    echo ""
    echo -e "${YELLOW}Installiere Homebrew...${NC}"
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

    # Füge Homebrew zu PATH hinzu
    if [[ -f "/opt/homebrew/bin/brew" ]]; then
      eval "$(/opt/homebrew/bin/brew shellenv)"
    fi

    echo -e "${GREEN}✅ Homebrew installiert${NC}"
  else
    echo -e "${RED}❌ Homebrew erforderlich. Installation abgebrochen.${NC}"
    echo ""
    echo "Manuelle Installation:"
    echo "  /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
    exit 1
  fi
else
  echo -e "${GREEN}✅ Homebrew gefunden${NC}"
fi
PKG_MANAGER="brew"

echo ""

# ============================================
# 3. Chrome installieren (macOS)
# ============================================
echo -e "${BLUE}🌐 Prüfe Google Chrome...${NC}"

CHROME_INSTALLED=false

if [[ -d "/Applications/Google Chrome.app" ]]; then
  echo -e "${GREEN}✅ Google Chrome bereits installiert${NC}"
  CHROME_INSTALLED=true
else
  echo -e "${YELLOW}⚠️  Google Chrome nicht gefunden${NC}"
  echo "Bitte manuell installieren von: https://www.google.com/chrome/"
  echo ""
  echo "Drücke ENTER wenn Chrome installiert ist (oder zum Überspringen)..."
  read -r

  if [[ -d "/Applications/Google Chrome.app" ]]; then
    echo -e "${GREEN}✅ Chrome verifiziert${NC}"
    CHROME_INSTALLED=true
  else
    echo -e "${YELLOW}⚠️  Chrome nicht gefunden - fahre trotzdem fort${NC}"
  fi
fi

echo ""

# ============================================
# 4. Installiere poppler (pdftotext)
# ============================================
echo -e "${BLUE}📄 Installiere poppler (pdftotext)...${NC}"

if command -v pdftotext &> /dev/null; then
  echo -e "${GREEN}✅ pdftotext bereits installiert${NC}"
else
  brew install poppler
  echo -e "${GREEN}✅ pdftotext installiert${NC}"
fi

echo ""

# ============================================
# 5. Installiere wget
# ============================================
echo -e "${BLUE}⬇️  Installiere wget...${NC}"

if command -v wget &> /dev/null; then
  echo -e "${GREEN}✅ wget bereits installiert${NC}"
else
  brew install wget
  echo -e "${GREEN}✅ wget installiert${NC}"
fi

echo ""

# ============================================
# 6. Installiere curl (Fallback)
# ============================================
echo -e "${BLUE}🌐 Installiere curl...${NC}"

if command -v curl &> /dev/null; then
  echo -e "${GREEN}✅ curl bereits installiert${NC}"
else
  brew install curl
  echo -e "${GREEN}✅ curl installiert${NC}"
fi

echo ""

# ============================================
# 7. Installiere jq (JSON-Prozessor)
# ============================================
echo -e "${BLUE}🔧 Installiere jq...${NC}"

if command -v jq &> /dev/null; then
  echo -e "${GREEN}✅ jq bereits installiert${NC}"
else
  brew install jq
  echo -e "${GREEN}✅ jq installiert${NC}"
fi

echo ""

# ============================================
# 8. Installiere git (falls nicht vorhanden)
# ============================================
echo -e "${BLUE}📦 Prüfe git...${NC}"

if command -v git &> /dev/null; then
  GIT_VERSION=$(git --version)
  echo -e "${GREEN}✅ git bereits installiert ($GIT_VERSION)${NC}"
else
  echo -e "${YELLOW}Installiere git...${NC}"
  brew install git
  echo -e "${GREEN}✅ git installiert${NC}"
fi

echo ""

# ============================================
# 9. Installiere pandoc (für Dokument-Export)
# ============================================
echo -e "${BLUE}📝 Installiere pandoc (optional)...${NC}"

if command -v pandoc &> /dev/null; then
  echo -e "${GREEN}✅ pandoc bereits installiert${NC}"
else
  echo -e "${YELLOW}Installiere pandoc (für Zitat-Export nach Word)...${NC}"
  brew install pandoc
  echo -e "${GREEN}✅ pandoc installiert${NC}"
fi

echo ""

# ============================================
# 10. Installiere Node.js + npm
# ============================================
echo -e "${BLUE}⚙️  Installiere Node.js + npm...${NC}"

if command -v node &> /dev/null; then
  NODE_VERSION=$(node --version)
  echo -e "${GREEN}✅ Node.js bereits installiert ($NODE_VERSION)${NC}"
else
  brew install node
  echo -e "${GREEN}✅ Node.js installiert${NC}"
fi

echo ""

# ============================================
# 11. Installiere Python 3
# ============================================
echo -e "${BLUE}🐍 Installiere Python 3...${NC}"

if command -v python3 &> /dev/null; then
  PYTHON_VERSION=$(python3 --version)
  echo -e "${GREEN}✅ Python 3 bereits installiert ($PYTHON_VERSION)${NC}"
else
  brew install python3
  echo -e "${GREEN}✅ Python 3 installiert${NC}"
fi

echo ""

# ============================================
# 12. Installiere Playwright (Nur CDP-Client)
# ============================================
echo -e "${BLUE}🎭 Installiere Playwright...${NC}"
echo -e "${YELLOW}Hinweis: Playwright wird NUR als CDP-Client verwendet um sich mit echtem Chrome zu verbinden${NC}"
echo -e "${YELLOW}         NICHT für Headless-Browsing. User hat volle Kontrolle über Browser.${NC}"

# Initialisiere npm falls nötig (idempotent)
if [ ! -f "package.json" ]; then
  echo -e "${YELLOW}Erstelle package.json...${NC}"
  npm init -y > /dev/null 2>&1
fi

# Installiere/Update Playwright (idempotent)
if [ ! -d "node_modules/playwright" ]; then
  echo -e "${YELLOW}Installiere Playwright (kann einige Minuten dauern)...${NC}"
  npm install playwright

  # Installiere Chromium-Browser (nur Fallback - wir nutzen echtes Chrome via CDP)
  echo -e "${YELLOW}Installiere Playwright Chromium (nur Fallback)...${NC}"
  npx playwright install chromium

  echo -e "${GREEN}✅ Playwright installiert (CDP-Client-Modus)${NC}"
else
  echo -e "${GREEN}✅ Playwright bereits installiert${NC}"
  # Stelle sicher dass Playwright aktuell ist (idempotent)
  echo -e "${YELLOW}Prüfe Playwright-Version...${NC}"
  npm list playwright 2>/dev/null || echo "  (Version konnte nicht ermittelt werden)"
fi

echo ""

# ============================================
# 13. Verzeichnisstruktur erstellen
# ============================================
echo -e "${BLUE}📁 Erstelle Verzeichnisstruktur...${NC}"

# Erstelle runs-Verzeichnis
mkdir -p runs

# Erstelle config-Verzeichnis falls nicht vorhanden
mkdir -p config

# Erstelle logs-Verzeichnis
mkdir -p logs

echo -e "${GREEN}✅ Verzeichnisstruktur erstellt${NC}"
echo "   - runs/     (Output für jede Recherche)"
echo "   - config/   (Config-Templates)"
echo "   - logs/     (Globale Logs)"
echo ""

# ============================================
# 14. Berechtigungen setzen
# ============================================
echo -e "${BLUE}🔒 Setze Berechtigungen...${NC}"

# Mache alle Scripts ausführbar
chmod +x scripts/*.sh 2>/dev/null || true
chmod +x scripts/*.py 2>/dev/null || true
chmod +x scripts/*.js 2>/dev/null || true

echo -e "${GREEN}✅ Berechtigungen gesetzt${NC}"
echo ""

# ============================================
# 14b. Installiere Git Pre-Commit Hooks
# ============================================
echo -e "${BLUE}🔒 Installiere Git Pre-Commit Hooks...${NC}"

if [ -f "scripts/setup_git_hooks.sh" ]; then
  bash scripts/setup_git_hooks.sh
  echo -e "${GREEN}✅ Git Hooks installiert (Secret-Scanning aktiv)${NC}"
else
  echo -e "${YELLOW}⚠️  scripts/setup_git_hooks.sh nicht gefunden - überspringe${NC}"
fi

echo ""

# ============================================
# 15. Verifizierung
# ============================================
echo -e "${BLUE}🧪 Verifiziere Installation...${NC}"
echo ""

# Prüfe alle erforderlichen Befehle
VERIFICATION_FAILED=false

echo -n "  Prüfe pdftotext... "
if command -v pdftotext &> /dev/null; then
  echo -e "${GREEN}✅${NC}"
else
  echo -e "${RED}❌${NC}"
  VERIFICATION_FAILED=true
fi

echo -n "  Prüfe wget... "
if command -v wget &> /dev/null; then
  echo -e "${GREEN}✅${NC}"
else
  echo -e "${RED}❌${NC}"
  VERIFICATION_FAILED=true
fi

echo -n "  Prüfe curl... "
if command -v curl &> /dev/null; then
  echo -e "${GREEN}✅${NC}"
else
  echo -e "${RED}❌${NC}"
  VERIFICATION_FAILED=true
fi

echo -n "  Prüfe node... "
if command -v node &> /dev/null; then
  echo -e "${GREEN}✅${NC}"
else
  echo -e "${RED}❌${NC}"
  VERIFICATION_FAILED=true
fi

echo -n "  Prüfe npm... "
if command -v npm &> /dev/null; then
  echo -e "${GREEN}✅${NC}"
else
  echo -e "${RED}❌${NC}"
  VERIFICATION_FAILED=true
fi

echo -n "  Prüfe python3... "
if command -v python3 &> /dev/null; then
  echo -e "${GREEN}✅${NC}"
else
  echo -e "${RED}❌${NC}"
  VERIFICATION_FAILED=true
fi

echo -n "  Prüfe jq... "
if command -v jq &> /dev/null; then
  echo -e "${GREEN}✅${NC}"
else
  echo -e "${RED}❌${NC}"
  VERIFICATION_FAILED=true
fi

echo -n "  Prüfe git... "
if command -v git &> /dev/null; then
  echo -e "${GREEN}✅${NC}"
else
  echo -e "${RED}❌${NC}"
  VERIFICATION_FAILED=true
fi

echo -n "  Prüfe pandoc... "
if command -v pandoc &> /dev/null; then
  echo -e "${GREEN}✅${NC}"
else
  echo -e "${YELLOW}⚠️  (Optional - für Zitat-Export)${NC}"
fi

echo -n "  Prüfe Playwright... "
if [ -d "node_modules/playwright" ]; then
  echo -e "${GREEN}✅${NC}"
else
  echo -e "${RED}❌${NC}"
  VERIFICATION_FAILED=true
fi

if [ "$CHROME_INSTALLED" = true ]; then
  echo -e "  Chrome/Chromium... ${GREEN}✅${NC}"
else
  echo -e "  Chrome/Chromium... ${YELLOW}⚠️  (Manuelle Installation erforderlich)${NC}"
fi

echo ""

if [ "$VERIFICATION_FAILED" = true ]; then
  echo -e "${RED}❌ Einige Abhängigkeiten konnten nicht installiert werden${NC}"
  echo "Bitte prüfe die obigen Fehler und versuche es erneut."
  exit 1
fi

# ============================================
# 16. Encryption-at-Rest Check (MANDATORY für Production)
# ============================================
echo ""
echo -e "${BLUE}🔒 Prüfe Disk-Encryption (MANDATORY für Production)...${NC}"
echo ""

ENCRYPTION_ENABLED=false

# macOS: FileVault check
if [[ "$OSTYPE" == "darwin"* ]]; then
  if fdesetup status | grep -q "FileVault is On"; then
    echo -e "${GREEN}✅ FileVault ist aktiviert${NC}"
    ENCRYPTION_ENABLED=true
  else
    echo -e "${RED}❌ FileVault ist NICHT aktiviert!${NC}"
    echo ""
    echo -e "${YELLOW}⚠️  SICHERHEITSWARNUNG:${NC}"
    echo "   AcademicAgent speichert sensitive Forschungsinhalte (PDFs, Zitate)."
    echo "   GDPR/ISO-27001 erfordert Encryption-at-Rest für PII."
    echo ""
    echo "   FileVault aktivieren:"
    echo "   1. System Settings → Privacy & Security → FileVault"
    echo "   2. Click 'Turn On FileVault'"
    echo "   3. Neustart erforderlich"
    echo ""
    echo "   ⚠️  Ohne FileVault sind deine Forschungsdaten bei Laptop-Verlust kompromittiert!"
    echo ""
  fi
fi

if [ "$ENCRYPTION_ENABLED" = false ]; then
  echo "Möchtest du trotzdem fortfahren? (y/n)"
  read -r CONTINUE_WITHOUT_ENCRYPTION

  if [[ ! "$CONTINUE_WITHOUT_ENCRYPTION" =~ ^[Yy]$ ]]; then
    echo ""
    echo "Setup abgebrochen. Bitte aktiviere Disk-Encryption und führe setup.sh erneut aus."
    exit 1
  fi

  echo ""
  echo -e "${YELLOW}⚠️  Fortfahren OHNE Disk-Encryption (nicht empfohlen für Production)${NC}"
fi

echo ""

# ============================================
# 17. Erfolgsmeldung
# ============================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}✅ Setup erfolgreich abgeschlossen!${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${BLUE}📋 Nächste Schritte:${NC}"
echo ""
echo "  1. Chrome mit Remote-Debugging starten:"
echo -e "     ${YELLOW}\$ bash scripts/start_chrome_debug.sh${NC}"
echo ""
echo "  2. (Optional) Bei DBIS einloggen:"
echo "     → Chrome öffnen und zu https://dbis.de gehen"
echo "     → Mit Uni-Account einloggen"
echo ""
echo "  3. VS Code in diesem Verzeichnis öffnen:"
echo -e "     ${YELLOW}\$ code .${NC}"
echo ""
echo "  4. Claude Code Chat starten:"
echo "     → Cmd+Shift+P → 'Claude Code: Start Chat'"
echo ""
echo "  5. Eine Recherche starten:"
echo -e "     ${YELLOW}/academicagent${NC}"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${BLUE}📖 Dokumentation:${NC}"
echo "  - README.md          (Vollständiger Guide)"
echo "  - ERROR_RECOVERY.md  (Fehlerbehebung)"
echo "  - SECURITY.md        (Sicherheitsdokumentation)"
echo ""
echo -e "${BLUE}🧪 Chrome-CDP testen (optional):${NC}"
echo -e "  ${YELLOW}\$ bash scripts/start_chrome_debug.sh${NC}"
echo -e "  ${YELLOW}\$ sleep 3${NC}"
echo -e "  ${YELLOW}\$ curl http://localhost:9222/json/version${NC}"
echo "  (Sollte Chrome-Version anzeigen)"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${GREEN}Viel Erfolg bei der Recherche! 📚🤖${NC}"
echo ""
