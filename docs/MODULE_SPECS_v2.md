# Academic Agent v2.2 - Modul-Spezifikationen

**Erstellt:** 2026-02-23
**Aktualisiert:** 2026-02-27 (v2.2 - DBIS Search Integration)
**Status:** Agent-basierte Architektur + DBIS Meta-Portal

---

## 📋 Übersicht: Agents + Python-Module

### 7 Claude Code Agents (v2.2)

1. **linear_coordinator** (Sonnet 4.5) - Master Orchestrator
2. **query_generator** (Haiku 4.5) - Query Expansion
3. **discipline_classifier** (Haiku 4.5) - Discipline Detection ⭐ *NEW v2.2*
4. **llm_relevance_scorer** (Haiku 4.5) - Relevanz-Bewertung
5. **quote_extractor** (Haiku 4.5) - Zitat-Extraktion
6. **dbis_browser** (Sonnet 4.5) - PDF Download (Chrome MCP)
7. **dbis_search** (Sonnet 4.5) - DBIS Search Automation ⭐ *NEW v2.2*

### Python CLI-Module

- **search_engine.py** - Multi-API Search
- **five_d_scorer.py** - 5D-Ranking (Citations, Recency, Quality, Authority)
- **pdf_parser.py** - PDF Text Extraction
- **pdf_fetcher.py** - PDF Download (Unpaywall + CORE)

---

## 1. linear_coordinator Agent (Sonnet 4.5)

**File:** `.claude/agents/linear_coordinator.md`

**Rolle:** Master Orchestrator

**Tools:** Bash, Read, Write, Task, Grep, Glob

**Workflow (8 Phases in v2.2):**

```
Phase 1: Context Setup
  → Read config/research_modes.yaml
  → Read config/academic_context.md
  → Read config/dbis_disciplines.yaml (NEW v2.2)
  → Bash: python -m src.state.run_manager --create
  → Bash: python -m src.state.database init --db-path runs/{timestamp}/session.db

Phase 2: Query Generation
  → Task(subagent_type="query_generator", prompt=user_query)

Phase 2a: Discipline Classification (NEW v2.2)
  → Task(subagent_type="discipline_classifier", prompt={query, expanded_queries})
  → Output: primary_discipline, relevant_databases

Phase 3: Hybrid Search (ENHANCED v2.2)
  Track 1 (Fast - APIs):
    → Bash: python -m src.search.search_engine --query "..." --sources api
  Track 2 (Comprehensive - DBIS):
    → Task(subagent_type="dbis_search", prompt={query, discipline, databases})
  → Merge & deduplicate results
  → Annotate source (api/dbis)

Phase 4: Ranking
  → Bash: python -m src.ranking.five_d_scorer --papers papers.json
  → Task(subagent_type="llm_relevance_scorer", prompt=papers_json)
  → Source-aware scoring (DBIS papers get discipline-match boost)

Phase 5: PDF Acquisition
  → Bash: python unpaywall_client.py, core_client.py
  → Falls Fehler: Task(subagent_type="dbis_browser", prompt=doi)

Phase 6: Quote Extraction
  → Bash: python -m src.extraction.pdf_parser --pdf paper.pdf
  → Task(subagent_type="quote_extractor", prompt=pdf_text)

Phase 7: Export Results
  → Bash: python -m src.export.csv_exporter (with source annotation)
  → Bash: python -m src.export.markdown_exporter (with source breakdown)
  → Bash: python -m src.export.bibtex_exporter
```

**Output:** JSON mit Research Results

---

## 2. query_generator Agent (Haiku 4.5)

**File:** `.claude/agents/query_generator.md`

**Input:**
```json
{
  "user_query": "DevOps Governance",
  "research_mode": "standard",
  "academic_context": "Software Engineering"
}
```

**Output:**
```json
{
  "expanded_queries": [
    "DevOps governance frameworks",
    "Continuous delivery governance",
    "Infrastructure as Code compliance"
  ],
  "keywords": ["DevOps", "governance", "compliance", "automation"],
  "boolean_query": "(DevOps OR continuous-delivery) AND governance",
  "filters": {
    "year_min": 2017,
    "venue_type": "conference OR journal"
  }
}
```

**Verantwortlichkeiten:**
- Query Expansion (Synonyme, verwandte Begriffe)
- Boolean Query Construction
- API-spezifische Optimierung

---

## 3. discipline_classifier Agent (Haiku 4.5) ⭐ *NEW v2.2*

**File:** `.claude/agents/discipline_classifier.md`

**Purpose:** Detect academic discipline from query to select relevant DBIS databases

**Input:**
```json
{
  "user_query": "Lateinische Metrik",
  "expanded_queries": [
    "Latin Meter",
    "Classical Prosody",
    "Quantitative Verse"
  ]
}
```

**Output:**
```json
{
  "primary_discipline": "Klassische Philologie",
  "secondary_disciplines": ["Literaturwissenschaft", "Linguistik"],
  "dbis_category_id": "2.1",
  "relevant_databases": [
    "L'Année philologique",
    "JSTOR Classics",
    "Perseus Digital Library"
  ],
  "confidence": 0.95
}
```

**Logic:**
1. Analyze query keywords and context
2. Map to discipl academic taxonomy (from config/dbis_disciplines.yaml)
3. Identify top 3-5 most relevant databases
4. Return DBIS category ID for navigation

**Used by:** linear_coordinator in Phase 2a

---

## 4. llm_relevance_scorer Agent (Haiku 4.5)

**File:** `.claude/agents/llm_relevance_scorer.md`

**Input:**
```json
{
  "user_query": "DevOps Governance",
  "papers": [
    {
      "title": "A Framework for DevOps Governance",
      "abstract": "This paper presents..."
    }
  ]
}
```

**Output:**
```json
{
  "scores": [
    {
      "paper_id": "doi:10.1109/...",
      "relevance_score": 0.92,
      "reasoning": "Directly addresses DevOps governance frameworks"
    }
  ]
}
```

**Features:**
- Batch-Processing (10 papers)
- Semantisches Verständnis
- Reasoning für Transparenz

---

## 5. quote_extractor Agent (Haiku 4.5)

**File:** `.claude/agents/quote_extractor.md`

**Input:**
```json
{
  "user_query": "DevOps Governance",
  "pdf_text": "Full PDF text...",
  "paper_metadata": {
    "title": "...",
    "authors": "..."
  }
}
```

**Output:**
```json
{
  "quotes": [
    {
      "quote": "DevOps governance requires continuous compliance monitoring",
      "page": 5,
      "context_before": "In modern software development...",
      "context_after": "...which ensures regulatory adherence.",
      "relevance": 0.95
    }
  ]
}
```

**Constraints:**
- ≤25 Wörter pro Zitat
- Context Window: 50 Wörter vor/nach
- Validiert gegen PDF-Text

---

## 6. dbis_browser Agent (Sonnet 4.5)

**File:** `.claude/agents/dbis_browser.md`

**Purpose:** PDF download via DBIS institutional access

**Tools:** Chrome MCP
- `mcp__chrome__navigate`
- `mcp__chrome__click`
- `mcp__chrome__type`
- `mcp__chrome__screenshot`
- `mcp__chrome__wait`

**Input:**
```json
{
  "doi": "10.1109/ICSE.2023.00042",
  "paper_title": "DevOps Governance Framework"
}
```

**Workflow:**

```
1. Navigate to DOI → Publisher
2. Detect Paywall
3. If TIB Shibboleth:
   a. Navigate to Shibboleth Login
   b. Screenshot → User sieht Browser
   c. WAIT for manual login (interaktiv!)
   d. Screenshot confirmation
4. Find PDF Download Button
5. Click & Download
6. Return PDF Path
```

**Publisher-Flows:**
- IEEE Xplore
- ACM Digital Library
- Springer
- Elsevier/ScienceDirect

**Output:**
```json
{
  "pdf_path": "runs/{timestamp}/pdfs/paper_5.pdf",
  "status": "success",
  "download_method": "dbis_tib_shibboleth"
}
```

---

## 7. dbis_search Agent (Sonnet 4.5) ⭐ *NEW v2.2*

**File:** `.claude/agents/dbis_search.md`

**Purpose:** Automated search across discipline-specific databases via DBIS portal

**Tools:** Chrome MCP (same as dbis_browser)

**Input:**
```json
{
  "user_query": "Lateinische Metrik",
  "discipline": "Klassische Philologie",
  "databases": [
    "L'Année philologique",
    "JSTOR Classics",
    "Perseus Digital Library"
  ],
  "limit": 50
}
```

**Workflow:**
```
1. Navigate to DBIS (https://dbis.ur.de/UBTIB)
2. Select discipline category
3. For each database in list:
   a. Click "Zur Datenbank" (activates TIB license!)
   b. Wait for redirect to database website
   c. Find search interface (database-specific selector)
   d. Execute search with optimized query
   e. Extract results from HTML:
      - Title
      - Authors
      - Year
      - DOI (if available)
      - Journal/Venue
      - URL
   f. Return to DBIS for next database
4. Merge all results
5. Annotate source (database name)
6. Return to coordinator
```

**Database-Specific Strategies:**
Uses `config/dbis_disciplines.yaml` for:
- Search field selectors
- Result selectors
- Pagination logic
- Export functions (if available)

**Output:**
```json
{
  "papers": [
    {
      "title": "De metris Horatianis",
      "authors": ["Schmidt, M."],
      "year": 2019,
      "doi": null,
      "url": "https://...",
      "source": "L'Année philologique",
      "source_type": "dbis",
      "journal": "Rheinisches Museum",
      "relevance": 0.88
    }
  ],
  "statistics": {
    "databases_searched": 3,
    "total_papers": 87,
    "search_time_seconds": 72
  }
}
```

**Performance:**
- Time: 60-90 seconds (browser automation)
- Papers: 50-100 per search
- Parallel execution: Possible (multiple browser instances)

### DBIS Auto-Discovery Mode (NEW v2.3)

**Enhancement:** Automatically discover available databases instead of relying solely on config

**Discovery Input:**
```json
{
  "user_query": "Mietrecht Kündigungsfristen",
  "discipline": "Rechtswissenschaft",
  "discovery_config": {
    "enabled": true,
    "dbis_url": "https://dbis.ur.de/dbis/dbliste.php?bib_id=ubtib&lett=f&sGeb=9.1",
    "max_databases": 5,
    "preferred_databases": ["Beck-Online", "Juris", "HeinOnline"],
    "blacklist": ["Katalog", "Directory", "Encyclopedia"]
  },
  "fallback_databases": ["Beck-Online", "Juris"]
}
```

**Enhanced Workflow:**
```
Phase 0: Database Selection Strategy

IF discovery_config.enabled:
    → Try Discovery Mode (Phase 1)
    → If fails: Use fallback_databases (Phase 2)
ELSE:
    → Use predefined databases from input

Phase 1: Discovery Mode (NEW)
1. Navigate to discovery_config.dbis_url
2. Wait for database list page load
3. Scrape all database entries:
   FOR each element matching ".datenbank, .db-entry":
     a. Extract database name (.db-name, h3, .title)
     b. Extract traffic light status (img[src*="amp"])
     c. Extract access link (a:contains("Zur Datenbank"))
4. Filter databases:
   a. Keep only green (free) or yellow (TIB license)
   b. Exclude blacklisted terms (Katalog, Directory, etc.)
5. Prioritize databases:
   a. Preferred databases first (from config)
   b. Green light before yellow
   c. Alphabetical order
6. Select TOP N (discovery_config.max_databases)
7. Cache result for 24h (key: discipline + date)

Phase 2: Fallback Mode (if Discovery fails)
→ Use fallback_databases from input

Phase 3: Search Selected Databases
→ Continue with normal DBIS search workflow
```

**Discovery Selectors (from config):**
```yaml
discovery_selectors:
  database_entry: ".datenbank, .db-entry, tr.dbis-entry"
  database_name: ".db-name, h3, .title, td.name"
  traffic_light: "img[src*='amp'], .access-status"
  access_link: "a:contains('Zur Datenbank'), .db-link"

  # Traffic light colors
  green_indicator: "amp_gruen"     # Free access
  yellow_indicator: "amp_gelb"     # TIB license
  red_indicator: "amp_rot"         # No access (skip)
```

**Blacklist (global):**
```yaml
discovery_blacklist:
  - "Katalog"         # Library catalogs
  - "Directory"       # Directories
  - "Encyclopedia"    # Reference works
  - "Handbook"        # Handbooks
  - "Lexikon"         # Encyclopedias
  - "Bibliography"    # Pure bibliographies
```

**Caching Strategy:**
```python
cache_key = f"dbis_discovery_{discipline}_{date.today().isoformat()}"
cache_ttl = 86400  # 24 hours

# First query of the day: Discovery scraping (~15s)
# Subsequent queries: Instant cache hit (~0s)
```

**Error Handling:**
```
Discovery Failure Scenarios:
1. DBIS page load timeout → Use fallback_databases
2. No databases found → Use fallback_databases
3. All databases blacklisted → Use fallback_databases
4. Scraping error → Log error + Use fallback_databases
5. Fallback empty → Return empty + log critical error
```

**Benefits:**
- 📈 Scales to 100+ databases per discipline
- 🔄 Automatically includes new DBIS databases
- 🎯 Reduced manual config maintenance
- 🚀 First run: +15s, subsequent: +0s (cached)

**Error Handling:**
- Database not found → Skip, log warning
- Search interface changed → Fallback strategy
- Timeout → Return partial results
- License missing → Skip, note in logs

---

## Python CLI-Module

### search_engine.py

**Usage:**
```bash
python -m src.search.search_engine \
  --query "DevOps Governance" \
  --mode standard \
  --output results.json
```

**Output:**
```json
{
  "papers": [
    {
      "doi": "10.1109/...",
      "title": "...",
      "abstract": "...",
      "authors": [...],
      "year": 2023,
      "venue": "ICSE",
      "citations": 15
    }
  ],
  "sources": ["crossref", "openalex", "semantic_scholar"],
  "total_found": 47,
  "deduplicated": 35
}
```

---

### five_d_scorer.py

**Usage:**
```bash
python -m src.ranking.five_d_scorer \
  --papers papers.json \
  --weights relevance:0.4,recency:0.2,quality:0.2,authority:0.2 \
  --output scored.json
```

**Input:** Papers JSON + Optional LLM Relevance Scores

**Output:**
```json
{
  "ranked_papers": [
    {
      "doi": "10.1109/...",
      "total_score": 0.87,
      "breakdown": {
        "relevance": 0.92,
        "recency": 0.85,
        "quality": 0.78,
        "authority": 0.90
      }
    }
  ]
}
```

---

### dbis_search_orchestrator.py ⭐ *NEW v2.2*

**Usage:**
```bash
python -m src.search.dbis_search_orchestrator \
  --query "Mietrecht Kündigungsfristen" \
  --discipline "Rechtswissenschaft" \
  --max-databases 5 \
  --output dbis_config.json
```

**Purpose:** Prepares configuration for dbis_search agent (Discovery + Fallback)

**Input:**
- `--query`: User search query
- `--discipline`: Detected discipline (from discipline_classifier)
- `--max-databases`: Max databases to select (default: 3)
- `--mode`: quick/standard/deep (default: standard)

**Output (Agent-ready config):**
```json
{
  "user_query": "Mietrecht Kündigungsfristen",
  "discipline": "Rechtswissenschaft",
  "mode": "discovery",
  "discovery": {
    "enabled": true,
    "dbis_url": "https://dbis.ur.de/dbis/dbliste.php?bib_id=ubtib&lett=f&sGeb=9.1",
    "max_databases": 5,
    "preferred_databases": ["Beck-Online", "Juris", "HeinOnline"],
    "selectors": {
      "database_entry": ".datenbank, .db-entry",
      "database_name": ".db-name, h3",
      "traffic_light": "img[src*='amp']",
      "access_link": "a:contains('Zur Datenbank')"
    },
    "blacklist": ["Katalog", "Directory", "Encyclopedia"]
  },
  "fallback_databases": [
    {
      "name": "Beck-Online",
      "priority": 1,
      "search_selector": "#query"
    },
    {
      "name": "Juris",
      "priority": 2
    }
  ],
  "limit": 50
}
```

**Logic:**
1. Load `config/dbis_disciplines.yaml` for discipline
2. Check if `discovery_enabled: true`
3. Build discovery config with selectors
4. Add preferred_databases for prioritization
5. Add fallback_databases for error recovery
6. Return JSON config for dbis_search agent

**Discovery Decision:**
```python
if config[discipline].get("discovery_enabled", False):
    mode = "discovery"
    # Build discovery config
else:
    mode = "config"
    # Use predefined databases
```

---

### pdf_parser.py

**Usage:**
```bash
python -m src.extraction.pdf_parser \
  --pdf paper.pdf \
  --output text.json
```

**Output:**
```json
{
  "text": "Full extracted text...",
  "pages": 12,
  "metadata": {
    "title": "...",
    "author": "..."
  }
}
```

---

## State Management (SQLite)

**Tables:**

```sql
CREATE TABLE sessions (
  id TEXT PRIMARY KEY,
  query TEXT,
  mode TEXT,
  created_at TIMESTAMP,
  status TEXT
);

CREATE TABLE papers (
  id TEXT PRIMARY KEY,
  session_id TEXT,
  doi TEXT,
  title TEXT,
  abstract TEXT,
  score REAL,
  pdf_path TEXT,
  FOREIGN KEY (session_id) REFERENCES sessions(id)
);

CREATE TABLE quotes (
  id TEXT PRIMARY KEY,
  paper_id TEXT,
  quote TEXT,
  page INTEGER,
  context_before TEXT,
  context_after TEXT,
  FOREIGN KEY (paper_id) REFERENCES papers(id)
);
```

---

## Interface: Agent ↔ Python Module

**Agent ruft Module via Bash:**
```bash
# In linear_coordinator.md:
python -m src.search.search_engine \
  --query "DevOps Governance" \
  --mode standard \
  > /tmp/results.json
```

**Agent liest Output:**
```bash
# In linear_coordinator.md:
cat /tmp/results.json
```

**Agent spawnt Subagent:**
```python
# In linear_coordinator.md (konzeptuell):
Task(
  subagent_type="query_generator",
  prompt="Generate queries for: DevOps Governance"
)
```

---

Für vollständige Architektur siehe [ARCHITECTURE_v2.md](./ARCHITECTURE_v2.md)
