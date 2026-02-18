# 🤖 Agent-Entwicklung

Dieser Guide erklärt wie man neue Agents für AcademicAgent entwickelt.

## Agent SDK Grundlagen

AcademicAgent nutzt das **Claude Agent SDK** (Teil von Claude Code). Agents sind Markdown-Dateien mit System-Prompts und Tool-Definitionen.

### Agent-Struktur

```markdown
<!-- .claude/agents/my-agent.md -->

# Agent Name

Short description of what this agent does.

## Capabilities

- Capability 1
- Capability 2

## Tools Available

- Tool1
- Tool2

## Instructions

Detailed instructions for how to accomplish tasks...

### Example

Example usage...

## Important Notes

- Note 1
- Note 2
```

---

## Bestehende Agents

### 1. Setup-Agent

**Datei:** `.claude/agents/setup-agent.md`

**Zweck:** Interaktive Recherche-Konfiguration erstellen

**Tools:**
- `Read` - Template lesen
- `Write` - Konfig schreiben
- `AskUserQuestion` - User nach Parametern fragen

**Beispiel-Flow:**
```
1. Lies config template
2. Frage User nach Forschungsfrage
3. Frage nach Keywords
4. Frage nach Disziplinen
5. Schreibe config/[name].md
```

### 2. Browser-Agent

**Datei:** `.claude/agents/browser-agent.md`

**Zweck:** Browser-Automatisierung via CDP

**Tools:**
- `Bash` - CDP-Wrapper aufrufen
- `Read` - Datenbank-Configs lesen
- `Grep` - Selektoren suchen

**Besonderheiten:**
- Muss DBIS navigieren können
- Kennt Datenbank-spezifische Selektoren
- Handle Login/CAPTCHA-Anforderungen

**Beispiel-Implementierung:**
```python
# Browser-Agent ruft auf:
python3 scripts/cdp_wrapper.py navigate "https://ieeexplore.ieee.org"
python3 scripts/cdp_wrapper.py search "DevOps Governance"
python3 scripts/cdp_wrapper.py download_pdf "https://..." "output.pdf"
```

### 3. Search-Agent

**Datei:** `.claude/agents/search-agent.md`

**Zweck:** Datenbank-spezifische Suchstrings generieren

**Tools:**
- `Read` - Keywords und DB-Configs lesen
- `Write` - Suchstrings schreiben
- `Grep` - Syntax-Rules finden

**Algorithmus:**
```
1. Lade Keywords (Primary, Secondary, Related)
2. Für jede Datenbank:
   a. Lade Syntax-Rules
   b. Baue Boolean Query
   c. Füge Synonyme hinzu
   d. Validiere Syntax
3. Schreibe search_strings.json
```

### 4. Scoring-Agent

**Datei:** `.claude/agents/scoring-agent.md`

**Zweck:** 5D-Bewertung aller Kandidaten

**Tools:**
- `Read` - Kandidaten lesen
- `Bash` - Python-Scoring-Script aufrufen
- `Write` - Ranked Liste schreiben

**5D-Implementation:**
```python
# Scoring-Agent ruft auf:
python3 scripts/score_candidates.py \
  --candidates runs/[id]/metadata/candidates.json \
  --keywords runs/[id]/metadata/config.md \
  --output runs/[id]/metadata/ranked_candidates.json
```

### 5. Extraction-Agent

**Datei:** `.claude/agents/extraction-agent.md`

**Zweck:** Zitate aus PDFs extrahieren

**Tools:**
- `Bash` - pdftotext aufrufen
- `Read` - PDF-Text lesen
- `Write` - quote_library.json schreiben

**Algorithmus:**
```
1. Für jedes PDF:
   a. pdftotext -layout pdf.pdf text.txt
   b. Lies Text
   c. Finde Absätze mit Keywords
   d. Extrahiere Zitat + Kontext + Seitenzahl
   e. Berechne Relevanz-Score
2. Gruppiere nach Kategorie
3. Schreibe quote_library.json
```

---

## Neuen Agent erstellen

### Schritt 1: Agent-Datei anlegen

```bash
touch .claude/agents/my-new-agent.md
```

### Schritt 2: System-Prompt schreiben

```markdown
# My New Agent

You are a specialized agent for [specific task].

## Your Role

You will be invoked by the Orchestrator to perform [task description].

## Tools Available

You have access to:
- `Bash` - Execute shell commands
- `Read` - Read files
- `Write` - Write files
- `Grep` - Search in files
- [Other tools...]

## Task Instructions

When invoked, you will receive:
- Input: [description]
- Expected Output: [description]

Your workflow:
1. [Step 1]
2. [Step 2]
3. [Step 3]

## Output Format

You must output a JSON file at [path] with structure:
```json
{
  "status": "success",
  "output": {...},
  "metrics": {...}
}
```

## Error Handling

If errors occur:
- Retry up to 3 times with exponential backoff
- If still failing, output status "failed" with error details
- Log all errors to [log path]

## Examples

### Example 1: [Description]

Input:
```
[Input data]
```

Actions:
1. [Action 1]
2. [Action 2]

Output:
```json
[Output data]
```

## Important Notes

- [Important note 1]
- [Important note 2]
```

### Schritt 3: Agent in Orchestrator integrieren

```markdown
<!-- .claude/skills/academicagent/SKILL.md -->

## Phase X: [New Phase]

Use the Task tool to invoke my-new-agent:

```json
{
  "description": "Perform [task]",
  "prompt": "Execute [task] with inputs: ${inputs}. Output to [path].",
  "subagent_type": "my-new-agent"
}
```

Wait for completion. Read output from [path].

Validate output:
- Check status == "success"
- Validate required fields present
- [Other validations]

If failed:
- Retry up to 2 times
- If still failing, ask user for manual intervention

Proceed to Phase X+1.
```

### Schritt 4: Testen

```bash
# Test agent standalone
# In Claude Code Chat:
/my-new-agent

# Test mit Orchestrator
/academicagent
```

---

## Agent Best Practices

### 1. Klare Tool-Nutzung

✅ **DO:**
```markdown
Use the Read tool to read the configuration file at config/academic_context.md.

Extract the following fields:
- research_question
- keywords (primary, secondary)
- disciplines

Store in variables for later use.
```

❌ **DON'T:**
```markdown
Read the config somehow and get the data.
```

### 2. Strukturierte Outputs

✅ **DO:**
```python
# Agent schreibt strukturiertes JSON
{
  "status": "success",
  "phase": 0,
  "output": {
    "databases": [...]
  },
  "metrics": {
    "duration_seconds": 123,
    "count": 11
  },
  "errors": []
}
```

❌ **DON'T:**
```
Found 11 databases, they are listed below...
```

### 3. Idempotenz

Agents sollten idempotent sein (wiederholbare Ausführung):

✅ **DO:**
```markdown
Before starting, check if output file already exists:
- If exists and valid → Return cached result
- If exists but invalid → Delete and regenerate
- If not exists → Generate new
```

### 4. Logging

✅ **DO:**
```markdown
Log all actions to runs/[timestamp]/logs/phase_X.log:

```
[2026-02-18 14:30:00] INFO: Starting Phase X
[2026-02-18 14:30:05] INFO: Loaded 11 databases
[2026-02-18 14:30:10] ERROR: Database Y failed: timeout
[2026-02-18 14:30:15] INFO: Completed Phase X successfully
```
```

### 5. Error Handling

```markdown
Implement 3-tier error handling:

1. Retry-able errors (network, timeout):
   - Retry up to 3 times with exponential backoff
   - Log each retry attempt

2. Recoverable errors (missing input):
   - Ask user for manual input
   - Provide clear instructions

3. Fatal errors (invalid configuration):
   - Fail immediately with clear error message
   - Do not retry
```

---

## Prompt Engineering für Agents

### Prinzipien

1. **Spezifisch:** Exact tool names, file paths, commands
2. **Sequenziell:** Nummerierte Schritte
3. **Conditional:** "If X then Y, else Z"
4. **Validierend:** Immer Output validieren

### Template

```markdown
## Task: [Task Name]

### Input
You will receive:
- [Input 1]: [description] at [path]
- [Input 2]: [description] from [source]

### Processing Steps

1. **Load Inputs**
   ```
   Use Read tool to load [input 1] from [path]
   Parse JSON structure
   Validate required fields: [field1, field2]
   ```

2. **Process Data**
   ```
   For each item in [input]:
     - Apply transformation [X]
     - Calculate metric [Y]
     - Store result
   ```

3. **Validate Results**
   ```
   Check:
   - Result count > 0
   - All required fields present
   - No duplicate entries
   ```

4. **Write Output**
   ```
   Use Write tool to save to [path]
   Format: JSON with structure:
   {
     "status": "success",
     "output": [...]
   }
   ```

### Output
[Path and format description]

### Error Cases

- **If [error case 1]:**
  - Action: [recovery action]
  - Output: status "failed", reason [description]

- **If [error case 2]:**
  - Action: [recovery action]
  - Output: status "retry", reason [description]
```

---

## Agent-zu-Agent Kommunikation

### Via File System

Agents kommunizieren über gemeinsame Dateien:

```
Phase 0 (Browser-Agent)
  ↓ writes
runs/[id]/metadata/databases.json
  ↓ reads
Phase 1 (Search-Agent)
  ↓ writes
runs/[id]/metadata/search_strings.json
  ↓ reads
Phase 2 (Browser-Agent)
```

### Via Orchestrator

Orchestrator reicht Daten weiter:

```markdown
<!-- In Orchestrator -->

Phase 0 complete. Result: ${databases}

Pass to Phase 1:
{
  "prompt": "Generate search strings for databases: ${databases}",
  "subagent_type": "search-agent"
}
```

---

## Testing & Debugging

### Unit-Testing Agent Logic

Wenn Agent Python-Scripte aufruft:

```python
# tests/unit/test_scoring_agent.py

def test_calculate_5d_score():
    candidate = {
        'title': 'Test Paper',
        'year': 2023,
        'citations': 100,
        ...
    }

    score = calculate_5d_score(candidate)

    assert score['score'] > 0
    assert score['score'] <= 100
    assert 'breakdown' in score
```

### Integration-Testing Agents

```python
# tests/integration/test_agent_flow.py

def test_setup_agent_creates_valid_config():
    # Invoke setup-agent with test inputs
    result = invoke_agent(
        agent='setup-agent',
        inputs={'research_question': 'Test Question', ...}
    )

    # Validate output
    assert os.path.exists('config/test_config.md')

    with open('config/test_config.md') as f:
        content = f.read()
        assert 'Test Question' in content
```

### Manual Testing

```bash
# Teste Agent standalone
# In Claude Code Chat:
/my-agent

# Mit spezifischen Inputs:
/my-agent input1="value1" input2="value2"

# Prüfe Logs:
tail -f runs/[timestamp]/logs/my_agent.log
```

### Debugging mit Debug-Modus

```bash
# Aktiviere Debug-Modus
export ACADEMIC_AGENT_DEBUG=1

# Agent produziert jetzt ausführliche Logs
/my-agent
```

---

## Nächste Schritte

- **[Datenbanken hinzufügen](03-adding-databases.md)** - Neue DBs integrieren
- **[Testing](04-testing.md)** - Umfassende Test-Strategie
- **[Architektur](01-architecture.md)** - Zurück zur Architektur

**[← Zurück zum Developer Guide](README.md)**
