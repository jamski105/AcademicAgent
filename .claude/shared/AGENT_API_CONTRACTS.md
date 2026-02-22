# Agent API Contracts

**Purpose:** Input/Output specifications for all agents. This file contains ONLY technical contracts - no explanatory prose.

**Last Updated:** 2026-02-22

---

## Workflow Overview

| Phase | Agent | Input Files | Output Files |
|-------|-------|-------------|--------------|
| **0** | browser-agent | `run_config.json`, `research_state.json` | `databases.json` |
| **1** | search-agent | `run_config.json`, `databases.json` | `search_strings.json` |
| **2** | browser-agent | `search_strings.json`, `databases.json` | `candidates.json` |
| **3** | scoring-agent | `candidates.json`, `run_config.json` | `ranked_candidates.json` |
| **4** | browser-agent | `ranked_candidates.json` | `downloads.json`, `downloads/*.pdf` |
| **5** | extraction-agent | `downloads/*.pdf`, `run_config.json` | `quotes.json` |
| **6** | orchestrator | `quotes.json`, `ranked_candidates.json` | `quote_library.json`, `bibliography.bib` |

---

## File Locations

All files in: `runs/<run_id>/`

```
runs/<run_id>/
├── config/
│   ├── run_config.json
│   └── <ProjectName>_Config.md
├── metadata/
│   ├── databases.json
│   ├── search_strings.json
│   ├── candidates.json
│   └── ranked_candidates.json
├── downloads/
│   ├── downloads.json
│   └── *.pdf
├── outputs/
│   ├── quotes.json
│   ├── quote_library.json
│   ├── bibliography.bib
│   └── Annotated_Bibliography.md
├── logs/
│   └── phase_*.log
└── research_state.json
```

---

## Setup-Agent (Pre-Phase)

**Input:** User dialog

**Outputs:**
- `config/run_config.json`
- `config/<ProjectName>_Config.md`

---

## Browser-Agent Phase 0

**Input:** `config/run_config.json`

**Output:** `metadata/databases.json`

**Schema:**
```json
{
  "databases": [
    {
      "name": "string",
      "url": "string (URL)",
      "relevance": "enum: high|medium|low",
      "discipline": "string",
      "access_status": "enum: green|yellow|red|free",
      "dbis_resource_id": "string (DBIS resource ID)",
      "came_from_dbis": "boolean (true if navigated via DBIS)",
      "dbis_validated": "boolean (true if DBIS proxy used)"
    }
  ],
  "timestamp": "string (ISO 8601)"
}
```

**Neue Required Fields (seit DBIS-Automatisierung):**
- `access_status`: DBIS Zugangsampel (grün/gelb/rot/frei)
- `dbis_resource_id`: DBIS Ressourcen-ID (z.B. "123456")
- `came_from_dbis`: Wurde über DBIS-Proxy navigiert?
- `dbis_validated`: DBIS-Session aktiv?

---

## Search-Agent Phase 1

**Inputs:**
- `config/run_config.json`
- `metadata/databases.json`

**Output:** `metadata/search_strings.json`

**Schema:**
```json
{
  "primary_string": "string",
  "variations": ["string"],
  "databases": {
    "database_name": "string (search query)"
  },
  "timestamp": "string (ISO 8601)"
}
```

---

## Browser-Agent Phase 2

**Inputs:**
- `metadata/search_strings.json`
- `metadata/databases.json`

**Output:** `metadata/candidates.json`

**Schema:**
```json
{
  "candidates": [
    {
      "doi": "string",
      "title": "string",
      "authors": ["string"],
      "year": "number",
      "abstract": "string",
      "source_db": "string",
      "pdf_url": "string (URL)",
      "citations": "number"
    }
  ],
  "total_results": "number",
  "databases_searched": ["string"],
  "timestamp": "string (ISO 8601)"
}
```

---

## Scoring-Agent Phase 3

**Inputs:**
- `metadata/candidates.json`
- `config/run_config.json`

**Output:** `metadata/ranked_candidates.json`

**Schema:**
```json
{
  "ranked": [
    {
      "doi": "string",
      "title": "string",
      "authors": ["string"],
      "year": "number",
      "abstract": "string",
      "source_db": "string",
      "pdf_url": "string (URL)",
      "citations": "number",
      "scores": {
        "relevance": "number (0-1)",
        "citation_impact": "number (0-1)",
        "recency": "number (0-1)",
        "methodology": "number (0-1)",
        "accessibility": "number (0 or 1)"
      },
      "total_score": "number (sum of scores)",
      "rank": "number"
    }
  ],
  "total_scored": "number",
  "timestamp": "string (ISO 8601)"
}
```

---

## Browser-Agent Phase 4

**Input:** `metadata/ranked_candidates.json`

**Outputs:**
- `downloads/downloads.json`
- `downloads/*.pdf`

**Schema downloads.json:**
```json
{
  "downloads": [
    {
      "doi": "string",
      "filename": "string",
      "status": "enum: success|failed",
      "size_kb": "number"
    }
  ],
  "success_count": "number",
  "failed_dois": ["string"],
  "timestamp": "string (ISO 8601)"
}
```

**PDF naming:** `paper_001.pdf`, `paper_002.pdf`, etc.

---

## Extraction-Agent Phase 5

**Inputs:**
- `downloads/*.pdf`
- `config/run_config.json`

**Output:** `outputs/quotes.json`

**Schema:**
```json
{
  "quotes": [
    {
      "doi": "string",
      "paper_title": "string",
      "authors": ["string"],
      "year": "number",
      "page": "number",
      "quote_text": "string",
      "context": "enum: intro|methods|results|discussion|conclusion",
      "relevance_score": "number (0-1)"
    }
  ],
  "total_papers_processed": "number",
  "total_quotes_extracted": "number",
  "timestamp": "string (ISO 8601)"
}
```

---

## Orchestrator Phase 6

**Inputs:**
- `outputs/quotes.json`
- `metadata/ranked_candidates.json`
- `config/run_config.json` (for citation_style)

**Outputs:**
- `Quote_Library.csv` (with full citations in user-selected style)
- `outputs/bibliography.bib`
- `outputs/Annotated_Bibliography.md`
- `outputs/search_report.md`

**Quote_Library.csv Schema:**

CSV with the following columns:
- `Quote_ID` - Unique quote identifier (e.g., "Q001")
- `Source_ID` - Source identifier from ranked_candidates
- `Authors` - Semicolon-separated author list
- `Year` - Publication year
- `Title` - Source title
- `Page` - Page number where quote appears
- `Quote` - Extracted quote text (max 35 words)
- `Context` - One-sentence context description
- `Relevance` - One-sentence relevance statement
- `Keywords_Matched` - Semicolon-separated matched keywords
- `Full_Citation` - Complete formatted citation in user-selected style (APA 7, MLA, Chicago, IEEE, or Harvard)

**Citation Style Selection:**
- Read from `run_config.json` → `output_preferences.citation_style`
- Default: "APA 7" if not specified
- Supported: "APA 7", "MLA", "Chicago", "IEEE", "Harvard"

**Script:**
```bash
python3 scripts/create_quote_library_with_citations.py \
  <quotes.json> \
  <ranked_candidates.json> \
  <run_config.json> \
  <output.csv>
```

---

## Required: research_state.json

**Updated after EVERY phase:**

```json
{
  "run_id": "string (YYYY-MM-DD_HH-MM-SS)",
  "current_phase": "number (0-6)",
  "status": "enum: running|completed|failed",
  "last_update": "string (ISO 8601)",
  "errors": ["string"]
}
```

---

## Validation Rules

1. **All JSON outputs MUST be validated** via `scripts/validation_gate.py`
2. **Text fields MUST be sanitized** (remove HTML, injection patterns)
3. **Required fields cannot be null** unless explicitly marked optional
4. **Unknown values:** Use `"unknown"` or `null` for optional fields
5. **Never fabricate data** - use `null` if data unavailable

---

## Error Handling

**Retry Policy:**
- Phases 0-4: 3x retry with exponential backoff (5s, 15s, 45s)
- Phases 5-6: No retry (manual intervention required)

**On error:**
1. Log to `logs/phase_X.log`
2. Update `research_state.json` with error details
3. Follow retry policy or halt

---

**End of API Contracts**
