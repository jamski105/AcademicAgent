#!/bin/bash

# 🛠️ AcademicAgent - Complete Setup Script
# Version: 2.2
# Purpose: Fresh installation on new VM with all dependencies

set -e  # Exit on error

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${BLUE}🤖 AcademicAgent Setup v2.2${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ============================================
# 1. OS Detection
# ============================================
echo -e "${BLUE}📋 Detecting operating system...${NC}"

OS="unknown"
if [[ "$OSTYPE" == "darwin"* ]]; then
  OS="macos"
  echo -e "${GREEN}✅ macOS detected${NC}"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
  OS="linux"
  echo -e "${GREEN}✅ Linux detected${NC}"
else
  echo -e "${RED}❌ Unsupported OS: $OSTYPE${NC}"
  echo "Currently supported: macOS, Linux"
  exit 1
fi

echo ""

# ============================================
# 2. Package Manager Detection & Installation
# ============================================
echo -e "${BLUE}📦 Checking package manager...${NC}"

if [[ "$OS" == "macos" ]]; then
  # macOS: Check for Homebrew
  if ! command -v brew &> /dev/null; then
    echo -e "${YELLOW}⚠️  Homebrew not found. Installing...${NC}"
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

    # Add Homebrew to PATH
    if [[ -f "/opt/homebrew/bin/brew" ]]; then
      eval "$(/opt/homebrew/bin/brew shellenv)"
    fi

    echo -e "${GREEN}✅ Homebrew installed${NC}"
  else
    echo -e "${GREEN}✅ Homebrew found${NC}"
  fi
  PKG_MANAGER="brew"

elif [[ "$OS" == "linux" ]]; then
  # Linux: Detect package manager
  if command -v apt &> /dev/null; then
    PKG_MANAGER="apt"
    echo -e "${GREEN}✅ apt found${NC}"
  elif command -v yum &> /dev/null; then
    PKG_MANAGER="yum"
    echo -e "${GREEN}✅ yum found${NC}"
  elif command -v dnf &> /dev/null; then
    PKG_MANAGER="dnf"
    echo -e "${GREEN}✅ dnf found${NC}"
  else
    echo -e "${RED}❌ No supported package manager found${NC}"
    exit 1
  fi
fi

echo ""

# ============================================
# 3. Install Chrome / Chromium
# ============================================
echo -e "${BLUE}🌐 Installing Chrome/Chromium...${NC}"

CHROME_INSTALLED=false

if [[ "$OS" == "macos" ]]; then
  if [[ -d "/Applications/Google Chrome.app" ]]; then
    echo -e "${GREEN}✅ Google Chrome already installed${NC}"
    CHROME_INSTALLED=true
  else
    echo -e "${YELLOW}⚠️  Google Chrome not found${NC}"
    echo "Please install manually from: https://www.google.com/chrome/"
    echo ""
    echo "Press ENTER when Chrome is installed (or to skip)..."
    read

    if [[ -d "/Applications/Google Chrome.app" ]]; then
      echo -e "${GREEN}✅ Chrome verified${NC}"
      CHROME_INSTALLED=true
    else
      echo -e "${YELLOW}⚠️  Chrome not found - continuing anyway${NC}"
    fi
  fi

elif [[ "$OS" == "linux" ]]; then
  if command -v google-chrome &> /dev/null || command -v chromium &> /dev/null || command -v chromium-browser &> /dev/null; then
    echo -e "${GREEN}✅ Chrome/Chromium already installed${NC}"
    CHROME_INSTALLED=true
  else
    echo -e "${YELLOW}Installing Chromium...${NC}"
    if [[ "$PKG_MANAGER" == "apt" ]]; then
      sudo apt update
      sudo apt install -y chromium-browser
    elif [[ "$PKG_MANAGER" == "yum" ]] || [[ "$PKG_MANAGER" == "dnf" ]]; then
      sudo $PKG_MANAGER install -y chromium
    fi
    echo -e "${GREEN}✅ Chromium installed${NC}"
    CHROME_INSTALLED=true
  fi
fi

echo ""

# ============================================
# 4. Install poppler (pdftotext)
# ============================================
echo -e "${BLUE}📄 Installing poppler (pdftotext)...${NC}"

if command -v pdftotext &> /dev/null; then
  echo -e "${GREEN}✅ pdftotext already installed${NC}"
else
  if [[ "$PKG_MANAGER" == "brew" ]]; then
    brew install poppler
  elif [[ "$PKG_MANAGER" == "apt" ]]; then
    sudo apt update
    sudo apt install -y poppler-utils
  elif [[ "$PKG_MANAGER" == "yum" ]] || [[ "$PKG_MANAGER" == "dnf" ]]; then
    sudo $PKG_MANAGER install -y poppler-utils
  fi
  echo -e "${GREEN}✅ pdftotext installed${NC}"
fi

echo ""

# ============================================
# 5. Install wget
# ============================================
echo -e "${BLUE}⬇️  Installing wget...${NC}"

if command -v wget &> /dev/null; then
  echo -e "${GREEN}✅ wget already installed${NC}"
else
  if [[ "$PKG_MANAGER" == "brew" ]]; then
    brew install wget
  elif [[ "$PKG_MANAGER" == "apt" ]]; then
    sudo apt update
    sudo apt install -y wget
  elif [[ "$PKG_MANAGER" == "yum" ]] || [[ "$PKG_MANAGER" == "dnf" ]]; then
    sudo $PKG_MANAGER install -y wget
  fi
  echo -e "${GREEN}✅ wget installed${NC}"
fi

echo ""

# ============================================
# 6. Install curl (fallback)
# ============================================
echo -e "${BLUE}🌐 Installing curl...${NC}"

if command -v curl &> /dev/null; then
  echo -e "${GREEN}✅ curl already installed${NC}"
else
  if [[ "$PKG_MANAGER" == "brew" ]]; then
    brew install curl
  elif [[ "$PKG_MANAGER" == "apt" ]]; then
    sudo apt update
    sudo apt install -y curl
  elif [[ "$PKG_MANAGER" == "yum" ]] || [[ "$PKG_MANAGER" == "dnf" ]]; then
    sudo $PKG_MANAGER install -y curl
  fi
  echo -e "${GREEN}✅ curl installed${NC}"
fi

echo ""

# ============================================
# 7. Install Node.js + npm
# ============================================
echo -e "${BLUE}⚙️  Installing Node.js + npm...${NC}"

if command -v node &> /dev/null; then
  NODE_VERSION=$(node --version)
  echo -e "${GREEN}✅ Node.js already installed ($NODE_VERSION)${NC}"
else
  if [[ "$PKG_MANAGER" == "brew" ]]; then
    brew install node
  elif [[ "$PKG_MANAGER" == "apt" ]]; then
    # Install Node.js 18.x LTS
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
    sudo apt install -y nodejs
  elif [[ "$PKG_MANAGER" == "yum" ]] || [[ "$PKG_MANAGER" == "dnf" ]]; then
    curl -fsSL https://rpm.nodesource.com/setup_18.x | sudo bash -
    sudo $PKG_MANAGER install -y nodejs
  fi
  echo -e "${GREEN}✅ Node.js installed${NC}"
fi

echo ""

# ============================================
# 8. Install Python 3
# ============================================
echo -e "${BLUE}🐍 Installing Python 3...${NC}"

if command -v python3 &> /dev/null; then
  PYTHON_VERSION=$(python3 --version)
  echo -e "${GREEN}✅ Python 3 already installed ($PYTHON_VERSION)${NC}"
else
  if [[ "$PKG_MANAGER" == "brew" ]]; then
    brew install python3
  elif [[ "$PKG_MANAGER" == "apt" ]]; then
    sudo apt update
    sudo apt install -y python3 python3-pip
  elif [[ "$PKG_MANAGER" == "yum" ]] || [[ "$PKG_MANAGER" == "dnf" ]]; then
    sudo $PKG_MANAGER install -y python3 python3-pip
  fi
  echo -e "${GREEN}✅ Python 3 installed${NC}"
fi

echo ""

# ============================================
# 9. Install Playwright (CDP Client Only)
# ============================================
echo -e "${BLUE}🎭 Installing Playwright...${NC}"
echo -e "${YELLOW}Note: Playwright is used ONLY as CDP client to connect to real Chrome${NC}"
echo -e "${YELLOW}      NOT for headless browsing. User has full control over browser.${NC}"

if [ ! -d "node_modules/playwright" ]; then
  # Initialize npm if needed
  if [ ! -f "package.json" ]; then
    echo -e "${YELLOW}Creating package.json...${NC}"
    npm init -y > /dev/null 2>&1
  fi

  echo -e "${YELLOW}Installing Playwright (this may take a few minutes)...${NC}"
  npm install playwright

  # Install Chromium browser (fallback only - we use real Chrome via CDP)
  echo -e "${YELLOW}Installing Playwright Chromium (fallback only)...${NC}"
  npx playwright install chromium

  echo -e "${GREEN}✅ Playwright installed (CDP client mode)${NC}"
else
  echo -e "${GREEN}✅ Playwright already installed${NC}"
fi

echo ""

# ============================================
# 10. Create Directory Structure
# ============================================
echo -e "${BLUE}📁 Creating directory structure...${NC}"

# Create runs directory
mkdir -p runs

# Create config directory if it doesn't exist
mkdir -p config

# Create logs directory
mkdir -p logs

echo -e "${GREEN}✅ Directory structure created${NC}"
echo "   - runs/     (Output für jede Recherche)"
echo "   - config/   (Config-Templates)"
echo "   - logs/     (Global Logs)"
echo ""

# ============================================
# 11. Set Permissions
# ============================================
echo -e "${BLUE}🔒 Setting permissions...${NC}"

# Make all scripts executable
chmod +x scripts/*.sh 2>/dev/null || true
chmod +x scripts/*.py 2>/dev/null || true
chmod +x scripts/*.js 2>/dev/null || true

echo -e "${GREEN}✅ Permissions set${NC}"
echo ""

# ============================================
# 12. Verification
# ============================================
echo -e "${BLUE}🧪 Verifying installation...${NC}"
echo ""

# Check all required commands
VERIFICATION_FAILED=false

echo -n "  Checking pdftotext... "
if command -v pdftotext &> /dev/null; then
  echo -e "${GREEN}✅${NC}"
else
  echo -e "${RED}❌${NC}"
  VERIFICATION_FAILED=true
fi

echo -n "  Checking wget... "
if command -v wget &> /dev/null; then
  echo -e "${GREEN}✅${NC}"
else
  echo -e "${RED}❌${NC}"
  VERIFICATION_FAILED=true
fi

echo -n "  Checking curl... "
if command -v curl &> /dev/null; then
  echo -e "${GREEN}✅${NC}"
else
  echo -e "${RED}❌${NC}"
  VERIFICATION_FAILED=true
fi

echo -n "  Checking node... "
if command -v node &> /dev/null; then
  echo -e "${GREEN}✅${NC}"
else
  echo -e "${RED}❌${NC}"
  VERIFICATION_FAILED=true
fi

echo -n "  Checking npm... "
if command -v npm &> /dev/null; then
  echo -e "${GREEN}✅${NC}"
else
  echo -e "${RED}❌${NC}"
  VERIFICATION_FAILED=true
fi

echo -n "  Checking python3... "
if command -v python3 &> /dev/null; then
  echo -e "${GREEN}✅${NC}"
else
  echo -e "${RED}❌${NC}"
  VERIFICATION_FAILED=true
fi

echo -n "  Checking Playwright... "
if [ -d "node_modules/playwright" ]; then
  echo -e "${GREEN}✅${NC}"
else
  echo -e "${RED}❌${NC}"
  VERIFICATION_FAILED=true
fi

if [ "$CHROME_INSTALLED" = true ]; then
  echo -e "  Chrome/Chromium... ${GREEN}✅${NC}"
else
  echo -e "  Chrome/Chromium... ${YELLOW}⚠️  (Manual installation required)${NC}"
fi

echo ""

if [ "$VERIFICATION_FAILED" = true ]; then
  echo -e "${RED}❌ Some dependencies failed to install${NC}"
  echo "Please check the errors above and try again."
  exit 1
fi

# ============================================
# 13. Success Message
# ============================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}✅ Setup completed successfully!${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${BLUE}📋 Next Steps:${NC}"
echo ""
echo "  1. Start Chrome with Remote Debugging:"
echo -e "     ${YELLOW}\$ bash scripts/start_chrome_debug.sh${NC}"
echo ""
echo "  2. (Optional) Login to DBIS:"
echo "     → Open Chrome and go to https://dbis.de"
echo "     → Login with your university account"
echo ""
echo "  3. Open VS Code in this directory:"
echo -e "     ${YELLOW}\$ code .${NC}"
echo ""
echo "  4. Start Claude Code Chat:"
echo "     → Cmd+Shift+P → 'Claude Code: Start Chat'"
echo ""
echo "  5. Start a research:"
echo -e "     ${YELLOW}/start-research${NC}"
echo "     or"
echo -e "     ${YELLOW}/setup-agent${NC}"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${BLUE}📖 Documentation:${NC}"
echo "  - README.md          (Overview)"
echo "  - SKILLS_USAGE.md    (Skill documentation)"
echo "  - ERROR_RECOVERY.md  (Troubleshooting)"
echo ""
echo -e "${BLUE}🧪 Test Chrome CDP (optional):${NC}"
echo -e "  ${YELLOW}\$ bash scripts/start_chrome_debug.sh${NC}"
echo -e "  ${YELLOW}\$ sleep 3${NC}"
echo -e "  ${YELLOW}\$ curl http://localhost:9222/json/version${NC}"
echo "  (Should show Chrome version)"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${GREEN}Happy Researching! 📚🤖${NC}"
echo ""
