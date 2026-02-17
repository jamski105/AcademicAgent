# 📚 Skills Usage Guide - AcademicAgent

**Version:** 2.2
**Audience:** End Users

Dieser Guide erklärt alle verfügbaren Skills und wann du sie verwenden solltest.

---

## 🚀 Quick Start

**Für die meisten User:**

```
/start-research
```

Das war's! Der Skill führt dich durch den gesamten Prozess.

---

## 📋 Übersicht aller Skills

### Main Skills (Production)

| Skill | Beschreibung | Wann verwenden |
|-------|--------------|----------------|
| **`/start-research`** | Interaktiver Einstieg mit Config-Auswahl | **IMMER für neue Recherchen** |
| **`/orchestrator`** | Hauptagent (koordiniert alle 7 Phasen) | Nur für Resume oder manuelle Starts |

### Debug/Test Skills (Optional)

| Skill | Beschreibung | Wann verwenden |
|-------|--------------|----------------|
| `/setup-agent` | Interaktive Config-Generierung | Wenn du nur Config erstellen willst |
| `/browser-agent` | Browser-Automation testen | Debugging von CDP/UI-Navigation |
| `/search-agent` | Boolean-Suchstrings testen | Debugging von Search-Queries |
| `/scoring-agent` | 5D-Scoring testen | Debugging von Ranking-Logik |
| `/extraction-agent` | PDF-Extraktion testen | Debugging von Zitat-Extraktion |

---

## 🎯 Workflow-Szenarien

### Szenario 1: Neue Recherche starten (Standard)

**Situation:** Du möchtest eine neue Literaturrecherche durchführen.

**Lösung:**

```
/start-research
```

**Was passiert:**
1. Du wählst eine bestehende Config oder erstellst eine neue
2. Chrome wird automatisch gestartet (falls nicht schon aktiv)
3. Der Orchestrator startet automatisch
4. 7 Phasen laufen durch mit 5 Checkpoints für deine Approval

**Dauer:** 3.5-4 Stunden (je nach Modus)

---

### Szenario 2: Unterbrochene Recherche fortsetzen

**Situation:** Die Recherche wurde abgebrochen (Chrome-Crash, Terminal geschlossen, etc.)

**Lösung:**

```bash
# 1. State prüfen
python3 scripts/validate_state.py runs/[Timestamp]/metadata/research_state.json

# 2. Chrome starten
bash scripts/start_chrome_debug.sh

# 3. Im Chat:
/orchestrator
```

**Was passiert:**
- Orchestrator erkennt automatisch den State
- Überspringt abgeschlossene Phasen
- Setzt fort wo es unterbrochen wurde

**Mehr:** Siehe [ERROR_RECOVERY.md](ERROR_RECOVERY.md)

---

### Szenario 3: Nur Config erstellen (ohne Recherche)

**Situation:** Du willst mehrere Configs vorbereiten, aber noch nicht recherchieren.

**Lösung:**

```
/setup-agent
```

**Was passiert:**
1. Interaktiver Dialog für Config-Erstellung
2. Config wird in `config/` gespeichert
3. Agent stoppt (startet KEINE Recherche)

**Tipp:** Nutze später `/start-research` und wähle die Config aus.

---

### Szenario 4: Browser-Navigation debuggen

**Situation:** Der Browser-Agent findet Suchfelder nicht, oder du willst UI-Patterns testen.

**Lösung:**

```
/browser-agent Navigate to IEEE Xplore and take a screenshot
```

**Was passiert:**
- Browser-Agent verbindet sich mit Chrome (muss laufen!)
- Führt deine Anweisung aus
- Gibt strukturierte Results zurück (JSON)

**Tipp:** Nützlich um neue Datenbanken zu testen oder Patterns zu debuggen.

---

### Szenario 5: Suchstrings testen

**Situation:** Du willst sehen welche Boolean-Strings für dein Thema generiert werden.

**Lösung:**

```
/search-agent Generate search strings for "Lean Governance in DevOps"
```

**Was passiert:**
- Liest deine Keywords/Clusters
- Generiert Boolean-Strings für verschiedene Datenbanken
- Zeigt Beispiele (z.B. IEEE, Scopus, etc.)

**Tipp:** Nutze das um Suchstrings vor der eigentlichen Recherche zu validieren.

---

## 📖 Detaillierte Skill-Beschreibungen

### `/start-research`

**Funktion:** Haupteinstiegspunkt für Recherchen

**Input:** Keine (interaktiv)

**Output:**
- Vollständige Recherche (18 PDFs, Quote Library, Bibliography)
- Gespeichert in `runs/[Timestamp]/`

**Workflow:**
```
User: /start-research
  ↓
Config-Auswahl (oder neue Config erstellen)
  ↓
Chrome-Check + Start
  ↓
Orchestrator-Start automatisch
  ↓
7 Phasen (0-6) mit 5 Checkpoints
  ↓
Fertig! (3.5-4h)
```

**Checkpoints (Human-in-the-Loop):**
- **Checkpoint 0:** Datenbanken validieren
- **Checkpoint 1:** Suchstrings genehmigen
- **Checkpoint 3:** Top 27 Quellen → User wählt Top 18
- **Checkpoint 5:** Zitat-Qualität prüfen
- **Checkpoint 6:** Finale Outputs bestätigen

---

### `/orchestrator`

**Funktion:** Hauptagent (koordiniert alle 7 Phasen)

**Input:** Optional: `run-id` (z.B. `2026-02-17_14-30-00`)

**Output:** Vollständige Recherche in `runs/[run-id]/`

**Die 7 Phasen:**

| Phase | Name | Dauer | Checkpoint | Subagent |
|-------|------|-------|------------|----------|
| **0** | DBIS-Navigation | 15-20 Min | ✅ | browser-agent |
| **1** | Suchstring-Generierung | 5-10 Min | ✅ | search-agent |
| **2** | Datenbank-Durchsuchung | 90-120 Min | ❌ | browser-agent |
| **3** | 5D-Scoring & Ranking | 20-30 Min | ✅ | scoring-agent |
| **4** | PDF-Downloads | 20-30 Min | ❌ | browser-agent |
| **5** | Zitat-Extraktion | 30-45 Min | ✅ | extraction-agent |
| **6** | Finalisierung | 15-20 Min | ✅ | Python-Scripts |

**State Management:**
- Nach jeder Phase wird State gespeichert
- Resume möglich nach Unterbrechung
- Automatische Checksum-Validierung

**Background-Services:**
- CDP Health Monitor (prüft Chrome alle 5 Min)
- Automatischer Chrome-Restart bei Crash

---

### `/setup-agent`

**Funktion:** Interaktive Config-Generierung

**Input:** Keine (interaktiv)

**Output:** `config/Config_Interactive_[Timestamp].md`

**Dialog-Flow:**
1. Recherche-Modus wählen (Quick Quote, Deep Research, etc.)
2. Forschungsfrage eingeben
3. Keywords definieren
4. Datenbanken auswählen
5. Quality-Filter setzen

**Tipp:** Nutze das wenn du mehrere Configs vorbereiten willst.

---

### `/browser-agent` (Debug)

**Funktion:** Browser-Automation via CDP testen

**Input:** Task-Beschreibung (z.B. "Navigate to IEEE")

**Output:** JSON mit Results (URLs, Screenshots, etc.)

**Beispiele:**

```
/browser-agent Navigate to https://ieeexplore.ieee.org and take screenshot

/browser-agent Search for "DevOps" in IEEE Xplore

/browser-agent Click the "Advanced Search" link
```

**Voraussetzung:** Chrome muss mit CDP laufen:
```bash
bash scripts/start_chrome_debug.sh
```

---

### `/search-agent` (Debug)

**Funktion:** Boolean-Suchstrings generieren und testen

**Input:** Task-Beschreibung oder Config-Pfad

**Output:** JSON mit Suchstrings pro Datenbank

**Beispiele:**

```
/search-agent Generate search strings for "Lean Governance"

/search-agent Test search syntax for IEEE Xplore
```

**Output-Format:**
```json
{
  "database": "IEEE Xplore",
  "strings": [
    "(\"lean governance\" OR \"lean management\") AND (DevOps OR \"continuous delivery\")",
    ...
  ]
}
```

---

### `/scoring-agent` (Debug)

**Funktion:** 5D-Scoring und Ranking testen

**Input:** Task-Beschreibung oder Candidate-JSON

**Output:** JSON mit Rankings

**Die 5 Dimensionen:**
1. **Citations:** Anzahl Zitierungen (Google Scholar)
2. **Recency:** Publikationsjahr (neuere = besser)
3. **Relevance:** Keyword-Match im Titel/Abstract
4. **Journal Quality:** Impact Factor / Conference Rank
5. **Open Access:** PDF verfügbar?

**Beispiel:**

```
/scoring-agent Rank candidates from runs/[Timestamp]/metadata/candidates.json
```

---

### `/extraction-agent` (Debug)

**Funktion:** PDF → Text → Zitate extrahieren

**Input:** Task-Beschreibung oder PDF-Pfad

**Output:** JSON mit Zitaten + Seitenzahlen

**Beispiele:**

```
/extraction-agent Extract quotes from runs/[Timestamp]/downloads/

/extraction-agent Test extraction for paper.pdf
```

**Output-Format:**
```json
{
  "quotes": [
    {
      "text": "Lean principles enable...",
      "page": 5,
      "context": "In the context of DevOps...",
      "relevance": 0.85
    }
  ]
}
```

**Technologie:** `pdftotext` + `grep` (5x schneller als Browser-basiert)

---

## 🛡️ Best Practices

### 1. Nutze immer `/start-research` für neue Recherchen

**Gut:**
```
/start-research
```

**Nicht empfohlen:**
```
/setup-agent
# dann manuell
/orchestrator
```

**Warum:** `/start-research` macht automatisch alle Pre-Checks (Chrome, DBIS, Config).

---

### 2. Resume mit State-Validierung

**Gut:**
```bash
python3 scripts/validate_state.py runs/[Timestamp]/metadata/research_state.json
bash scripts/start_chrome_debug.sh
/orchestrator
```

**Nicht empfohlen:**
```
/orchestrator  # ohne State-Check
```

**Warum:** State-Validierung zeigt dir wo du stehst und ob Daten korrumpiert sind.

---

### 3. Debug-Skills nur zum Testen

**Gut:**
```
# Produktion
/start-research

# Debugging
/browser-agent Test navigation to IEEE
```

**Nicht empfohlen:**
```
# Manuelle Orchestrierung von Subagents
/browser-agent Search in IEEE
/scoring-agent Rank results
/extraction-agent Extract quotes
# etc.
```

**Warum:** Der Orchestrator macht das automatisch und besser (State Management, Error Recovery).

---

## 🆘 Troubleshooting

### Skill findet Config nicht

**Problem:** `/start-research` sagt "No configs found"

**Lösung:**
```bash
# Prüfe config/ Verzeichnis
ls -la config/*.md

# Erstelle neue Config
/setup-agent
```

---

### Browser-Agent verbindet nicht

**Problem:** `/browser-agent` sagt "CDP not reachable"

**Lösung:**
```bash
# Chrome mit CDP starten
bash scripts/start_chrome_debug.sh

# Teste Verbindung
curl http://localhost:9222/json/version
```

---

### Orchestrator überspringt keine Phasen bei Resume

**Problem:** Orchestrator startet von Phase 0 obwohl State vorhanden

**Lösung:**
```bash
# State validieren
python3 scripts/validate_state.py runs/[Timestamp]/metadata/research_state.json

# Falls korrumpiert: State neu erstellen oder von vorne starten
```

---

## 📖 Siehe auch

- **[README.md](README.md)** - Projekt-Übersicht & Installation
- **[ERROR_RECOVERY.md](ERROR_RECOVERY.md)** - Error Handling & Resume
- **[.claude/skills/README.md](.claude/skills/README.md)** - Entwickler-Dokumentation (Skills intern)
- **[AGENT_WORKFLOW.md](AGENT_WORKFLOW.md)** - Detaillierter Agent-Workflow

---

## 📊 Skill-Nutzungs-Statistik

**Typische User-Session:**

```
100% → /start-research     (alle User)
  ↓
 5% → /orchestrator         (bei Resume)
  ↓
 2% → /browser-agent        (Debugging)
 1% → /search-agent         (Debugging)
 1% → /scoring-agent        (Debugging)
 1% → /extraction-agent     (Debugging)
```

**Empfehlung:** Bleib bei `/start-research` – es ist der einfachste und robusteste Weg!

---

**Happy Researching! 📚🤖**
