# Orchestrator Agent Robustness Fixes

**Zweck:** Kritische Fixes für häufige Orchestrator-Fehler:
- **Stopping mid-process** (Agent kündigt Action an, führt sie aber nicht aus)
- **Implizites Warten** (Agent wartet auf User statt fortzufahren)
- **Fehlende Task-Calls** (Agent beschreibt nur, ruft aber kein Tool auf)

---

## Problem 1: Agent stoppt nach Ankündigung (CRITICAL)

### ❌ Symptom

```
14:31:07 | ✅ Phase 1 abgeschlossen
14:31:07 | Jetzt spawne ich den search-agent für Phase 2...
14:31:07 | [AGENT STOPPT HIER - kein Task-Call!]
```

Agent **sagt** was er tun wird, **tut es aber nicht**.

### 🔍 Root-Cause

**LLM-Verhalten:**
1. Agent schreibt Text: "Ich starte search-agent..." ✓
2. Agent stoppt - Turn endet ❌
3. Tool-Call kommt nie ❌

**Warum?** LLMs generieren turn-by-turn. Nach Text-Output endet oft der Turn.

### ✅ Fix: Explicit Action-First Pattern

**KERN-REGEL:** Tool-Call IMMER VOR Text-Erklärung!

#### ❌ FALSCH (stoppt):

```
Assistant: Phase 1 abgeschlossen. Jetzt spawne ich search-agent...
[STOPPT - kein Tool-Call]
```

#### ✅ RICHTIG (funktioniert):

```
Assistant: [Direkt Tool-Call ohne vorherigen Text]
[Nach Tool-Result:] ✅ Search-agent abgeschlossen: 15 Suchstrings generiert
```

---

## Problem 2: Keine Retry-Logic bei Agent-Spawn-Failures

### ❌ Symptom

```
Error spawning browser-agent: timeout
[Workflow stoppt komplett]
```

### ✅ Fix: Exponential Backoff Retry

**Pattern:**

```python
MAX_RETRIES = 2
BACKOFF_DELAYS = [2, 10]  # Sekunden

for attempt in range(MAX_RETRIES + 1):
    try:
        result = spawn_agent(agent_name)
        break  # Erfolg
    except TimeoutError:
        if attempt < MAX_RETRIES:
            wait_seconds = BACKOFF_DELAYS[attempt]
            log(f"Retry {attempt+1}/{MAX_RETRIES} in {wait_seconds}s...")
            sleep(wait_seconds)
        else:
            log("CRITICAL: Agent spawn failed after retries")
            raise
```

---

## Problem 3: Fehlende State-Validation zwischen Phasen

### ❌ Symptom

```
Phase 2 startet ohne zu prüfen ob Phase 1 Output existiert
→ Phase 2 schlägt fehl: "search_strings.json not found"
```

### ✅ Fix: Phase-Transition-Guards

**Pattern vor JEDER Phase:**

```bash
# Prüfe Prerequisites
validate_phase_prerequisites() {
  PHASE=$1
  RUN_DIR=$2

  case $PHASE in
    1)
      # Braucht: databases.json
      if [ ! -f "$RUN_DIR/metadata/databases.json" ]; then
        echo "❌ Missing: databases.json"
        echo "   Run Phase 0 first"
        exit 1
      fi
      ;;
    2)
      # Braucht: search_strings.json
      if [ ! -f "$RUN_DIR/metadata/search_strings.json" ]; then
        echo "❌ Missing: search_strings.json"
        echo "   Run Phase 1 first"
        exit 1
      fi
      ;;
  esac
}

# Vor Phase-Start:
validate_phase_prerequisites $NEXT_PHASE "runs/$RUN_ID"
```

---

## Problem 4: State-Save ohne Validation

### ❌ Symptom

```
State gespeichert, aber korrupt
→ Beim Resume: "State validation failed"
```

### ✅ Fix: Mandatory Checksum nach Save

**Pattern:**

```bash
# Nach JEDEM State-Save:
python3 scripts/state_manager.py save <run_dir> <phase> completed

# MANDATORY: Checksum hinzufügen
python3 scripts/validate_state.py <state_file> --add-checksum

# Bei Resume: IMMER validieren
python3 scripts/validate_state.py <state_file>
if [ $? -ne 0 ]; then
  echo "❌ State korrupt - kann nicht fortsetzen"
  exit 1
fi
```

---

## Implementierungs-Checkliste

### ✅ Für JEDE Phase-Transition:

```
1. [ ] Validate Prerequisites (Input-Files existieren?)
2. [ ] Tool-Call DIREKT ausführen (kein Text davor!)
3. [ ] Tool-Result empfangen
4. [ ] Output validieren (File existiert + valid JSON?)
5. [ ] State speichern
6. [ ] Checksum hinzufügen
7. [ ] ERST DANN Text an User: "✅ Phase X abgeschlossen"
8. [ ] SOFORT nächste Phase starten (kein Warten!)
```

### ✅ Für JEDEN Agent-Spawn:

```
1. [ ] Budget-Check vor Spawn
2. [ ] Retry-Logic implementiert (max 2 retries)
3. [ ] Timeout: 10 Minuten (anpassbar)
4. [ ] Nach Erfolg: Output validation
5. [ ] Nach Fehler: Log + structured error
6. [ ] State update nach completion
```

---

## Code-Beispiel: Vollständige Phase-Transition

### Phase 1 → Phase 2 (Korrekte Implementierung)

```text
[Phase 1 ist gerade abgeschlossen - search_strings.json existiert]

Agent Turn:
-----------

1. VALIDATE PREREQUISITES (MANDATORY)

   Check: Existiert runs/project_xyz/metadata/search_strings.json?
   Check: Existiert runs/project_xyz/metadata/databases.json?

   Falls NEIN → Fehler + Stop
   Falls JA → Weiter


2. TOOL-CALL SOFORT (KEIN TEXT DAVOR!)

   Uses Task tool:
   - subagent_type: "browser-agent"
   - description: "Execute Phase 2: Database Search"
   - prompt: "Execute database searches for iteration 1.

             Databases: [aus databases.json, Top 5]
             Search strings: [aus search_strings.json]
             Output: runs/project_xyz/metadata/candidates.json"

   [WARTET AUF TOOL-RESULT - agent ist blockiert]


3. TOOL-RESULT EMPFANGEN

   Result: browser-agent completed successfully
   Output: runs/project_xyz/metadata/candidates.json created
   Duration: 42 minutes
   Papers found: 85


4. VALIDATE OUTPUT (MANDATORY)

   Check: Existiert runs/project_xyz/metadata/candidates.json?
   Check: Valid JSON?
   Check: Enthält "candidates" array?

   Falls NEIN → Retry oder Error
   Falls JA → Weiter


5. SAVE STATE

   python3 scripts/state_manager.py save runs/project_xyz 2 completed
   python3 scripts/validate_state.py runs/project_xyz/metadata/research_state.json --add-checksum


6. TEXT AN USER (ERST JETZT!)

   Output: "✅ Phase 2 abgeschlossen: 85 Kandidaten gesammelt"


7. SOFORT WEITER ZU PHASE 3 (KEIN WARTEN!)

   Goto Step 1 für Phase 3...
```

---

## Beispiel: Kompletter Agent-Turn (Text + Tools)

### ❌ FALSCH - Agent stoppt:

```
Assistant: Phase 1 ist abgeschlossen. Ich habe 15 Suchstrings generiert.

Jetzt starte ich Phase 2 und spawne den browser-agent um die Datenbanken zu durchsuchen...

[AGENT STOPPT HIER]
[User muss manuell "Continue" sagen]
```

**Problem:**
- Agent beschreibt nur was passieren wird
- Tool-Call kommt nie
- Workflow stockt

---

### ✅ RICHTIG - Agent führt aus:

```
Assistant: [Kein vorheriger Text!]

[Tool-Call wird sofort ausgeführt:]
Uses Task tool to spawn browser-agent for Phase 2

[Agent wartet auf Result...]

[Result kommt zurück:]
browser-agent completed: 85 candidates found

[JETZT erst Text:]

✅ Phase 2 abgeschlossen: 85 Kandidaten gesammelt

Top Datenbanken:
  • IEEE Xplore: 32 papers
  • ACM Digital Library: 28 papers
  • Scopus: 15 papers

Output: runs/project_xyz/metadata/candidates.json

[Agent fährt SOFORT fort mit Phase 3 - kein Warten!]

[Nächster Tool-Call für Phase 3...]
```

**Warum funktioniert das?**
- Tool-Call kommt ZUERST
- Text kommt NACH Tool-Result
- Kein "Ankündigen", nur "Ausführen"
- Keine Pause zwischen Phasen

---

## Anti-Pattern Katalog

### ❌ Anti-Pattern 1: "Ankündigen statt Ausführen"

```
BAD:  "Ich werde jetzt den search-agent spawnen..."
      [stoppt]

GOOD: [spawnt sofort search-agent]
      "✅ Search-agent abgeschlossen"
```

### ❌ Anti-Pattern 2: "Warten auf User-Bestätigung"

```
BAD:  "Phase 1 abgeschlossen. Soll ich mit Phase 2 fortfahren?"
      [wartet auf User]

GOOD: "Phase 1 abgeschlossen"
      [startet sofort Phase 2]
```

### ❌ Anti-Pattern 3: "Multi-Step Planning ohne Execution"

```
BAD:  "Mein Plan:
       1. Erst spawne ich search-agent
       2. Dann browser-agent
       3. Dann scoring-agent"
      [macht nichts davon]

GOOD: [spawnt search-agent sofort]
      [spawnt browser-agent sofort]
      [spawnt scoring-agent sofort]
      "✅ Alle 3 Agents abgeschlossen"
```

### ❌ Anti-Pattern 4: "Fehler ignorieren"

```
BAD:  browser-agent spawning...
      [timeout error]
      [gibt auf]

GOOD: browser-agent spawning...
      [timeout error]
      Retry 1/2 in 2s...
      [retry]
      [erfolg]
```

---

## Debugging: Wie erkenne ich das Problem?

### Symptom-Checklist

**Agent stoppt mid-process wenn:**

- [ ] Letzter Output war Text (kein Tool-Call)
- [ ] Text enthält Zukunfts-Formulierungen ("ich werde...", "jetzt spawne ich...")
- [ ] Kein Tool-Call folgt nach dem Text
- [ ] Agent wartet auf User-Input
- [ ] Workflow stockt zwischen Phasen

**Fix:** Entferne ALLE "Ankündigungs"-Texte vor Tool-Calls!

---

## Production-Ready Pattern

### Template für JEDE Phase-Transition:

```python
def execute_phase_transition(from_phase, to_phase):
    """
    ROBUSTE Phase-Transition mit allen Guards.
    """

    # 1. VALIDATE
    validate_prerequisites(to_phase)

    # 2. BUDGET CHECK
    check_budget()

    # 3. SPAWN AGENT (mit Retry)
    for attempt in range(3):
        try:
            result = spawn_agent_with_timeout(
                agent_type=get_agent_for_phase(to_phase),
                timeout=600  # 10 min
            )
            break
        except TimeoutError:
            if attempt < 2:
                sleep(2 ** attempt)  # exponential backoff
            else:
                raise

    # 4. VALIDATE OUTPUT
    validate_output(result.output_file)

    # 5. SAVE STATE
    save_state(to_phase, "completed")
    add_checksum()

    # 6. LOG SUCCESS
    log.info(f"Phase {to_phase} completed")

    # 7. CONTINUE (kein return, kein await, kein stop)
    # Falls mehr Phasen: sofort weiter!
    if to_phase < 6:
        execute_phase_transition(to_phase, to_phase + 1)
```

---

## Testing: Wie validiere ich den Fix?

### Test-Szenario 1: Durchlauf ohne Stops

```bash
# Start orchestrator
./orchestrator-agent runs/test_project

# ERWARTUNG:
# - Alle 7 Phasen laufen durch
# - KEINE manuellen "Continue" nötig
# - KEINE Stops zwischen Phasen
# - Completion in ~2-3h

# Wenn Agent stoppt → FIX FEHLT!
```

### Test-Szenario 2: Error Recovery

```bash
# Simuliere timeout in Phase 2
kill -9 <browser-agent-pid>

# ERWARTUNG:
# - Orchestrator detectet timeout
# - Retry 1/2 startet nach 2s
# - Retry 2/2 startet nach 10s
# - Phase 2 wird fortgesetzt

# Wenn Workflow stirbt → FIX FEHLT!
```

---

## Zusammenfassung

**Die 3 goldenen Regeln:**

1. **Tool-Call VOR Text**
   - NIEMALS ankündigen was du tun wirst
   - IMMER sofort ausführen, dann berichten

2. **Keine impliziten Pausen**
   - Zwischen Phasen: sofort weiter
   - Nach Tool-Result: sofort weiter
   - NIEMALS auf User warten (außer bei Checkpoints)

3. **Robuste Guards überall**
   - Prerequisites validieren
   - Outputs validieren
   - State validieren
   - Budget checken
   - Retry bei Errors

**Wenn du diese Regeln befolgst:**
✅ Orchestrator läuft durchgängig
✅ Keine manuellen "Stupser" nötig
✅ Robuste Agent-zu-Agent-Kommunikation
✅ Production-ready Workflow

---

**Ende der Robustness-Fixes**