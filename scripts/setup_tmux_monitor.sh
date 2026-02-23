#!/bin/bash
# Live-Status-Monitoring via tmux
# Version: 1.0.0 (2026-02-23)
# Usage: bash scripts/setup_tmux_monitor.sh <run-id>

set -euo pipefail

RUN_ID=${1:-}

[ -z "$RUN_ID" ] && {
    echo "❌ ERROR: RUN_ID erforderlich"
    echo "Usage: $0 <run-id>"
    exit 1
}

# Check tmux installiert
if ! command -v tmux &> /dev/null; then
    echo "❌ tmux nicht installiert"
    echo ""
    echo "Installation:"
    echo "  macOS:   brew install tmux"
    echo "  Ubuntu:  sudo apt install tmux"
    echo "  Arch:    sudo pacman -S tmux"
    exit 1
fi

# Check ob bereits in tmux
if [ -n "${TMUX:-}" ]; then
    echo "⚠️  Bereits in tmux-Session"
    echo "   Exit mit: Ctrl+B dann D"
    exit 1
fi

# Session Name (sanitized)
SESSION_NAME="academic_${RUN_ID//[^a-zA-Z0-9]/_}"

# Check Session existiert schon
if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
    echo "♻️  Session existiert bereits: $SESSION_NAME"
    echo "   Attachen..."
    tmux attach -t "$SESSION_NAME"
    exit 0
fi

echo "🖥️  Erstelle tmux Live-Monitor"
echo "   Session: $SESSION_NAME"
echo "   Run-ID: $RUN_ID"
echo ""

# Erstelle Session (detached)
tmux new-session -d -s "$SESSION_NAME" -x 200 -y 50

# Split horizontal (Links: Orchestrator Log, Rechts: Status Watch)
tmux split-window -h -t "$SESSION_NAME"

# Links: Orchestrator Log (tail -f)
tmux send-keys -t "$SESSION_NAME:0.0" \
    "echo '🎯 Orchestrator Log (Live)' && echo '' && tail -f runs/$RUN_ID/orchestrator.log 2>/dev/null || echo 'Warte auf Log...'" C-m

# Rechts: Status Watcher
tmux send-keys -t "$SESSION_NAME:0.1" \
    "bash scripts/status_watcher.sh $RUN_ID 2>/dev/null || watch -n 5 'cat runs/$RUN_ID/research_state.json 2>/dev/null | jq .'" C-m

# Pane-Titel setzen (falls tmux >=3.2)
tmux select-pane -t "$SESSION_NAME:0.0" -T "Orchestrator Log"
tmux select-pane -t "$SESSION_NAME:0.1" -T "Research State"

# Fokus auf linkes Pane
tmux select-pane -t "$SESSION_NAME:0.0"

echo "✅ tmux Session erstellt"
echo ""
echo "╭──────────────────────────────────────────────────────────────╮"
echo "│ 🎮 TMUX CONTROLS                                             │"
echo "├──────────────────────────────────────────────────────────────┤"
echo "│ Detach:      Ctrl+B, dann D                                  │"
echo "│ Switch Pane: Ctrl+B, dann Pfeiltasten                        │"
echo "│ Scroll:      Ctrl+B, dann [, dann Pfeiltasten, Q zum exit   │"
echo "│ Kill:        Ctrl+B, dann X (bestätigen)                     │"
echo "╰──────────────────────────────────────────────────────────────╯"
echo ""
echo "Attache in 2 Sekunden..."
sleep 2

# Attach zu Session
tmux attach -t "$SESSION_NAME"

# Cleanup nach Detach/Exit
echo ""
echo "👋 Session detached: $SESSION_NAME"
echo "   Re-attach mit: tmux attach -t $SESSION_NAME"
echo "   Kill mit:      tmux kill-session -t $SESSION_NAME"
