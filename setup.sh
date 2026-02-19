#!/bin/bash

# 🛠️ AcademicAgent - Vollständiges Setup-Script
# Version: 3.1 (Enhanced Security Edition)
# Letztes Update: 2026-02-18
# Zweck: Frische Installation auf neuer VM mit allen Abhängigkeiten

set -e  # Bei Fehler abbrechen

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
# 1. Betriebssystem-Erkennung
# ============================================
echo -e "${BLUE}📋 Erkenne Betriebssystem...${NC}"

OS="unknown"
if [[ "$OSTYPE" == "darwin"* ]]; then
  OS="macos"
  echo -e "${GREEN}✅ macOS erkannt${NC}"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
  OS="linux"
  echo -e "${GREEN}✅ Linux erkannt${NC}"
else
  echo -e "${RED}❌ Nicht unterstütztes OS: $OSTYPE${NC}"
  echo "Aktuell unterstützt: macOS, Linux"
  exit 1
fi

echo ""

# ============================================
# 2. Paketmanager-Erkennung & Installation
# ============================================
echo -e "${BLUE}📦 Prüfe Paketmanager...${NC}"

if [[ "$OS" == "macos" ]]; then
  # macOS: Prüfe auf Homebrew
  if ! command -v brew &> /dev/null; then
    echo -e "${YELLOW}⚠️  Homebrew nicht gefunden. Installiere...${NC}"
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

    # Füge Homebrew zu PATH hinzu
    if [[ -f "/opt/homebrew/bin/brew" ]]; then
      eval "$(/opt/homebrew/bin/brew shellenv)"
    fi

    echo -e "${GREEN}✅ Homebrew installiert${NC}"
  else
    echo -e "${GREEN}✅ Homebrew gefunden${NC}"
  fi
  PKG_MANAGER="brew"

elif [[ "$OS" == "linux" ]]; then
  # Linux: Erkenne Paketmanager
  if command -v apt &> /dev/null; then
    PKG_MANAGER="apt"
    echo -e "${GREEN}✅ apt gefunden${NC}"
  elif command -v yum &> /dev/null; then
    PKG_MANAGER="yum"
    echo -e "${GREEN}✅ yum gefunden${NC}"
  elif command -v dnf &> /dev/null; then
    PKG_MANAGER="dnf"
    echo -e "${GREEN}✅ dnf gefunden${NC}"
  else
    echo -e "${RED}❌ Kein unterstützter Paketmanager gefunden${NC}"
    exit 1
  fi
fi

echo ""

# ============================================
# 3. Chrome / Chromium installieren
# ============================================
echo -e "${BLUE}🌐 Installiere Chrome/Chromium...${NC}"

CHROME_INSTALLED=false

if [[ "$OS" == "macos" ]]; then
  if [[ -d "/Applications/Google Chrome.app" ]]; then
    echo -e "${GREEN}✅ Google Chrome bereits installiert${NC}"
    CHROME_INSTALLED=true
  else
    echo -e "${YELLOW}⚠️  Google Chrome nicht gefunden${NC}"
    echo "Bitte manuell installieren von: https://www.google.com/chrome/"
    echo ""
    echo "Drücke ENTER wenn Chrome installiert ist (oder zum Überspringen)..."
    read

    if [[ -d "/Applications/Google Chrome.app" ]]; then
      echo -e "${GREEN}✅ Chrome verifiziert${NC}"
      CHROME_INSTALLED=true
    else
      echo -e "${YELLOW}⚠️  Chrome nicht gefunden - fahre trotzdem fort${NC}"
    fi
  fi

elif [[ "$OS" == "linux" ]]; then
  if command -v google-chrome &> /dev/null || command -v chromium &> /dev/null || command -v chromium-browser &> /dev/null; then
    echo -e "${GREEN}✅ Chrome/Chromium bereits installiert${NC}"
    CHROME_INSTALLED=true
  else
    echo -e "${YELLOW}Installiere Chromium...${NC}"
    if [[ "$PKG_MANAGER" == "apt" ]]; then
      sudo apt update
      sudo apt install -y chromium-browser
    elif [[ "$PKG_MANAGER" == "yum" ]] || [[ "$PKG_MANAGER" == "dnf" ]]; then
      sudo $PKG_MANAGER install -y chromium
    fi
    echo -e "${GREEN}✅ Chromium installiert${NC}"
    CHROME_INSTALLED=true
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
  if [[ "$PKG_MANAGER" == "brew" ]]; then
    brew install poppler
  elif [[ "$PKG_MANAGER" == "apt" ]]; then
    sudo apt update
    sudo apt install -y poppler-utils
  elif [[ "$PKG_MANAGER" == "yum" ]] || [[ "$PKG_MANAGER" == "dnf" ]]; then
    sudo $PKG_MANAGER install -y poppler-utils
  fi
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
  if [[ "$PKG_MANAGER" == "brew" ]]; then
    brew install wget
  elif [[ "$PKG_MANAGER" == "apt" ]]; then
    sudo apt update
    sudo apt install -y wget
  elif [[ "$PKG_MANAGER" == "yum" ]] || [[ "$PKG_MANAGER" == "dnf" ]]; then
    sudo $PKG_MANAGER install -y wget
  fi
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
  if [[ "$PKG_MANAGER" == "brew" ]]; then
    brew install curl
  elif [[ "$PKG_MANAGER" == "apt" ]]; then
    sudo apt update
    sudo apt install -y curl
  elif [[ "$PKG_MANAGER" == "yum" ]] || [[ "$PKG_MANAGER" == "dnf" ]]; then
    sudo $PKG_MANAGER install -y curl
  fi
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
  if [[ "$PKG_MANAGER" == "brew" ]]; then
    brew install jq
  elif [[ "$PKG_MANAGER" == "apt" ]]; then
    sudo apt update
    sudo apt install -y jq
  elif [[ "$PKG_MANAGER" == "yum" ]] || [[ "$PKG_MANAGER" == "dnf" ]]; then
    sudo $PKG_MANAGER install -y jq
  fi
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
  if [[ "$PKG_MANAGER" == "brew" ]]; then
    brew install git
  elif [[ "$PKG_MANAGER" == "apt" ]]; then
    sudo apt update
    sudo apt install -y git
  elif [[ "$PKG_MANAGER" == "yum" ]] || [[ "$PKG_MANAGER" == "dnf" ]]; then
    sudo $PKG_MANAGER install -y git
  fi
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
  if [[ "$PKG_MANAGER" == "brew" ]]; then
    brew install pandoc
  elif [[ "$PKG_MANAGER" == "apt" ]]; then
    sudo apt update
    sudo apt install -y pandoc
  elif [[ "$PKG_MANAGER" == "yum" ]] || [[ "$PKG_MANAGER" == "dnf" ]]; then
    sudo $PKG_MANAGER install -y pandoc
  fi
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
  if [[ "$PKG_MANAGER" == "brew" ]]; then
    brew install node
  elif [[ "$PKG_MANAGER" == "apt" ]]; then
    # Installiere Node.js 18.x LTS
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
    sudo apt install -y nodejs
  elif [[ "$PKG_MANAGER" == "yum" ]] || [[ "$PKG_MANAGER" == "dnf" ]]; then
    curl -fsSL https://rpm.nodesource.com/setup_18.x | sudo bash -
    sudo $PKG_MANAGER install -y nodejs
  fi
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
  if [[ "$PKG_MANAGER" == "brew" ]]; then
    brew install python3
  elif [[ "$PKG_MANAGER" == "apt" ]]; then
    sudo apt update
    sudo apt install -y python3 python3-pip
  elif [[ "$PKG_MANAGER" == "yum" ]] || [[ "$PKG_MANAGER" == "dnf" ]]; then
    sudo $PKG_MANAGER install -y python3 python3-pip
  fi
  echo -e "${GREEN}✅ Python 3 installiert${NC}"
fi

echo ""

# ============================================
# 12. Installiere Playwright (Nur CDP-Client)
# ============================================
echo -e "${BLUE}🎭 Installiere Playwright...${NC}"
echo -e "${YELLOW}Hinweis: Playwright wird NUR als CDP-Client verwendet um sich mit echtem Chrome zu verbinden${NC}"
echo -e "${YELLOW}         NICHT für Headless-Browsing. User hat volle Kontrolle über Browser.${NC}"

if [ ! -d "node_modules/playwright" ]; then
  # Initialisiere npm falls nötig
  if [ ! -f "package.json" ]; then
    echo -e "${YELLOW}Erstelle package.json...${NC}"
    npm init -y > /dev/null 2>&1
  fi

  echo -e "${YELLOW}Installiere Playwright (kann einige Minuten dauern)...${NC}"
  npm install playwright

  # Installiere Chromium-Browser (nur Fallback - wir nutzen echtes Chrome via CDP)
  echo -e "${YELLOW}Installiere Playwright Chromium (nur Fallback)...${NC}"
  npx playwright install chromium

  echo -e "${GREEN}✅ Playwright installiert (CDP-Client-Modus)${NC}"
else
  echo -e "${GREEN}✅ Playwright bereits installiert${NC}"
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
# 16. Erfolgsmeldung
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
