# 🛠️ AcademicAgent Developer Guide

Willkommen zum Developer Guide! Diese Dokumentation hilft dir, AcademicAgent zu verstehen, zu erweitern und beizutragen.

## Für wen ist dieser Guide?

Dieser Guide richtet sich an **Entwickler, Contributors und Maintainer**, die:
- AcademicAgent erweitern möchten (neue Features, Agents, Datenbanken)
- Bugs fixen möchten
- Die Architektur verstehen wollen
- Zum Projekt beitragen möchten

**Voraussetzungen:**
- Python 3.10+ Kenntnisse
- Verständnis von async/await
- Claude Code Agent SDK Grundlagen
- Git & GitHub Workflow

## 📚 Inhaltsverzeichnis

### 1. [Architektur-Übersicht](01-architecture.md)
System-Design, Komponenten und Datenfluss.

**Themen:**
- High-Level Architektur
- 7-Phasen-Workflow (technisch)
- Agent-Hierarchie
- State-Management
- CDP-Integration
- Datenbank-Strategie

**Für:** Verstehen wie das System funktioniert

---

### 2. [Agent-Entwicklung](02-agent-development.md)
Wie man neue Agents erstellt und bestehende erweitert.

**Themen:**
- Agent SDK Grundlagen
- Agent-Struktur & Konventionen
- Tool-Nutzung Best Practices
- Prompt Engineering für Agents
- Testing & Debugging
- Agent-zu-Agent Kommunikation

**Für:** Neue Agents entwickeln oder bestehende anpassen

---

### 3. [Datenbanken hinzufügen](03-adding-databases.md)
Integration neuer akademischer Datenbanken.

**Themen:**
- Datenbank-Katalog verstehen
- YAML-Konfiguration
- Browser-Navigation implementieren
- Suchstring-Anpassung
- PDF-Download-Strategien
- Testing & Validierung

**Für:** Support für neue Datenbanken hinzufügen

---

### 4. [Testing-Guide](04-testing.md)
Umfassender Guide für Unit-, Integration- und E2E-Tests.

**Themen:**
- Test-Struktur & Organisation
- Unit-Tests mit pytest
- Mocking & Fixtures
- Integration-Tests
- CI/CD-Pipeline
- Coverage & Qualität

**Für:** Tests schreiben und Test-Infrastruktur verstehen

---

### 5. [Security-Considerations](05-security.md)
Sicherheitsaspekte für Entwickler.

**Themen:**
- Threat-Model verstehen
- Input-Sanitierung implementieren
- Action-Gate verwenden
- Domain-Validierung
- Secrets-Management
- Security-Testing

**Für:** Sichere Features entwickeln

---

### 6. [Contribution-Guide](06-contribution-guide.md)
Wie man zum Projekt beiträgt.

**Themen:**
- Development-Setup
- Git-Workflow
- Code-Konventionen
- Pull-Request-Prozess
- Review-Guidelines
- Community-Standards

**Für:** Beiträge zum Projekt einreichen

---

## 🚀 Quick Start für Entwickler

### Setup Development Environment

```bash
# 1. Repository forken und klonen
git clone https://github.com/jamski105/AcademicAgent.git
cd AcademicAgent

# 2. Development-Dependencies installieren
bash setup.sh

# 3. Test-Dependencies installieren
pip install -r tests/requirements-test.txt

# 4. Pre-Commit-Hooks installieren
bash scripts/setup_git_hooks.sh

# 5. Tests ausführen
python3 -m pytest tests/unit/ -v

# 6. Development-Branch erstellen
git checkout -b feature/my-feature
```

### Erster Beitrag

1. **Issue finden** oder erstellen
   - Siehe [GitHub Issues](https://github.com/jamski105/AcademicAgent/issues)
   - Label "good first issue" für Anfänger

2. **Lokale Änderungen machen**
   ```bash
   # Edit files...

   # Tests ausführen
   pytest tests/unit/ -v

   # Commit
   git commit -m "feat: add feature X"
   ```

3. **Pull Request erstellen**
   - Push zu deinem Fork
   - Erstelle PR mit Beschreibung
   - Warte auf Review

---

## 📊 Projekt-Struktur

```
AcademicAgent/
├── .claude/
│   ├── agents/                 # Agent-Definitionen
│   │   ├── browser-agent.md
│   │   ├── search-agent.md
│   │   ├── scoring-agent.md
│   │   ├── extraction-agent.md
│   │   └── setup-agent.md
│   └── skills/                 # Skill-Definitionen
│       └── academicagent/
│           └── SKILL.md        # Orchestrator
│
├── config/
│   ├── database_disciplines.yaml  # Datenbank-Katalog
│   └── academic_context.md        # Konfig-Template
│
├── scripts/
│   ├── cdp_wrapper.py          # CDP-Client
│   ├── cost_tracker.py         # Kosten-Tracking
│   ├── metrics.py              # Metriken-Collector
│   ├── retry_strategy.py       # Retry-Handler
│   ├── safe_bash.py            # Action-Gate
│   └── validate_state.py       # State-Validierung
│
├── tests/
│   ├── unit/                   # Unit-Tests
│   │   ├── test_action_gate.py
│   │   ├── test_validate_domain.py
│   │   ├── test_sanitize_html.py
│   │   └── test_retry_strategy.py
│   └── requirements-test.txt   # Test-Dependencies
│
├── docs/
│   ├── user-guide/             # Für Endnutzer
│   ├── developer-guide/        # Für Contributors (DU BIST HIER)
│   ├── api-reference/          # Technische Referenz
│   ├── DBIS_USAGE.md           # DBIS-Integration
│   └── THREAT_MODEL.md         # Sicherheitsanalyse
│
├── ERROR_RECOVERY.md           # Fehlerbehandlung
├── SECURITY.md                 # Sicherheitsdoku
├── README.md                   # Projekt-Übersicht
└── setup.sh                    # Setup-Script
```

---

## 🧰 Development-Tools

### Nützliche Scripts

```bash
# State validieren
python3 scripts/validate_state.py runs/[timestamp]/metadata/research_state.json

# Kosten analysieren
python3 scripts/cost_tracker.py runs/[timestamp]/metadata/llm_costs.jsonl

# Metriken anzeigen
python3 scripts/metrics.py summarize runs/[timestamp]/metadata/metrics.jsonl

# Safe Bash (mit Action-Gate)
python3 scripts/safe_bash.py "command"

# Chrome-Verbindung testen
curl http://localhost:9222/json/version
```

### Debugging

```bash
# Debug-Modus aktivieren
export ACADEMIC_AGENT_DEBUG=1

# Detaillierte CDP-Logs
export CDP_DEBUG=1

# Python-Debugger
python3 -m pdb scripts/validate_state.py [args]
```

### Code-Qualität

```bash
# Tests mit Coverage
pytest tests/unit/ -v --cov=scripts --cov-report=html

# Linting (wenn konfiguriert)
pylint scripts/*.py

# Type-Checking (wenn konfiguriert)
mypy scripts/*.py
```

---

## 🗺️ Architektur-Diagramm (High-Level)

```
┌──────────────────────────────────────────────────────────────┐
│                     User Interface                           │
│              (VS Code + Claude Code Chat)                    │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────┐
│                  Orchestrator Skill                          │
│              (/academicagent SKILL.md)                       │
│  • Workflow-Management                                       │
│  • Phase-Transitions                                         │
│  • Human-in-the-Loop Checkpoints                            │
│  • State-Persistence                                         │
└────────┬──────────────┬──────────────┬───────────┬───────────┘
         │              │              │           │
         ▼              ▼              ▼           ▼
┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐
│  Setup     │ │  Browser   │ │  Search    │ │  Scoring   │
│  Agent     │ │  Agent     │ │  Agent     │ │  Agent     │
│            │ │            │ │            │ │            │
│ • Config   │ │ • DBIS Nav │ │ • Boolean  │ │ • 5D Score │
│   Setup    │ │ • DB Search│ │   Queries  │ │ • Ranking  │
│ • Validate │ │ • PDF DL   │ │ • Per-DB   │ │ • Sorting  │
└────────────┘ └─────┬──────┘ └────────────┘ └────────────┘
                     │
                     ▼
              ┌─────────────┐        ┌────────────┐
              │ CDP Wrapper │───────▶│  Chrome    │
              │             │        │  (Debug)   │
              │ • Navigate  │        │            │
              │ • Search    │        │  Port 9222 │
              │ • Download  │        └────────────┘
              └─────────────┘
                     │
                     ▼
              ┌─────────────┐
              │ Extraction  │
              │   Agent     │
              │             │
              │ • pdftotext │
              │ • Quotes    │
              │ • Relevance │
              └─────────────┘
                     │
                     ▼
              ┌─────────────┐
              │  Outputs    │
              │             │
              │ • BibTeX    │
              │ • JSON      │
              │ • Markdown  │
              └─────────────┘
```

---

## 🔑 Kern-Konzepte

### 1. Agent-basierte Architektur

Jede Aufgabe wird von einem spezialisierten Agent durchgeführt:
- **Orchestrator** - Workflow-Management
- **Browser-Agent** - Web-Automatisierung
- **Search-Agent** - Suchstring-Generierung
- **Scoring-Agent** - Paper-Bewertung
- **Extraction-Agent** - Zitat-Extraktion
- **Setup-Agent** - Konfig-Erstellung

### 2. State-Management

Persistenter State ermöglicht:
- Fortsetzung nach Unterbrechung
- Fehler-Recovery
- Audit-Trail
- Reproduzierbarkeit

**State-Datei:**
```json
{
  "version": "3.0",
  "current_phase": 3,
  "completed_phases": [0, 1, 2],
  "metadata": {...},
  "checksum": "sha256:..."
}
```

### 3. Sicherheits-Framework

Mehrschichtige Sicherheit:
1. **Input-Sanitierung** - HTML-Bereinigung
2. **Action-Gate** - Befehlsvalidierung
3. **Domain-Whitelist** - Nur akademische Datenbanken
4. **Least-Privilege** - Minimale Berechtigungen

### 4. Iterative Datenbanksuche

Stoppt automatisch wenn genug Papers gefunden:
```
Iteration 1: Top 5 DBs → 23 papers
Check: 23 < 50 → Continue
Iteration 2: Next 5 DBs → 52 papers (total)
Check: 52 ≥ 50 → Stop ✓
```

---

## 📖 Weiterführende Dokumentation

### Für Entwickler:
- **[Architektur](01-architecture.md)** - Tiefes Verständnis des Systems
- **[Agent-Entwicklung](02-agent-development.md)** - Neue Agents schreiben
- **[Testing](04-testing.md)** - Test-Infrastruktur

### Für Sicherheit:
- **[Security-Considerations](05-security.md)** - Sichere Entwicklung
- **[SECURITY.md](../../SECURITY.md)** - Sicherheitsdoku
- **[THREAT_MODEL.md](../THREAT_MODEL.md)** - Bedrohungsanalyse

### Für Contributors:
- **[Contribution-Guide](06-contribution-guide.md)** - Beitragen zum Projekt

### Für Nutzer:
- **[User Guide](../user-guide/README.md)** - Für Endnutzer
- **[API Reference](../api-reference/README.md)** - Technische Referenz

---

## 💬 Community & Support

### Fragen stellen

- **GitHub Discussions:** [github.com/jamski105/AcademicAgent/discussions](https://github.com/jamski105/AcademicAgent/discussions)
- **Issues:** [github.com/jamski105/AcademicAgent/issues](https://github.com/jamski105/AcademicAgent/issues)

### Beitragen

- **Pull Requests:** Willkommen für Features, Bugfixes, Doku
- **Code Reviews:** Hilf bei Review von PRs
- **Dokumentation:** Verbessere Guides und README

### Code of Conduct

Wir erwarten:
- Respektvolle Kommunikation
- Konstruktives Feedback
- Hilfsbereitschaft gegenüber Anfängern
- Fokus auf technische Qualität

---

## 🎯 Roadmap & Contributing

### Aktuelle Priorities

Siehe [GitHub Projects](https://github.com/jamski105/AcademicAgent/projects):

**High Priority:**
- Neue Datenbanken (PsycINFO, ERIC, etc.)
- Performance-Optimierungen
- Besseres Error-Handling

**Medium Priority:**
- Web-UI für Konfiguration
- Mehr Ausgabe-Formate (APA, MLA, etc.)
- Windows-Support

**Low Priority:**
- ML-basiertes Relevanz-Scoring
- Automatische Duplikatserkennung

### Wo beitragen?

- **Good First Issues:** [Label: good-first-issue](https://github.com/jamski105/AcademicAgent/labels/good-first-issue)
- **Help Wanted:** [Label: help-wanted](https://github.com/jamski105/AcademicAgent/labels/help-wanted)
- **Dokumentation:** Immer willkommen!

---

**Happy Coding! 🚀**

Starte mit [Architektur-Übersicht →](01-architecture.md)
