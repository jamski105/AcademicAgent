# 🤝 Agent Handover Contracts

**Version:** 3.2
**Last Updated:** 2026-02-20

This document defines the **input/output contracts** between the Orchestrator and all specialized agents in the AcademicAgent system.

---

## Overview

### Workflow Phases (0-6)

| Phase | Name | Primary Agent | Human Checkpoint | Input Files | Output Files |
|-------|------|---------------|------------------|-------------|--------------|
| **0** | DBIS Navigation | browser-agent | ✅ (after) | run_config.json, research_state.json | databases.json |
| **1** | Search String Gen | search-agent | ✅ (after) | run_config.json, databases.json | search_strings.json |
| **2** | Iterative Search | browser-agent | ❌ | search_strings.json, databases.json | candidates.json |
| **3** | 5D Scoring | scoring-agent | ✅ (after) | candidates.json, run_config.json | ranked_candidates.json |
| **4** | PDF Download | browser-agent | ❌ | ranked_candidates.json (top 18) | downloads.json, downloads/*.pdf |
| **5** | Citation Extract | extraction-agent | ✅ (after) | downloads/*.pdf, run_config.json | quotes.json |
| **6** | Finalization | orchestrator | ✅ (after) | quotes.json | quote_library.json, bibliography.bib, outputs/*.md |

**Human-in-the-Loop Checkpoints:** Phases 0, 1, 3, 5, 6 (5 total)

---

## Run Directory Structure

All agents read/write to a shared run directory:

```
runs/<run_id>/
├── config/
│   ├── run_config.json          # User-provided config (setup-agent creates this)
│   └── <ProjectName>_Config.md  # Academic context markdown
├── metadata/
│   ├── databases.json           # Phase 0 output
│   ├── search_strings.json      # Phase 1 output
│   ├── candidates.json          # Phase 2 output
│   └── ranked_candidates.json   # Phase 3 output
├── downloads/
│   ├── downloads.json           # Phase 4 output (metadata)
│   └── *.pdf                    # Downloaded PDFs
├── outputs/
│   ├── quotes.json              # Phase 5 output
│   ├── quote_library.json       # Phase 6 output
│   ├── bibliography.bib         # Phase 6 output
│   ├── Annotated_Bibliography.md # Phase 6 output
│   └── search_report.md         # Phase 6 output
├── logs/
│   ├── phase_0.log
│   ├── phase_1.log
│   ├── ...
│   └── cdp_health.log           # Browser-agent CDP diagnostics
└── research_state.json          # Persistent state (current phase, retry counts, errors)
```

---

## Agent Contracts

### 1. Setup-Agent

**Purpose:** Interactive config creation (before Phase 0)

**Inputs:**
- User dialogue (research question, keywords, disciplines)
- (Optional) Template: `config/.example/academic_context_cs_example.md`

**Outputs:**
- `runs/<run_id>/config/run_config.json`
- `runs/<run_id>/config/<ProjectName>_Config.md`

**Failure Modes:**
- Invalid discipline name → Ask user to select from list
- Empty research question → Retry with user

**Retry Policy:** Ask user (no auto-retry)

---

### 2. Browser-Agent

**Purpose:** CDP-based web automation (Phases 0, 2, 4)

#### Phase 0: DBIS Navigation

**Inputs:**
- `run_config.json` (disciplines)
- `research_state.json` (phase, run_id)

**Outputs:**
- `metadata/databases.json`:
  ```json
  {
    "databases": [
      {"name": "IEEE Xplore", "url": "...", "relevance": "high", "discipline": "Computer Science"}
    ]
  }
  ```

**Failure Modes:**
- DBIS portal unreachable → Retry 3x with backoff (via `cdp_fallback_manager.py`)
- Session cookie expired → Alert user, request manual re-login
- CDP crash → Restart Chrome with clean profile

**Retry Policy:** 3 retries with exponential backoff (5s, 15s, 45s)

#### Phase 2: Iterative Database Search

**Inputs:**
- `metadata/search_strings.json`
- `metadata/databases.json`
- `research_state.json` (iteration count)

**Outputs:**
- `metadata/candidates.json`:
  ```json
  {
    "candidates": [
      {
        "doi": "10.1109/...",
        "title": "...",
        "authors": ["..."],
        "year": 2024,
        "abstract": "...",
        "source_db": "IEEE Xplore",
        "pdf_url": "...",
        "citations": 42
      }
    ],
    "iterations": 3,
    "databases_searched": ["IEEE", "ACM"],
    "total_results": 127
  }
  ```

**Failure Modes:**
- Zero results in database → Try next database, log warning
- Anti-bot CAPTCHA → Alert user, request manual solve
- Network timeout → Retry current database 2x

**Retry Policy:** Per-database retry (2x), then skip database

#### Phase 4: PDF Download

**Inputs:**
- `metadata/ranked_candidates.json` (top 18)

**Outputs:**
- `downloads/downloads.json`:
  ```json
  {
    "downloads": [
      {"doi": "...", "filename": "paper_001.pdf", "status": "success", "size_kb": 542}
    ],
    "success_count": 16,
    "failed_dois": ["10.1109/FAILED"]
  }
  ```
- `downloads/*.pdf` files

**Failure Modes:**
- Paywall encountered → Log as "failed", continue with rest
- PDF corrupted → Run `pdf_security_validator.py`, skip if invalid
- Disk full → Abort immediately, alert user

**Retry Policy:** 2 retries per PDF, then skip

---

### 3. Search-Agent

**Purpose:** Boolean search string generation (Phase 1)

**Inputs:**
- `config/run_config.json` (research_question, keywords)
- `metadata/databases.json` (database names for syntax adaptation)

**Outputs:**
- `metadata/search_strings.json`:
  ```json
  {
    "primary_string": "(machine learning) AND (security OR privacy)",
    "variations": [
      "ML AND security",
      "\"deep learning\" AND threat"
    ],
    "databases": {
      "IEEE": "(machine learning) AND (security)",
      "ACM": "machine AND learning AND security"
    }
  }
  ```

**Failure Modes:**
- Keywords too broad (>1M results expected) → Ask user to narrow
- Unknown database syntax → Use generic Boolean (AND/OR/NOT)

**Retry Policy:** Ask user for clarification

---

### 4. Scoring-Agent

**Purpose:** 5D relevance scoring (Phase 3)

**Inputs:**
- `metadata/candidates.json`
- `config/run_config.json` (research_question for relevance calc)

**Outputs:**
- `metadata/ranked_candidates.json`:
  ```json
  {
    "ranked": [
      {
        "doi": "...",
        "title": "...",
        "scores": {
          "relevance": 0.92,
          "citation_impact": 0.78,
          "recency": 0.85,
          "methodology": 0.88,
          "accessibility": 1.0
        },
        "total_score": 4.43,
        "rank": 1
      }
    ]
  }
  ```

**Failure Modes:**
- candidates.json malformed → CRITICAL: abort, validation failed upstream
- Score calculation NaN → Default to 0.5 for that dimension, log warning

**Retry Policy:** No retry (validation issue = upstream bug)

---

### 5. Extraction-Agent

**Purpose:** Quote extraction from PDFs (Phase 5)

**Inputs:**
- `downloads/*.pdf` (all successfully downloaded PDFs)
- `config/run_config.json` (research focus for quote selection)

**Outputs:**
- `outputs/quotes.json`:
  ```json
  {
    "quotes": [
      {
        "doi": "...",
        "page": 5,
        "quote_text": "...",
        "context": "introduction|methods|results|discussion",
        "relevance_score": 0.89
      }
    ]
  }
  ```

**Failure Modes:**
- PDF text extraction failed (scanned image PDF) → Skip, log warning
- No relevant quotes found in paper → Return empty array for that DOI
- Malformed PDF (corrupted) → Already filtered by Phase 4 validator

**Retry Policy:** No retry (skipped PDFs logged for user review)

---

### 6. Orchestrator-Agent (Phase 6)

**Purpose:** Final output generation

**Inputs:**
- `outputs/quotes.json`
- `metadata/ranked_candidates.json` (for BibTeX)

**Outputs:**
- `outputs/quote_library.json` (structured quotes)
- `outputs/bibliography.bib` (BibTeX)
- `outputs/Annotated_Bibliography.md` (human-readable)
- `outputs/search_report.md` (workflow summary)

**Failure Modes:**
- Missing quotes.json → CRITICAL: extraction-agent failed
- Invalid BibTeX syntax → Validate with `bibtex-validate`, fix encoding

**Retry Policy:** Abort if inputs missing (upstream failure)

---

## Uncertainty Handling

All agents MUST follow these rules when encountering **unknown/uncertain data**:

### 1. Unknown Fields
- **DO:** Use `"unknown"` or `null` for missing optional fields
- **DON'T:** Guess or fabricate data (e.g., fake DOIs, invented authors)

### 2. Low Confidence
- **DO:** Include `confidence` score (0.0-1.0) in output if applicable
- **DON'T:** Silently drop uncertain results (user decides threshold)

### 3. Ask-User Triggers
- **Empty required field** (e.g., research_question) → ASK USER
- **Ambiguous user intent** (e.g., "recent papers" = last 1yr or 5yr?) → ASK USER
- **Destructive action** (e.g., delete run directory) → ASK USER

### 4. Skip vs. Abort
- **Skip:** Individual item failed (1 PDF download, 1 database search) → Continue with rest
- **Abort:** Critical failure (all databases unreachable, validation gate failed) → Stop workflow, alert user

---

## Validation Gate (MANDATORY)

**After every agent completes**, orchestrator MUST run:

```bash
python3 scripts/validation_gate.py \
  --agent <agent_name> \
  --phase <phase_num> \
  --output-file runs/$RUN_ID/metadata/<output>.json \
  --schema schemas/<agent>_output_schema.json \
  --run-id $RUN_ID \
  --write-sanitized
```

**What it checks:**
- JSON schema compliance
- Required fields present
- Text fields sanitized (HTML stripped, injection patterns removed)
- Type correctness (e.g., year is integer)

**If validation fails:**
- Orchestrator ABORTS workflow
- User is alerted with diagnostic info
- Logs show which field/schema constraint failed

---

## Error Propagation

```
Agent Error → Orchestrator Catches → Logs to research_state.json → User Alert

If retry_count < max_retries:
  → Orchestrator retries agent with exponential backoff
Else:
  → Orchestrator asks user: [Retry / Skip / Abort]
```

**research_state.json structure:**

```json
{
  "run_id": "run_1234567890",
  "current_phase": 2,
  "phase_status": {
    "0": "completed",
    "1": "completed",
    "2": "in_progress"
  },
  "errors": [
    {
      "phase": 2,
      "agent": "browser-agent",
      "error": "Network timeout on IEEE Xplore",
      "timestamp": "2026-02-20T14:32:15Z",
      "retry_count": 1
    }
  ],
  "last_checkpoint": "2026-02-20T14:30:00Z"
}
```

---

## References

- **Validation Schemas:** [schemas/](../../schemas/)
- **Agent Prompts:** [.claude/agents/](../../.claude/agents/)
- **Orchestrator Workflow:** [orchestrator-agent.md](../../.claude/agents/orchestrator-agent.md)
- **User Workflow Guide:** [02-basic-workflow.md](../user-guide/02-basic-workflow.md)
