# Academic Agent v2.0 - Architektur-Dokumentation

**Erstellt:** 2026-02-23
**Ziel:** Detaillierte Architektur-Beschreibung für v2.0

---

## 📋 Übersicht

### Vergleich: v1.0 vs v2.0

| Aspect | v1.0 (Alt) | v2.0 (Neu) |
|--------|-----------|------------|
| **Agents** | 1 Orchestrator + 5 Sub-Agents | 1 Linear Coordinator |
| **Architektur** | Hierarchisch, asynchron | Linear Coordinator + Module |
| **Datenquellen** | Web-Scraping (Browser) | APIs (CrossRef, OpenAlex, S2) |
| **Koordination** | Asynchron via Task-Tool | Synchron, Schritt-für-Schritt |
| **Modularität** | Agent-basiert | Hybrid: 3 Haiku-Agents + 10 Python-Module |
| **User Feedback** | Headless + tmux (unsichtbar) | Headful Browser + stdout |
| **PDF Access** | Direct Download (fehlerhaft) | API → DBIS Browser (Institutional) |
| **State** | JSON (research_state.json) | SQLite + JSON Backup |
| **Fehlerbehandlung** | Abbruch | Fallback-Chain + Recovery |
| **Erfolgsrate** | ~60% | **Ziel: 85-92%** |
| **Cost pro Run** | ~$2.15 | **$0.27 (87% günstiger)** |

---

## 🏗️ Architektur-Entscheidung: Linear Coordinator + Module

### v1.0 Problem: Multi-Agent-Hierarchie

```
┌─────────────────────────────────────┐
│      Orchestrator Agent             │  ← Versagt beim Agent-Spawning
│   (Task-Tool Koordination)          │
└──────────────┬──────────────────────┘
               │
    ┌──────────┼──────────┬──────────┬──────────┐
    ▼          ▼          ▼          ▼          ▼
┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│ Search │ │Browser │ │Scoring │ │Extract │ │ Setup  │
│ Agent  │ │ Agent  │ │ Agent  │ │ Agent  │ │ Agent  │
└────────┘ └────────┘ └────────┘ └────────┘ └────────┘
```

**Probleme:**
- Asynchrone Kommunikation (Task-Tool) ist fehleranfällig
- Orchestrator muss Agent-Lifecycle managen (spawn, wait, error-handling)
- Debugging schwer: Welcher Agent hat versagt? Wo ist der State?
- Overhead: Jeder Sub-Agent hat eigenen Context, eigene Instruktionen

---

### Warum KEIN Monolithischer Agent?

```
❌ Monolithischer Agent (FALSCH):
┌─────────────────────────────────────────────┐
│   Ein riesiger "Do Everything" Agent        │
│                                             │
│   - Search-Logik                            │
│   - Browser-Steuerung                       │
│   - Scoring-Algorithmen                     │
│   - PDF-Parsing                             │
│   - Quote-Extraction                        │
│   - Error-Handling                          │
│                                             │
│   (10.000+ Zeilen Prompt)                  │
└─────────────────────────────────────────────┘
```

**Probleme:**
- Prompt Explosion (10.000+ Zeilen)
- Keine Spezialisierung (macht alles "ok", nichts "gut")
- Testing unmöglich (nur E2E-Tests)
- Debugging Albtraum (alles in einem Stack Trace)

---

### v2.0 Lösung: Linear Coordinator + Module

```
v2.0 Architektur (RICHTIG):
┌────────────────────────────────────────────────────────────┐
│              Linear Coordinator Agent                      │
│          (Koordiniert Workflow, macht nicht alles selbst)  │
└──────────────────────┬─────────────────────────────────────┘
                       │
                       │ Ruft Python-Module direkt auf:
                       │
    ┌──────────────────┼─────────────────┬─────────────────┬────────────┐
    ▼                  ▼                 ▼                 ▼            ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ SearchEngine │ │ PDFFetcher   │ │ FiveDScorer  │ │QuoteExtractor│ │ StateManager │
│  (Modul)     │ │  (Modul)     │ │  (Modul)     │ │  (Modul)     │ │  (Modul)     │
│              │ │              │ │              │ │              │ │              │
│ - CrossRef   │ │ - Unpaywall  │ │ - Relevanz   │ │ - PDF Parse  │ │ - SQLite     │
│ - OpenAlex   │ │ - CORE       │ │ - Recency    │ │ - Validation │ │ - JSON       │
│ - S2 API     │ │ - Browser    │ │ - Authority  │ │ - Context    │ │ - Checkpoints│
└──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘
```

**Vorteile:**
- ✅ Ein Agent (keine Task-Tool-Koordination)
- ✅ Modularer Code (Python-Klassen, testbar, wiederverwendbar)
- ✅ Spezialisierung (jedes Modul ist ein Experte)
- ✅ Linearer Flow (Agent ruft Module sequenziell auf)
- ✅ Klarer State (ein Process, ein Stack Trace)
- ✅ Debugging einfach (Modul-Tests + Integration-Tests)

---

## 🤖 Agents vs Python-Module

### Agents = LLM-Prompts (.md Dateien)

```
.claude/agents/
├── linear_coordinator.md    # Sonnet Agent (Prompt für LLM)
├── query_generator.md        # Haiku Agent (Prompt für LLM)
├── five_d_scorer.md          # Haiku Agent (Prompt für LLM)
└── quote_extractor.md        # Haiku Agent (Prompt für LLM)
```

**Was sind das?**
- Markdown-Dateien mit Instruktionen für den LLM
- Enthalten Prompt-Engineering
- Werden via Anthropic SDK / Task Tool aufgerufen
- **4 Agents gesamt:** 1 Sonnet + 3 Haiku

---

### Python-Module = Deterministischer Code (.py Dateien)

```
src/pdf/
├── pdf_fetcher.py               # Python-Klasse (KEIN Agent!)
├── unpaywall_client.py          # API-Client (KEIN Agent!)
├── dbis_browser_downloader.py  # Browser-Code (KEIN Agent!)
└── shibboleth_auth.py           # Auth-Logik (KEIN Agent!)
```

**Was sind das?**
- Normale Python-Klassen und Funktionen
- Deterministischer Code (API-Calls, Browser, etc.)
- Werden von Agents AUFGERUFEN (import + direkter Call)
- **10 Module gesamt:** Alle in `src/`

---

## 📂 Ordnerstruktur v2.0 (Implementiert)

```
.claude/
├── agents/                      # 4 Agent-Definitionen (.md)
│   ├── linear_coordinator.md   # Sonnet - Haupt-Coordinator
│   ├── query_generator.md      # Haiku - Boolean-Queries
│   ├── five_d_scorer.md        # Haiku - Relevanz-Scoring
│   └── quote_extractor.md      # Haiku - Zitat-Extraktion
│
├── skills/research/             # Research Skill (Entry-Point)
│   ├── SKILL.md                # ✅ Implementiert - User-Interaktion
│   └── scripts/
│       └── config_loader.py    # ✅ Implementiert - Config laden/validieren
│
└── settings.json               # ✅ Implementiert - Agent-Konfiguration

config/                          # ✅ Implementiert - Konfigurationsdateien
├── research_modes.yaml         # Quick/Standard/Deep Modi
├── api_config.yaml             # API Keys, Rate-Limits, Endpoints
└── academic_context.md         # Optional - Akademischer Kontext

src/                            # Python-Module
├── coordinator/
│   ├── __init__.py
│   └── coordinator_runner.py   # Python-Wrapper für Agent-Execution
│
├── search/
│   ├── __init__.py
│   ├── search_engine.py        # Wrapper für alle Search-APIs
│   ├── crossref_client.py      # CrossRef API
│   ├── openalex_client.py      # OpenAlex API
│   ├── semantic_scholar_client.py  # Semantic Scholar API
│   └── deduplicator.py         # DOI-basierte Deduplizierung
│
├── ranking/
│   ├── __init__.py
│   ├── five_d_scorer.py        # 5D-Scoring: Hybrid (Python + Haiku Relevanz)
│   ├── citation_enricher.py    # Citation Counts via APIs
│   └── portfolio_balancer.py   # Portfolio-Balance
│
├── pdf/
│   ├── __init__.py
│   ├── pdf_fetcher.py              # Orchestriert PDF-Download
│   ├── unpaywall_client.py         # Unpaywall API
│   ├── core_client.py              # CORE API
│   ├── dbis_browser_downloader.py  # DBIS via Headful Browser
│   ├── publisher_navigator.py      # Publisher-Navigation (IEEE, ACM, Springer)
│   └── shibboleth_auth.py          # TIB Shibboleth-Auth
│
├── extraction/
│   ├── __init__.py
│   ├── quote_extractor.py      # Quote-Extraction (Haiku)
│   ├── quote_validator.py      # Validierung gegen PDF
│   └── pdf_parser.py           # PyMuPDF Wrapper
│
├── state/
│   ├── __init__.py
│   ├── state_manager.py        # SQLite + JSON State
│   ├── database.py             # SQLAlchemy Models
│   └── checkpointer.py         # Resume-Funktionalität
│
├── ui/
│   ├── __init__.py
│   ├── progress_ui.py          # Rich Progress Bars
│   └── error_formatter.py      # User-friendly Errors
│
└── utils/
    ├── __init__.py
    ├── retry.py                # Retry-Logik mit tenacity
    ├── rate_limiter.py         # Rate-Limiting
    ├── cache.py                # Lokales Caching
    └── config.py               # Pydantic Config Models
```

---

## 🎯 Entry-Point: Research Skill

### Skill-Struktur (Implementiert)

```
.claude/skills/research/
├── SKILL.md                    # ✅ Entry-Point mit User-Interaktion
└── scripts/
    └── config_loader.py        # ✅ Config-Loading & Validierung
```

### Workflow: User → Skill → Agent → Module

```
User: /research "DevOps Governance"
  ↓
SKILL.md:
  1. Begrüßt User
  2. Fragt nach Recherche-Modus (Quick/Standard/Deep)
  3. Lädt config/research_modes.yaml
  4. Lädt optional config/academic_context.md
  5. Validiert mit config_loader.py
  6. Spawnt Linear Coordinator Agent (EINMAL!)
  ↓
Linear Coordinator Agent:
  1. Initialisiert State (SQLite + JSON)
  2. Ruft SearchEngine.search() auf
  3. Ruft FiveDScorer.score() auf
  4. Ruft PDFFetcher.fetch() auf
  5. Ruft QuoteExtractor.extract() auf
  6. Erstellt finale Ausgabe
  ↓
Python-Module:
  - Deterministischer Code
  - API-Calls
  - PDF-Downloads
  - Datenverarbeitung
```

### Wichtige Design-Entscheidung: Simplicity

**Warum nur SKILL.md + config_loader.py?**

❌ **NICHT:** Komplexe Skill-Struktur mit vielen Scripts
```
skills/research/
├── SKILL.md
├── scripts/
│   ├── setup_research.py
│   ├── load_context.py
│   ├── validate_config.py
│   ├── mode_selector.py
│   └── ... (zu viel!)
```

✅ **SONDERN:** Minimal aber effektiv
```
skills/research/
├── SKILL.md              # LLM macht User-Interaktion
└── scripts/
    └── config_loader.py  # Python macht Datenverarbeitung
```

**Prinzip:** "LLM wo nötig (UX), Python wo möglich (Data)"

---

## 📁 Konfigurationsdateien (Implementiert)

### config/research_modes.yaml

Definiert 4 Recherche-Modi:

```yaml
modes:
  quick:
    max_papers: 15
    estimated_duration_min: 20
    api_sources: [crossref, openalex, semantic_scholar]

  standard:  # Empfohlen
    max_papers: 25
    estimated_duration_min: 35
    api_sources: [crossref, openalex, semantic_scholar, google_scholar]

  deep:
    max_papers: 40
    estimated_duration_min: 60
    api_sources: [crossref, openalex, semantic_scholar, google_scholar, ieee_xplore]

  custom:
    # User-definierbar
```

**Features:**
- Mode-spezifische Scoring-Kriterien
- API-Prioritäten
- Fallback-Strategien
- Portfolio-Balance (Deep Mode)

### config/api_config.yaml

Zentrale API-Konfiguration:

```yaml
api_keys:
  crossref_email: ""
  openalex_email: ""
  semantic_scholar_api_key: ""
  unpaywall_email: ""
  core_api_key: ""

rate_limits:
  crossref: {requests_per_second: 50}
  openalex: {requests_per_second: 10}
  semantic_scholar: {requests_per_second: 1}

timeouts:
  api_request: 30
  pdf_download: 60

retry:
  max_attempts: 3
  backoff_factor: 2
```

**Features:**
- Environment Variable Fallback
- Adaptive Rate-Limiting
- Retry-Strategien
- Health Checks
- Caching (SQLite, 24h TTL)

### config/academic_context.md (Optional)

User-spezifische Präferenzen:

```markdown
## Disziplin
Computer Science / Software Engineering

## Keywords
- DevOps
- Continuous Integration
- Infrastructure as Code

## Bevorzugte Datenbanken
- IEEE Xplore
- ACM Digital Library

## Qualitätskriterien
- Minimum Citation Count: 3
- Max Paper Age: 7 Jahre
```

**Verwendung:** Query-Optimierung, Relevanz-Scoring, Datenbank-Auswahl

---

## ⚙️ Agent-Konfiguration: .claude/settings.json

```json
{
  "agents": {
    "linear_coordinator": {
      "model": "claude-sonnet-4-5",
      "max_tokens": 8192,
      "temperature": 0.3
    },
    "query_generator": {
      "model": "claude-haiku-4",
      "max_tokens": 2048,
      "temperature": 0.5
    },
    "five_d_scorer": {
      "model": "claude-haiku-4",
      "temperature": 0.2
    },
    "quote_extractor": {
      "model": "claude-haiku-4",
      "temperature": 0.1
    }
  },
  "workflow": {
    "default_mode": "standard",
    "auto_resume_on_error": true,
    "checkpoint_interval_minutes": 5
  },
  "pdf": {
    "fallback_chain": ["unpaywall", "core", "dbis_browser"],
    "dbis_browser_delay_seconds": 15
  },
  "scoring": {
    "relevance_weight": 0.4,
    "recency_weight": 0.2,
    "quality_weight": 0.2,
    "authority_weight": 0.2,
    "use_llm_relevance": true
  }
}
```

---

Für vollständige Code-Beispiele siehe [V2_ROADMAP_FULL.md](../V2_ROADMAP_FULL.md)
