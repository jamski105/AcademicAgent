#!/bin/bash
# Auto-Launch Live Monitor in separatem Terminal
# Wird vom Orchestrator aufgerufen zu Beginn des Workflows

set -euo pipefail

RUN_ID=$1

if [ -z "$RUN_ID" ]; then
    echo "❌ Fehler: RUN_ID fehlt"
    echo "Usage: bash scripts/launch_live_monitor.sh <run-id>"
    exit 1
fi

REPO_DIR=$(cd "$(dirname "$0")/.." && pwd)
WATCHER_SCRIPT="$REPO_DIR/scripts/status_watcher.sh"

echo "╭────────────────────────────────────────────────────────────╮"
echo "│ 🖥️  Starte Live Monitor                                     │"
echo "├────────────────────────────────────────────────────────────┤"
echo "│ Run ID:     $RUN_ID                                        │"
echo "│ Script:     status_watcher.sh                              │"
echo "│ Mode:       Auto-Launch                                    │"
echo "╰────────────────────────────────────────────────────────────╯"
echo ""

# Detect OS and launch appropriate terminal
case "$(uname -s)" in
    Darwin)
        # macOS: Use osascript to open new Terminal window
        osascript -e "tell application \"Terminal\"
            do script \"cd '$REPO_DIR' && bash '$WATCHER_SCRIPT' '$RUN_ID'\"
            activate
        end tell" > /dev/null 2>&1 &

        echo "✅ Live Monitor gestartet in neuem Terminal-Fenster (macOS)"
        ;;

    Linux)
        # Linux: Try different terminal emulators
        if command -v gnome-terminal &> /dev/null; then
            gnome-terminal -- bash -c "cd '$REPO_DIR' && bash '$WATCHER_SCRIPT' '$RUN_ID'; exec bash" &
            echo "✅ Live Monitor gestartet in gnome-terminal"
        elif command -v konsole &> /dev/null; then
            konsole -e "cd '$REPO_DIR' && bash '$WATCHER_SCRIPT' '$RUN_ID'" &
            echo "✅ Live Monitor gestartet in konsole"
        elif command -v xterm &> /dev/null; then
            xterm -e "cd '$REPO_DIR' && bash '$WATCHER_SCRIPT' '$RUN_ID'" &
            echo "✅ Live Monitor gestartet in xterm"
        else
            echo "⚠️  Kein Terminal-Emulator gefunden"
            echo "   Starte manuell: bash scripts/status_watcher.sh $RUN_ID"
        fi
        ;;

    *)
        echo "⚠️  Unbekanntes OS: $(uname -s)"
        echo "   Starte manuell: bash scripts/status_watcher.sh $RUN_ID"
        ;;
esac

# Kurze Pause damit Terminal sich öffnet
sleep 1

echo ""
echo "╭────────────────────────────────────────────────────────────╮"
echo "│ ℹ️  Live Monitor läuft jetzt                                │"
echo "├────────────────────────────────────────────────────────────┤"
echo "│ • Zeigt Echtzeit-Updates                                   │"
echo "│ • Iterations-Fortschritt                                   │"
echo "│ • Budget-Tracking                                          │"
echo "│ • Live-Logs                                                │"
echo "│                                                            │"
echo "│ Schließe das Monitoring-Fenster NICHT während der         │"
echo "│ Recherche läuft.                                           │"
echo "╰────────────────────────────────────────────────────────────╯"
echo ""
