# 🤝 AGENT CONTRACTS

**Letzte Aktualisierung:** 2026-02-20

Dieses Dokument definiert die **Input/Output-Verträge** für alle Agents im AcademicAgent-System.

---

## 📋 Workflow-Phasen

| Phase | Agent | Input-Dateien | Output-Dateien |
|-------|-------|---------------|----------------|
| **0** | browser-agent | `run_config.json`, `research_state.json` | `databases.json` |
| **1** | search-agent | `run_config.json`, `databases.json` | `search_strings.json` |
| **2** | browser-agent | `search_strings.json`, `databases.json` | `candidates.json` |
| **3** | scoring-agent | `candidates.json`, `run_config.json` | `ranked_candidates.json` |
| **4** | browser-agent | `ranked_candidates.json` | `downloads.json`, `downloads/*.pdf` |
| **5** | extraction-agent | `downloads/*.pdf`, `run_config.json` | `quotes.json` |
| **6** | orchestrator | `quotes.json`, `ranked_candidates.json` | `quote_library.json`, `bibliography.bib` |

---

## 📁 Verzeichnisstruktur

Alle Dateien befinden sich in: `runs/<run_id>/`

```
runs/<run_id>/
├── config/
│   ├── run_config.json          # Deine Recherche-Konfiguration
│   └── <ProjectName>_Config.md  # Akademischer Kontext
├── metadata/
│   ├── databases.json           # Phase 0: Gefundene Datenbanken
│   ├── search_strings.json      # Phase 1: Generierte Suchstrings
│   ├── candidates.json          # Phase 2: Gefundene Paper
│   └── ranked_candidates.json   # Phase 3: Bewertete & sortierte Paper
├── downloads/
│   ├── downloads.json           # Phase 4: Download-Metadaten
│   └── *.pdf                    # Heruntergeladene PDFs
├── outputs/
│   ├── quotes.json              # Phase 5: Extrahierte Zitate
│   ├── quote_library.json       # Phase 6: Finale Zitat-Bibliothek
│   ├── bibliography.bib         # Phase 6: BibTeX-Datei
│   └── Annotated_Bibliography.md # Phase 6: Annotierte Bibliographie
├── logs/
│   └── phase_*.log              # Logs für jede Phase
└── research_state.json          # Workflow-Status (aktuelle Phase, Fehler)
```

---

## 🔧 Agent-Contracts

### Setup-Agent (Pre-Phase)

**Zweck:** Interaktive Konfiguration erstellen

**Inputs:**
- User-Dialog (Forschungsfrage, Keywords, Disziplinen)

**Outputs:**
- `config/run_config.json`
- `config/<ProjectName>_Config.md`

**Was du tun musst:**
1. Frage User nach Forschungsfrage, Keywords, Disziplinen
2. Erstelle `run_config.json` mit allen erforderlichen Feldern
3. Validiere Eingaben (keine leeren Pflichtfelder)

---

### Browser-Agent (Phasen 0, 2, 4)

**Zweck:** Web-Navigation via CDP für Datenbank-Zugriff

#### Phase 0: DBIS-Navigation

**Input:** `config/run_config.json`

**Output:** `metadata/databases.json`

**Was du tun musst:**
1. Navigiere zu DBIS-Portal
2. Suche Datenbanken basierend auf Disziplinen aus `run_config.json`
3. Extrahiere Datenbank-Namen, URLs, Relevanz
4. Speichere als JSON in `metadata/databases.json`

**Format `databases.json`:**
```json
{
  "databases": [
    {
      "name": "IEEE Xplore",
      "url": "https://ieeexplore.ieee.org",
      "relevance": "high",
      "discipline": "Computer Science"
    }
  ],
  "timestamp": "2026-02-20T14:30:00Z"
}
```

#### Phase 2: Iterative Datenbanksuche

**Inputs:**
- `metadata/search_strings.json`
- `metadata/databases.json`

**Output:** `metadata/candidates.json`

**Was du tun musst:**
1. Iteriere über alle Datenbanken aus `databases.json`
2. Führe Suche mit Strings aus `search_strings.json` aus
3. Extrahiere Metadaten: DOI, Titel, Autoren, Jahr, Abstract, PDF-URL, Citations
4. Sammle alle Kandidaten in `candidates.json`

**Format `candidates.json`:**
```json
{
  "candidates": [
    {
      "doi": "10.1109/EXAMPLE.2024.123456",
      "title": "Paper Title",
      "authors": ["Author A", "Author B"],
      "year": 2024,
      "abstract": "Abstract text...",
      "source_db": "IEEE Xplore",
      "pdf_url": "https://...",
      "citations": 42
    }
  ],
  "total_results": 127,
  "databases_searched": ["IEEE Xplore", "ACM Digital Library"],
  "timestamp": "2026-02-20T15:00:00Z"
}
```

#### Phase 4: PDF-Download

**Input:** `metadata/ranked_candidates.json` (nur Top 18)

**Outputs:**
- `downloads/downloads.json`
- `downloads/*.pdf`

**Was du tun musst:**
1. Lies Top 18 Paper aus `ranked_candidates.json`
2. Navigiere zu jeder PDF-URL und lade herunter
3. Speichere PDFs als `paper_001.pdf`, `paper_002.pdf`, etc.
4. Logge Erfolg/Fehler in `downloads.json`

**Format `downloads.json`:**
```json
{
  "downloads": [
    {
      "doi": "10.1109/...",
      "filename": "paper_001.pdf",
      "status": "success",
      "size_kb": 542
    }
  ],
  "success_count": 16,
  "failed_dois": ["10.1109/FAILED"],
  "timestamp": "2026-02-20T16:00:00Z"
}
```

---

### Search-Agent (Phase 1)

**Zweck:** Boolean-Suchstrings generieren

**Inputs:**
- `config/run_config.json` (research_question, keywords)
- `metadata/databases.json` (für Syntax-Anpassung)

**Output:** `metadata/search_strings.json`

**Was du tun musst:**
1. Lies Forschungsfrage und Keywords aus `run_config.json`
2. Generiere primären Boolean-Suchstring (AND/OR/NOT)
3. Erstelle Variationen für verschiedene Datenbanken
4. Speichere in `search_strings.json`

**Format `search_strings.json`:**
```json
{
  "primary_string": "(machine learning) AND (security OR privacy)",
  "variations": [
    "ML AND security",
    "\"deep learning\" AND threat"
  ],
  "databases": {
    "IEEE Xplore": "(machine learning) AND (security)",
    "ACM Digital Library": "machine AND learning AND security"
  },
  "timestamp": "2026-02-20T14:45:00Z"
}
```

---

### Scoring-Agent (Phase 3)

**Zweck:** 5D-Bewertung der Paper

**Inputs:**
- `metadata/candidates.json`
- `config/run_config.json` (für Relevanz-Berechnung)

**Output:** `metadata/ranked_candidates.json`

**Was du tun musst:**
1. Lies alle Kandidaten aus `candidates.json`
2. Berechne 5 Scores für jedes Paper:
   - **Relevance:** Wie relevant für Forschungsfrage? (0-1)
   - **Citation Impact:** Normalisierte Zitationszahl (0-1)
   - **Recency:** Wie aktuell? (0-1)
   - **Methodology:** Qualität der Methodik (0-1)
   - **Accessibility:** PDF verfügbar? (0 oder 1)
3. Berechne Gesamt-Score (Summe der 5 Dimensionen)
4. Sortiere absteigend nach Gesamt-Score
5. Speichere in `ranked_candidates.json`

**Format `ranked_candidates.json`:**
```json
{
  "ranked": [
    {
      "doi": "10.1109/...",
      "title": "Paper Title",
      "authors": ["Author A"],
      "year": 2024,
      "abstract": "...",
      "source_db": "IEEE Xplore",
      "pdf_url": "https://...",
      "citations": 42,
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
  ],
  "total_scored": 127,
  "timestamp": "2026-02-20T15:30:00Z"
}
```

---

### Extraction-Agent (Phase 5)

**Zweck:** Zitate aus PDFs extrahieren

**Inputs:**
- `downloads/*.pdf` (alle heruntergeladenen PDFs)
- `config/run_config.json` (Forschungsfokus)

**Output:** `outputs/quotes.json`

**Was du tun musst:**
1. Lies alle PDFs aus `downloads/`
2. Extrahiere relevante Zitate (max 3-5 pro Paper)
3. Erfasse: Zitat-Text, Seitenzahl, Kontext (intro/methods/results/discussion)
4. Speichere in `quotes.json`

**Format `quotes.json`:**
```json
{
  "quotes": [
    {
      "doi": "10.1109/...",
      "paper_title": "Paper Title",
      "authors": ["Author A"],
      "year": 2024,
      "page": 5,
      "quote_text": "This is an important finding...",
      "context": "results",
      "relevance_score": 0.89
    }
  ],
  "total_papers_processed": 16,
  "total_quotes_extracted": 48,
  "timestamp": "2026-02-20T17:00:00Z"
}
```

---

### Orchestrator-Agent (Phase 6)

**Zweck:** Finale Ausgaben generieren

**Inputs:**
- `outputs/quotes.json`
- `metadata/ranked_candidates.json`

**Outputs:**
- `outputs/quote_library.json`
- `outputs/bibliography.bib`
- `outputs/Annotated_Bibliography.md`
- `outputs/search_report.md`

**Was du tun musst:**
1. Lies Zitate aus `quotes.json`
2. Erstelle strukturierte Quote Library (`quote_library.json`)
3. Generiere BibTeX-Datei (`bibliography.bib`)
4. Erstelle annotierte Bibliographie (Markdown)
5. Schreibe Workflow-Report (Zusammenfassung)

---

## ⚠️ Wichtige Regeln

### 1. Immer research_state.json aktualisieren

Nach jeder Phase MUSS `research_state.json` aktualisiert werden:

```json
{
  "run_id": "2026-02-20_14-30-00",
  "current_phase": 2,
  "status": "running",
  "last_update": "2026-02-20T15:00:00Z",
  "errors": []
}
```

### 2. Fehlerbehandlung

**Bei Fehler:**
- Logge in `logs/phase_X.log`
- Aktualisiere `research_state.json` mit Fehler-Details
- Folge Retry-Policy (siehe unten)

**Retry-Policies:**
- **Phase 0-4:** 3x Retry mit Exponential Backoff (5s, 15s, 45s)
- **Phase 5-6:** Kein Retry (Validierungs-Fehler = manuelles Eingreifen nötig)

### 3. Validierung

**Vor dem Speichern jeder Output-Datei:**
1. Validiere JSON-Schema
2. Prüfe Pflichtfelder
3. Sanitize Text (entferne HTML, Injection-Patterns)

**Nutze:** `python3 scripts/validation_gate.py`

### 4. Unsicherheit handhaben

**Wenn Daten unsicher/unbekannt:**
- ✅ Nutze `"unknown"` oder `null` für optionale Felder
- ✅ Füge `confidence` Score hinzu (0.0-1.0)
- ❌ NIEMALS Daten erfinden oder raten

**Wenn User-Input nötig:**
- ✅ Frage User explizit
- ❌ Nicht einfach fortfahren mit Default-Werten

---

## 📚 Verwandte Dokumentation

- **[07-agent-handover-contracts.md](developer-guide/07-agent-handover-contracts.md)** - Detaillierte technische Spezifikation für Entwickler
- **[SECURITY.md](../SECURITY.md)** - Sicherheitsrichtlinien für alle Agents
- **[ERROR_RECOVERY.md](../ERROR_RECOVERY.md)** - Fehlerbehandlung & Recovery-Strategien
