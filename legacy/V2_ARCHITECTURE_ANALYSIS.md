# Academic Agent v1.0 - Architektur-Analyse

**Erstellt:** 2026-02-23
**Zweck:** Detaillierte Code-Analyse für v2.0 Planung

---

## 📁 Aktuelle Struktur (legacy/)

### Code-Organisation

```
legacy/
├── .claude/
│   ├── agents/          # 5 Agent-Definitionen (.md)
│   ├── shared/          # Shared Policies (Security, Observability)
│   └── skills/          # Claude Code Skills
├── scripts/             # 28 Python-Scripts
├── shared/              # ORCHESTRATOR_BASH_LIB.sh
├── config/              # academic_context.md, database_disciplines.yaml
├── schemas/             # JSON Schemas (candidates, quotes, ranked)
├── tests/               # unit/, integration/, e2e/
└── 01 TEST_RUN/         # Letzter Test-Run (komplett)
```

### Python-Scripts (28 Files, ~8k Lines)

**Größte Dateien:**
- `generate_config.py` (525 lines) - Setup & Konfiguration
- `metrics.py` (488 lines) - Observability
- `cost_tracker.py` (460 lines) - Budget-Tracking
- `retry_strategy.py` (434 lines) - Retry-Logic
- `cdp_wrapper.py` (422 lines) - Chrome DevTools Protocol
- `pdf_security_validator.py` (406 lines) - PDF-Validierung

**Kategorien:**
1. **Setup** (3): generate_config, interactive_setup, validate_config
2. **Browser** (5): cdp_wrapper, cdp_fallback_manager, browser_cdp_helper.js, track_navigation
3. **State** (2): state_manager, validate_state
4. **Security** (5): validation_gate, action_gate, pdf_security_validator, sanitize_html, validate_domain
5. **Retry/Error** (4): retry_strategy, enforce_retry, error_handler.sh, error_types
6. **Observability** (4): metrics, logger, log_event, cost_tracker
7. **Output** (3): create_bibliography, create_quote_library_with_citations
8. **Monitoring** (2): live_monitor, status_watcher

---

## 🤖 Agent-System (v1.0)

### Agent-Definitionen (.claude/agents/)

1. **orchestrator-agent.md** - Workflow-Koordination (BROKEN)
2. **search-agent.md** - Boolean-Suchstring-Generierung (✅ WORKS)
3. **browser-agent.md** - Web-Scraping (⚠️ PARTIAL)
4. **scoring-agent.md** - 5D-Scoring (✅ WORKS)
5. **extraction-agent.md** - Quote-Extraktion (✅ WORKS)
6. **setup-agent.md** - Initial Setup (✅ WORKS)

### Agent-Tools & Permissions

| Agent | Tools | DisallowedTools |
|-------|-------|-----------------|
| orchestrator | Task, Read, Write, Bash | Edit |
| search | Read, Write, Grep, Glob, WebSearch | Edit, Bash, Task |
| browser | Read, Write, Bash (CDP) | Edit, Task |
| scoring | Read, Write, Grep, Glob | Edit, Bash, WebFetch, Task |
| extraction | Read, Write | Edit, Bash, Task |

**Problem:** Orchestrator spawnt keine Sub-Agents (Task-Tool failure)

---

## 🔑 Kern-Komponenten

### 1. State Management (state_manager.py)

**Funktionen:**
- `save_state(run_dir, phase, status, data)` - State speichern
- `load_state(run_dir)` - State laden
- `get_last_completed_phase(run_dir)` - Letzte Phase finden
- `get_resume_point(run_dir)` - Resume-Punkt bestimmen

**State-File:** `metadata/research_state.json`

**Status-Werte:** `pending`, `in_progress`, `completed`, `failed`

**✅ Gut:** Funktioniert, ermöglicht Resume
**⚠️ Problem:** JSON-basiert, keine Queries möglich

---

### 2. Quote Extraction (create_quote_library_with_citations.py)

**Funktionen:**
- `format_apa7_reference(source)` - APA 7 Zitierung
- `format_mla_reference(source)` - MLA 9 Zitierung
- `format_chicago_reference(source)` - Chicago 17 Zitierung

**Input:** `metadata/quotes.json` + `metadata/candidates.json`
**Output:** `outputs/Quote_Library.csv`, `outputs/bibliography.md`

**✅ Gut:** Multi-Format-Support, funktioniert
**❌ Fehlt:** Validierung ob Zitat wirklich im PDF steht

---

### 3. Browser Automation (cdp_wrapper.py, 422 lines)

**Hauptklasse:** `CDPSession`

**Methoden:**
- `connect()` - Chrome DevTools Protocol verbinden
- `navigate(url)` - Seite öffnen
- `extract_results()` - HTML-Parsing
- `download_pdf(url)` - PDF herunterladen

**✅ Gut:** CDP funktioniert
**❌ Problem:** Headless mode, CSS-Selektoren veraltet

---

### 4. Security (validation_gate.py, 292 lines)

**Validierungen:**
- Domain-Whitelisting
- Path-Sanitization
- Injection-Detection
- File-Type-Validation

**✅ Gut:** Umfassende Security-Checks
**⚠️ Overhead:** Zu viele Validierungen für API-basiertes System

---

### 5. Retry Logic (retry_strategy.py, 434 lines)

**Strategien:**
- Exponential Backoff
- Circuit Breaker
- Rate Limiting
- Timeout Management

**✅ Gut:** Professionelle Fehlerbehandlung
**📦 Keep:** Für v2.0 übernehmen (mit tenacity library)

---

## 📊 Datenfluss v1.0

```
Phase 0: Setup
├─► generate_config.py → run_config.json
└─► setup-agent → metadata/databases.json

Phase 1: Search Strings
└─► search-agent → metadata/search_strings.json

Phase 2: Web Search
├─► browser-agent + cdp_wrapper.py
├─► Browser navigiert zu ACM/IEEE/Scholar
└─► metadata/candidates.json (15 Papers)

Phase 3: Ranking
├─► scoring-agent
├─► 5D-Scoring (Python logic, nicht external script)
└─► metadata/ranked_candidates.json (6 Papers)

Phase 4: PDF Download
├─► browser-agent + cdp_wrapper.py
└─► pdfs/ (1/6 erfolgreich)

Phase 5: Quote Extraction
├─► extraction-agent (PyMuPDF)
├─► create_quote_library_with_citations.py
└─► outputs/quote_library.json (18 Zitate)

Phase 6: Finalization
└─► create_bibliography.py → outputs/bibliography.md
```

---

## ✅ Was funktioniert (Migrieren zu v2.0)

### 1. Search-Agent Logik
**Dateien:** `.claude/agents/search-agent.md`
**Funktionalität:** Boolean-Query-Generierung
**Migration:** ✅ Portieren, aber für APIs anpassen

### 2. 5D-Scoring
**Dateien:** `.claude/agents/scoring-agent.md`
**Funktionalität:** Relevanz, Recency, Quality, Authority, Portfolio-Balance
**Migration:** ✅ Behalten + Citation-Counts via API hinzufügen

### 3. Quote-Extraktion
**Dateien:** `create_quote_library_with_citations.py`
**Funktionalität:** PDF-Parsing + APA/MLA/Chicago
**Migration:** ✅ Behalten + Validierung hinzufügen

### 4. Retry-Logic
**Dateien:** `retry_strategy.py`
**Funktionalität:** Exponential Backoff, Circuit Breaker
**Migration:** ✅ Behalten (mit tenacity library)

### 5. State Management
**Dateien:** `state_manager.py`
**Funktionalität:** Phase-Tracking, Resume-Funktionalität
**Migration:** ✅ Behalten + SQLite hinzufügen

---

## ❌ Was nicht funktioniert (Neu machen)

### 1. Orchestrator
**Dateien:** `.claude/agents/orchestrator-agent.md`
**Problem:** Spawnt keine Sub-Agents nach Phase 1
**v2 Lösung:** Linear Workflow Agent (synchron)

### 2. Browser-Scraping
**Dateien:** `cdp_wrapper.py`, `.claude/agents/browser-agent.md`
**Problem:** CSS-Selektoren veraltet, Anti-Bot-Protection
**v2 Lösung:** APIs primär, Browser nur Fallback

### 3. Live Monitor
**Dateien:** `live_monitor.py`, `setup_tmux_monitor.sh`
**Problem:** tmux unsichtbar, zu komplex
**v2 Lösung:** stdout + rich library

---

## 🔧 v2.0 Migrations-Plan

### Phase 0 (Foundation)
**Migrieren:**
- `state_manager.py` → `src/database/state.py` (+ SQLite)
- `retry_strategy.py` → `src/utils/retry.py` (mit tenacity)

**Neu erstellen:**
- `src/api/base_client.py` (NEU)
- `src/workflow_v2.py` (Linear statt Orchestrator)

### Phase 1 (Search)
**Migrieren:**
- `.claude/agents/search-agent.md` Logik → `src/search/query_generator_v2.py`

**Neu erstellen:**
- `src/search/crossref_client.py` (NEU)
- `src/search/openalex_client.py` (NEU)
- `src/search/semantic_scholar_client.py` (NEU)

### Phase 2 (Ranking)
**Migrieren:**
- `.claude/agents/scoring-agent.md` Logik → `src/ranking/scorer_v2.py`

### Phase 3 (PDF)
**Neu erstellen:**
- `src/pdf/unpaywall_client.py` (NEU)
- `src/pdf/core_client.py` (NEU)

**Optional migrieren:**
- `cdp_wrapper.py` → `src/pdf/browser_downloader.py` (headful mode)

### Phase 4 (Extraction)
**Migrieren:**
- `create_quote_library_with_citations.py` → `src/extraction/quote_extractor_v2.py`

**Neu hinzufügen:**
- `src/extraction/quote_validator.py` (NEU - gegen Halluzination)

### Phase 5 (UX)
**Neu erstellen:**
- `src/ui/progress_bar.py` (rich library, NEU)
- `src/ui/live_metrics.py` (NEU)

**Löschen:**
- `live_monitor.py` (zu komplex)
- `setup_tmux_monitor.sh` (nicht nötig)

---

## 📦 Code-Wiederverwendung

### Übernehmen (70% des Codes)
- ✅ State Management Logik
- ✅ Retry Strategies
- ✅ Quote Extraction & Citation Formatting
- ✅ 5D-Scoring Algorithmus
- ✅ Security Validation Utils (teilweise)
- ✅ Error Types & Logging

### Neu schreiben (30% des Codes)
- ❌ Orchestrator (Linear Workflow)
- ❌ Browser-Scraping (API-First)
- ❌ Live Monitor (stdout + rich)
- ❌ Setup Scripts (vereinfachen)

---

## 🎯 Kern-Erkenntnisse

### Was v1 richtig macht
1. **Modulare Agent-Architektur** - Gute Separation of Concerns
2. **State Management** - Resume-Funktionalität solide
3. **Multi-Format-Citations** - APA/MLA/Chicago Support
4. **Security-First** - Umfassende Validierungen
5. **Observability** - Gutes Logging & Metrics

### Was v1 falsch macht
1. **Orchestrator-Komplexität** - Asynchrone Koordination versagt
2. **Scraping-First** - Fragil, keine APIs
3. **Headless Browser** - User sieht nichts
4. **Zu viele Shell-Scripts** - 20+ .sh Files, schwer wartbar
5. **Kein Testing** - Tests existieren, aber nicht verwendet

---

**Fazit:** 70% des Codes ist gut und wiederverwendbar. 30% (Orchestrator, Browser, Monitoring) neu schreiben.
