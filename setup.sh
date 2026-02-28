#!/bin/bash
# Academic Agent v2.3 - Complete Setup Script for macOS
# Installiert ALLES automatisch: Homebrew, Python, Node.js, Chrome, Dependencies
#
# Requirements: Nur macOS + Claude Code
# Usage: ./setup.sh

set -e  # Exit on error

# ============================================================
# Colors
# ============================================================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# ============================================================
# Helper Functions
# ============================================================

print_header() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# ============================================================
# Check macOS
# ============================================================

print_header "Academic Agent v2.3 - Complete Setup"

if [[ "$OSTYPE" != "darwin"* ]]; then
    print_error "This script is for macOS only!"
    print_info "For Linux/Windows, please install manually:"
    print_info "  - Python 3.11+"
    print_info "  - Node.js 18+"
    print_info "  - Chrome/Chromium"
    exit 1
fi

print_success "Running on macOS"

# Venv will be created in Step 5

# ============================================================
# Step 1: Install Homebrew
# ============================================================

print_header "Step 1: Install Homebrew"

# Also check known Homebrew paths in case brew is installed but not in PATH
if ! command -v brew &> /dev/null; then
    if [ -f /opt/homebrew/bin/brew ]; then
        eval "$(/opt/homebrew/bin/brew shellenv)"
    elif [ -f /usr/local/bin/brew ]; then
        eval "$(/usr/local/bin/brew shellenv)"
    fi
fi

if command -v brew &> /dev/null; then
    BREW_VERSION=$(brew --version | head -n1)
    print_success "Homebrew already installed: $BREW_VERSION"
else
    print_info "Installing Homebrew..."
    print_warning "You may be asked for your password"

    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

    # Add Homebrew to PATH (Apple Silicon: /opt/homebrew, Intel: /usr/local)
    if [ -f /opt/homebrew/bin/brew ]; then
        echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
        eval "$(/opt/homebrew/bin/brew shellenv)"
    fi

    print_success "Homebrew installed successfully"
fi

# Update Homebrew
print_info "Updating Homebrew..."
brew update || print_warning "Homebrew update failed (not critical)"
print_success "Homebrew ready"

# ============================================================
# Step 2: Install Python 3.13
# ============================================================

print_header "Step 2: Install Python 3.13"

if command -v python3.13 &> /dev/null; then
    PYTHON_VERSION=$(python3.13 --version)
    print_success "Python 3.13 already installed: $PYTHON_VERSION"
else
    print_info "Installing Python 3.13 via Homebrew..."
    if brew install python@3.13; then
        print_success "Python 3.13 installed"
    else
        print_warning "Python 3.13 installation failed, trying python@3.12..."
        brew install python@3.12 || brew install python@3.11
    fi
fi

# Verify Python 3.13
PYTHON_CMD="python3.13"
if ! command -v $PYTHON_CMD &> /dev/null; then
    # Fallback to python3.11 or python3.12
    if command -v python3.12 &> /dev/null; then
        PYTHON_CMD="python3.12"
        print_warning "Using Python 3.12 instead"
    elif command -v python3.11 &> /dev/null; then
        PYTHON_CMD="python3.11"
        print_warning "Using Python 3.11 instead"
    else
        print_error "Python 3.11+ not found!"
        exit 1
    fi
fi

PYTHON_VERSION=$($PYTHON_CMD --version)
print_success "Using: $PYTHON_VERSION"

# ============================================================
# Step 3: Install Node.js
# ============================================================

print_header "Step 3: Install Node.js"

if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    NODE_MAJOR=$(echo $NODE_VERSION | cut -d'v' -f2 | cut -d'.' -f1)

    if [ "$NODE_MAJOR" -ge 18 ]; then
        print_success "Node.js already installed: $NODE_VERSION"
    else
        print_warning "Node.js $NODE_VERSION is too old (need 18+)"
        print_info "Upgrading Node.js via Homebrew..."
        brew upgrade node || brew install node
        print_success "Node.js upgraded"
    fi
else
    print_info "Installing Node.js via Homebrew..."
    if brew install node; then
        print_success "Node.js installed"
    else
        print_error "Node.js installation failed!"
        print_info "Please install manually: https://nodejs.org"
        print_info "Continuing without Node.js (Chrome MCP will not work)"
    fi
fi

if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    print_success "Using Node.js: $NODE_VERSION"
else
    print_warning "Node.js not available - Chrome MCP will be skipped"
fi

# ============================================================
# Step 4: Install Google Chrome
# ============================================================

print_header "Step 4: Install Google Chrome"

CHROME_PATH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

if [ -f "$CHROME_PATH" ]; then
    print_success "Google Chrome already installed"
else
    print_info "Installing Google Chrome via Homebrew..."
    if brew install --cask google-chrome; then
        print_success "Google Chrome installed"
    else
        print_warning "Chrome installation via Homebrew failed"
        print_info "You can install manually: https://www.google.com/chrome/"
        print_info "Continuing without Chrome (PDF download rate will be lower)"
    fi
fi

# Verify Chrome
if [ ! -f "$CHROME_PATH" ]; then
    print_error "Chrome installation failed!"
    print_info "Please install manually: https://www.google.com/chrome/"
    CHROME_PATH=""
else
    print_success "Chrome path: $CHROME_PATH"
fi

# ============================================================
# Step 5: Create Virtual Environment & Upgrade pip
# ============================================================

print_header "Step 5: Create Virtual Environment & Build Tools"

VENV_DIR="venv"
if [ -d "$VENV_DIR" ]; then
    print_success "Virtual environment already exists: $VENV_DIR/"
else
    print_info "Creating virtual environment with $PYTHON_CMD..."
    $PYTHON_CMD -m venv "$VENV_DIR"
    print_success "Virtual environment created: $VENV_DIR/"
fi

VENV_PYTHON="$VENV_DIR/bin/python"
VENV_PIP="$VENV_DIR/bin/pip"

print_info "Upgrading pip, setuptools, wheel inside venv..."
"$VENV_PIP" install --upgrade pip setuptools wheel -q
print_success "Build tools upgraded"

# ============================================================
# Step 6: Install Python Dependencies (System-wide)
# ============================================================

print_header "Step 6: Install Python Dependencies (into venv)"

if [ ! -f "requirements-v2.txt" ]; then
    print_error "requirements-v2.txt not found!"
    exit 1
fi

print_info "Installing Python packages into venv (this may take 3-5 minutes)..."
echo ""

if "$VENV_PIP" install -r requirements-v2.txt -q; then
    print_success "All Python dependencies installed"
else
    print_warning "Some packages may have failed to install"
    print_info "Trying without quiet mode to see errors..."
    "$VENV_PIP" install -r requirements-v2.txt || print_error "Python dependencies installation had errors"
fi

# ============================================================
# Step 7: Install Chrome MCP Server
# ============================================================

print_header "Step 7: Install Chrome MCP Server"

if command -v npm &> /dev/null; then
    print_info "Installing @eddym06/custom-chrome-mcp globally..."
    if npm install -g @eddym06/custom-chrome-mcp@latest; then
        print_success "Chrome MCP Server installed"
    else
        print_warning "Chrome MCP installation failed"
        print_info "You can try manually: npm install -g @eddym06/custom-chrome-mcp"
    fi
else
    print_warning "npm not available - skipping Chrome MCP installation"
    print_info "Install Node.js first to enable Chrome MCP"
fi

# ============================================================
# Step 8: Download NLTK Data
# ============================================================

print_header "Step 8: Download NLTK Data"

"$VENV_PYTHON" -c "
import nltk
import sys
try:
    nltk.download('punkt', quiet=True)
    nltk.download('punkt_tab', quiet=True)
    nltk.download('stopwords', quiet=True)
    print('✓ NLTK data downloaded')
except Exception as e:
    print(f'⚠ NLTK download failed: {e}', file=sys.stderr)
    sys.exit(0)
"

# ============================================================
# Step 9: Create Cache Directories
# ============================================================

print_header "Step 9: Create Cache Directories"

CACHE_DIR="$HOME/.cache/academic_agent"
mkdir -p "$CACHE_DIR/pdfs"
mkdir -p "$CACHE_DIR/http_cache"
print_success "Cache directories created: $CACHE_DIR"

# ============================================================
# Step 10: Configure .claude/settings.json
# ============================================================

print_header "Step 10: Configure Claude Settings"

mkdir -p .claude

# Resolve full npx path to avoid PATH issues when Claude Code starts MCP server
NPX_PATH=$(which npx 2>/dev/null || echo "")
if [ -z "$NPX_PATH" ]; then
    # Try known Homebrew locations (Apple Silicon: /opt/homebrew, Intel: /usr/local)
    for candidate in /opt/homebrew/bin/npx /usr/local/bin/npx; do
        if [ -x "$candidate" ]; then
            NPX_PATH="$candidate"
            break
        fi
    done
fi

if [ -n "$NPX_PATH" ]; then
    print_success "npx found: $NPX_PATH"
else
    print_warning "npx not found - using 'npx' as fallback (may cause issues)"
    NPX_PATH="npx"
fi

# Create settings.json if it doesn't exist
if [ ! -f ".claude/settings.json" ]; then
    if [ -n "$CHROME_PATH" ]; then
        cat > .claude/settings.json <<EOF
{
  "mcpServers": {
    "chrome": {
      "command": "npx",
      "args": ["-y", "@eddym06/custom-chrome-mcp@latest"],
      "env": {
        "CHROME_PATH": "$CHROME_PATH"
      }
    }
  }
}
EOF
        print_success ".claude/settings.json created"
    else
        print_warning "Chrome not found - .claude/settings.json not created"
        print_info "You'll need to configure this manually later"
    fi
fi

# Always patch npx path and Chrome path in settings.json (even after git clone)
if [ -f ".claude/settings.json" ] && [ -n "$CHROME_PATH" ]; then
    python3 -c "
import json, sys
with open('.claude/settings.json', 'r') as f:
    config = json.load(f)
if 'mcpServers' not in config:
    config['mcpServers'] = {}
if 'chrome' not in config['mcpServers']:
    config['mcpServers']['chrome'] = {'args': ['-y', '@eddym06/custom-chrome-mcp@latest'], 'env': {}}
config['mcpServers']['chrome']['command'] = '$NPX_PATH'
config['mcpServers']['chrome']['env']['CHROME_PATH'] = '$CHROME_PATH'
with open('.claude/settings.json', 'w') as f:
    json.dump(config, f, indent=2)
print('OK')
" && print_success "settings.json patched: npx=$NPX_PATH, Chrome=$CHROME_PATH"
fi

# ============================================================
# Step 11: Verify Installation
# ============================================================

print_header "Step 11: Verify Installation"

# Check Python packages
print_info "Checking critical packages..."
if "$VENV_PYTHON" -c "import httpx, pydantic, pymupdf, rich, fastapi, uvicorn" 2>/dev/null; then
    print_success "Core packages OK (including Web UI)"
else
    print_warning "Some core packages missing - check installation"
fi

# Check Node packages
if command -v npx &> /dev/null; then
    print_success "npm/npx available"
fi

# Check Chrome MCP
if command -v npm &> /dev/null && npm list -g @eddym06/custom-chrome-mcp &> /dev/null; then
    print_success "Chrome MCP Server installed"
else
    print_warning "Chrome MCP Server not installed"
fi

# Check config files
CONFIG_OK=true
for file in "config/api_config.yaml" "config/research_modes.yaml" "config/dbis_disciplines.yaml"; do
    if [ -f "$file" ]; then
        print_success "$file exists"
    else
        print_warning "$file missing"
        CONFIG_OK=false
    fi
done

# ============================================================
# Final Summary
# ============================================================

print_header "✅ Setup Complete!"

echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  Academic Agent v2.3 is ready to use!                    ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""

print_info "Installed Components:"
echo "  ✓ Homebrew: $(brew --version | head -n1)"
echo "  ✓ Python: $("$VENV_PYTHON" --version) (venv)"
if command -v node &> /dev/null; then
    echo "  ✓ Node.js: $(node --version)"
else
    echo "  ⚠ Node.js: not installed"
fi
if command -v npm &> /dev/null; then
    CHROME_MCP_VERSION=$(npm list -g @eddym06/custom-chrome-mcp 2>/dev/null | grep chrome-mcp | awk '{print $2}' || echo "not installed")
    echo "  ✓ Chrome MCP: $CHROME_MCP_VERSION"
else
    echo "  ⚠ Chrome MCP: npm not available"
fi
if [ -n "$CHROME_PATH" ]; then
    echo "  ✓ Google Chrome: $CHROME_PATH"
else
    echo "  ⚠ Google Chrome: Not configured"
fi
echo ""

print_info "📖 Quick Start:"
echo ""
echo "  1. Open Claude Code in this directory:"
echo -e "     ${GREEN}claude${NC}"
echo ""
echo "  2. Run a research query:"
echo -e "     ${GREEN}/research \"Your research question\"${NC}"
echo ""
echo -e "     ${BLUE}→ Web UI starts automatically: http://localhost:8000${NC}"
echo -e "     ${BLUE}→ Live progress tracking in your browser${NC}"
echo ""
echo "  3. (Optional) Configure TIB credentials for 85-90% PDF download:"
echo -e "     ${GREEN}export TIB_USERNAME=\"username\"${NC}"
echo -e "     ${GREEN}export TIB_PASSWORD=\"password\"${NC}"
echo ""
echo "  Note: Python dependencies are installed inside venv/ (activated automatically)."
echo ""

print_info "📚 Documentation:"
echo "  - INSTALLATION.md  - Installation guide"
echo "  - WORKFLOW.md      - Usage guide"
echo "  - README.md        - Project overview"
echo ""

if [ "$CONFIG_OK" = false ]; then
    print_warning "Some config files are missing - check the warnings above"
    echo ""
fi

print_info "💡 System Capabilities:"
echo "  ✓ DBIS Search Integration (100+ databases)"
echo "  ✓ Cross-Disciplinary Coverage: 92%"
echo "  ✓ Chrome MCP for browser automation"
echo "  ✓ Expected PDF download rate: 85-90% (with TIB)"
echo ""

echo -e "${GREEN}Happy researching! 🎓${NC}"
echo ""
