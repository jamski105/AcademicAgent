# Agent Workflow - Setup & Orchestrator

Dokumentation wie die Research-Agenten zusammenarbeiten und Daten übergeben.

---

## 1. Zwei Startmöglichkeiten

### Option A: Mit Setup-Agent (interaktiv)

**Wann nutzen:** User hat noch keine Config, will durch Dialog geführt werden

```
User tippt: /setup
↓
setup-agent startet
↓
Interaktiver Dialog:
  - Welcher Recherche-Modus?
  - Was ist die Forschungsfrage?
  - Welche Keywords?
  - Welche Datenbanken?
  - Quality-Filter?
↓
setup-agent erstellt: config/Config_Interactive_20260217_195833.md
↓
setup-agent startet Chrome & DBIS-Check automatisch
↓
setup-agent ruft orchestrator auf mit der generierten Config
↓
orchestrator führt 6 Phasen aus
```

**Ausgabe:** Vollautomatisch von Null zur fertigen Recherche

---

### Option B: Direkt mit bestehender Config

**Wann nutzen:** User hat bereits eine Config-Datei erstellt (manuell oder früher via Setup)

```
User tippt: /orchestrator
↓
orchestrator startet
↓
orchestrator listet verfügbare Configs aus config/
↓
User wählt Config (z.B. Config_Demo_DevOps.md)
↓
orchestrator erstellt neuen Run-Ordner: runs/2026-02-17_19-58-33/
↓
orchestrator kopiert Config → runs/<run-id>/config.md (Snapshot)
↓
orchestrator führt 6 Phasen aus
```

**Ausgabe:** Schneller Start mit vorbereiteter Config

---

## 2. Config-Dateien - Zwei Arten

### Manuelle Config (Template-basiert)

**Speicherort:** `config/Config_Demo_DevOps.md`

**Erstellt durch:** User füllt `config/Config_Template.md` aus

**Inhalt:**
```markdown
# Config - Lean Governance in DevOps

## 1. PROJECT INFO
Projekt-Titel: ...
Forschungsfrage: ...

## 2. SEARCH CLUSTERS
Cluster 1: lean governance, lightweight governance
Cluster 2: DevOps, CI/CD
Cluster 3: automation, pull requests

## 3. DATABASES
1. IEEE Xplore
2. SpringerLink
3. Scopus

## 4. SOURCE PORTFOLIO
Target Total: 18 Quellen
Breakdown: 10 Primary, 6 Practice, 2 Standards

## 5. QUALITY THRESHOLDS
Min Year: 2015
Citation Threshold: 50
Min Score: 4.0/5.0
```

---

### Automatische Config (Setup-Agent generiert)

**Speicherort:** `config/Config_Interactive_20260217_143022.md`

**Erstellt durch:** setup-agent nach Dialog mit User

**Inhalt:** Identisch zur manuellen Config, nur automatisch befüllt

**Vorteil:**
- User muss kein Template verstehen
- Intelligente Vorschläge basierend auf Disziplin
- Modus-Optimierungen (Quick Quote = weniger Quellen, etc.)

---

## 3. Datenfluss zwischen Agenten

```
┌─────────────────┐
│   setup-agent   │ (nur bei Option A)
└────────┬────────┘
         │
         │ 1. Dialog mit User
         │ 2. Generiert Config
         ↓
   config/Config_Interactive_XYZ.md
         │
         │ 3. Übergibt Pfad an orchestrator
         ↓
┌─────────────────┐
│  orchestrator   │
└────────┬────────┘
         │
         │ 4. Liest Config
         │ 5. Erstellt Run-Ordner
         ↓
   runs/2026-02-17_19-58-33/
         ├── config.md (Snapshot der gewählten Config)
         ├── metadata/
         │   ├── research_state.json (Fortschritt)
         │   ├── databases.json (Phase 0)
         │   ├── search_strings.json (Phase 1)
         │   ├── candidates.json (Phase 2)
         │   ├── ranked_top27.json (Phase 3)
         │   └── quotes.json (Phase 5)
         ├── downloads/ (Phase 4: PDFs)
         └── logs/
         │
         │ 6. Delegiert an Sub-Agenten
         ↓
┌──────────────────────────────────────┐
│  Sub-Agenten (via Task tool)        │
│  - browser-agent (Phasen 0,2,4)     │
│  - search-agent (Phase 1)            │
│  - scoring-agent (Phase 3)           │
│  - extraction-agent (Phase 5)        │
└──────────────────────────────────────┘
         │
         │ 7. Returnieren JSON-Ergebnisse
         ↓
   orchestrator speichert in runs/<run-id>/metadata/
         │
         │ 8. Finalisierung (Phase 6)
         ↓
   runs/<run-id>/Quote_Library.csv
   runs/<run-id>/Annotated_Bibliography.md
```

---

## 4. Wichtige Unterscheidung

### Was macht setup-agent?

✅ **Interaktiver Dialog** mit User
✅ **Config-Generierung** basierend auf Antworten
✅ **Chrome & DBIS-Setup** automatisch
✅ **Orchestrator starten** mit generierter Config

❌ Macht KEINE Research-Phasen
❌ Delegiert NICHT an Sub-Agenten
❌ Erstellt KEINEN Run-Ordner

---

### Was macht orchestrator?

✅ **Config laden** (manuell oder vom setup-agent)
✅ **Run-Ordner erstellen** mit Timestamp
✅ **6 Phasen koordinieren**
✅ **Sub-Agenten delegieren** (browser, search, scoring, extraction)
✅ **State Management** (Resume-Fähigkeit)
✅ **Checkpoints** mit User (Freigaben einholen)

❌ Macht KEINEN interaktiven Setup-Dialog
❌ Fragt NICHT nach Keywords/Datenbanken (nur: "Welche Config?")

---

## 5. Typische Workflows

### Workflow 1: Erstmalige Nutzung (Setup-Agent)

```bash
# User startet
/setup

# Setup-Agent Dialog
Agent: "Was schreibst du gerade?"
User: "Eine Masterarbeit über DevOps"

Agent: "Ich schlage Deep Research Mode vor (18 Quellen, 3-4h). Passt?"
User: "Ja"

Agent: "Was ist deine Forschungsfrage?"
User: "Wie wird Lean Governance in DevOps umgesetzt?"

Agent: "Ich habe diese Keywords extrahiert: [Liste]. Passt?"
User: "Ja"

Agent: "Disziplin?"
User: "Informatik"

Agent: "Empfohlene DBs: IEEE, Scopus, ACM. OK?"
User: "Ja"

# Setup-Agent erstellt Config
Agent: "Config erstellt: config/Config_Interactive_20260217_143022.md"

# Setup-Agent startet orchestrator
Agent: "Starte Recherche..."

# Orchestrator übernimmt
Orchestrator: "Run erstellt: runs/2026-02-17_14-30-22/"
Orchestrator: "Phase 0: Database Identification..."
[... 6 Phasen ...]
```

---

### Workflow 2: Mit vorbereiteter Config

```bash
# User hat config/Config_Demo_DevOps.md erstellt

# User startet
/orchestrator

# Orchestrator startet
Orchestrator: "Verfügbare Configs:
  1. Config_Demo_DevOps.md
  2. Config_Interactive_20260216_120000.md
Welche nutzen?"

User: "1"

# Orchestrator lädt Config
Orchestrator: "Config geladen: Lean Governance in DevOps"
Orchestrator: "Forschungsfrage: Wie wird Lean Governance..."
Orchestrator: "18 Quellen geplant, 40-50 Zitate"
Orchestrator: "Run-ID: runs/2026-02-17_19-58-33/"

Orchestrator: "Phase 0: Database Identification starten?"
User: "Ja"

[... 6 Phasen ...]
```

---

### Workflow 3: Resume nach Fehler

```bash
# Recherche wurde in Phase 2 unterbrochen

# User startet
/orchestrator

Orchestrator: "Existierende Runs:
  1. 2026-02-17_14-30-22 (completed)
  2. 2026-02-17_19-58-33 (stopped at phase 2)
Neuer Run oder fortsetzen?"

User: "2 fortsetzen"

# Orchestrator liest State
Orchestrator: "Resume von Phase 2 (Database Searching)"
Orchestrator: "Fortschritt: 15/30 Search Strings abgeschlossen"
Orchestrator: "Fortsetzen?"

User: "Ja"

[... Phase 2-6 ...]
```

---

## 6. Config-Snapshot-Prinzip

**Wichtig:** Orchestrator arbeitet mit Snapshots!

```
config/Config_Demo_DevOps.md (Original, kann sich ändern)
         │
         │ Beim Run-Start kopieren
         ↓
runs/2026-02-17_19-58-33/config.md (Snapshot, frozen)
```

**Warum?**
- **Reproduzierbarkeit:** Jeder Run hat seine exakte Config
- **Unabhängigkeit:** Änderungen am Original beeinflussen alte Runs nicht
- **Debugging:** Man kann später sehen welche Config verwendet wurde

---

## 7. State Management

**State-Datei:** `runs/<run-id>/metadata/research_state.json`

**Inhalt:**
```json
{
  "run_id": "2026-02-17_19-58-33",
  "config_path": "runs/2026-02-17_19-58-33/config.md",
  "current_phase": 2,
  "completed_phases": [0, 1],
  "phase_0": {
    "status": "completed",
    "databases_found": 5,
    "timestamp": "2026-02-17T14:35:12Z"
  },
  "phase_1": {
    "status": "completed",
    "search_strings_generated": 30,
    "timestamp": "2026-02-17T14:42:18Z"
  },
  "phase_2": {
    "status": "in_progress",
    "progress": "15/30 strings",
    "last_checkpoint": "2026-02-17T15:10:33Z"
  }
}
```

**Nutzung:**
- Nach jeder Phase: State aktualisieren
- Bei Resume: State laden → passende Phase fortsetzen
- Bei Fehler: State zeigt wo es hängt

**Script:**
```bash
# State speichern
python3 scripts/state_manager.py save <run_dir> <phase> <status>

# State laden
python3 scripts/state_manager.py load <run_dir>

# Resume-Point ermitteln
python3 scripts/state_manager.py resume <run_dir>
```

---

## 8. Zusammenfassung

| Aspekt | setup-agent | orchestrator |
|--------|-------------|--------------|
| **Aufgabe** | Config erstellen | Research durchführen |
| **Input** | User-Dialog | Config-Datei |
| **Output** | Config-Datei | Quote Library + PDFs |
| **Dauer** | 2-5 Min | 3-4 Stunden |
| **Sub-Agenten** | Keine | 4 (browser, search, scoring, extraction) |
| **Start** | `/setup` | `/orchestrator` |
| **Optional?** | Ja (kann übersprungen werden) | Nein (Kern-Agent) |

**Regel:**
- setup-agent = **Config-Builder**
- orchestrator = **Research-Executor**

---

## 9. Häufige Fehler

### ❌ Falsch: Orchestrator macht Dialog
```
orchestrator: "Was ist deine Forschungsfrage?"
orchestrator: "Welche Keywords?"
```
→ Das macht der setup-agent!

### ✅ Richtig: Orchestrator lädt Config
```
orchestrator: "Welche Config nutzen?"
orchestrator: "Config geladen. Phase 0 starten?"
```

---

### ❌ Falsch: Setup-Agent führt Phasen aus
```
setup-agent: "Starte Phase 1: Search Strings..."
```
→ Das macht der orchestrator!

### ✅ Richtig: Setup-Agent übergibt an Orchestrator
```
setup-agent: "Config erstellt. Übergebe an Orchestrator..."
```

---

**Ende der Workflow-Dokumentation**
