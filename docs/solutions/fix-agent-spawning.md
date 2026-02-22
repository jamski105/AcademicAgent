# Lösung: Agent-Spawning-Problem

**Problem:** Orchestrator-agent spawnt keine Sub-Agents (browser-agent, scoring-agent, extraction-agent)

**Impact:** Keine echte Datenbanksuche, nur synthetische Demo-Daten

---

## Diagnose

### Schritt 1: Prüfe orchestrator-agent.md

```bash
# Prüfe ob Task() Tool verfügbar ist:
grep -A 5 "^tools:" .claude/agents/orchestrator-agent.md
```

**Erwartet:**
```yaml
tools:
  - Read
  - Grep
  - Glob
  - Bash
  - Task   # ← Muss vorhanden sein!
  - Write
```

### Schritt 2: Prüfe ob Task() in Anweisungen erwähnt wird

```bash
grep -n "Task(" .claude/agents/orchestrator-agent.md | head -5
```

**Sollte zeigen:** Zeilen mit Task()-Beispielen (ca. Zeile 196, 270, 850)

### Schritt 3: Prüfe Logs auf Task-Aufrufe

```bash
# Suche nach Task-Spawns im letzten Run:
grep -r "Task\|spawning\|browser-agent" runs/2026-02-22_09-59-07/logs/
```

**Wenn leer:** Orchestrator hat nie versucht, Sub-Agents zu spawnen

---

## Root Causes (mögliche)

### Ursache 1: Agent ignoriert Instruktionen

**Symptom:** Orchestrator hat alle Anweisungen, nutzt sie aber nicht

**Warum passiert das?**
- Instruktionen zu lang (1400+ Zeilen)
- Agent "überfliegt" und generiert direkt Output
- Keine explizite Validierung dass Task() genutzt wurde

**Fix:** Vereinfache Kern-Anweisungen

```markdown
# In orchestrator-agent.md ganz oben einfügen:

## KRITISCHE REGEL - NIEMALS UMGEHEN

**Du MUSST für jede Phase den entsprechenden Sub-Agent spawnen:**

Phase 2 (Database Search):
→ SPAWN: browser-agent via Task()
→ NIEMALS: Direkt candidates.json generieren

Phase 3 (Scoring):
→ SPAWN: scoring-agent via Task()
→ NIEMALS: Direkt ranked_candidates.json generieren

Phase 4 (Extraction):
→ SPAWN: extraction-agent via Task()
→ NIEMALS: Direkt quotes.json generieren

**DEMO-MODUS IST VERBOTEN.**
```

### Ursache 2: Task() im Agent-Kontext nicht verfügbar

**Symptom:** Tool ist definiert, aber wirft Error beim Aufruf

**Test:**
```bash
# Erstelle Test-Agent:
cat > .claude/agents/test-spawner.md << 'EOF'
name: test-spawner
tools:
  - Task
  - Write

description: Test if Task() works

## Task
Spawn a simple agent to test Task() functionality:

Task(
  subagent_type="Bash",
  description="Test spawn",
  prompt="Echo 'Hello from spawned agent'"
)
EOF

# Rufe ihn auf:
claude code task --agent test-spawner --prompt "Test Task() call"
```

**Wenn Error:** Task() ist im Agent-Kontext blockiert → SDK-Bug

### Ursache 3: Budget-Check verhindert Spawn

**Symptom:** `scripts/safe_bash.py` blockiert Task()-Aufrufe

**Test:**
```bash
# Prüfe ob Budget-Check vor Task() kommt:
grep -B 5 -A 5 "Task(" .claude/agents/orchestrator-agent.md | grep -i budget
```

**Wenn Budget-Check VOR Task():**
```python
# ALT (könnte blockieren):
result = safe_bash("check_budget.sh")
if result.return_code != 0:
    # Agent gibt auf und macht Demo-Daten
    generate_synthetic_data()

# NEU (Fail-Safe):
result = safe_bash("check_budget.sh")
if result.return_code != 0:
    raise Exception("Budget exhausted - cannot continue")
    # Nie in Demo-Modus fallen!
```

---

## Lösungen

### Lösung A: Explizite Task()-Validierung

Füge in [orchestrator-agent.md](../../.claude/agents/orchestrator-agent.md) ein:

```markdown
## Phase Execution Validation

Nach JEDER Phase:

1. Prüfe ob Sub-Agent gespawnt wurde:
   ```bash
   if [ ! -f "$PHASE_MARKER" ]; then
       echo "ERROR: Sub-Agent wurde nicht gespawnt!"
       exit 1
   fi
   ```

2. Schreibe Marker-File:
   ```bash
   # In jedem Task()-Aufruf:
   Task(...)
   echo "spawned" > runs/$RUN_ID/metadata/.phase_2_spawned
   ```

3. Validiere Output:
   ```bash
   if [ ! -f "candidates.json" ]; then
       echo "ERROR: Sub-Agent hat kein Output produziert!"
       exit 1
   fi
   ```
```

### Lösung B: Direkt browser-agent nutzen (Bypass)

Wenn orchestrator nicht funktioniert, umgehe ihn:

```bash
# Erstelle neues Skill: /search-directly

#!/bin/bash
# .claude/skills/search-directly.sh

RUN_ID=$(ls -t runs/ | head -1)
SEARCH_STRINGS="runs/$RUN_ID/metadata/search_strings.json"

# Spawn browser-agent direkt:
claude code task \
  --agent browser-agent \
  --prompt "Execute Phase 2: Database Search

Run ID: $RUN_ID
Search strings: $SEARCH_STRINGS

For each database (ACM, IEEE, Scopus):
1. Open via DBIS
2. Execute search with query
3. Download first 100 results
4. Save to candidates.json
5. Download PDFs to runs/$RUN_ID/downloads/

CRITICAL: Use real databases, NO synthetic data!"
```

### Lösung C: Verbose-Mode für Debugging

Füge Debug-Output hinzu:

```markdown
# In orchestrator-agent.md:

## Debug Mode

Setze VERBOSE=1 für detailliertes Logging:

```bash
export VERBOSE=1
export DEBUG_TASK_CALLS=1

# Vor jedem Task():
echo "[DEBUG] About to spawn: $AGENT_TYPE"
echo "[DEBUG] Prompt: $PROMPT"

# Nach jedem Task():
echo "[DEBUG] Task returned: $RESULT"
echo "[DEBUG] Output files:"
ls -lh runs/$RUN_ID/metadata/
```

Dann Run mit:
```bash
VERBOSE=1 /academicagent --resume 2026-02-22_09-59-07
```

---

## Test-Prozedur

Nach dem Fix:

### 1. Teste einzelnen Agent-Spawn

```bash
# Manueller Test:
claude code task \
  --agent browser-agent \
  --prompt "Test: Open ACM Digital Library via DBIS"
```

**Erwartung:**
- Chrome-Fenster öffnet sich
- Navigation zu DBIS
- ACM wird geöffnet
- Terminal zeigt Progress

### 2. Teste orchestrator mit einem Search-String

```bash
# Erstelle minimal-config:
cat > /tmp/test_config.json << EOF
{
  "research_question": "Test",
  "keywords": ["test"],
  "databases": ["ACM"],
  "target_citations": 1
}
EOF

# Run orchestrator:
claude code task \
  --agent orchestrator-agent \
  --prompt "Execute ONLY Phase 2 with config: /tmp/test_config.json"
```

**Erwartung:**
- orchestrator spawnt browser-agent
- Browser-Fenster öffnet sich
- 1 Paper wird gesucht
- candidates.json enthält ECHTES Paper

### 3. Teste kompletten Workflow

```bash
/academicagent --quick
```

**Erwartung:**
- Setup-Agent: 2-3 Fragen (nicht 10!)
- Orchestrator spawnt 3 Sub-Agents
- Chrome-Fenster öffnet sich für Phase 2
- PDFs in downloads/ vorhanden
- Quotes haben echte Seitenzahlen

---

## Erfolgs-Kriterien

✅ **Fix erfolgreich wenn:**

1. `grep "Task(" runs/*/logs/orchestrator.log` zeigt 3+ Aufrufe
2. `ls runs/*/logs/browser_*.log` existiert
3. `ls runs/*/downloads/*.pdf` zeigt PDFs
4. Chrome-Fenster wird während Run sichtbar
5. Keine synthetischen DOIs (10.1145/SYNTHETIC.*)

❌ **Fix fehlgeschlagen wenn:**

1. Keine Task()-Aufrufe in Logs
2. candidates.json hat "SYNTHETIC" in DOIs
3. downloads/ Ordner leer
4. Kein Chrome-Fenster sichtbar

---

## Fallback-Plan

Wenn alle Fixes fehlschlagen:

**Plan B: Manuelle Phase-Execution**

```bash
# 1. Setup (funktioniert)
/academicagent --setup-only

# 2. Search (manuell via direktem Agent)
./scripts/manual_search.sh runs/LATEST/

# 3. Scoring (direkter Agent)
claude code task --agent scoring-agent --prompt "Score: runs/LATEST/metadata/candidates.json"

# 4. Extraction (direkter Agent)
claude code task --agent extraction-agent --prompt "Extract: runs/LATEST/metadata/ranked_candidates.json"

# 5. Output (funktioniert)
./scripts/generate_outputs.sh runs/LATEST/
```

---

**Nächste Schritte:**
1. Teste Lösung A (Validierung)
2. Falls fehlgeschlagen: Lösung B (Bypass)
3. Falls fehlgeschlagen: Lösung C (Debug-Mode)
4. Falls alles fehlgeschlagen: Plan B (Manuell)

**Siehe auch:**
- [setup-agent-optimization.md](./setup-agent-optimization.md) - Fragen reduzieren
- [live-status-implementation.md](./live-status-implementation.md) - Status-Anzeige
