#!/bin/bash
# Wrapper-Script für academicagent
# Ermöglicht interaktiven TUI-Modus oder Standard-Workflow

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Farben für Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Zeige Banner
show_banner() {
    echo ""
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                                                              ║"
    echo "║           🎓 Academic Agent - Recherche-Assistent            ║"
    echo "║                                                              ║"
    echo "║                        Version 4.0                           ║"
    echo "║                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""
}

# Parse Arguments
INTERACTIVE_MODE=false
FORCE_CLI=false
RESUME_RUN=""

for arg in "$@"; do
    case $arg in
        --interactive|-i)
            INTERACTIVE_MODE=true
            shift
            ;;
        --cli)
            FORCE_CLI=true
            shift
            ;;
        --resume)
            RESUME_RUN="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --interactive, -i   Use interactive TUI mode (recommended)"
            echo "  --cli               Use classic CLI workflow"
            echo "  --resume <run-id>   Resume an existing research run"
            echo "  --help, -h          Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 --interactive              # Start interactive setup"
            echo "  $0 --resume 2026-02-22_10-30-00  # Resume a run"
            exit 0
            ;;
    esac
done

# Wenn keine Argumente, frage User
if [ "$INTERACTIVE_MODE" = false ] && [ "$FORCE_CLI" = false ] && [ -z "$RESUME_RUN" ]; then
    show_banner
    echo "Wie möchtest du fortfahren?"
    echo ""
    echo "  1) 🎨 Interaktiver Modus (TUI) - Empfohlen!"
    echo "     ↳ Benutzerfreundlich, geführter Setup mit Pfeiltasten"
    echo ""
    echo "  2) 💬 Chat-Modus (Standard)"
    echo "     ↳ Konversationell, via Claude Code Chat"
    echo ""
    echo "  3) 🔄 Fortsetzen"
    echo "     ↳ Existierenden Run fortsetzen"
    echo ""
    read -p "Deine Wahl [1-3]: " choice

    case $choice in
        1)
            INTERACTIVE_MODE=true
            ;;
        2)
            FORCE_CLI=true
            ;;
        3)
            echo ""
            read -p "Run-ID zum Fortsetzen: " RESUME_RUN
            ;;
        *)
            echo "${RED}❌ Ungültige Wahl. Beende.${NC}"
            exit 1
            ;;
    esac
fi

cd "$PROJECT_ROOT"

# Resume-Modus
if [ -n "$RESUME_RUN" ]; then
    echo "${BLUE}🔄 Setze Run fort: $RESUME_RUN${NC}"

    if [ ! -d "runs/$RESUME_RUN" ]; then
        echo "${RED}❌ Run nicht gefunden: runs/$RESUME_RUN${NC}"
        exit 1
    fi

    # Nutze das bestehende Resume-Script
    if [ -f "scripts/resume_research.sh" ]; then
        bash scripts/resume_research.sh "$RESUME_RUN"
    else
        echo "${RED}❌ Resume-Script nicht gefunden!${NC}"
        exit 1
    fi

    exit $?
fi

# Interaktiver TUI-Modus
if [ "$INTERACTIVE_MODE" = true ]; then
    echo "${BLUE}🎨 Starte interaktiven TUI-Modus...${NC}"
    echo ""

    # Prüfe ob Python und questionary verfügbar
    if ! command -v python3 &> /dev/null; then
        echo "${RED}❌ Python 3 nicht gefunden!${NC}"
        exit 1
    fi

    # Teste ob questionary installiert ist
    if ! python3 -c "import questionary" 2>/dev/null; then
        echo "${YELLOW}⚠️  questionary nicht installiert${NC}"
        echo ""
        echo "Installiere jetzt automatisch..."
        pip3 install questionary

        if [ $? -ne 0 ]; then
            echo "${RED}❌ Installation fehlgeschlagen!${NC}"
            echo "Bitte installiere manuell: pip3 install questionary"
            exit 1
        fi

        echo "${GREEN}✓ questionary erfolgreich installiert${NC}"
        echo ""
    fi

    # Starte Interactive Setup
    python3 scripts/interactive_setup.py
    exit $?
fi

# Standard CLI-Modus (via /academicagent Skill)
if [ "$FORCE_CLI" = true ]; then
    echo "${BLUE}💬 Starte Chat-Modus...${NC}"
    echo ""
    echo "Nutze den /academicagent Befehl in Claude Code Chat:"
    echo ""
    echo "  ${GREEN}/academicagent${NC}"
    echo ""
    echo "Oder rufe direkt auf:"
    echo "  claude code chat --message '/academicagent'"
    echo ""
    exit 0
fi

# Fallback - sollte nie erreicht werden
echo "${RED}❌ Unerwarteter Fehler im Workflow${NC}"
exit 1
