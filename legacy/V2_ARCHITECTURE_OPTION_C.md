# Academic Agent v2.0 - Architektur Option C

**Option:** Linear Coordinator + Module (Anthropic Best Practice)
**Datum:** 2026-02-23

---

## 🎯 Architektur-Entscheidung: Option C

**Basierend auf:**
- ✅ Anthropic Cookbook Best Practices (Sub-Agents Pattern)
- ✅ v1.0 Fehler-Analyse (Orchestrator versagt)
- ✅ Simplicity > Complexity

**Option C = Linear Coordinator + Module**

---

## 📐 Architektur-Diagramm

```
┌─────────────────────────────────────────────────────┐
│   🎯 Linear Coordinator (Sonnet 4.5)                │
│   ├─ src/coordinator.py                             │
│   ├─ Führt Workflow linear aus (Phase 0-6)         │
│   ├─ Ruft Module direkt auf (function calls)       │
│   └─ Nutzt Tools für externe APIs                  │
└─────────────────────────────────────────────────────┘
           │
           │ Sequential Execution
           │
           ├──► 📦 Module 1: Search (Haiku)
           │    ├─ Tool: search_crossref()
           │    ├─ Tool: search_openalex()
           │    ├─ Tool: search_semantic_scholar()
           │    └─ Parallel via ThreadPoolExecutor
           │
           ├──► 📦 Module 2: Ranking (Haiku)
           │    ├─ 5D-Scoring (local)
           │    ├─ Deduplication
           │    └─ Portfolio-Balance
           │
           ├──► 📦 Module 3: PDF Acquisition (Haiku)
           │    ├─ Tool: unpaywall_fetch()
           │    ├─ Tool: core_fetch()
           │    ├─ Tool: browser_download() [Fallback]
           │    └─ Parallel Downloads
           │
           └──► 📦 Module 4: Quote Extraction (Haiku)
                ├─ Tool: extract_pdf_text()
                ├─ Tool: validate_quote()
                └─ Parallel Processing
```

---

## 🔑 Kern-Komponenten

### 1. Linear Coordinator

**File:** `src/coordinator.py`
**Model:** Claude Sonnet 4.5
**Verantwortlich für:**
- Workflow-Orchestration (Phase 0-6)
- Modul-Aufrufe (function calls, nicht Task-Tool)
- Fortschritt-Tracking
- Error Handling & Fallbacks
- User Communication

**Pseudocode:**
```python
class LinearCoordinator:
    def __init__(self):
        self.client = anthropic.Anthropic()
        self.model = "claude-sonnet-4-5"
        self.modules = {
            "search": SearchModule(),
            "ranking": RankingModule(),
            "pdf": PDFModule(),
            "extraction": ExtractionModule()
        }

    def run_workflow(self, research_question):
        # Phase 0: Setup
        config = self.setup(research_question)

        # Phase 1: Search
        papers = self.modules["search"].execute(config.query)

        # Phase 2: Ranking
        ranked = self.modules["ranking"].execute(papers)

        # Phase 3: PDF Acquisition
        pdfs = self.modules["pdf"].execute(ranked[:15])

        # Phase 4: Quote Extraction
        quotes = self.modules["extraction"].execute(pdfs)

        # Phase 5: Finalization
        return self.finalize(quotes)
```

---

### 2. Module (Hybrid: Python + Haiku)

**WICHTIG:** Module sind NICHT alle Agents!

**2 Typen:**

#### A. Python-Module (Deterministisch, KEIN LLM)
- API-Clients (CrossRef, OpenAlex, Semantic Scholar)
- PDF-Downloader
- Deduplication-Logik
- State-Manager (SQLite)
- **Kein LLM nötig** → Normale Python-Klassen

#### B. Haiku-Module (Semantisch, MIT LLM)
- Quote-Extraction (braucht Textverständnis)
- Query-Generation (braucht Kontext-Verständnis)
- Relevanz-Scoring (teilweise semantisch)
- **Model:** Claude Haiku 4.5 (günstig für repetitive Semantic-Tasks)

**Characteristics:**
- Spezifische, fokussierte Tasks
- Python-Module: Direkte Logik
- Haiku-Module: LLM-Calls für Semantik
- Strukturierte Outputs (Pydantic Models)
- Parallel ausführbar

---

#### Modul 1: Search

**File:** `src/modules/search_module.py`

**Input:**
```python
SearchRequest(
    query: str,
    target_count: int,
    databases: List[str]
)
```

**Output:**
```python
SearchResult(
    papers: List[Paper],
    sources: Dict[str, int],  # CrossRef: 10, OpenAlex: 8, ...
    duration: float
)
```

**Tools:**
```python
tools = [
    {
        "name": "search_crossref",
        "description": "Search peer-reviewed papers via CrossRef API",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "limit": {"type": "integer", "default": 20}
            }
        }
    },
    # ... OpenAlex, Semantic Scholar
]
```

**Execution:**
```python
# Parallel API-Calls
with ThreadPoolExecutor() as executor:
    futures = {
        executor.submit(crossref_client.search, query): "CrossRef",
        executor.submit(openalex_client.search, query): "OpenAlex",
        executor.submit(s2_client.search, query): "S2"
    }
    results = [f.result() for f in as_completed(futures)]
```

---

#### Modul 2: Ranking

**File:** `src/modules/ranking_module.py`

**Input:** `List[Paper]`
**Output:** `List[RankedPaper]` (sorted by score)

**Scoring:**
```python
def score_paper(paper):
    relevance = compute_relevance(paper.title, paper.abstract, query)
    recency = compute_recency(paper.year)
    quality = compute_quality(paper.journal, paper.citations)
    authority = compute_authority(paper.authors, paper.citations)
    accessibility = compute_accessibility(paper.doi, paper.open_access)

    return (relevance * 0.3) + (recency * 0.2) + (quality * 0.2) + \
           (authority * 0.15) + (accessibility * 0.15)
```

**Keine Tools nötig** (lokale Berechnung)

---

#### Modul 3: PDF Acquisition

**File:** `src/modules/pdf_module.py`

**Input:** `List[RankedPaper]` (top 15)
**Output:** `List[DownloadedPDF]`

**Fallback-Chain:**
1. **Unpaywall API** (Open Access)
2. **CORE API** (Repositories)
3. **Browser Download** (Playwright, headful)
4. **Manual Instructions** (User-Download)

**Tools:**
```python
tools = [
    {"name": "unpaywall_fetch", "description": "Fetch Open Access PDF"},
    {"name": "core_fetch", "description": "Fetch from repository"},
    {"name": "browser_download", "description": "Headful browser download"}
]
```

**Execution:**
```python
# Parallel Downloads
with ThreadPoolExecutor(max_workers=5) as executor:
    futures = [executor.submit(download_pdf, paper) for paper in papers]
    pdfs = [f.result() for f in as_completed(futures)]
```

---

#### Modul 4: Quote Extraction

**File:** `src/modules/extraction_module.py`

**Input:** `List[DownloadedPDF]`
**Output:** `List[ValidatedQuote]`

**Tools:**
```python
tools = [
    {"name": "extract_pdf_text", "description": "Extract text from PDF (PyMuPDF)"},
    {"name": "validate_quote", "description": "Validate quote against PDF (fuzzy match)"}
]
```

**Validation (KRITISCH):**
```python
def validate_quote(quote_text, pdf_text):
    from fuzzywuzzy import fuzz
    best_match = max(
        fuzz.partial_ratio(quote_text, pdf_text[i:i+len(quote_text)+50])
        for i in range(len(pdf_text) - len(quote_text))
    )
    return best_match >= 90  # 90% threshold
```

---

## 🔄 Execution Flow

### Sequentielle Phasen

```python
def run_workflow(research_question):
    # Phase 0: Setup (Coordinator)
    config = setup_phase(research_question)

    # Phase 1: Search (Modul 1 - Parallel)
    papers = search_module.execute(config)

    # Phase 2: Ranking (Modul 2 - Sequential)
    ranked = ranking_module.execute(papers)

    # Phase 3: PDF Acquisition (Modul 3 - Parallel)
    pdfs = pdf_module.execute(ranked[:15])

    # Phase 4: Quote Extraction (Modul 4 - Parallel)
    quotes = extraction_module.execute(pdfs)

    # Phase 5: Finalization (Coordinator)
    return finalize_phase(quotes)
```

### Parallel Execution (innerhalb Module)

**Phase 1 - Search:**
```
CrossRef API  ┐
OpenAlex API  ├──► Parallel ──► Merge Results
Semantic S2   ┘
```

**Phase 3 - PDF Downloads:**
```
Paper 1 PDF  ┐
Paper 2 PDF  │
Paper 3 PDF  ├──► Parallel ──► Collect PDFs
...          │
Paper 15 PDF ┘
```

**Phase 4 - Quote Extraction:**
```
PDF 1 Quotes  ┐
PDF 2 Quotes  ├──► Parallel ──► Validate & Collect
PDF 3 Quotes  ┘
```

---

## 🆚 Vergleich: v1.0 vs v2.0 (Option C)

| Aspect | v1.0 | v2.0 (Option C) |
|--------|------|-----------------|
| **Koordination** | Orchestrator-Agent (Task-Tool) | Linear Coordinator (function calls) |
| **Sub-Agents** | 5 Agents (async spawning) | 4 Module (direkte Aufrufe) |
| **Model** | Alle Sonnet | Coordinator: Sonnet, Module: Haiku |
| **Parallelisierung** | ❌ Keine | ✅ ThreadPoolExecutor |
| **Fehlerbehandlung** | ❌ Abbruch | ✅ Fallback-Chain |
| **API-Calls** | ❌ Browser-Scraping | ✅ Tools (CrossRef, OpenAlex, S2) |
| **Komplexität** | ❌ Hoch (Agent spawnt Agent) | ✅ Niedrig (linear) |
| **Erfolgsrate** | 60% (6.3/10) | **Ziel: 99%** |

---

## 💰 Cost Optimization

**v1.0 Kosten (35 Min Run):**
- 208,753 Tokens × Sonnet (~$2.15)

**v2.0 Kosten (Geschätzt 18 Min):**
```
Coordinator (Sonnet):   50k tokens  × $3/1M  = $0.15
Module 1 (Haiku):       30k tokens  × $0.25/1M = $0.008
Module 2 (Haiku):       20k tokens  × $0.25/1M = $0.005
Module 3 (Haiku):       40k tokens  × $0.25/1M = $0.010
Module 4 (Haiku):       60k tokens  × $0.25/1M = $0.015
──────────────────────────────────────────────────────
Total:                 200k tokens            ≈ $0.19
```

**Einsparung:** ~90% Kosten (Haiku statt Sonnet für Module)

---

## 🎯 Warum Option C?

### ✅ Vorteile

1. **Simplicity** - Linear, kein komplexes Agent-Spawning
2. **Anthropic Best Practice** - Sub-Agents Pattern aus Cookbook
3. **Zuverlässig** - Keine async Koordination (v1 Problem)
4. **Schnell** - Parallel Execution wo möglich
5. **Günstig** - Haiku für repetitive Tasks
6. **Transparent** - User sieht jeden Schritt

### ❌ v1.0 Probleme gelöst

- ✅ Orchestrator spawnt keine Agents → Coordinator ruft Module direkt
- ✅ Async Koordination fehleranfällig → Synchron, linear
- ✅ Keine Parallelisierung → ThreadPoolExecutor
- ✅ Teuer (alles Sonnet) → Haiku für Module

---

## 📋 Implementation Reihenfolge

### Sprint 1 (Woche 1-2): Foundation
1. Coordinator Skeleton (`coordinator.py`)
2. Module Base Class (`base_module.py`)
3. Tool Definitions (`tools.py`)
4. SQLite Schema (`database.py`)

### Sprint 2 (Woche 3-4): Search Module
1. Search Module (`search_module.py`)
2. API Clients (CrossRef, OpenAlex, S2)
3. Parallel Execution
4. Tests

### Sprint 3 (Woche 5): Ranking Module
1. Ranking Module (`ranking_module.py`)
2. 5D-Scoring
3. Deduplication
4. Tests

### Sprint 4 (Woche 6-7): PDF Module
1. PDF Module (`pdf_module.py`)
2. Unpaywall/CORE Clients
3. Browser Fallback
4. Tests

### Sprint 5 (Woche 8): Extraction Module
1. Extraction Module (`extraction_module.py`)
2. Quote Validator
3. Parallel Processing
4. Tests

### Sprint 6 (Woche 9-10): Integration & Testing
1. E2E Tests
2. UX (Progress Bar)
3. Error Handling
4. Documentation

---

**Status:** Architecture defined
**Next:** Implement Phase 0 (Coordinator Skeleton)
