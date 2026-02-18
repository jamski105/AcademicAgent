# 🤖 Agents API Reference

Dokumentation aller spezialisierten Agents.

## setup-agent

**Datei:** `.claude/agents/setup-agent.md`

### Beschreibung

Interaktive Erstellung von Recherche-Konfigurationen.

### Tools

- `Read` - Templates lesen
- `Write` - Konfig schreiben
- `AskUserQuestion` - User-Input sammeln
- `Grep` - Beispiele suchen

### Input

Keine Parameter (interaktiv).

### Output

```markdown
# Datei: config/[name].md

# Recherche-Konfiguration

## Forschungsfrage
[User-Input]

## Keywords
...

## Disziplinen
...

## Suchparameter
...
```

### Workflow

1. Lies Template von `config/academic_context.md`
2. Frage User nach:
   - Forschungsfrage
   - Primary Keywords
   - Secondary Keywords
   - Disziplinen
   - Zeitraum
   - Sprachen
   - Zielanzahl Papers
3. Validiere Inputs
4. Schreibe `config/[name].md`
5. Bestätige mit User

### Invocation

```bash
# In Claude Code Chat:
/setup-agent
```

### Beispiel

```
User: /setup-agent

Agent: Willkommen! Ich helfe dir eine Recherche-Konfiguration zu erstellen.

Agent: Was ist deine Forschungsfrage?
User: Wie ermöglichen Lean-Prinzipien Governance in DevOps-Teams?

Agent: Welche Primary Keywords? (kommagetrennt)
User: Lean Governance, DevOps, Agile Teams

...

Agent: Konfig gespeichert in: config/devops_governance.md
```

---

## browser-agent

**Datei:** `.claude/agents/browser-agent.md`

### Beschreibung

Browser-Automatisierung für Datenbank-Navigation und PDF-Downloads via Chrome DevTools Protocol (CDP).

### Tools

- `Bash` - CDP-Wrapper aufrufen
- `Read` - Datenbank-Configs lesen
- `Write` - Ergebnisse schreiben
- `Grep` - Selektoren suchen

### Input

Via Orchestrator:

```json
{
  "task": "navigate_dbis" | "search_databases" | "download_pdfs",
  "config": {
    "keywords": [...],
    "databases": [...],
    "search_strings": {...}
  },
  "run_dir": "runs/[timestamp]"
}
```

### Output

**Task: navigate_dbis**
```json
{
  "databases": [
    {
      "name": "IEEE Xplore",
      "url": "https://ieeexplore.ieee.org",
      "priority": 1,
      "source": "curated" | "dbis_discovered"
    },
    ...
  ]
}
```

**Task: search_databases**
```json
{
  "candidates": [
    {
      "title": "Paper Title",
      "authors": ["Author1", "Author2"],
      "year": 2023,
      "venue": "Journal/Conference",
      "abstract": "...",
      "url": "...",
      "doi": "...",
      "database": "IEEE Xplore",
      "pdf_url": "..."
    },
    ...
  ],
  "metadata": {
    "total_candidates": 52,
    "databases_searched": 10,
    "iterations": 2
  }
}
```

**Task: download_pdfs**
```json
{
  "downloaded": 18,
  "failed": 0,
  "files": ["Smith_2023_Lean.pdf", ...]
}
```

### Workflow

#### navigate_dbis

1. Lade kuratierte Datenbanken aus `database_disciplines.yaml`
2. Navigiere zu DBIS-Portal
3. Suche mit Keywords
4. Parse Ergebnisse, berechne Relevanz-Scores
5. Merge kuratierte + discovered Datenbanken
6. Sortiere nach Priorität
7. Schreibe `databases.json`

#### search_databases

1. Lade Datenbanken und Suchstrings
2. Für jede Datenbank-Iteration (jeweils 5 DBs):
   a. Navigiere zu DB
   b. Handle Login falls nötig
   c. Fülle Search-Feld mit Query
   d. Klicke Search-Button
   e. Parse Ergebnisse
   f. Extrahiere Metadaten
3. Check Target erreicht
4. Schreibe `candidates.json`

#### download_pdfs

1. Lade ausgewählte Papers
2. Für jedes Paper:
   a. Navigiere zu Paper-URL
   b. Finde PDF-Link
   c. Download mit Retry-Logic
   d. Speichere in `downloads/`
3. Log Fehler
4. Schreibe Download-Report

### CDP-Commands

```bash
# Navigate
python3 scripts/cdp_wrapper.py navigate "URL"

# Search
python3 scripts/cdp_wrapper.py search_database "DB_NAME" "QUERY"

# Download PDF
python3 scripts/cdp_wrapper.py download_pdf "URL" "OUTPUT_PATH"

# Get HTML
python3 scripts/cdp_wrapper.py get_html
```

### Invocation

```markdown
<!-- In Orchestrator -->
Use Task tool with subagent_type="browser-agent":

{
  "description": "Navigate DBIS and find databases",
  "prompt": "Task: navigate_dbis. Config: ${config}. Output: ${run_dir}/metadata/databases.json",
  "subagent_type": "browser-agent"
}
```

---

## search-agent

**Datei:** `.claude/agents/search-agent.md`

### Beschreibung

Generiert datenbank-spezifische Boolean-Suchstrings.

### Tools

- `Read` - Keywords und DB-Configs
- `Write` - Suchstrings schreiben
- `Grep` - Syntax-Rules finden

### Input

```json
{
  "databases": [...],  # Von browser-agent
  "keywords": {
    "primary": ["Kw1", "Kw2"],
    "secondary": ["Kw3", "Kw4"],
    "related": ["Kw5"]
  },
  "run_dir": "runs/[timestamp]"
}
```

### Output

```json
{
  "search_strings": {
    "IEEE Xplore": "(...)",
    "ACM Digital Library": "...",
    "SpringerLink": "...",
    ...
  }
}
```

### Workflow

1. Lade Datenbanken
2. Für jede Datenbank:
   a. Lade Syntax-Rules aus `database_disciplines.yaml`
   b. Baue Primary Keywords Query (OR-verknüpft)
   c. Baue Secondary Keywords Query
   d. Kombiniere mit AND
   e. Füge Synonyme hinzu (optional)
   f. Apply Field-Restrictions (title/abstract)
   g. Validate Syntax
   h. Truncate falls zu lang
3. Schreibe `search_strings.json`

### Syntax-Rules

Jede DB hat eigene Regeln:

**IEEE Xplore:**
```
("Term1" OR "Term2") AND ("Term3")
```

**ACM:**
```
[[Title: term1]] OR [[Abstract: term2]]
```

**PubMed:**
```
(term1[TIAB] OR term2[TIAB]) AND term3[MeSH]
```

### Invocation

```markdown
<!-- In Orchestrator -->
{
  "description": "Generate search strings",
  "prompt": "Generate Boolean search strings for databases: ${databases}. Keywords: ${keywords}.",
  "subagent_type": "search-agent"
}
```

---

## scoring-agent

**Datei:** `.claude/agents/scoring-agent.md`

### Beschreibung

Bewertet Kandidaten mit 5D-Bewertungssystem und rankt sie.

### Tools

- `Read` - Kandidaten lesen
- `Bash` - Scoring-Script aufrufen
- `Write` - Ranked Liste schreiben

### Input

```json
{
  "candidates": [...],  # Von browser-agent
  "config": {
    "keywords": {...}
  },
  "run_dir": "runs/[timestamp]"
}
```

### Output

```json
{
  "ranked_candidates": [
    {
      "rank": 1,
      "title": "...",
      "score": 92,
      "breakdown": {
        "citations": 19,
        "recency": 19,
        "relevance": 25,
        "quality": 20,
        "open_access": 9
      },
      ...
    },
    ...
  ]
}
```

### Workflow

1. Lade Kandidaten
2. Für jeden Kandidaten:
   a. Berechne Citations-Score (20%)
   b. Berechne Recency-Score (20%)
   c. Berechne Relevance-Score (25%)
   d. Berechne Quality-Score (20%)
   e. Berechne Open-Access-Score (15%)
   f. Summiere zu Gesamt-Score (0-100)
3. Sortiere nach Score (absteigend)
4. Füge Rank hinzu
5. Schreibe `ranked_candidates.json`

### 5D-Scoring-Formeln

**Citations (20 Punkte):**
```
0-10:    citations * 0.5
10-50:   5 + (citations - 10) * 0.125
50-100:  10 + (citations - 50) * 0.1
100-300: 15 + (citations - 100) * 0.015
300+:    min(20, 18 + (citations - 300) * 0.001)
```

**Recency (20 Punkte):**
```
max(0, 20 - (current_year - pub_year) * 1)
```

**Relevance (25 Punkte):**
```
Primary in Title: +8 per keyword
Primary in Abstract: +4 per keyword
Secondary in Title: +3 per keyword
Secondary in Abstract: +1 per keyword
Cap at 25
```

**Quality (20 Punkte):**
```
Journal Q1: 20
Journal Q2: 16
Journal Q3: 12
Journal Q4: 8
Conf A*: 20
Conf A: 17
Conf B: 13
Conf C: 9
Unknown: 5
```

**Open Access (15 Punkte):**
```
Gold OA: 15
Green OA: 12
PDF available: 9
Paywall: 0
```

### Invocation

```markdown
{
  "description": "Score and rank candidates",
  "prompt": "Score all candidates with 5D system. Keywords: ${keywords}.",
  "subagent_type": "scoring-agent"
}
```

---

## extraction-agent

**Datei:** `.claude/agents/extraction-agent.md`

### Beschreibung

Extrahiert relevante Zitate aus PDFs mit Seitenzahlen.

### Tools

- `Bash` - pdftotext aufrufen
- `Read` - PDF-Text lesen
- `Write` - quote_library.json schreiben

### Input

```json
{
  "pdfs": [
    "downloads/Smith_2023_Lean.pdf",
    ...
  ],
  "keywords": {...},
  "run_dir": "runs/[timestamp]"
}
```

### Output

```json
{
  "metadata": {
    "total_quotes": 42,
    "total_papers": 18,
    "generation_date": "2026-02-18",
    "categories": ["Cat1", "Cat2", ...]
  },
  "quotes_by_category": {
    "Category 1": [
      {
        "id": "Q001",
        "source": "Smith_2023_Lean.pdf",
        "author": "Smith & Miller",
        "year": 2023,
        "page": 7,
        "text": "Quote text...",
        "context": "Surrounding paragraph...",
        "relevance_score": 92,
        "keywords_matched": ["kw1", "kw2"],
        "category": "Category 1"
      },
      ...
    ]
  },
  "quotes_by_paper": {...}
}
```

### Workflow

1. Für jedes PDF:
   a. `pdftotext -layout pdf.pdf text.txt`
   b. Lies Text
   c. Split in Pages (via form-feed `\f`)
   d. Für jede Page:
      - Split in Paragraphs
      - Check Keywords im Paragraph
      - Falls Match:
        * Extrahiere Zitat (1-3 Sätze)
        * Extrahiere Kontext (umliegender Paragraph)
        * Berechne Relevanz-Score
        * Speichere mit Seitenzahl
   e. Gruppiere Zitate nach Kategorie
2. Deduplicate ähnliche Zitate
3. Sortiere nach Relevanz
4. Schreibe `quote_library.json`

### Relevanz-Score

```
Score = 0

Primary Keyword Match: +10 per keyword
Secondary Keyword Match: +5 per keyword
Position in Paper:
  - Introduction: +5
  - Results/Discussion: +10
  - Conclusion: +5
Quote Length:
  - 1 Satz: +5
  - 2-3 Sätze: +10
  - > 3 Sätze: +5

Cap at 100
```

### Invocation

```markdown
{
  "description": "Extract quotes from PDFs",
  "prompt": "Extract relevant quotes from PDFs in downloads/. Keywords: ${keywords}.",
  "subagent_type": "extraction-agent"
}
```

---

## Nächste Schritte

- **[Skills Reference](skills.md)** - Orchestrator-Skill Dokumentation
- **[Utilities Reference](utilities.md)** - Python-Modules

**[← Zurück zur API Reference](README.md)**
