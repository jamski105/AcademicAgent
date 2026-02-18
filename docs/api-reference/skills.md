# 🎯 Skills API Reference

Dokumentation der Skill-Definitionen.

## /academicagent (Orchestrator-Skill)

**Datei:** `.claude/skills/academicagent/SKILL.md`

### Beschreibung

Haupt-Orchestrator-Skill der den gesamten 7-Phasen-Workflow koordiniert.

### Invocation

```bash
# In Claude Code Chat:
/academicagent
```

### Workflow-Phasen

#### Phase 0: DBIS-Navigation

**Dauer:** 15-20 Minuten
**Checkpoint:** ✅ Ja

**Prozess:**

1. Prüfe ob State existiert (Continuation)
2. Falls neue Recherche:
   - Erstelle Konfig via setup-agent ODER
   - Lade existierende Konfig
3. Invoke browser-agent: Task "navigate_dbis"
4. Warte auf Ergebnis (databases.json)
5. **CHECKPOINT:** Zeige User Datenbankliste
6. Validiere User-Approval
7. Save State: Phase 0 complete

#### Phase 1: Suchstring-Generierung

**Dauer:** 5-10 Minuten
**Checkpoint:** ✅ Ja

**Prozess:**

1. Lade Datenbanken von Phase 0
2. Invoke search-agent
3. Warte auf Ergebnis (search_strings.json)
4. **CHECKPOINT:** Zeige User Suchstrings
5. Validiere User-Approval
6. Save State: Phase 1 complete

#### Phase 2: Iterative Datenbanksuche

**Dauer:** 90-120 Minuten
**Checkpoint:** ❌ Nein

**Prozess:**

1. Lade Datenbanken und Suchstrings
2. Loop:
   ```
   iteration = 0
   while iteration < max_iterations:
     # Select next batch (5 DBs)
     batch = databases[iteration*5:(iteration+1)*5]

     # Invoke browser-agent für batch
     invoke browser-agent: Task "search_databases"

     # Warte auf Ergebnis
     candidates += result['candidates']

     # Check Target
     if len(candidates) >= target:
       break

     iteration += 1
   ```
3. Save State: Phase 2 complete

#### Phase 3: 5D-Bewertung & Ranking

**Dauer:** 20-30 Minuten
**Checkpoint:** ✅ Ja

**Prozess:**

1. Lade Kandidaten von Phase 2
2. Invoke scoring-agent
3. Warte auf Ergebnis (ranked_candidates.json)
4. **CHECKPOINT:** Zeige User Top 27 Kandidaten
5. User wählt Top 18
6. Save State: Phase 3 complete

#### Phase 4: PDF-Download

**Dauer:** 20-30 Minuten
**Checkpoint:** ❌ Nein

**Prozess:**

1. Lade ausgewählte Papers von Phase 3
2. Invoke browser-agent: Task "download_pdfs"
3. Monitor Progress (optionally show updates)
4. Warte auf Ergebnis
5. Save State: Phase 4 complete

#### Phase 5: Zitat-Extraktion

**Dauer:** 30-45 Minuten
**Checkpoint:** ✅ Ja

**Prozess:**

1. Lade PDFs von downloads/
2. Invoke extraction-agent
3. Warte auf Ergebnis (quote_library.json)
4. **CHECKPOINT:** Zeige User Beispiel-Zitate
5. Validiere Qualität
6. Save State: Phase 5 complete

#### Phase 6: Finalisierung

**Dauer:** 15-20 Minuten
**Checkpoint:** ✅ Ja

**Prozess:**

1. Generiere bibliography.bib:
   - Lies ranked_candidates.json
   - Konvertiere zu BibTeX-Format
   - Schreibe bibliography.bib

2. Generiere summary.md:
   - Statistiken sammeln
   - Top Papers listen
   - Empfehlungen generieren
   - Schreibe summary.md

3. **CHECKPOINT:** Zeige User finale Outputs
4. Validiere Vollständigkeit
5. Save State: Phase 6 complete
6. Mark Research: COMPLETE

### State-Management

**State-Datei:** `runs/[timestamp]/metadata/research_state.json`

```json
{
  "version": "3.0",
  "run_id": "2026-02-18_14-30-00",
  "current_phase": 3,
  "completed_phases": [0, 1, 2],
  "pending_phases": [3, 4, 5, 6],
  "config": {...},
  "phase_outputs": {
    "phase_0": {...},
    "phase_1": {...},
    "phase_2": {...}
  },
  "checksum": "sha256:..."
}
```

**State-Operations:**

```markdown
## Load or Initialize State

1. Check if runs/[timestamp]/ exists
2. If exists:
   - Load research_state.json
   - Validate checksum
   - Ask user: "Continue from Phase X?"
3. If not exists:
   - Create new run_id (timestamp)
   - Initialize empty state
   - Set current_phase = 0

## Save State (after each phase)

1. Update current_phase
2. Add to completed_phases
3. Add phase_output
4. Calculate checksum
5. Write atomically (temp file + rename)
6. Create backup
```

### Error Handling

**Retry Logic:**

```markdown
For each agent invocation:

1. Try invoke
2. If fails:
   - Log error
   - Check if retry-able:
     - Network error: RETRY (max 3)
     - Timeout: RETRY (max 2)
     - Invalid input: ASK USER
     - Fatal error: FAIL
3. If max retries exceeded:
   - Save error to state
   - Ask user for manual intervention
```

**Recovery:**

```markdown
If research interrupted:

1. User invokes /academicagent again
2. Orchestrator detects existing state
3. Prompts: "Resume from Phase X?"
4. If yes:
   - Load state
   - Validate integrity
   - Continue from next phase
5. If no:
   - Archive old run
   - Start new research
```

### Checkpoints

**Checkpoint-Flow:**

```markdown
At each checkpoint:

1. Present Information:
   - Clear heading: "📍 Checkpoint X: [Name]"
   - Summary of results
   - Options for user

2. Wait for User Input:
   - "approve" / "yes" → Continue
   - "reject" / "no" → Retry phase
   - "modify" → Allow modifications
   - "skip" → Skip (if applicable)

3. Validate & Continue:
   - Log user decision
   - Update state
   - Proceed to next phase
```

### Monitoring & Logging

**CDP-Health-Monitor:**

Läuft parallel alle 5 Minuten:

```markdown
While research active:

1. Check CDP connection (port 9222)
2. If not responding:
   - Log warning
   - Attempt restart
   - Wait 30 seconds
   - Retry connection
3. Check Chrome memory usage
4. If > 2GB:
   - Log warning
   - Consider restart
5. Log health status to cdp_health.log
```

### Invocation-Beispiele

**Neue Recherche:**

```
User: /academicagent

Orchestrator: Willkommen! Ich starte eine neue Literaturrecherche.

[Führt durch Setup oder lädt Konfig]

Orchestrator: Phase 0: DBIS-Navigation...
[15 Min später]

Orchestrator: 📍 Checkpoint 0: Datenbanken validieren
Gefundene Datenbanken (11):
1. IEEE Xplore (Score: 95)
2. ACM Digital Library (Score: 93)
...

Genehmigen? (ja/nein)

User: ja

Orchestrator: Phase 1: Suchstring-Generierung...
[...]
```

**Fortsetzung:**

```
User: /academicagent

Orchestrator: Ich habe einen unterbrochenen State gefunden:
Run: 2026-02-18_14-30-00
Zuletzt: Phase 2 (52 Kandidaten gefunden)

Fortsetzen mit Phase 3? (ja/nein)

User: ja

Orchestrator: Phase 3: 5D-Bewertung & Ranking...
[...]
```

---

## Parameter & Konfiguration

### Iterative Suchparameter

```yaml
# In research config oder defaults:

databases_per_iteration: 5      # DBs pro Iteration
target_candidates: 50            # Ziel-Anzahl Kandidaten
max_iterations: 5                # Max Iterationen
min_candidates_per_db: 3         # Skip unproduktive DBs
```

### Checkpoint-Konfiguration

```yaml
checkpoints:
  phase_0: true   # Datenbanken validieren
  phase_1: true   # Suchstrings freigeben
  phase_2: false  # Keine User-Interaktion
  phase_3: true   # Paper-Auswahl
  phase_4: false  # Keine User-Interaktion
  phase_5: true   # Zitatqualität prüfen
  phase_6: true   # Finale Bestätigung
```

### Timeout-Konfiguration

```yaml
timeouts:
  phase_0: 1200   # 20 Min
  phase_1: 600    # 10 Min
  phase_2: 7200   # 120 Min
  phase_3: 1800   # 30 Min
  phase_4: 1800   # 30 Min
  phase_5: 2700   # 45 Min
  phase_6: 1200   # 20 Min

  per_database: 900  # 15 Min pro DB
  per_pdf: 300       # 5 Min pro PDF
```

---

## Nächste Schritte

- **[Utilities Reference](utilities.md)** - Python-Module API
- **[Agents Reference](agents.md)** - Agent-Details

**[← Zurück zur API Reference](README.md)**
