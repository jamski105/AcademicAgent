# 🎨 Interaktiver TUI-Modus

## Übersicht

Der interaktive TUI (Text User Interface) Modus bietet eine benutzerfreundliche Alternative zum konversationellen Chat-Setup für Academic Agent.

**Status:** ✅ Implementiert (Version 4.0)

---

## Features

### ✨ Hauptvorteile

- **Benutzerfreundlich**: Navigation mit Pfeiltasten statt tippen
- **Schneller**: Reduziert Chat-Messages drastisch
- **Visuell**: Klare Übersicht über alle Optionen
- **Smart**: Automatische Keyword-Extraktion aus Forschungsfrage
- **Flexibel**: 3 vorkonfigurierte Modi (Quick/Standard/Deep)

### 🎯 User Flow

```
1. Forschungsfrage eingeben
   ↓
2. Keywords automatisch extrahiert
   ↓ (optional bearbeiten)
3. Modus wählen (↑↓ Navigation)
   ↓
4. Konfigurations-Übersicht
   ↓
5. Start bestätigen
   ↓
6. Orchestrator startet automatisch
```

---

## Installation

### Voraussetzungen

- Python 3.8+
- pip3

### Dependency installieren

```bash
pip3 install questionary
```

Das Wrapper-Script installiert `questionary` automatisch, falls nicht vorhanden.

---

## Nutzung

### Variante 1: Via Wrapper (Empfohlen)

```bash
cd /path/to/AcademicAgent
bash scripts/academicagent_wrapper.sh
```

**Zeigt Auswahlmenü:**
```
Wie möchtest du fortfahren?

  1) 🎨 Interaktiver Modus (TUI) - Empfohlen!
     ↳ Benutzerfreundlich, geführter Setup mit Pfeiltasten

  2) 💬 Chat-Modus (Standard)
     ↳ Konversationell, via Claude Code Chat

  3) 🔄 Fortsetzen
     ↳ Existierenden Run fortsetzen

Deine Wahl [1-3]:
```

### Variante 2: Direkt TUI starten

```bash
bash scripts/academicagent_wrapper.sh --interactive
```

### Variante 3: Python-Script direkt

```bash
python3 scripts/interactive_setup.py
```

### Variante 4: Run fortsetzen

```bash
bash scripts/academicagent_wrapper.sh --resume 2026-02-22_14-30-00
```

---

## Screenshot-Flow (Text-Darstellung)

### Schritt 1: Willkommen

```
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║           🎓 Academic Agent - Quick Setup (TUI)              ║
║                                                              ║
║                        Version 4.0                           ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝

✓ Akademischer Kontext gefunden
  Fachgebiet: Software Engineering
  Basis-Keywords: DevOps, Lean, Agile
```

### Schritt 2: Forschungsfrage

```
? Was ist deine Forschungsfrage?
  > Wie beeinflussen Lean Governance Prinzipien DevOps-Teams?_
```

### Schritt 3: Keyword-Extraktion

```
🔍 Extrahiere Keywords...

✓ Erkannte Keywords: Lean, Governance, Prinzipien, DevOps, Teams
  (+ 2 weitere)

? Möchtest du die Keywords bearbeiten? (Y/n)
```

### Schritt 4: Modus-Auswahl

```
? Welchen Recherche-Modus möchtest du verwenden?
  → Quick (5 Zitate, empfohlen für Tests)
    Standard (20 Zitate, für normale Recherchen)
    Deep (50 Zitate, für umfassende Literaturreviews)

  [↑↓ Navigation] [ENTER Auswahl]
```

### Schritt 5: Konfigurations-Übersicht

```
╔══════════════════════════════════════════════════════════════╗
║                   KONFIGURATION                              ║
╚══════════════════════════════════════════════════════════════╝
  Modus:           Quick
  Ziel-Zitate:     5
  Datenbanken:     ~3
  Keywords:        7 erkannt
  Zeitraum:        2019-2026
  Geschätzte Zeit: 30-45 Min

? Möchtest du jetzt starten? (Y/n)
```

### Schritt 6: Start

```
📝 Erstelle Run-Konfiguration...
✓ Konfiguration gespeichert: runs/2026-02-22_14-30-00/run_config.json
✓ Run ID: 2026-02-22_14-30-00

🚀 Starte Recherche-Pipeline für Run: 2026-02-22_14-30-00

[Orchestrator-Agent übernimmt...]
```

---

## Konfigurierte Modi

### Quick Mode
- **Zitate**: 5
- **Datenbanken**: ~3
- **Zeit**: 30-45 Min
- **Ideal für**: Tests, Schnellrecherchen

### Standard Mode
- **Zitate**: 20
- **Datenbanken**: ~5
- **Zeit**: 1-2 Stunden
- **Ideal für**: Normale Bachelor-/Masterarbeiten

### Deep Mode
- **Zitate**: 50
- **Datenbanken**: ~8
- **Zeit**: 3-5 Stunden
- **Ideal für**: Umfassende Literaturreviews, PhD-Recherchen

---

## Automatische Features

### 1. Keyword-Extraktion

Das Script analysiert die Forschungsfrage und extrahiert automatisch relevante Keywords:

**Algorithmus:**
1. Entfernt Stopwords (deutsch/englisch)
2. Extrahiert Begriffe > 3 Zeichen
3. Behält Großschreibung bei
4. Kombiniert mit Context-Keywords (falls vorhanden)
5. Zeigt Top 5-8 Keywords

**Beispiel:**
```
Input:  "Wie beeinflussen Lean Governance Prinzipien DevOps-Teams?"
Output: ["Lean", "Governance", "Prinzipien", "DevOps", "Teams"]
```

### 2. Context-Integration

Wenn `config/academic_context.md` existiert:
- Lädt Fachgebiet
- Lädt Basis-Keywords
- Kombiniert mit extrahierten Keywords
- Zeigt Profil-Übersicht

### 3. Run-Konfiguration

Generiert automatisch `runs/{run-id}/run_config.json`:

```json
{
  "run_id": "2026-02-22_14-30-00",
  "research_question": "...",
  "keywords": [...],
  "mode": "Quick",
  "citations_target": 5,
  "databases": {
    "max_count": 3,
    "selection_strategy": "iterative",
    "initial_batch": 5
  },
  "quality": {
    "min_citations": 5,
    "peer_review_required": true
  },
  "time_range": {
    "start_year": 2019,
    "end_year": 2026
  },
  "strategy": "iterative",
  "created_at": "2026-02-22T14:30:00",
  "academic_context": "Software Engineering"
}
```

### 4. Orchestrator-Start

Nach Setup startet automatisch der orchestrator-agent via:
```bash
claude code task \
  --subagent-type orchestrator-agent \
  --description "Run research pipeline for {run-id}" \
  --prompt "[detaillierte Anweisungen]"
```

---

## Fehlerbehandlung

### questionary nicht installiert
```
❌ questionary nicht installiert!

Installiere mit:
  pip3 install questionary
```

**Lösung**: Wrapper-Script installiert automatisch, oder manuell:
```bash
pip3 install questionary
```

### Python 3 nicht gefunden
```
❌ Python 3 nicht gefunden!
```

**Lösung**: Python 3.8+ installieren:
```bash
# macOS
brew install python3

# Ubuntu/Debian
sudo apt install python3 python3-pip
```

### Run-Verzeichnis existiert nicht
```
❌ Run nicht gefunden: runs/2026-02-22_14-30-00
```

**Lösung**: Prüfe Run-ID oder starte neuen Run

---

## Technische Details

### Verwendete Bibliothek

**questionary**: Moderne Python-Bibliothek für interaktive CLI-Prompts

**Features:**
- Text-Input
- Select-Menü (Pfeiltasten)
- Confirm (Yes/No)
- Multi-Select
- Custom Styling
- Validierung

**Dokumentation:** https://github.com/tmbo/questionary

### Styling

Custom Style für Academic Agent:
```python
custom_style = Style([
    ('qmark', 'fg:#673ab7 bold'),          # Fragezeichen (Lila)
    ('question', 'bold'),                   # Frage-Text (Fett)
    ('answer', 'fg:#0e639c bold'),         # Antwort (Blau)
    ('pointer', 'fg:#673ab7 bold'),        # Pfeil (Lila)
    ('selected', 'fg:#0e639c'),            # Auswahl (Blau)
])
```

### Architektur

```
academicagent_wrapper.sh
    │
    ├─→ --interactive
    │   └─→ interactive_setup.py
    │       ├─→ load_academic_context()
    │       ├─→ extract_keywords_from_question()
    │       ├─→ create_run_config()
    │       └─→ spawn_orchestrator()
    │
    ├─→ --cli
    │   └─→ claude code chat '/academicagent'
    │
    └─→ --resume
        └─→ resume_research.sh
```

---

## Vergleich: TUI vs. Chat

| Feature | TUI-Modus | Chat-Modus |
|---------|-----------|------------|
| Setup-Geschwindigkeit | ⚡ 1-2 Min | 🐢 3-5 Min |
| User-Interaktionen | ✅ 5-7 Inputs | ⚠️ 10-15 Messages |
| Keyword-Extraktion | 🤖 Automatisch | 💬 Konversationell |
| Übersicht | ✅ Visuell | ⚠️ Text-basiert |
| Flexibilität | ⚠️ 3 Modi | ✅ Voll customizable |
| Dependency | ⚠️ questionary | ✅ Keine |

**Empfehlung:**
- **TUI-Modus**: Für schnelle, standardisierte Recherchen
- **Chat-Modus**: Für komplexe, hochgradig customisierte Recherchen

---

## Integration mit bestehendem System

### 1. Keine Breaking Changes

- Chat-Modus (`/academicagent`) funktioniert weiterhin
- Setup-Agent und Orchestrator unverändert
- TUI ist **zusätzliche Option**, kein Ersatz

### 2. Gemeinsame Konfig

- TUI generiert dieselbe `run_config.json` wie Chat
- Orchestrator arbeitet identisch
- Kompatibel mit `--resume`

### 3. Workflow-Optionen

```bash
# Option A: TUI → Orchestrator
bash scripts/academicagent_wrapper.sh --interactive

# Option B: Chat → Setup-Agent → Orchestrator
claude code chat --message '/academicagent'

# Option C: Direct Script → Orchestrator
python3 scripts/interactive_setup.py

# Option D: Resume (beide Modi)
bash scripts/academicagent_wrapper.sh --resume {run-id}
```

---

## Nächste Schritte (Optional)

### Geplante Erweiterungen

1. **Multi-Select für Keywords**
   - Manuelle Keyword-Auswahl/Hinzufügung
   - Prioritäten setzen

2. **Database-Auswahl**
   - Manuelle DB-Auswahl vor Start
   - Preview verfügbarer DBs

3. **Progress-Bar Integration**
   - Echtzeit-Fortschritt im TUI
   - Live-Updates während Recherche

4. **Resume-Integration**
   - Liste verfügbarer Runs
   - Status-Preview vor Resume

---

## FAQ

### Kann ich questionary deinstallieren?

Ja, wenn du nur den Chat-Modus nutzt. TUI-Modus benötigt questionary.

### Funktioniert der TUI-Modus in allen Terminals?

Ja, questionary ist kompatibel mit:
- macOS Terminal
- iTerm2
- Linux Terminals (bash, zsh)
- Windows Terminal (WSL)

### Kann ich eigene Modi definieren?

Ja, editiere `get_mode_config()` in [interactive_setup.py](../../scripts/interactive_setup.py:174-190).

### Ist der TUI-Modus schneller als Chat?

Ja, ca. 50-60% weniger Zeit für Setup, da:
- Weniger User-Interaktionen nötig
- Automatische Keyword-Extraktion
- Vorkonfigurierte Modi

---

## Troubleshooting

### Script startet nicht

**Problem**: `bash: permission denied`

**Lösung**:
```bash
chmod +x scripts/academicagent_wrapper.sh
chmod +x scripts/interactive_setup.py
```

### Keine Pfeiltasten-Navigation

**Problem**: Terminal unterstützt keine Pfeiltasten-Events

**Lösung**: Nutze Chat-Modus stattdessen:
```bash
bash scripts/academicagent_wrapper.sh --cli
```

### Orchestrator startet nicht

**Problem**: `claude code` Befehl nicht gefunden

**Lösung**: Claude Code CLI installieren/aktualisieren

---

**Siehe auch:**
- [Original Lösungs-Dokument](../solutions/interactive-cli-tui.md)
- [academicagent Skill](../../.claude/skills/academicagent/SKILL.md)
- [Setup-Agent Dokumentation](../../.claude/agents/setup-agent.md)
