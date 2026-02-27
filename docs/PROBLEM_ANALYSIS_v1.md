# Academic Agent v1.0 - Problem-Analyse & Post-Mortem

**Erstellt:** 2026-02-23
**Ziel:** Dokumentation der v1.0 Fehler als Lerngrundlage für v2.0

---

## 📊 v1.0 Performance-Übersicht

### Erfolgsrate: 60% (6.3/10)

| Metrik | Wert | Status |
|--------|------|--------|
| Erfolgsrate | 60% | ❌ Zu niedrig |
| Manuelle Interventionen | 4x pro Run | ❌ Nicht autonom |
| PDF-Download | 17% | ❌ Kritisch niedrig |
| Peer-Review Coverage | 57% | ⚠️ Unzureichend |
| Dauer Quick Mode | 35 Min | ⚠️ Zu langsam |
| Cost pro Run | $2.15 | ⚠️ Zu teuer |

---

## ❌ Kritische Fehler (Must Fix)

### 1. Orchestrator-Agent versagt (CRITICAL)

**Problem:**
- Orchestrator spawnt keine Sub-Agents nach Phase 1
- Workflow bricht ab, benötigt manuelle Intervention
- Versprochen: Autonom | Realität: 4x manuelle Agent-Starts pro Run

**Symptome:**
```
Phase 1: Setup ✅
Phase 2: Search ... ⏳ (startet nicht)
→ User muss manuell Search-Agent spawnen
Phase 3: Browser ... ⏳ (startet nicht)
→ User muss manuell Browser-Agent spawnen
```

**Root Cause:**
- Zu komplexe Agent-Hierarchie (Orchestrator → 5 Sub-Agents)
- Task-Tool Kommunikation funktioniert nicht zuverlässig
- Asynchrone Agent-Koordination fehlerhaft
- Agent-Spawning hat 40% Fehlerrate

**Impact:**
- System ist NICHT autonom verwendbar
- User-Frustration extrem hoch
- Produktiv-Einsatz unmöglich

**v2.0 Lösung:**
- Linear Coordinator (1 Agent) + Python-Module
- KEIN Task-Tool Spawning (außer Initial-Start)
- Synchrone Ausführung (deterministisch)

---

### 2. Web-Scraping instabil (HIGH)

**Problem:**
- ACM/IEEE/Scopus Selektoren "veraltet" → Nur Google Scholar funktioniert
- 5/6 PDF-Downloads fehlgeschlagen
- ResearchGate: 403 Forbidden
- ProQuest: Auth-Problem
- Jede UI-Änderung bricht Selektoren

**Root Cause:**
- CSS-Selektoren ändern sich ständig
- Anti-Bot-Protection (403 Forbidden)
- Institutional Access nicht implementiert
- Headless Browser wird erkannt

**Impact:**
- Niedrige Paper-Qualität
- Manuelle PDF-Downloads nötig
- Nur 17% PDF-Erfolgsrate

**v2.0 Lösung:**
- APIs (CrossRef, OpenAlex, Semantic Scholar) statt Scraping
- DBIS-Browser mit Institutional Access (TIB)
- Headful Browser (transparenter für User)
- Fallback-Chain: Unpaywall → CORE → DBIS

---

### 3. User Transparency fehlt (HIGH)

**Problem:**
- Headless Browser → User sieht nichts
- Live-Monitor (tmux) funktioniert nicht
- User-Zitat: "wirkt so als würdest du nichts machen"
- Status-Updates zu selten

**Root Cause:**
- Falsches UX-Design (headless statt headful)
- Monitoring zu komplex (tmux statt stdout)
- Keine Real-time Progress Bars

**Impact:**
- User verliert Vertrauen
- User fühlt sich hilflos
- Unklare Fehler-Kommunikation

**v2.0 Lösung:**
- Headful Browser (User sieht Browser-Navigation)
- stdout Progress Bars (rich library)
- Live Metrics Dashboard (CLI)
- User-friendly Error Messages

---

## ⚠️ Weitere Probleme

### 4. PDF-Download fehlerhaft (CRITICAL)

**Problem:**
- 5/6 PDFs fehlgeschlagen (83% Fehlerrate!)
- Nur 17% Erfolgsrate bei 6 Test-Papers
- Kein Institutional Access

**Root Cause:**
- Direct Download ohne Institutional Access
- Keine API-First-Strategie
- Kein Fallback-Mechanismus

**v2.0 Lösung:**
- 3-Step Fallback: Unpaywall → CORE → DBIS
- DBIS mit TIB Shibboleth-Auth
- Ziel: 85-90% Erfolgsrate

---

### 5. Niedrige Peer-Review Coverage (MEDIUM)

**Problem:**
- Nur 57% Peer-reviewed Papers
- Rest: Conference Talks, Blog Posts, Preprints

**Root Cause:**
- Google Scholar filtert nicht nach Peer-Review
- Keine Qualitätskontrolle

**v2.0 Lösung:**
- CrossRef API (nur Peer-reviewed Journals)
- OpenAlex Venue-Filter
- Ziel: 95%+ Peer-reviewed

---

### 6. Performance zu langsam (MEDIUM)

**Problem:**
- Quick Mode: 35 Minuten (Ziel: 15-20 Min)
- Paper-Suche: 7 Minuten (zu lange!)

**Root Cause:**
- Web-Scraping langsamer als API-Calls
- Kein Parallelismus
- Zu viele Timeouts

**v2.0 Lösung:**
- API-Calls statt Scraping (1-2 Min statt 7 Min)
- Parallele API-Requests
- Ziel: 15-20 Min Quick Mode

---

### 7. Kosten zu hoch (LOW)

**Problem:**
- $2.15 pro Run (hauptsächlich Sonnet-Calls)
- Orchestrator + 5 Sub-Agents = viele LLM-Calls

**Root Cause:**
- Zu viele Agent-Ebenen
- Overhead durch Agent-Koordination

**v2.0 Lösung:**
- 1 Sonnet + 3 Haiku + 10 Python-Module
- Python statt LLM wo möglich
- Ziel: $0.27 pro Run (87% günstiger)

---

## ✅ Was funktioniert (Keep & Improve)

### 1. Suchstring-Generierung (10/10)

**Was gut funktioniert:**
- KI-gestützte Boolean-Query-Erstellung
- Datenbank-spezifische Syntax
- Keyword-Clustering intelligent

**V2 Plan:**
- Behalten + API-optimierte Queries
- Haiku statt Sonnet (günstiger)

---

### 2. 5D-Scoring-Methodik (8/10)

**Was gut funktioniert:**
- Relevanz, Recency, Quality, Authority, Portfolio-Balance
- Duplikaterkennung funktioniert
- Transparente Gewichtung

**V2 Plan:**
- Behalten + Citation-Counts via API
- LLM-Relevanz-Scoring (Szenario B)

---

### 3. Zitat-Extraktion (9/10)

**Was gut funktioniert:**
- 18 perfekte Zitate extrahiert (≤25 Wörter)
- Kontext + Seitenzahlen + APA 7
- Thematische Clustering

**V2 Plan:**
- Behalten + Validierung gegen PDF
- Haiku statt Sonnet

---

### 4. JSON State Management (8/10)

**Was gut funktioniert:**
- research_state.json als Single Source of Truth
- 23 State-Updates erfolgreich
- Checkpointing funktioniert

**V2 Plan:**
- Behalten + SQLite für Querying
- JSON als Backup

---

## 📋 Lessons Learned

### Do

- ✅ API-First: Verlässliche APIs statt fragiles Scraping
- ✅ Simplicity: Linear statt komplex-hierarchisch
- ✅ Transparency: User muss alles sehen können
- ✅ Modularity: Python-Module statt Agent-Hierarchie
- ✅ Testing: Unit + Integration + E2E Tests

### Don't

- ❌ Multi-Agent-Hierarchien (zu fehleranfällig)
- ❌ Asynchrone Agent-Koordination (Task-Tool)
- ❌ Web-Scraping als Primärstrategie
- ❌ Headless Browser ohne User-Feedback
- ❌ Keine Test-Coverage

---

## 🚀 v2.0 Migration Path

1. **Phase 0:** Neue Architektur aufsetzen (Linear Coordinator)
2. **Phase 1-3:** Neue Module implementieren (Search, Ranking, PDF)
3. **Phase 4:** Funktionierende v1-Module migrieren (Quotes, Scoring)
4. **Phase 5-6:** UX + Testing
5. **Phase 7:** v1 archivieren, v2 als Default

**Was löschen:**
- .claude/agents/orchestrator-agent.md
- 50+ obsolete Shell-Scripts
- Alte CDP-Wrapper

**Was behalten:**
- 5D-Scoring Logik
- Quote-Extraction Logik
- JSON Schemas

---

## 📚 Verwandte Dokumentation

- [V2_ROADMAP.md](../V2_ROADMAP.md) - Neue Architektur & Timeline
- [ARCHITECTURE_v2.md](ARCHITECTURE_v2.md) - Architektur-Details
- [MODULE_SPECS_v2.md](MODULE_SPECS_v2.md) - Modul-Spezifikationen
