# Academic Agent v2.2 - Architektur-Dokumentation

**Erstellt:** 2026-02-23
**Aktualisiert:** 2026-02-27 (v2.2 - DBIS Search Integration)
**Ziel:** Agent-basierte Architektur über Claude Code + DBIS Meta-Portal

---

## 📋 Übersicht

### Architektur-Paradigma: Agent Orchestration via Claude Code

```
User → Claude Code → linear_coordinator Agent
  → Spawnt Subagenten (query_gen, scorer, extractor, dbis_browser)
  → Ruft Python-Module auf (search, ranking, parsing)
  → Nutzt Chrome MCP für Browser Automation
```

**Kernprinzip:** Keine direkten Anthropic API-Calls, alles über Claude Code Agenten.

---

## 🏗️ Neue Architektur v2.0

### High-Level Übersicht

```
┌─────────────────────────────────────────────────────────┐
│ User: /research "DevOps Governance"                     │
└────────────────────┬────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────┐
│ SKILL.md (.claude/skills/research/)                     │
│ → Spawnt: Task(subagent_type="linear_coordinator")     │
└────────────────────┬────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────┐
│ LINEAR COORDINATOR AGENT (Sonnet 4.5)                   │
│ (.claude/agents/linear_coordinator.md)                  │
│                                                         │
│ Orchestriert 8 Phasen:                                 │
│                                                         │
│ Phase 1: Context Setup                                 │
│   → Read config files (Bash: cat)                       │
│   → Init database (Bash: python -m state.database)     │
│                                                         │
│ Phase 2: Query Generation                              │
│   → Task(subagent="query_generator") ◄─── Haiku Agent  │
│                                                         │
│ Phase 2a: Discipline Classification (NEW v2.2)         │
│   → Task(subagent="discipline_classifier") ◄─── Haiku  │
│   → Maps query to DBIS categories                      │
│   → Identifies relevant databases                      │
│                                                         │
│ Phase 3: Hybrid Search (ENHANCED v2.2)                 │
│   Track 1 (Fast):                                      │
│   → Bash: python -m src.search.search_engine (APIs)    │
│   Track 2 (Comprehensive):                             │
│   → Task(subagent="dbis_search") ◄─── Chrome MCP       │
│   → Merges & deduplicates results                      │
│                                                         │
│ Phase 4: Ranking                                       │
│   → Bash: python -m src.ranking.five_d_scorer          │
│   → Task(subagent="llm_relevance_scorer") ◄─── Haiku   │
│                                                         │
│ Phase 5: PDF Acquisition                               │
│   → Bash: python unpaywall + core clients              │
│   → Task(subagent="dbis_browser") ◄─── Chrome MCP      │
│                                                         │
│ Phase 6: Quote Extraction                              │
│   → Bash: python -m src.extraction.pdf_parser          │
│   → Task(subagent="quote_extractor") ◄─── Haiku Agent  │
│                                                         │
│ Phase 7: Export Results (NEW v2.1)                     │
│   → Bash: python -m src.export.csv_exporter            │
│   → Bash: python -m src.export.markdown_exporter       │
│   → Bash: python -m src.export.bibtex_exporter         │
│   → Save to runs/{timestamp}/                          │
│                                                         │
│ Output: runs/2026-02-27_14-30-00/                      │
│   ├── pdfs/, results.json, quotes.csv                  │
│   ├── summary.md, bibliography.bib                     │
│   └── session.db, logs                                 │
└─────────────────────────────────────────────────────────┘
```

---

## 🤖 Agents (Claude Code Subagents)

### 1. linear_coordinator (Sonnet 4.5)

**Rolle:** Master Orchestrator
**File:** `.claude/agents/linear_coordinator.md`
**Tools:** Bash, Read, Write, Task, Grep, Glob

**Verantwortlichkeiten:**
- Orchestriert 7-Phasen Workflow
- Spawnt Subagenten via Task tool
- Ruft Python-Module via Bash auf
- State Management (SQLite + Run Directory)
- Error Handling & Recovery
- Progress Tracking
- Export Management (CSV, Markdown, BibTeX)

### 2. query_generator (Haiku 4.5)

**Rolle:** Query Expansion
**File:** `.claude/agents/query_generator.md`
**Input:** User query, research mode, academic context
**Output:** Boolean queries, keywords, filters

**Verantwortlichkeiten:**
- Kreative Query-Expansion
- Synonyme & verwandte Begriffe
- Boolean-Query-Konstruktion
- API-spezifische Query-Optimierung

### 3. llm_relevance_scorer (Haiku 4.5)

**Rolle:** Semantische Relevanz-Bewertung
**File:** `.claude/agents/llm_relevance_scorer.md`
**Input:** Papers (Title, Abstract), User query
**Output:** Relevanz-Scores (0-1)

**Verantwortlichkeiten:**
- Semantisches Verständnis von Paper-Inhalten
- Relevanz-Bewertung pro Paper
- Batch-Processing (10 papers)
- JSON Output für five_d_scorer

### 4. quote_extractor (Haiku 4.5)

**Rolle:** Zitat-Extraktion aus PDFs
**File:** `.claude/agents/quote_extractor.md`
**Input:** PDF Text, User query
**Output:** Relevante Zitate mit Context

**Verantwortlichkeiten:**
- Findet relevante Textstellen
- Extrahiert prägnante Zitate (≤25 Wörter)
- Kontext-Window (50 Wörter)
- Validierung gegen PDF-Text

### 5. dbis_browser (Sonnet 4.5)

**Rolle:** Browser Automation für PDF-Download
**File:** `.claude/agents/dbis_browser.md`
**Tools:** Chrome MCP (mcp__chrome__*)

**Verantwortlichkeiten:**
- DOI → Publisher Website Navigation
- Paywall Detection
- Shibboleth Auth Flow (TIB Hannover)
- **Interaktiver Login** (User sieht Browser, Login manuell)
- PDF Download Link Detection
- Publisher-spezifische Flows:
  - IEEE Xplore
  - ACM Digital Library
  - Springer
  - Elsevier/ScienceDirect

---

## 🐍 Python-Module (CLI-fähig)

### Phase 3: Search

**search_engine.py** (CLI)
```bash
python -m src.search.search_engine \
  --query "DevOps Governance" \
  --mode standard \
  --output results.json
```

**Integriert:**
- `crossref_client.py` - CrossRef API (50 req/s, anonymous)
- `openalex_client.py` - OpenAlex API (100 req/day, anonymous)
- `semantic_scholar_client.py` - S2 API (100 req/5min, anonymous)
- `deduplicator.py` - DOI-basierte Deduplizierung

### Phase 4: Ranking

**five_d_scorer.py** (CLI)
```bash
python -m src.ranking.five_d_scorer \
  --papers papers.json \
  --weights relevance:0.4,recency:0.2,quality:0.2,authority:0.2 \
  --output scored.json
```

**Features:**
- Relevanz (wird von llm_relevance_scorer Agent ergänzt)
- Recency (log-scaled, max 10 Jahre)
- Quality (Citation Count, log-scaled)
- Authority (Venue-Heuristic)
- Portfolio Balance (optional)

### Phase 5: PDF Acquisition

**pdf_fetcher.py** (Wrapper)
- `unpaywall_client.py` - Unpaywall API (~40% Erfolg)
- `core_client.py` - CORE API (~10% zusätzlich)
- Falls fehlgeschlagen → Coordinator spawnt dbis_browser Agent

### Phase 6: Quote Extraction

**pdf_parser.py** (CLI)
```bash
python -m src.extraction.pdf_parser \
  --pdf paper.pdf \
  --output text.json
```

**Features:**
- PyMuPDF Text-Extraktion
- Page-by-page
- Text Cleaning & Normalization

---

## 🌐 Chrome MCP Integration

### Setup (.claude/settings.json)

```json
{
  "mcpServers": {
    "chrome": {
      "command": "npx",
      "args": ["-y", "@eddym06/custom-chrome-mcp@latest"],
      "env": {
        "CHROME_PATH": "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
      }
    }
  }
}
```

### dbis_browser Agent - Chrome MCP Tools

**Verfügbare Tools:**
- `mcp__chrome__navigate` - URL Navigation
- `mcp__chrome__click` - Element Click
- `mcp__chrome__type` - Text Input
- `mcp__chrome__screenshot` - Screenshot
- `mcp__chrome__wait` - Wait for Element
- `mcp__chrome__evaluate` - JS Execution

**Workflow:**
1. Navigate zu DOI-URL
2. Redirect zu Publisher Website
3. Detect Paywall/Login
4. Falls TIB Shibboleth:
   - Navigate zu Shibboleth Login
   - **PAUSE für manuellen Login** (User sieht Browser!)
   - Screenshot zur Bestätigung
5. Find PDF Download Link
6. Click & Download
7. Return PDF Path

---

## 🌍 DBIS Search Architecture (NEW v2.2)

### Konzept: DBIS als Meta-Portal

**Problem:** Hunderte von Fachdatenbanken, jeweils eigene API/Interface
**Lösung:** DBIS (Database Information System) als einheitlicher Zugang

**Vorteil:**
- Eine Integration → Zugang zu 100+ Datenbanken
- Automatische TIB-Lizenz Aktivierung
- Fachgebiets-basierte Selektion

### Phase 2a: Discipline Classification

**discipline_classifier Agent (Haiku)**

Input:
```json
{
  "user_query": "Lateinische Metrik",
  "expanded_queries": ["Latin Meter", "Classical Prosody", ...]
}
```

Output:
```json
{
  "primary_discipline": "Klassische Philologie",
  "secondary_disciplines": ["Literaturwissenschaft", "Linguistik"],
  "dbis_categories": ["2.1", "2.2"],  // DBIS Fachgebiet-IDs
  "relevant_databases": [
    "L'Année philologique",
    "JSTOR Classics",
    "Perseus Digital Library"
  ]
}
```

### Phase 3: DBIS Search Agent

**dbis_search Agent (Sonnet + Chrome MCP)**

**Workflow:**
```
1. Navigate zu DBIS Portal
   → https://dbis.ur.de/UBTIB

2. Select Discipline
   → Klickt Fachgebiet (z.B. "Klassische Philologie")

3. Filter for Licensed Databases
   → Nur grüne Ampel (TIB-Lizenz vorhanden)

4. For each relevant database:
   a) Click "Zur Datenbank"
      → Aktiviert TIB-Lizenz via DBIS Redirect!

   b) Wait for database website load

   c) Find search interface
      → Database-specific strategies (config/dbis_disciplines.yaml)

   d) Execute search
      → Enter query, apply filters

   e) Extract results
      → Scrape HTML for papers (Title, Authors, Year, DOI)
      → Or use Export function (BibTeX/RIS if available)

   f) Return to DBIS for next database

5. Merge all results
   → Annotate source (database name)
   → Return to coordinator
```

**Database-Specific Strategies:**

```yaml
# config/dbis_disciplines.yaml
databases:
  "L'Année philologique":
    search_selector: "#search-field"
    search_type: "advanced"
    export_format: "bibtex"

  "JSTOR":
    search_selector: "input[name='Query']"
    search_type: "basic"
    result_selector: ".card--result"

  "IEEE Xplore":
    search_selector: "#xploreSearchInput"
    filters: ["Conference", "Journal"]
```

### DBIS Auto-Discovery (NEW v2.3)

**Problem:** Manually defining all databases for each discipline doesn't scale
- Jura: only 2 DBs defined, but DBIS has 20+
- New databases added to DBIS → not automatically available
- 100+ databases × 15 disciplines = too much manual config

**Solution:** Automatic Database Discovery

**Architecture:**

```
discipline_classifier → discipline + dbis_url
                              ↓
                    dbis_search Agent
                              ↓
                  ┌──────────┴──────────┐
                  ↓                     ↓
         Discovery Mode          Config Mode
         (Try First)             (Fallback)
                  ↓                     ↓
    1. Navigate to DBIS      Use predefined
       discipline page       databases from
    2. Scrape database       config file
       list from HTML
    3. Filter:
       - Green/yellow only
       - Blacklist applied
    4. Prioritize:
       - Preferred DBs first
       - Quality score
    5. Select TOP 3-5
                  ↓                     ↓
                  └──────────┬──────────┘
                             ↓
                    Search Selected DBs
```

**Discovery Algorithm:**

```python
def discover_databases(discipline_url, config):
    # 1. Navigate to DBIS discipline page
    driver.get(discipline_url)

    # 2. Extract all database entries
    databases = []
    for entry in find_all(".datenbank"):
        name = entry.find(".db-name").text
        traffic_light = entry.find("img[src*='amp']").attr("src")
        link = entry.find("a:contains('Zur Datenbank')").attr("href")

        # 3. Filter by traffic light (green/yellow only)
        if "amp_gruen" in traffic_light or "amp_gelb" in traffic_light:
            # 4. Apply blacklist
            if not any(blocked in name for blocked in BLACKLIST):
                databases.append({
                    "name": name,
                    "link": link,
                    "access": "free" if "gruen" in traffic_light else "tib"
                })

    # 5. Prioritize by preferred databases
    preferred = config.get("preferred_databases", [])
    databases.sort(key=lambda db: (
        0 if db["name"] in preferred else 1,  # Preferred first
        0 if db["access"] == "free" else 1,   # Green before yellow
        db["name"]                             # Alphabetical
    ))

    # 6. Select TOP N
    return databases[:config.get("discovery_max_databases", 5)]
```

**Blacklist (global):**
```yaml
discovery_blacklist:
  - "Katalog"         # Library catalogs
  - "Directory"       # Directories
  - "Encyclopedia"    # Reference works
  - "Handbook"        # Handbooks
  - "Lexikon"         # Lexica
```

**Config Example:**

```yaml
"Rechtswissenschaft":
  dbis_category_id: "9.1"
  dbis_url: "https://dbis.ur.de/dbis/dbliste.php?bib_id=ubtib&lett=f&sGeb=9.1"

  # Discovery Settings
  discovery_enabled: true          # Try discovery first
  discovery_max_databases: 5       # Select TOP 5

  # Preferred (if found during discovery, prioritize)
  preferred_databases:
    - "Beck-Online"
    - "Juris"
    - "HeinOnline"

  # Fallback (if discovery fails)
  fallback_databases:
    - name: "Beck-Online"
      priority: 1
    - name: "Juris"
      priority: 2
```

**Caching Strategy:**

```python
# Cache discovered databases for 24h
cache_key = f"dbis_discovery_{discipline}_{date.today()}"

if cache_key in cache:
    databases = cache.get(cache_key)
else:
    databases = discover_databases(discipline_url, config)
    cache.set(cache_key, databases, ttl=86400)  # 24h
```

**Why cache?**
- Discovery scraping is slow (~10-20 seconds)
- DBIS database list doesn't change daily
- Multiple queries same day → reuse discovery

**Fallback Chain:**

```
1. Try Discovery
   ↓ (failed?)
2. Try fallback_databases from config
   ↓ (empty?)
3. Use general_databases (CrossRef, OpenAlex)
   ↓ (failed?)
4. Return empty + log error
```

**Performance Impact:**
- **First run (no cache):** +15 seconds (discovery scraping)
- **Subsequent runs (cached):** +0 seconds (instant)
- **Config mode:** +0 seconds (no discovery)

**Benefits:**
- 📈 **Scalability:** New DBIS databases automatically available
- 🔄 **Maintainability:** Less manual config needed
- 🌍 **Coverage:** All disciplines get 100% DBIS coverage

---

### Result Merging

**Coordinator merges:**
- API Papers (CrossRef, OpenAlex, S2)
- DBIS Papers (all databases)

**Deduplication:**
- Primary: DOI matching
- Secondary: Title similarity (>85%)
- Keeps source annotation

**Source-Aware Ranking:**
- DBIS papers get +0.05 boost if discipline matches
- Reason: More likely to be relevant if found in specialized DB

---

## 💾 State Management

### SQLite Database (state/database.py)

**Tables:**
- `sessions` - Research Sessions
- `papers` - Candidate Papers
- `quotes` - Extracted Quotes
- `checkpoints` - Resume Points

**Features:**
- Atomic Transactions
- Auto-Commit
- Checkpoint & Resume
- JSON Export

---

## 📁 Repository-Struktur

```
AcademicAgent/
├── setup.sh                       # ← Installation (inkl Chrome MCP)
├── .claude/
│   ├── settings.json             # ← Chrome MCP Config
│   ├── agents/
│   │   ├── linear_coordinator.md       # Master Agent
│   │   ├── query_generator.md          # Query Expansion
│   │   ├── discipline_classifier.md    # Discipline Detection (NEW v2.2)
│   │   ├── llm_relevance_scorer.md     # Relevanz-Bewertung
│   │   ├── quote_extractor.md          # Zitat-Extraktion
│   │   ├── dbis_browser.md             # PDF Download (Chrome MCP)
│   │   └── dbis_search.md              # DBIS Search (NEW v2.2, Chrome MCP)
│   └── skills/research/
│       └── SKILL.md                 # Entry Point
├── config/
│   ├── research_modes.yaml          # Quick/Standard/Deep
│   ├── dbis_disciplines.yaml        # DBIS Database Registry (NEW v2.2)
│   └── academic_context.md          # Optional User Context
├── src/
│   ├── classification/                  # NEW v2.2
│   │   └── discipline_classifier.py # CLI Module
│   ├── search/
│   │   ├── search_engine.py         # CLI Wrapper (Hybrid in v2.2)
│   │   ├── dbis_search_orchestrator.py  # NEW v2.2
│   │   ├── crossref_client.py
│   │   ├── openalex_client.py
│   │   ├── semantic_scholar_client.py
│   │   └── deduplicator.py
│   ├── ranking/
│   │   └── five_d_scorer.py         # CLI Wrapper
│   ├── pdf/
│   │   ├── pdf_fetcher.py           # Wrapper (Unpaywall+CORE)
│   │   ├── unpaywall_client.py
│   │   └── core_client.py
│   ├── extraction/
│   │   ├── pdf_parser.py            # CLI Wrapper
│   │   └── quote_validator.py
│   ├── state/
│   │   ├── database.py              # SQLite Schema
│   │   ├── state_manager.py
│   │   └── checkpointer.py
│   ├── ui/
│   │   ├── progress_ui.py
│   │   └── error_formatter.py
│   └── utils/
│       ├── config.py
│       ├── rate_limiter.py
│       ├── retry.py
│       └── cache.py
└── tests/
    ├── unit/
    ├── integration/
    └── agents/                      # Agent Tests
```

---

## 🔄 Workflow: User → Result

```
1. User: /research "DevOps Governance"
   ↓
2. SKILL.md:
   - Mode Selection (Quick/Standard/Deep)
   - Load Configs
   - Spawn linear_coordinator Agent
   ↓
3. linear_coordinator Agent:
   Phase 1: Context Setup
   Phase 2: Query Gen → query_generator Agent
   Phase 3: Search → search_engine.py (Bash)
   Phase 4: Ranking → five_d_scorer.py + llm_relevance_scorer Agent
   Phase 5: PDF → unpaywall/core + dbis_browser Agent (fallback)
   Phase 6: Quotes → pdf_parser.py + quote_extractor Agent
   ↓
4. Output: Research Results mit Zitaten
```

---

## 🎯 Design-Prinzipien

1. **Agent-First:** Alle LLM-Calls via Claude Code Agenten
2. **No API Keys:** Keine direkten Anthropic API-Calls
3. **Chrome MCP:** Browser Automation via MCP (nicht Playwright)
4. **CLI-Python:** Module sind CLI-fähig, von Agents aufrufbar
5. **Interaktiv:** User sieht Browser bei DBIS Login
6. **State-First:** Alles in SQLite, Resume-fähig

---

Für Details siehe:
- [MODULE_SPECS_v2.md](./MODULE_SPECS_v2.md) - Modul-Spezifikationen
- [WORKFLOW.md](../WORKFLOW.md) - Detaillierter Workflow
- [INSTALLATION.md](../INSTALLATION.md) - Setup-Anleitung
