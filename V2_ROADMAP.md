# Academic Agent v2.0 - Roadmap

**Erstellt:** 2026-02-23
**Status:** Architektur finalisiert - Szenario B (Smart-LLM) gewählt
**Ziel:** Ein zuverlässiges KI-Agenten-System für akademische Recherche
**Erfolgsmetrik:** 85-92% Erfolgsrate, vollständig autonom, transparent

---

## 📌 Executive Summary

### Kern-Architektur v2.0

```
1 Sonnet-Agent (Coordinator)
  ↓
  ├─ 3 Haiku-Agents (Semantik)
  │   ├─ QueryGenerator
  │   ├─ FiveDScorer-Relevanz (Hybrid)
  │   └─ QuoteExtractor
  │
  └─ 10 Python-Module (Deterministisch)
      ├─ API-Clients (CrossRef, OpenAlex, S2)
      ├─ PDF-Fetcher (Unpaywall, CORE, DBIS-Browser)
      ├─ StateManager, Deduplicator
      └─ ProgressUI, QuoteValidator
```

### Key Metrics (v1.0 → v2.0)

| Metrik | v1.0 | v2.0 (Szenario B) | Verbesserung |
|--------|------|-------------------|--------------|
| **Erfolgsrate** | 60% | 85-92% | +42% |
| **Manuelle Interventionen** | 4x pro Run | 0-1x | -75% |
| **Cost pro Run** | $2.15 | $0.27 | -87% |
| **Dauer Quick Mode** | 35 Min | 15-20 Min | -43% |
| **Relevanz-Ranking** | 70-75% | 92-95% | +25% |
| **PDF-Download** | 17% | 85-90% | +470% |

**Entwicklungszeit:** 14-16 Wochen
**Vollständige Docs:** [V2_ROADMAP_FULL.md](V2_ROADMAP_FULL.md), [MODULE_TYPES_OVERVIEW.md](MODULE_TYPES_OVERVIEW.md)

---

## 🎯 Vision

**Von:** Fragiles Multi-Agent-System mit 60% Erfolgsrate
**Zu:** Robustes, API-first Hybrid-System mit 85-92% Zuverlässigkeit

### Kernprinzipien v2.0
1. **API-First**: Verlässliche APIs statt fragiles Web-Scraping
2. **Simplicity**: Linear statt komplex-hierarchisch
3. **Quality**: LLM wo nötig (Szenario B), Python wo möglich
4. **Transparency**: User sieht jeden Schritt in Echtzeit
5. **Resilience**: Graceful Degradation bei Fehlern
6. **Speed**: 15-20 Min statt 35+ Min für Quick Mode

---

## 📊 Problem-Analyse v1.0

### Kritische Fehler (Must Fix)

#### 1. Orchestrator-Agent versagt ❌ CRITICAL
**Problem:**
- Orchestrator spawnt keine Sub-Agents nach Phase 1
- Workflow bricht ab, benötigt 4x manuelle Intervention
- Versprochen: Autonom | Realität: NICHT verwendbar

**Root Cause:**
- Zu komplexe Agent-Hierarchie (Orchestrator → 5 Sub-Agents)
- Task-Tool Kommunikation funktioniert nicht zuverlässig
- Asynchrone Agent-Koordination fehlerhaft

**v2.0 Lösung:** Linear Coordinator (1 Agent) + Python-Module (KEIN Task-Tool Spawning!)

---

#### 2. Web-Scraping instabil ❌ HIGH
**Problem:**
- ACM/IEEE/Scopus Selektoren "veraltet" → Nur Google Scholar
- 5/6 PDF-Downloads fehlgeschlagen (ResearchGate 403, ProQuest Auth)
- Jede UI-Änderung bricht Selektoren

**v2.0 Lösung:** APIs (CrossRef, OpenAlex, Semantic Scholar) + DBIS-Browser für PDFs

---

#### 3. User Transparency fehlt ❌ HIGH
**Problem:**
- Headless Browser → User sieht nichts
- Live-Monitor (tmux) funktioniert nicht
- User-Zitat: "wirkt so als würdest du nichts machen"

**v2.0 Lösung:** Headful Browser + stdout Progress Bars (rich library)

---

### Was funktioniert ✅ (Keep & Improve)

1. **Suchstring-Generierung** (10/10) - KI-gestützte Boolean-Queries → Behalten + API-optimieren
2. **5D-Scoring-Methodik** (8/10) - Relevanz/Recency/Quality/Authority → Behalten + Citations via API
3. **Zitat-Extraktion** (9/10) - 18 perfekte Zitate (≤25 Wörter) → Behalten + PDF-Validierung
4. **JSON State Management** (8/10) - research_state.json → Behalten + SQLite für Queries

---

## 🏗️ Architektur v2.0

### Architektur-Entscheidung: Szenario B (Smart-LLM)

**ENTSCHEIDUNG (2026-02-23):** v2.0 nutzt **Szenario B** - Qualität vor Kosten!

| Kriterium | Szenario A (Minimal-LLM) | Szenario B (Smart-LLM) | Gewinner |
|-----------|--------------------------|------------------------|----------|
| Cost pro Run | $0.17 | $0.27 | A (günstiger) |
| Relevanz-Ranking | 80-85% gut | 92-95% gut | ✅ B |
| False-Positives | 15-20% | 5-8% | ✅ B |
| Semantik | ❌ Keyword-basiert | ✅ LLM-gestützt | ✅ B |
| User-Zufriedenheit | Mittel | Hoch | ✅ B |

**Bottom Line:** +$0.10 für 10-15% bessere Qualität ist es wert!

---

### Warum Linear Coordinator statt Multi-Agent?

#### v1.0 Problem: Multi-Agent-Hierarchie
```
Orchestrator Agent
  ↓ (Task-Tool Spawning - fehleranfällig!)
  ├─ Search Agent
  ├─ Browser Agent
  ├─ Scoring Agent
  ├─ Extract Agent
  └─ Setup Agent
```

**Fehler:** Asynchrone Agent-Koordination, 40% Spawn-Fehler

#### v2.0 Lösung: Linear Coordinator + Module
```
Linear Coordinator (1 Sonnet Agent)
  ↓ (Direkte Python-Aufrufe - synchron!)
  ├─ SearchEngine.search()
  ├─ FiveDScorer.score()
  ├─ PDFFetcher.fetch()
  └─ QuoteExtractor.extract()
```

**Vorteile:**
- ✅ Kein Task-Tool Spawning (außer Initial-Start)
- ✅ Synchrone Ausführung (deterministisch)
- ✅ Ein Agent, ein Stack Trace (debugbar)
- ✅ Module testbar (Unit + Integration Tests)

---

### Ordnerstruktur v2.0

```
.claude/
├── agents/                      # 4 Agent-Prompts (.md)
│   ├── linear_coordinator.md   # Sonnet - Haupt-Coordinator
│   ├── query_generator.md      # Haiku - Boolean-Queries
│   ├── five_d_scorer.md        # Haiku - Relevanz-Scoring
│   └── quote_extractor.md      # Haiku - Zitat-Extraktion
│
└── skills/research/skill.py    # User-Command: /research

src/                            # 10 Python-Module
├── coordinator/                # Agent-Execution
├── search/                     # API-Clients (CrossRef, OpenAlex, S2)
├── ranking/                    # 5D-Scoring, Citations
├── pdf/                        # PDFFetcher + DBIS-Browser ← KILLER-FEATURE!
├── extraction/                 # Quote-Validation
├── state/                      # SQLite + JSON
├── ui/                         # Progress Bars (rich)
└── utils/                      # Rate-Limiter, Retry, Cache

tests/
├── unit/                       # 80%+ Coverage
├── integration/                # API-Clients, PDF-Chain
└── e2e/                        # Full Workflow Tests

docs/
├── ARCHITECTURE_v2.md          # Detaillierte Architektur
├── MODULE_SPECS_v2.md          # Modul-Spezifikationen + Code
├── PROBLEM_ANALYSIS_v1.md      # v1.0 Post-Mortem
└── PDF_ACQUISITION_FLOW.md     # DBIS-Browser Flow-Chart
```

**Detaillierte Infos:** Siehe [V2_ROADMAP_FULL.md](V2_ROADMAP_FULL.md) für Code-Beispiele

---

## 📅 Phasen & Timeline (14-16 Wochen)

### Phase 0: Foundation (Woche 1-2)
**Ziel:** Neue Basis-Infrastruktur ohne alte Komplexität

**Meilensteine:**
- API-Accounts (CrossRef, OpenAlex, S2, Unpaywall, CORE)
- Agent-Definitionen erstellen (4x .md Prompts)
- API-Client-Library (rate-limiting, retry, caching)
- SQLite Schema (Candidates, Papers, Quotes)
- Linear Workflow Skeleton (6 sequentielle Steps)
- Haiku-Integration testen (QueryGenerator Prototype)

**Akzeptanzkriterien:**
- API-Calls funktionieren mit Rate-Limiting
- SQLite speichert & liest korrekt
- Workflow führt 6 Dummy-Steps aus
- Haiku-Call funktioniert

---

### Phase 1: Search Engine (Woche 3-4)
**Ziel:** API-basierte Paper-Suche, 95%+ Erfolgsrate

**Meilensteine:**
- CrossRef, OpenAlex, Semantic Scholar API Integration
- Query-Generator v2 (API-optimiert, Haiku-gestützt)
- Multi-Source-Deduplication (DOI-basiert)
- Fallback auf Google Scholar (wenn APIs <10 Results)

**Akzeptanzkriterien:**
- 15+ Papers in <2 Min (statt 7 Min in v1)
- 90%+ Peer-Reviewed (statt 57% in v1)
- 100% DOI Coverage (statt 30% in v1)

---

### Phase 2: Ranking Engine (Woche 5)
**Ziel:** 5D-Scoring v2 mit LLM-Relevanz (Szenario B)

**Meilensteine:**
- 5D-Scoring aus v1 migrieren
- **LLM-Relevanz-Scoring** (Haiku) - Semantisches Verständnis
- Citation-Count Integration (OpenAlex)
- Journal Impact Factor (OpenAlex venue data)

**Akzeptanzkriterien:**
- Relevanz-Ranking: 92-95% Präzision
- Top 3 Papers haben >80% Relevanz-Score

---

### Phase 3: PDF Acquisition (Woche 6-8) 🔥 KILLER-FEATURE
**Ziel:** 85-90% PDF-Download-Erfolgsrate (statt 17% in v1)

**Strategie: 3-Step Fallback-Chain**
```
1. Unpaywall API    → 40% Erfolg (1-2s)
2. CORE API         → +10% Erfolg (2s)
3. DBIS Browser     → +35-40% Erfolg (15-25s, INSTITUTIONAL ACCESS!)
```

**Meilensteine:**
- **Woche 6:** Unpaywall + CORE API Clients
- **Woche 7:** DBIS Browser (Playwright, Shibboleth-Auth, Publisher-Navigation)
- **Woche 8:** Rate-Limiting (10-20s), Fallback-Chain, Testing

**DBIS-Browser Details:**
- Headful Browser (User sieht alles!)
- TIB Shibboleth-Authentifizierung
- Publisher-Navigation (IEEE, ACM, Springer, Elsevier)
- Human-Like Behavior (10-20s Delays, Maus-Bewegungen)

**Akzeptanzkriterien:**
- 85-90% PDFs erfolgreich downloaded
- 10-15% Papers übersprungen (kein Manual-Wait!)
- Headful Browser sichtbar
- Keine Account-Sperrung in Tests

---

### Phase 4: Quote Extraction (Woche 9)
**Ziel:** v1 System migrieren + Validierung

**Meilensteine:**
- v1 Extraction-Logik nach v2 portieren (Haiku)
- PDF-Text-Validierung (Quote wirklich im PDF?)
- Context-Window erweitern (50 Wörter vor/nach)

**Akzeptanzkriterien:**
- 100% Zitate validiert gegen PDF-Text
- ≤25 Wörter Compliance: 100%

---

### Phase 5: User Experience (Woche 10)
**Ziel:** Transparenz, Echtzeit-Feedback

**Meilensteine:**
- Real-time stdout Progress Bar (rich library)
- Live Metrics Dashboard (CLI)
- User-friendly Error Messages

**UI-Beispiel:**
```
╔═══════════════════════════════════════════════╗
║  Phase 2/6: Searching APIs                    ║
║  ████████████░░░░░  50% (7/15 Papers)         ║
║  ✅ CrossRef: 5 papers (3s)                   ║
║  ⏳ OpenAlex: In Progress...                  ║
╚═══════════════════════════════════════════════╝
```

---

### Phase 6: Testing & Reliability (Woche 11-12)
**Ziel:** 85-92% Erfolgsrate durch Tests

**Meilensteine:**
- Unit Tests (80%+ Coverage)
- Integration Tests (alle API-Clients)
- E2E Tests (5 verschiedene Themen)
- Stress Tests (Rate-Limiting, API-Ausfälle)

**Test-Szenarien:**
1. Happy Path: 15 Papers, alle PDFs verfügbar
2. Partial Fail: 15 Papers, 5 PDFs fehlgeschlagen
3. API Outage: CrossRef down → Fallback OpenAlex
4. Rate Limit: 100 Requests/min exceeded

---

### Phase 7: Migration & Cleanup (Woche 13-14)
**Ziel:** v1 → v2 Migration

**Meilensteine:**
- v1 Code archivieren (in legacy/)
- v2 als Default-System setzen
- Documentation Update
- Performance Benchmarks dokumentieren

**Was löschen:**
- .claude/agents/orchestrator-agent.md (broken)
- 50+ obsolete Shell-Scripts

**Was behalten:**
- 5D-Scoring Logik
- Quote-Extraction Logik
- JSON Schemas

---

## 🎯 Success Criteria & Go/No-Go

### MUSS erfüllt sein (alle!):
- ✅ Agent-Prompt ≤500 Zeilen, ≤120 Zeichen/Zeile
- ✅ Erfolgsrate ≥85%
- ✅ 0 manuelle Interventionen in 10 Test-Läufen
- ✅ PDF-Download ≥85%
- ✅ Unit Test Coverage ≥70%

### SOLLTE erfüllt sein (3 von 5):
- ⚠️ Erfolgsrate ≥90%
- ⚠️ Dauer ≤20 Min
- ⚠️ PDF-Download ≥90%
- ⚠️ Peer-Review ≥95%
- ⚠️ Unit Test Coverage ≥80%

### NO-GO wenn:
- 🔴 Agent-Prompt >600 Zeilen (zu komplex!)
- 🔴 Erfolgsrate <80%
- 🔴 >1 manuelle Intervention pro Lauf

---

## 📊 KPI Tracking

### Erfolgsrate-Messung

```python
# E2E-Test mit 20 verschiedenen Queries
def measure_success_rate():
    success_count = 0
    for query in test_queries:
        result = coordinator.run(query)
        if result.success and result.quotes_count >= 10:
            success_count += 1
    return success_count / len(test_queries) * 100
```

**Ziel:** ≥85% (17/20 erfolgreiche Läufe)

---

## 📚 Weiterführende Dokumentation

- **[V2_ROADMAP_FULL.md](V2_ROADMAP_FULL.md)** - Vollständige Roadmap mit Code-Beispielen (109KB)
- **[MODULE_TYPES_OVERVIEW.md](MODULE_TYPES_OVERVIEW.md)** - Modul-Übersicht mit LLM-Entscheidungen
- **[ARCHITECTURE_v2.md](ARCHITECTURE_v2.md)** - Detaillierte Architektur-Dokumentation (in Arbeit)
- **[MODULE_SPECS_v2.md](MODULE_SPECS_v2.md)** - Modul-Spezifikationen + Code (in Arbeit)
- **[PROBLEM_ANALYSIS_v1.md](PROBLEM_ANALYSIS_v1.md)** - v1.0 Post-Mortem (in Arbeit)

---

## 🚀 Next Steps

1. **Woche 1-2:** Phase 0 - Foundation starten
2. **API-Accounts erstellen:** CrossRef, OpenAlex, Semantic Scholar, Unpaywall, CORE
3. **Agent-Definitionen schreiben:** 4x .md Prompts (linear_coordinator, query_generator, five_d_scorer, quote_extractor)
4. **SQLite Schema designen:** Candidates, Papers, Quotes Tabellen

**Los geht's! 🎯**
