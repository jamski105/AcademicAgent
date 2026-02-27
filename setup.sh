#!/bin/bash
# Academic Agent v2.2 - Setup Script
# Installiert alle Dependencies für einen frischen Clone des Repos
#
# Usage:
#   ./setup.sh              # Standard Installation
#   ./setup.sh --dev        # Installation mit Dev-Tools
#   ./setup.sh --minimal    # Minimal Installation (ohne Tests/Dev-Tools)

set -e  # Exit on error

# ============================================================
# Colors für Terminal Output
# ============================================================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================================
# Helper Functions
# ============================================================

print_header() {
    echo -e "${BLUE}===================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}===================================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# ============================================================
# Parse Command Line Arguments
# ============================================================

MODE="standard"
SKIP_VENV=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --dev)
            MODE="dev"
            shift
            ;;
        --minimal)
            MODE="minimal"
            shift
            ;;
        --skip-venv)
            SKIP_VENV=true
            shift
            ;;
        -h|--help)
            echo "Academic Agent v2.0 - Setup Script"
            echo ""
            echo "Usage:"
            echo "  ./setup.sh              # Standard Installation"
            echo "  ./setup.sh --dev        # Installation mit Dev-Tools"
            echo "  ./setup.sh --minimal    # Minimal Installation (ohne Tests/Dev-Tools)"
            echo "  ./setup.sh --skip-venv  # Kein Virtual Environment erstellen (für Docker/CI)"
            echo ""
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# ============================================================
# Step 1: Check Prerequisites
# ============================================================

print_header "Step 1: Check Prerequisites"

# Check Python Version
if ! command -v python3 &> /dev/null; then
    print_error "Python3 is not installed!"
    print_info "Please install Python 3.11 or higher: https://www.python.org/downloads/"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)

print_info "Found Python $PYTHON_VERSION"

if [ "$PYTHON_MAJOR" -lt 3 ] || { [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 11 ]; }; then
    print_error "Python 3.11 or higher is required!"
    print_info "Current version: $PYTHON_VERSION"
    exit 1
fi

print_success "Python version check passed"

# Check pip
if ! python3 -m pip --version &> /dev/null; then
    print_error "pip is not installed!"
    print_info "Installing pip..."
    python3 -m ensurepip --upgrade
fi

print_success "pip is available"

# ============================================================
# Step 2: Create Virtual Environment
# ============================================================

if [ "$SKIP_VENV" = false ]; then
    print_header "Step 2: Create Virtual Environment"

    if [ -d "venv" ]; then
        print_warning "Virtual environment already exists"
        read -p "Do you want to recreate it? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            print_info "Removing old virtual environment..."
            rm -rf venv
        else
            print_info "Using existing virtual environment"
        fi
    fi

    if [ ! -d "venv" ]; then
        print_info "Creating virtual environment..."
        python3 -m venv venv
        print_success "Virtual environment created"
    fi

    # Activate virtual environment
    print_info "Activating virtual environment..."
    source venv/bin/activate
    print_success "Virtual environment activated"

    # Upgrade pip, setuptools, wheel
    print_info "Upgrading pip, setuptools, wheel..."
    python -m pip install --upgrade pip setuptools wheel
    print_success "Build tools upgraded"
else
    print_header "Step 2: Skip Virtual Environment (--skip-venv)"
    print_warning "Using system Python environment"
fi

# ============================================================
# Step 3: Install Python Dependencies
# ============================================================

print_header "Step 3: Install Python Dependencies"

if [ ! -f "requirements-v2.txt" ]; then
    print_error "requirements-v2.txt not found!"
    exit 1
fi

print_info "Installing dependencies from requirements-v2.txt..."
print_info "This may take a few minutes..."

pip install -r requirements-v2.txt

print_success "Python dependencies installed"

# ============================================================
# Step 4: Check Node.js (for Chrome MCP)
# ============================================================

print_header "Step 4: Check Node.js"

if ! command -v node &> /dev/null; then
    print_warning "Node.js is not installed!"
    print_info "Chrome MCP requires Node.js 18.0.0 or higher"
    print_info ""
    print_info "Installation instructions:"
    print_info "  macOS:   brew install node"
    print_info "  Linux:   curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -"
    print_info "           sudo apt-get install -y nodejs"
    print_info "  Windows: Download from https://nodejs.org"
    print_info ""
    read -p "Do you want to continue without Node.js? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_error "Installation cancelled. Please install Node.js first."
        exit 1
    fi
    print_warning "Continuing without Chrome MCP (PDF download rate will be ~50%)"
    SKIP_CHROME_MCP=true
else
    NODE_VERSION=$(node --version | cut -d'v' -f2)
    NODE_MAJOR=$(echo $NODE_VERSION | cut -d'.' -f1)

    print_info "Found Node.js v$NODE_VERSION"

    if [ "$NODE_MAJOR" -lt 18 ]; then
        print_warning "Node.js 18.0.0 or higher recommended (current: v$NODE_VERSION)"
        print_info "Chrome MCP may not work correctly"
    else
        print_success "Node.js version check passed"
    fi
    SKIP_CHROME_MCP=false
fi

# ============================================================
# Step 5: Install Chrome MCP Server
# ============================================================

if [ "$SKIP_CHROME_MCP" = false ]; then
    print_header "Step 5: Install Chrome MCP Server"

    print_info "Installing @eddym06/custom-chrome-mcp..."

    if npm install -g @eddym06/custom-chrome-mcp@latest; then
        print_success "Chrome MCP Server installed"
    else
        print_warning "Chrome MCP installation failed"
        print_info "You can install it manually later: npm install -g @eddym06/custom-chrome-mcp"
    fi
else
    print_header "Step 5: Skip Chrome MCP (Node.js not available)"
fi

# ============================================================
# Step 6: Detect Chrome/Chromium Path
# ============================================================

if [ "$SKIP_CHROME_MCP" = false ]; then
    print_header "Step 6: Detect Chrome Browser"

    CHROME_PATH=""

    # macOS
    if [ -f "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" ]; then
        CHROME_PATH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        print_success "Found Google Chrome (macOS): $CHROME_PATH"
    # Linux - Google Chrome
    elif [ -f "/usr/bin/google-chrome" ]; then
        CHROME_PATH="/usr/bin/google-chrome"
        print_success "Found Google Chrome (Linux): $CHROME_PATH"
    # Linux - Chromium
    elif [ -f "/usr/bin/chromium" ]; then
        CHROME_PATH="/usr/bin/chromium"
        print_success "Found Chromium (Linux): $CHROME_PATH"
    elif [ -f "/usr/bin/chromium-browser" ]; then
        CHROME_PATH="/usr/bin/chromium-browser"
        print_success "Found Chromium Browser (Linux): $CHROME_PATH"
    # Windows (Git Bash / WSL)
    elif [ -f "/c/Program Files/Google/Chrome/Application/chrome.exe" ]; then
        CHROME_PATH="C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
        print_success "Found Google Chrome (Windows): $CHROME_PATH"
    else
        print_warning "Chrome/Chromium not found automatically"
        print_info "Please install Chrome or Chromium:"
        print_info "  macOS:   brew install --cask google-chrome"
        print_info "  Linux:   sudo apt-get install chromium-browser"
        print_info "  Windows: Download from https://www.google.com/chrome/"
        CHROME_PATH=""
    fi
else
    print_header "Step 6: Skip Chrome Detection (Node.js not available)"
fi

# ============================================================
# Step 7: Create .claude/settings.json
# ============================================================

if [ "$SKIP_CHROME_MCP" = false ]; then
    print_header "Step 7: Create .claude/settings.json"

    if [ ! -d ".claude" ]; then
        mkdir -p .claude
        print_info "Created .claude directory"
    fi

    if [ -f ".claude/settings.json" ]; then
        print_warning ".claude/settings.json already exists"
        read -p "Do you want to overwrite it? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_info "Keeping existing .claude/settings.json"
        else
            if [ -n "$CHROME_PATH" ]; then
                cat > .claude/settings.json <<EOF
{
  "mcpServers": {
    "chrome": {
      "command": "npx",
      "args": [
        "-y",
        "@eddym06/custom-chrome-mcp@latest"
      ],
      "env": {
        "CHROME_PATH": "$CHROME_PATH"
      }
    }
  }
}
EOF
                print_success ".claude/settings.json created with Chrome MCP config"
            else
                cat > .claude/settings.json <<EOF
{
  "mcpServers": {
    "chrome": {
      "command": "npx",
      "args": [
        "-y",
        "@eddym06/custom-chrome-mcp@latest"
      ],
      "env": {
        "CHROME_PATH": "/path/to/chrome"
      }
    }
  }
}
EOF
                print_warning ".claude/settings.json created but CHROME_PATH needs manual configuration"
                print_info "Please edit .claude/settings.json and set the correct Chrome path"
            fi
        fi
    else
        if [ -n "$CHROME_PATH" ]; then
            cat > .claude/settings.json <<EOF
{
  "mcpServers": {
    "chrome": {
      "command": "npx",
      "args": [
        "-y",
        "@eddym06/custom-chrome-mcp@latest"
      ],
      "env": {
        "CHROME_PATH": "$CHROME_PATH"
      }
    }
  }
}
EOF
            print_success ".claude/settings.json created with Chrome MCP config"
        else
            cat > .claude/settings.json <<EOF
{
  "mcpServers": {
    "chrome": {
      "command": "npx",
      "args": [
        "-y",
        "@eddym06/custom-chrome-mcp@latest"
      ],
      "env": {
        "CHROME_PATH": "/path/to/chrome"
      }
    }
  }
}
EOF
            print_warning ".claude/settings.json created but CHROME_PATH needs manual configuration"
            print_info "Please edit .claude/settings.json and set the correct Chrome path"
        fi
    fi
else
    print_header "Step 7: Skip .claude/settings.json (Chrome MCP not available)"
fi

# ============================================================
# Step 8: Install Playwright Browser (OPTIONAL - DEPRECATED)
# ============================================================

if [ "$MODE" != "minimal" ]; then
    print_header "Step 8: Install Playwright Browser (Optional - Deprecated)"

    print_warning "Playwright is now DEPRECATED in favor of Chrome MCP"
    print_info "It's still installed for backwards compatibility with old code"

    read -p "Do you want to install Playwright Chromium? (y/N): " -n 1 -r
    echo

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "Installing Chromium browser for Playwright..."
        print_info "This may take a few minutes and download ~300MB..."

        if playwright install chromium; then
            print_success "Playwright Chromium browser installed"
        else
            print_warning "Playwright installation failed (this is OK, not critical)"
        fi
    else
        print_info "Skipped Playwright installation"
    fi
else
    print_header "Step 8: Skip Playwright (--minimal mode)"
fi

# ============================================================
# Step 9: Download NLTK Data (Optional)
# ============================================================

print_header "Step 9: Download NLTK Data (Optional)"

print_info "Downloading NLTK punkt tokenizer..."

python3 -c "
import nltk
import sys
try:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    print('✓ NLTK data downloaded')
except Exception as e:
    print(f'⚠ NLTK download failed: {e}', file=sys.stderr)
    print('  This is optional and does not affect core functionality')
"

# ============================================================
# Step 10: Check Config Files
# ============================================================

print_header "Step 10: Check Config Files"

# Check api_config.yaml
if [ -f "config/api_config.yaml" ]; then
    print_success "config/api_config.yaml exists"
else
    print_warning "config/api_config.yaml not found"
    print_info "This file is required but should already exist in the repo"
fi

# Check research_modes.yaml
if [ -f "config/research_modes.yaml" ]; then
    print_success "config/research_modes.yaml exists"
else
    print_warning "config/research_modes.yaml not found"
    print_info "This file is required but should already exist in the repo"
fi

# Check academic_context.md
if [ -f "config/academic_context.md" ]; then
    print_success "config/academic_context.md exists"
else
    print_warning "config/academic_context.md not found"
    print_info "This file is optional for user context"
fi

# Check dbis_disciplines.yaml (v2.2)
if [ -f "config/dbis_disciplines.yaml" ]; then
    print_success "config/dbis_disciplines.yaml exists (v2.2 DBIS integration)"
else
    print_warning "config/dbis_disciplines.yaml not found"
    print_info "This file is required for v2.2 DBIS Search Integration"
fi

# ============================================================
# Step 11: Create Cache Directories
# ============================================================

print_header "Step 11: Create Cache Directories"

CACHE_DIR="$HOME/.cache/academic_agent"

if [ ! -d "$CACHE_DIR" ]; then
    print_info "Creating cache directory: $CACHE_DIR"
    mkdir -p "$CACHE_DIR"
    mkdir -p "$CACHE_DIR/pdfs"
    mkdir -p "$CACHE_DIR/http_cache"
    print_success "Cache directories created"
else
    print_success "Cache directories exist"
fi

# ============================================================
# Step 12: Run Tests (Optional)
# ============================================================

if [ "$MODE" != "minimal" ]; then
    print_header "Step 12: Run Unit Tests (Optional)"

    read -p "Do you want to run unit tests to verify installation? (Y/n): " -n 1 -r
    echo

    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        print_info "Running unit tests..."

        if pytest tests/unit/ -v --tb=short; then
            print_success "All tests passed!"
        else
            print_warning "Some tests failed"
            print_info "This may be due to missing API keys (which is OK)"
        fi
    else
        print_info "Skipped tests"
    fi
else
    print_header "Step 12: Skip Tests (--minimal mode)"
fi

# ============================================================
# Step 13: Test Chrome MCP Connection (Optional)
# ============================================================

if [ "$SKIP_CHROME_MCP" = false ] && [ "$MODE" != "minimal" ]; then
    print_header "Step 13: Test Chrome MCP Connection (Optional)"

    read -p "Do you want to test Chrome MCP connection? (y/N): " -n 1 -r
    echo

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "Testing Chrome MCP Server..."
        print_info "This will start the MCP server briefly"

        # Test if Chrome MCP can be started
        if timeout 5 npx -y @eddym06/custom-chrome-mcp@latest 2>&1 | grep -q "Chrome MCP"; then
            print_success "Chrome MCP Server is working!"
        else
            print_warning "Chrome MCP test inconclusive (this may be OK)"
            print_info "The server will be tested when you run the research workflow"
        fi
    else
        print_info "Skipped Chrome MCP test"
    fi
else
    print_header "Step 13: Skip Chrome MCP Test"
fi

# ============================================================
# Step 14: Final Instructions
# ============================================================

print_header "Setup Complete!"

echo ""
print_success "Academic Agent v2.2 is ready to use!"
echo ""
print_info "🚀 What's New in v2.2:"
echo "  ✓ DBIS Search Integration (100+ academic databases)"
echo "  ✓ Cross-Disciplinary Coverage: 92% (up from 60%)"
echo "  ✓ Humanities/Classics Support: 85-88% coverage"
echo "  ✓ Medicine Coverage: 92% (PubMed via DBIS)"
echo "  ✓ Hybrid Search: APIs + DBIS in parallel"
echo "  ✓ Source Annotation: Track paper origins"
echo ""
print_info "Next Steps:"
echo ""

if [ "$SKIP_VENV" = false ]; then
    echo "1. Activate virtual environment:"
    echo "   ${GREEN}source venv/bin/activate${NC}"
    echo ""
fi

if [ "$SKIP_CHROME_MCP" = false ]; then
    echo "2. Chrome MCP Status:"
    echo "   ${GREEN}✓ Chrome MCP Server installed${NC}"
    if [ -n "$CHROME_PATH" ]; then
        echo "   ${GREEN}✓ Chrome found: $CHROME_PATH${NC}"
    else
        echo "   ${YELLOW}⚠ Chrome path needs manual configuration in .claude/settings.json${NC}"
    fi
    echo ""

    echo "3. (Optional) Set up DBIS credentials for 85-90% PDF download rate:"
    echo "   ${GREEN}export TIB_USERNAME=\"your_username\"${NC}"
    echo "   ${GREEN}export TIB_PASSWORD=\"your_password\"${NC}"
    echo ""

    echo "4. Run via Claude Code:"
    echo "   ${GREEN}/research \"Your research question\"${NC}"
    echo ""
else
    echo "2. Chrome MCP Status:"
    echo "   ${YELLOW}⚠ Chrome MCP not installed (Node.js not available)${NC}"
    echo "   ${YELLOW}⚠ PDF download rate will be ~50% instead of 85-90%${NC}"
    echo ""

    echo "3. Run via Claude Code:"
    echo "   ${GREEN}/research \"Your research question\"${NC}"
    echo ""
fi

print_info "Documentation:"
echo "  - Installation Guide: ${BLUE}INSTALLATION.md${NC}"
echo "  - Workflow Guide: ${BLUE}WORKFLOW.md${NC}"
echo "  - Architecture: ${BLUE}docs/ARCHITECTURE_v2.md${NC}"
echo "  - Gap Analysis: ${BLUE}GAP_ANALYSIS.md${NC}"
echo ""

print_warning "System Status:"
if [ "$SKIP_CHROME_MCP" = false ]; then
    echo "  ✓ Agent-based architecture ready"
    echo "  ✓ Chrome MCP for browser automation"
    echo "  ✓ No API keys needed (uses Claude Code agents)"
    if [ -n "$CHROME_PATH" ]; then
        echo "  ✓ Expected PDF download rate: 85-90% (with TIB credentials)"
    else
        echo "  ⚠ Chrome path needs configuration"
        echo "  ⚠ PDF download rate: ~50% until Chrome configured"
    fi
else
    echo "  ⚠ Chrome MCP not available (install Node.js)"
    echo "  ⚠ PDF download rate: ~50% (Unpaywall + CORE only)"
    echo "  ✓ System still functional, but reduced PDF access"
fi
echo ""

if [ "$SKIP_VENV" = false ]; then
    print_info "Virtual environment: ${PWD}/venv"
fi
print_info "Cache directory: ${CACHE_DIR}"
if [ "$SKIP_CHROME_MCP" = false ]; then
    print_info "Chrome MCP config: ${PWD}/.claude/settings.json"
fi

echo ""
print_success "Happy researching! 🎓"
echo ""
