# Lösung: Live-Status-Anzeige

**Problem:** Keine Sichtbarkeit während Agent läuft (40 Minuten Stille)

**Ziel:** Live-Dashboard mit Fortschrittsanzeige

**Status:** ✅ IMPLEMENTIERT (2026-02-22)

**Implementierte Lösung:** Lösung A (tmux Auto-Split)

---

## Problem-Analyse

### Warum keine Live-Updates?

1. **Agent-Output unsichtbar:** Task() blockiert, kein stdout-Streaming
2. **State nur am Ende:** research_state.json erst bei Completion
3. **Kein Watcher-Prozess:** Niemand liest State-File live

---

## Lösung A: tmux Auto-Split (Empfohlen)

**Vorteile:** Einfach, keine Dependencies, native Terminal-Integration

### Schritt 1: Status-Watcher-Script

```bash
#!/bin/bash
# scripts/status_watcher.sh

RUN_ID=$1
STATE_FILE="runs/$RUN_ID/metadata/research_state.json"
LOG_FILE="runs/$RUN_ID/logs/orchestrator.log"

while true; do
    clear
    echo "╔════════════════════════════════════════╗"
    echo "║   ACADEMIC AGENT - LIVE STATUS        ║"
    echo "╚════════════════════════════════════════╝"
    echo ""

    if [ -f "$STATE_FILE" ]; then
        # Parse JSON
        STATUS=$(jq -r '.status // "unknown"' $STATE_FILE 2>/dev/null)
        PHASE=$(jq -r '.current_phase // "N/A"' $STATE_FILE 2>/dev/null)
        PAPERS=$(jq -r '.progress_tracking.papers_processed // 0' $STATE_FILE 2>/dev/null)
        CITATIONS=$(jq -r '.progress_tracking.citations_found // 0' $STATE_FILE 2>/dev/null)
        DURATION=$(jq -r '.total_duration_minutes // 0' $STATE_FILE 2>/dev/null)

        echo "Run ID: $RUN_ID"
        echo "Status: $STATUS"
        echo "Phase: $PHASE/7"
        echo ""
        echo "Progress:"
        echo "  Papers: $PAPERS"
        echo "  Citations: $CITATIONS"
        echo "  Duration: ${DURATION} min"
    else
        echo "⏳ Warte auf State-File..."
        echo ""
        echo "Run: $RUN_ID"
    fi

    echo ""
    echo "─────────────────────────────────────────"
    echo "Letzte Log-Einträge:"
    if [ -f "$LOG_FILE" ]; then
        tail -n 5 "$LOG_FILE" | sed 's/^/  /'
    else
        echo "  (Noch keine Logs)"
    fi

    echo ""
    echo "Aktualisiert: $(date '+%H:%M:%S')"
    sleep 2
done
```

### Schritt 2: tmux-Integration in academicagent Skill

```bash
# In .claude/skills/academicagent.sh

#!/bin/bash

RUN_ID="$1"

# Prüfe ob in tmux
if [ -z "$TMUX" ]; then
    echo "🖥️   Starte tmux für Live-Status..."

    # Erstelle tmux Session
    tmux new-session -d -s academic_$RUN_ID

    # Split vertical
    tmux split-window -h -t academic_$RUN_ID

    # Links: Main Process
    tmux send-keys -t academic_$RUN_ID:0.0 \
        "cd $(pwd) && /academicagent --resume $RUN_ID" C-m

    # Rechts: Status Watcher
    tmux send-keys -t academic_$RUN_ID:0.1 \
        "bash scripts/status_watcher.sh $RUN_ID" C-m

    # Attach
    tmux attach -t academic_$RUN_ID

    exit 0
fi

# Ansonsten: Normale Execution
# ... (aktueller Code)
```

### Schritt 3: State häufiger schreiben

```markdown
# In orchestrator-agent.md ergänzen:

## Incremental State Updates

Nach JEDEM Sub-Task (nicht nur am Ende):

```bash
# Update State
jq '.current_phase = 2 | .status = "running"' research_state.json > tmp && mv tmp research_state.json

# Warte 2 Sekunden damit Watcher anzeigen kann
sleep 2
```

Schreibe State:
- Am Anfang jeder Phase
- Nach jedem Database-Search (papers_processed++)
- Nach jedem Quote (citations_found++)
- Bei Errors
- Am Ende
```

---

## Lösung B: Web-Dashboard

**Vorteile:** Schönes UI, Graphen, Multi-User

### Quick Implementation

```python
# scripts/dashboard_server.py
from flask import Flask, jsonify, render_template_string
import json
import os

app = Flask(__name__)

HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Academic Agent Status</title>
    <meta http-equiv="refresh" content="2">
    <style>
        body { font-family: monospace; background: #1e1e1e; color: #d4d4d4; padding: 20px; }
        .box { border: 1px solid #555; padding: 15px; margin: 10px 0; }
        .progress { background: #333; height: 20px; }
        .progress-bar { background: #0e639c; height: 100%; }
    </style>
</head>
<body>
    <h1>🔍 Academic Agent - Live Status</h1>
    <div class="box">
        <h2>Run: {{ run_id }}</h2>
        <p>Status: {{ state.status }}</p>
        <p>Phase: {{ state.current_phase }}/7</p>
        <div class="progress">
            <div class="progress-bar" style="width: {{ (state.current_phase / 7 * 100)|int }}%"></div>
        </div>
    </div>
    <div class="box">
        <h2>Progress</h2>
        <p>Papers: {{ state.progress_tracking.papers_processed }}</p>
        <p>Citations: {{ state.progress_tracking.citations_found }}</p>
        <p>Duration: {{ state.total_duration_minutes }} min</p>
    </div>
</body>
</html>
'''

@app.route('/status/<run_id>')
def status(run_id):
    state_file = f'runs/{run_id}/metadata/research_state.json'
    with open(state_file) as f:
        state = json.load(f)
    return render_template_string(HTML, run_id=run_id, state=state)

if __name__ == '__main__':
    app.run(port=5555)
```

```bash
# In academicagent Skill:
python3 scripts/dashboard_server.py &
DASHBOARD_PID=$!
open "http://localhost:5555/status/$RUN_ID"

# ... Run orchestrator ...

kill $DASHBOARD_PID
```

---

## Lösung C: Einfaches Tail (Minimal)

```bash
# In academicagent Skill:

echo "📋 Zeige Live-Logs (Strg+C zum Verstecken)..."
tail -f "runs/$RUN_ID/logs/orchestrator.log" &
TAIL_PID=$!

# Run orchestrator
# ...

kill $TAIL_PID 2>/dev/null
```

---

## Empfehlung: Lösung A (tmux)

**Warum:**
- ✅ Einfach zu implementieren (2 Files)
- ✅ Keine Dependencies (tmux meist vorhanden)
- ✅ Native Terminal-Erfahrung
- ✅ Status UND Logs sichtbar

**Implementierung:** 1-2 Stunden

---

**Siehe auch:**
- [fix-agent-spawning.md](./fix-agent-spawning.md)
- [setup-agent-optimization.md](./setup-agent-optimization.md)
