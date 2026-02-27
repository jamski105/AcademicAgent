# Academic Agent v2.2 - Workflow Guide

**Aktualisiert:** 2026-02-27 (v2.2 - DBIS Search Integration)
**Architektur:** Agent-basiert via Claude Code + DBIS Meta-Portal

---

## 🚀 Quick Start

```bash
# 1. Installation
./setup.sh

# 2. Aktiviere venv
source venv/bin/activate

# 3. Starte Research
/research "Your research question"
```

---

## 📖 User Journey

### 1. User startet Research

```bash
/research "DevOps Governance"
```

### 2. SKILL.md - Mode & Citation Style Selection

```
Academic Agent Research Assistant

Please select research mode:
1. Quick Mode (15 papers, ~20 min)
2. Standard Mode (25 papers, ~35 min) [Recommended]
3. Deep Mode (40 papers, ~60 min)

Your choice: 2

Select citation style:
1. APA 7 (Psychology, Education) [Recommended]
2. IEEE (Engineering, Computer Science)
3. Harvard (Business, Humanities)
4. MLA 9 (Literature, Arts)
5. Chicago (History, Social Sciences)

Your choice: 1
```

### 3. linear_coordinator Agent wird gespawnt

```
Spawning linear_coordinator Agent...

Phase 1/8: Context Setup ✓
Phase 2/8: Query Generation...
Phase 2a/8: Discipline Classification...
Phase 3/8: Hybrid Search (APIs + DBIS)...
```

### 4. Workflow läuft automatisch

**Phase 2: Query Generation**
- `query_generator` Agent erstellt erweiterte Queries
- Boolean Queries, Keywords, Filters

**Phase 2a: Discipline Classification** *(NEW in v2.2)*
- `discipline_classifier` Agent erkennt Fachgebiet
- Mapped Query zu DBIS-Kategorien
- Identifiziert relevante Fachdatenbanken
- Output: Primary Discipline + DBIS Keywords

**Phase 3: Hybrid Search** *(ENHANCED in v2.2)*

**Track 1: API Search (Fast - 2-3 Sekunden)**
- `search_engine.py` durchsucht CrossRef, OpenAlex, S2
- Parallel Execution
- ~50 Papers gefunden (STEM-fokussiert)

**Track 2: DBIS Search (Comprehensive - 60-90 Sekunden)**
- `dbis_search` Agent öffnet Browser
- Navigiert zu DBIS Portal (https://dbis.ur.de/UBTIB)

**Database Selection (NEW v2.3 - Auto-Discovery):**
- **Discovery Mode** (first choice):
  - Agent scraped DBIS-Seite für Fachgebiet
  - Extrahiert ALLE verfügbaren Datenbanken (100+)
  - Filtert nach TIB-Lizenz (grüne/gelbe Ampel)
  - Priorisiert bevorzugte DBs (Beck-Online, Juris, etc.)
  - Wählt TOP 3-5 automatisch aus
  - Cache für 24h (nächste Queries instant!)
- **Fallback Mode** (if discovery fails):
  - Nutzt vordefinierte Datenbank-Liste aus Config
  - Garantierte Mindest-Abdeckung

**Selected Databases (Examples):**
  - **Medizin:** PubMed, Cochrane Library, Europe PMC
  - **Klassische Philologie:** L'Année philologique, Perseus, JSTOR
  - **Informatik:** IEEE Xplore, ACM Digital Library, arXiv
  - **Rechtswissenschaft:** Beck-Online, Juris, HeinOnline ⭐ *via Discovery*
  - **Geisteswissenschaften:** JSTOR, Project MUSE, EBSCO

- Für jede Datenbank:
  - Klickt "Zur Datenbank" (aktiviert TIB-Lizenz!)
  - Sucht mit optimierter Query
  - Extrahiert Results (Titel, Autoren, Jahr, DOI)
- ~50-100 Papers gefunden (Discipline-specific!)
- **Discovery-Vorteil:** Auch unbekannte/neue DBs werden gefunden!

**Result Merging:**
- API Papers (~50) + DBIS Papers (~50-100)
- Automatische Deduplizierung (DOI + Title)
- ~80-120 unique Papers
- Source-Annotation (api/dbis) für Transparenz

**Phase 4: Ranking**
- `five_d_scorer.py` bewertet Papers (Citations, Recency, Venue)
- `llm_relevance_scorer` Agent bewertet semantische Relevanz
- Source-aware scoring (DBIS papers get slight boost for discipline-match)
- Top N Papers ausgewählt (15/25/40 je nach Mode)

**Phase 5: PDF Acquisition**
- Unpaywall API (~40% Erfolg)
- CORE API (~10% zusätzlich)
- Falls fehlgeschlagen: `dbis_browser` Agent
  - **Browser öffnet sich (sichtbar!)**
  - User kann manuell TIB Shibboleth Login durchführen
  - Agent downloaded PDF
- **Mit DBIS Search:** Viele Papers bereits mit direktem PDF-Link!

**Phase 6: Quote Extraction**
- `pdf_parser.py` extrahiert Text
- `quote_extractor` Agent findet relevante Zitate
- Validierung & Context Window

**Phase 7: Export Results**
- JSON Export (vollständige Results mit Source-Annotation)
- CSV Export (Quotes mit formatierten Zitationen + Source)
- Markdown Report (Human-readable Summary mit Coverage-Stats)
- BibTeX Export (für LaTeX)
- Logs & Temp Files speichern

### 5. Results

```
Research Complete! ✓

Found: 25 papers (12 from APIs, 13 from DBIS)
PDFs: 23/25 (92%)
Quotes: 48 relevant quotes

Coverage Breakdown:
├── CrossRef: 8 papers
├── OpenAlex: 3 papers
├── Semantic Scholar: 1 paper
└── DBIS Sources: 13 papers
    ├── L'Année philologique: 7 papers
    ├── JSTOR: 4 papers
    └── IEEE Xplore: 2 papers

Results saved to: runs/2026-02-27_14-30-00/
├── pdfs/ (23 PDFs, 95 MB)
├── results.json (full results with source annotation)
├── quotes.csv (48 quotes with APA7 citations + sources)
├── summary.md (markdown report with coverage stats)
├── bibliography.bib (BibTeX for LaTeX)
├── session.db (SQLite database)
├── session_log.txt (execution logs)
└── temp/ (intermediate files + DBIS extraction logs)
```

---

## 🔧 Development Workflow

### Neuen Agent entwickeln

1. **Agent-Datei erstellen:**
```bash
touch .claude/agents/my_agent.md
```

2. **Prompt schreiben:**
```markdown
# My Agent

## Role
...

## Tools
Bash, Read, Write

## Workflow
...
```

3. **Vom Coordinator aufrufen:**
```python
# In linear_coordinator.md:
Task(subagent_type="my_agent", prompt="...")
```

4. **Testen:**
```bash
# Integration Test
pytest tests/agents/test_my_agent.py
```

### Python-Modul CLI-fähig machen

```python
# my_module.py
import argparse
import json
import sys

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()

    # Process...
    result = {"status": "success"}

    # Output JSON to stdout
    print(json.dumps(result))

if __name__ == "__main__":
    main()
```

### Chrome MCP testen

```bash
# Test Chrome Connection
npx @eddym06/custom-chrome-mcp

# In Claude Code:
# Spawn dbis_browser Agent und teste Navigation
```

---

## 🧪 Testing

### Unit Tests

```bash
pytest tests/unit/
```

### Integration Tests

```bash
pytest tests/integration/
```

### Agent Tests

```bash
pytest tests/agents/
```

### E2E Test

```bash
python -m tests.e2e.test_full_workflow
```

---

## 🐛 Debugging

### Agent Logs

```bash
# Linear Coordinator Logs
tail -f ~/.claude/logs/linear_coordinator.log
```

### Python Module Logs

```bash
# Session Logs
tail -f runs/2026-02-27_14-30-00/session_log.txt

# Database State
sqlite3 runs/2026-02-27_14-30-00/session.db
SELECT * FROM papers;
```

### Chrome MCP Logs

```bash
# Chrome DevTools öffnet automatisch bei dbis_browser Agent
```

---

## 🔄 Resume nach Error

```bash
# System speichert automatisch Checkpoints
# Bei Fehler:

/research --resume runs/2026-02-27_14-30-00/

# Checkpoint wird aus Run-Directory geladen
# Resume startet ab letzter erfolgreicher Phase
```

---

## 🎯 Best Practices

1. **Mode Selection:**
   - Quick: Für Überblick
   - Standard: Für reguläre Research
   - Deep: Für umfassende Literaturrecherche

2. **DBIS Browser:**
   - Interaktiv: User sieht Browser
   - TIB Login manuell durchführen
   - Agent wartet auf Login-Completion

3. **API Limits:**
   - Keine API Keys nötig
   - System nutzt anonymous APIs
   - Rate-Limiting automatisch

4. **PDF Success Rate:**
   - Mit DBIS: 85-90%
   - Ohne DBIS: ~50%

5. **Output Management:**
   - Alle Dateien in `/runs/{timestamp}/`
   - Jeder Run eigenständig archivierbar
   - CSV mit wählbarem Zitierstil
   - Keine Cache-Pollution

---

---

## 🌍 Cross-Disciplinary Coverage (v2.2)

### **STEM Fields**
Coverage: **95%** (APIs + DBIS)
- Computer Science, Engineering, Physics, Math
- Primary Sources: CrossRef, OpenAlex, IEEE Xplore, arXiv

### **Medicine & Life Sciences**
Coverage: **90%** (DBIS-enhanced)
- Primary Sources: PubMed (via DBIS), Europe PMC, CrossRef

### **Humanities & Classics**
Coverage: **85%** (DBIS-powered!) ⭐ *NEW*
- Literature, History, Philosophy, Classics
- Primary Sources: JSTOR, L'Année philologique, Project MUSE

### **Social Sciences**
Coverage: **88%** (hybrid)
- Psychology, Economics, Sociology
- Primary Sources: CrossRef, OpenAlex, JSTOR

### **German Research**
Coverage: **80%** (BASE via DBIS)
- Deutschsprachige Publikationen
- Primary Source: BASE (Bielefeld Academic Search Engine)

---

## 📚 Siehe auch

- [INSTALLATION.md](./INSTALLATION.md) - Setup Guide
- [ARCHITECTURE_v2.md](./docs/ARCHITECTURE_v2.md) - Architektur
- [MODULE_SPECS_v2.md](./docs/MODULE_SPECS_v2.md) - Module Details
- [DBIS_INTEGRATION.md](./DBIS_INTEGRATION.md) - DBIS Search Details ⭐ *NEW*
