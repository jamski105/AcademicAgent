# Phase Execution Template

**Version:** 1.0.0 (2026-02-23)
**Purpose:** Standard-Workflow für Orchestrator Phasen 0-6

---

## Standard-Ablauf (gilt für ALLE Phasen)

### Step 1: Prerequisites Check
```bash
# Prüfe ob alle Voraussetzungen erfüllt sind
phase_guard $PHASE_NUM $RUN_ID
```

### Step 2: Spawn Agent (Action-First!)
```bash
# KEIN TEXT vor diesem Tool-Call!
export CURRENT_AGENT="<agent-name>"

# Tool-Call SOFORT
Task(
  subagent_type="<agent-type>",
  prompt="<phase-specific-prompt>"
)
```

### Step 3: Validate Output
```bash
# Nach Tool-Result
validate_phase_output $PHASE_NUM $RUN_ID
```

### Step 4: Continue Immediately
Kein Warten! Sofort mit nächster Phase weitermachen.

---

## Phase-Spezifische Konfigurationen

| Phase | Agent | Prerequisites | Output File |
|-------|-------|---------------|-------------|
| 0 | browser-agent | Chrome running (CDP), run_config.json | metadata/databases.json |
| 1 | search-agent | run_config.json, academic_context.md | metadata/search_strings.json |
| 2 | browser-agent | search_strings.json, databases.json | metadata/candidates.json |
| 3 | scoring-agent | candidates.json, run_config.json | metadata/ranked_sources.json |
| 4 | browser-agent | ranked_sources.json | pdfs/ (downloaded files) |
| 5 | extraction-agent | pdfs/, run_config.json | metadata/citations.json |
| 6 | orchestrator | citations.json | bibliography.md |

---

## Phase-Spezifische Prompts (Templates)

### Phase 0: DBIS Navigation
**Agent:** browser-agent
**Task:** Navigate DBIS and collect databases

**Prompt-Template:**
```
Mode: {mode} (quick/standard/deep)
Run-ID: {run_id}
Task: Navigate to DBIS, select databases matching academic_context.md
Output: runs/{run_id}/metadata/databases.json
```

### Phase 1: Search String Generation
**Agent:** search-agent
**Task:** Generate Boolean search strings

**Prompt-Template:**
```
Context: academic_context.md
Mode: {mode}
Task: Generate search strings for databases
Output: runs/{run_id}/metadata/search_strings.json
```

### Phase 2: Database Search (Iterativ)
**Agent:** browser-agent
**Task:** Execute searches in all databases

**Prompt-Template:**
```
Databases: metadata/databases.json
Search-Strings: metadata/search_strings.json
Mode: {mode}
Iterations: 30 (max)
Output: runs/{run_id}/metadata/candidates.json
```

### Phase 3: Scoring & Ranking
**Agent:** scoring-agent
**Task:** 5D-Scoring + Portfolio-Balance

**Prompt-Template:**
```
Input: metadata/candidates.json
Context: academic_context.md
Task: Score with 5D matrix (D1-D5)
Output: runs/{run_id}/metadata/ranked_sources.json
```

### Phase 4: PDF Download
**Agent:** browser-agent
**Task:** Download top-ranked PDFs

**Prompt-Template:**
```
Input: metadata/ranked_sources.json
Target: Top {count} sources (mode-dependent)
Output: runs/{run_id}/pdfs/
```

### Phase 5: Citation Extraction
**Agent:** extraction-agent
**Task:** Extract citations with page numbers

**Prompt-Template:**
```
Input: runs/{run_id}/pdfs/
Keywords: From academic_context.md
Task: Extract relevant passages + page numbers
Output: runs/{run_id}/metadata/citations.json
```

### Phase 6: Finalization
**Agent:** orchestrator (self)
**Task:** Generate bibliography.md

**Prompt-Template:**
```
Input: metadata/citations.json, ranked_sources.json
Task: Generate formatted bibliography
Output: runs/{run_id}/bibliography.md
```

---

## Error Handling per Phase

### Recoverable Errors
- Phase 0: DBIS unreachable → Retry 3x
- Phase 2: CDP connection lost → Retry with backoff
- Phase 4: PDF download failed → Skip einzelne PDFs

### Critical Errors (Abort Run)
- Phase 0: Chrome not running → Exit
- Phase 1: academic_context.md missing → Exit
- Phase 3: candidates.json invalid → Exit
- Phase 5: No PDFs found → Exit

---

## Validation Rules per Phase

### Phase 0
- Min 3 databases selected
- Each database has: name, url, access_info
- JSON valid

### Phase 1
- Min 1 search string generated
- Boolean operators present (AND/OR)
- Max 500 chars per string

### Phase 2
- Min 10 candidates found
- Each has: title, authors, year, source
- DOI or URL present

### Phase 3
- All candidates scored (D1-D5)
- Ranking score calculated
- Portfolio balanced

### Phase 4
- Min 5 PDFs downloaded (standard mode)
- File size > 10KB
- Valid PDF format

### Phase 5
- Min 3 citations extracted
- Page numbers present
- Keywords matched

### Phase 6
- bibliography.md created
- Valid Markdown format
- All citations included

---

## Referenz

Siehe auch:
- [EXECUTION_PATTERNS.md](./EXECUTION_PATTERNS.md) - Action-First, Retry Logic
- [ORCHESTRATOR_BASH_LIB.sh](./ORCHESTRATOR_BASH_LIB.sh) - Helper Functions
