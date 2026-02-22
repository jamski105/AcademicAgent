# 📁 AcademicAgent - Projektstruktur

**Version:** 3.3
**Letzte Aktualisierung:** 2026-02-22

Diese Dokumentation beschreibt die Ordnerstruktur und den Zweck aller Verzeichnisse und wichtigen Dateien im AcademicAgent-Projekt.

---

## 📊 Übersicht

```
AcademicAgent/
├── .claude/                    # Claude-Code-Agent-Konfiguration
├── .github/                    # GitHub-spezifische Dateien (CI/CD)
├── config/                     # Recherche-Konfigurationen
├── docs/                       # Dokumentation
├── runs/                       # Recherche-Ausgaben (Runtime-generiert)
├── schemas/                    # JSON-Schemas für Validierung
├── scripts/                    # Python/Bash-Utility-Scripte
├── tests/                      # Test-Suite (Unit, E2E, Red-Team)
└── [Root-Dateien]              # Setup, Lizenz, README, etc.
```

---

## 🔧 Root-Verzeichnis

### Hauptdateien

| Datei | Zweck |
|-------|-------|
| `README.md` | Haupt-Dokumentation, Schnellstart, Feature-Übersicht |
| `CHANGELOG.md` | Versionshistorie, Release-Notes |
| `LICENSE` | MIT-Lizenz |
| `SECURITY.md` | Sicherheitsdokumentation, Red-Team-Tests, Defense-in-Depth |
| `PRIVACY.md` | Datenschutzrichtlinie, GDPR-Compliance, Log-Redaction |
| `ERROR_RECOVERY.md` | Fehlerbehandlung, CDP-Probleme, State-Wiederherstellung |
| `setup.sh` | Installations-Script (Homebrew, Python, Chrome-Setup) |
| `requirements.txt` | Python-Dependencies für Produktion |
| `.gitignore` | Git-Ignores (runs/, .venv/, .env) |
| `.env.example` | Template für Umgebungsvariablen (ANTHROPIC_API_KEY) |

### Konfigurationsdateien

| Datei | Zweck |
|-------|-------|
| `package.json` | Node.js Dependencies (Playwright, CDP) |
| `package-lock.json` | Lock-File für Node-Dependencies |

---

## 🤖 `.claude/` - Claude-Code-Agent-Konfiguration

Enthält alle Agent-Definitionen und Skill-Konfigurationen für Claude Code.

### Struktur

```
.claude/
├── agents/                     # Agent-Definitionen (Prompts)
│   ├── browser-agent.md       # Browser-Automatisierung via CDP
│   ├── extraction-agent.md    # PDF-Zitat-Extraktion
│   ├── orchestrator-agent.md  # Haupt-Orchestrator (7 Phasen)
│   ├── scoring-agent.md       # 5D-Bewertungssystem
│   ├── search-agent.md        # Boolean-Query-Generierung
│   └── setup-agent.md         # Interaktive Konfig-Erstellung
├── shared/                     # Geteilte Dokumentation für Agents
│   ├── AGENT_API_CONTRACTS.md # Input/Output-Contracts
│   ├── CLI_UI_STANDARD.md     # CLI-Ausgabe-Standards
│   ├── DBIS_USAGE.md          # DBIS-Proxy-Mode
│   ├── ERROR_REPORTING_FORMAT.md # Error-Reporting
│   ├── OBSERVABILITY.md       # Logging & Monitoring
│   ├── ORCHESTRATOR_CLI_PATCHES.md # CLI-Patches
│   ├── ORCHESTRATOR_ROBUSTNESS_FIXES.md # Robustness
│   └── SECURITY_POLICY.md     # Sicherheitsrichtlinien
├── skills/                     # Skill-Definitionen
│   └── academicagent/         # Haupt-Skill (/academicagent)
├── settings.json              # Permissions & Tool-Zugriff
└── settings.local.json        # Lokale Overrides
```

### Agent-Übersicht

| Agent | Zweck | Phase |
|-------|-------|-------|
| `orchestrator-agent` | Koordiniert 7 Phasen, State-Management | Alle |
| `setup-agent` | Erstellt Recherche-Konfiguration | Setup |
| `browser-agent` | Navigiert Datenbanken, lädt PDFs | 0, 2, 4 |
| `search-agent` | Generiert Boolean-Suchstrings | 1 |
| `scoring-agent` | Rankt Kandidaten mit 5D-System | 3 |
| `extraction-agent` | Extrahiert Zitate aus PDFs | 5 |

---

## ⚙️ `config/` - Recherche-Konfigurationen

Enthält Recherche-Konfigurationsdateien im Markdown-Format.

```
config/
├── .example/                   # Template-Beispiele
│   └── academic_context_cs_example.md
├── academic_context.md         # Standard-Template
└── database_disciplines.yaml   # Datenbank-Definitionen
```

| Datei | Zweck |
|-------|-------|
| `academic_context.md` | Template für Recherche-Konfiguration |
| `database_disciplines.yaml` | Kuratierte Top-Datenbanken pro Disziplin |
| `.example/` | Beispiel-Konfigurationen für verschiedene Fachgebiete |

**Nutzer erstellen hier ihre eigenen `.md`-Dateien** mit Forschungsfrage, Keywords, Suchparametern.

---

## 📂 `runs/` - Recherche-Ausgaben (Runtime)

Wird automatisch beim Ausführen von `/academicagent` erstellt. Jede Recherche erhält einen eigenen Timestamp-Ordner.

```
runs/
└── 2026-02-18_14-30-00/        # Timestamp-basierte Run-ID
    ├── config/                 # Kopie der verwendeten Konfiguration
    │   └── run_config.json
    ├── metadata/               # Zwischen-Outputs der Phasen
    │   ├── research_state.json # State-Management
    │   ├── candidates.json     # Gerankte Kandidaten (Phase 3)
    │   ├── search_strings.json # Boolean-Queries (Phase 1)
    │   └── database_list.json  # Erkannte DBs (Phase 0)
    ├── downloads/              # Heruntergeladene PDFs (Phase 4)
    │   ├── paper_001.pdf
    │   └── ...
    ├── outputs/                # Finale Ausgaben
    │   ├── quote_library.json  # Extrahierte Zitate (Phase 5)
    │   ├── bibliography.bib    # BibTeX-Bibliographie
    │   └── summary.md          # Recherche-Zusammenfassung
    └── logs/                   # Strukturierte Logs
        ├── phase_0.log
        ├── cdp_health.log
        └── llm_costs.jsonl
```

**WICHTIG:** Dieses Verzeichnis ist in `.gitignore` (enthält große PDFs).

---

## 📐 `schemas/` - JSON-Validierungs-Schemas

JSON-Schemas für Output-Validierung via `validation_gate.py`.

```
schemas/
├── candidates_schema.json      # Schema für candidates.json
├── quotes_schema.json          # Schema für quote_library.json
└── ranked_sources_schema.json  # Schema für gerankte Quellen
```

Jedes Schema definiert:

- Required Fields
- Data Types
- Enums für Status-Felder
- Validierungsregeln

---

## 🔧 `scripts/` - Utility-Scripte & Core-Logic

Das Herzstück des Systems. Alle Python/Bash/JS-Scripte für Workflow-Logik.

### Sicherheits-Layer

| Script | Zweck |
|--------|-------|
| `safe_bash.py` | Safe-Bash-Wrapper mit Action-Gate-Validierung |
| `action_gate.py` | Validiert Tool-Aufrufe (Source-Tracking) |
| `validation_gate.py` | JSON-Schema + Injection-Detection |
| `sanitize_html.py` | HTML-Bereinigung, XSS-Prevention |
| `validate_domain.py` | Domain-Whitelisting (nur akademische Seiten) |
| `pdf_security_validator.py` | PDF Deep-Analysis, Metadata-Stripping |

### Browser-Automatisierung

| Script | Zweck |
|--------|-------|
| `browser_cdp_helper.js` | Node.js CDP-Wrapper für Browser-Steuerung |
| `cdp_wrapper.py` | Python CDP-Client mit Fallback-Mechanismus |
| `cdp_fallback_manager.py` | Auto-Recovery bei Chrome-Absturz |
| `cdp_health_check.sh` | CDP-Verbindungs-Monitoring |
| `start_chrome_debug.sh` | Startet Chrome mit Remote-Debugging (Port 9222) |
| `smart_chrome_setup.sh` | Intelligentes Chrome-Setup mit Fehlerbehandlung |
| `track_navigation.py` | Trackt Browser-Navigation, erkennt Redirects |

### State & Error-Management

| Script | Zweck |
|--------|-------|
| `state_manager.py` | Research-State-Management (Phase-Tracking) |
| `validate_state.py` | State-Validierung, Checksum-Verifikation |
| `error_handler.sh` | Zentraler Error-Handler für Bash-Scripte |
| `error_types.py` | Error-Type-Definitionen, Severity-Levels |
| `retry_strategy.py` | Exponential-Backoff-Retry-Handler |
| `enforce_retry.py` | Decorator-basierte Retry-Enforcement |

### Monitoring & Observability

| Script | Zweck |
|--------|-------|
| `logger.py` | Strukturiertes Logging mit PII-Redaction |
| `metrics.py` | Performance-Metriken-Sammlung |
| `cost_tracker.py` | LLM-API-Kosten-Tracking |
| `budget_limiter.py` | Token-Budget-Enforcement (warnt bei 80%) |
| `live_monitor.py` | Live-Monitoring für laufende Recherchen |

### Daten-Verarbeitung

| Script | Zweck |
|--------|-------|
| `create_bibliography.py` | Generiert BibTeX aus candidates.json |
| `create_quote_library_with_citations.py` | Extrahiert Zitate mit Seitenzahlen |
| `database_patterns.json` | DB-Selektoren für Browser-Agent |
| `domain_whitelist.json` | Erlaubte akademische Domains |

### Setup & Konfiguration

| Script | Zweck |
|--------|-------|
| `generate_config.py` | Generiert run_config.json aus academic_context.md |
| `select_config.py` | CLI-Tool zur Konfig-Auswahl |
| `validate_config.py` | Validiert Recherche-Konfiguration |
| `auto_permissions.py` | Auto-Grant für sichere Bash-Befehle |
| `setup_git_hooks.sh` | Installiert Pre-Commit-Hooks (Secret-Scanning) |

### Resilience & Gating

| Script | Zweck |
|--------|-------|
| `check_threshold.py` | Prüft Schwellwerte (Min. Kandidaten pro DB) |
| `resume_research.sh` | Fortsetzt unterbrochene Recherchen |

---

## 🧪 `tests/` - Test-Suite

Umfassende Test-Suite für Unit-, Integration- und Security-Tests.

```
tests/
├── unit/                       # Unit-Tests für einzelne Module
│   ├── test_action_gate.py    # Action-Gate-Validierung
│   ├── test_enforce_retry.py  # Retry-Enforcement
│   ├── test_logger_redaction.py # PII-Redaction
│   ├── test_pdf_security_validator.py # PDF-Security
│   ├── test_retry_strategy.py # Retry-Strategien
│   ├── test_safe_bash.py      # Safe-Bash-Wrapper
│   ├── test_sanitize_html.py  # HTML-Sanitierung
│   ├── test_validate_domain.py # Domain-Validierung
│   └── test_validation_gate.py # Output-Validierung
├── e2e/                        # End-to-End-Tests
│   └── test_minimal_pipeline.sh # Minimaler Workflow-Test
├── red_team/                   # Security-Tests
│   ├── injection_payloads.json # Injection-Test-Payloads
│   ├── run_tests.sh           # Red-Team-Test-Runner
│   └── test_results.json      # Test-Ergebnisse
├── fixtures/                   # Test-Fixtures (Dummy-Daten)
├── requirements-test.txt       # Test-Dependencies (pytest, etc.)
└── test_dbis_proxy.sh         # DBIS-Proxy-Mode-Test
```

### Test-Kategorien

| Kategorie | Beschreibung | Coverage |
|-----------|--------------|----------|
| **Unit Tests** | Einzelne Module isoliert testen | 85%+ |
| **E2E Tests** | Voller Workflow Phase 0-6 | Manuell |
| **Red-Team Tests** | Injection, XSS, Command-Injection | 90%+ Pass |
| **Security Tests** | Domain-Validation, Safe-Bash | 100% |

**Ausführen:**
```bash
pytest tests/unit/ -v --cov=scripts
```

---

## 🚀 `.github/` - CI/CD Pipeline

GitHub Actions Workflows für automatisierte Tests und Validierung.

```
.github/
└── workflows/
    └── ci.yml                  # Haupt-CI-Pipeline
```

### CI-Pipeline Jobs

| Job | Beschreibung |
|-----|--------------|
| `setup-test` | Installiert Dependencies (Python, Node, Homebrew) |
| `unit-tests` | Führt pytest mit Coverage aus |
| `security-tests` | Red-Team-Tests (90% Pass-Rate erforderlich) |
| `script-validation` | Syntax-Checks für Python/Bash |
| `secrets-scan` | Scannt nach API-Keys und Secrets |
| `build-validation` | Prüft Dateistruktur, Agent-Configs |
| `status-report` | Aggregiert alle Ergebnisse |

**Trigger:**

- Push zu `main` oder `develop`
- Pull Requests zu `main`

---

## 📚 `docs/` - Dokumentation

Projektdokumentation (aktuell minimal, sollte erweitert werden).

```
docs/
├── PROJEKTSTRUKTUR.md          # Diese Datei!
└── THREAT_MODEL.md             # Bedrohungsmodell & Security-Analyse
```

**Geplant (aus README referenziert, aber noch nicht erstellt):**

- `user-guide/` - Nutzer-Dokumentation
- `developer-guide/` - Entwickler-Dokumentation
- `api-reference/` - API-Referenz

---

## 🔐 Sicherheitsrelevante Dateien (Root)

| Datei | Zweck |
|-------|-------|
| `SECURITY.md` | Defense-in-Depth, Red-Team-Tests, Score 9.8/10 |
| `PRIVACY.md` | GDPR-Compliance, Log-Redaction-Policy |
| `ERROR_RECOVERY.md` | Fehlerbehandlung, State-Recovery |
| `.env.example` | Template für Secrets (ANTHROPIC_API_KEY) |

**Wichtig:**

- `.env` und `.env.*` sind in `.gitignore`
- Secrets werden automatisch aus Logs redacted
- Pre-Commit-Hook scannt nach versehentlichen Commits

---

## 📦 Dependencies & Virtual Environment

| Verzeichnis/Datei | Zweck |
|-------------------|-------|
| `.venv/` | Python Virtual Environment (gitignored) |
| `requirements.txt` | Python-Dependencies (Playwright, jsonschema) |
| `tests/requirements-test.txt` | Test-Dependencies (pytest, coverage) |
| `package.json` | Node.js Dependencies (für CDP-Helper) |

**Setup:**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
npm install
```

---

## 🎯 Wichtigste Dateien für Nutzer

Wenn du **AcademicAgent nutzen** möchtest, sind das die wichtigsten Dateien:

1. **`README.md`** - Starte hier für Schnellstart
2. **`setup.sh`** - Führe dies aus für Installation
3. **`config/academic_context.md`** - Erstelle deine Recherche-Konfiguration
4. **`runs/`** - Hier findest du deine Recherche-Ergebnisse
5. **`ERROR_RECOVERY.md`** - Bei Problemen

---

## 🛠️ Wichtigste Dateien für Entwickler

Wenn du **AcademicAgent erweitern** möchtest:

1. **`.claude/agents/`** - Agent-Prompts anpassen
2. **`scripts/`** - Core-Logic erweitern
3. **`tests/unit/`** - Tests hinzufügen
4. **`schemas/`** - JSON-Schemas definieren
5. **`.claude/shared/AGENT_API_CONTRACTS.md`** - Contracts verstehen

---

## 🗂️ Dateien die NICHT ins Git gehören

Über `.gitignore` ausgeschlossen:

- `runs/` - Große PDFs und Recherche-Daten
- `.venv/` - Virtual Environment
- `.env`, `.env.*` - Secrets
- `node_modules/` - Node-Dependencies
- `.pytest_cache/` - Test-Cache
- `__pycache__/` - Python-Bytecode
- `.DS_Store` - macOS-Metadaten

---

## 📊 Zusammenfassung

### Nach Funktion

| Kategorie | Verzeichnisse |
|-----------|---------------|
| **Agent-Definitionen** | `.claude/agents/`, `.claude/shared/` |
| **Konfiguration** | `config/`, `.claude/settings.json` |
| **Core-Logic** | `scripts/` (40+ Scripte) |
| **Ausgaben** | `runs/` (runtime-generiert) |
| **Tests** | `tests/unit/`, `tests/red_team/` |
| **Dokumentation** | `docs/`, `README.md`, `SECURITY.md` |
| **CI/CD** | `.github/workflows/` |

### Zeilen-Code (geschätzt)

- **Agent-Prompts:** ~3.000 Zeilen Markdown
- **Python-Scripte:** ~5.000 Zeilen Code
- **Bash-Scripte:** ~1.500 Zeilen Code
- **Tests:** ~2.000 Zeilen Code
- **Dokumentation:** ~2.500 Zeilen Markdown

**Gesamt:** ~14.000 Zeilen

---

## 🔗 Weiterführende Ressourcen

- **Haupt-README:** [README.md](../README.md)
- **Sicherheit:** [SECURITY.md](../SECURITY.md)
- **Fehlerbehandlung:** [ERROR_RECOVERY.md](../ERROR_RECOVERY.md)
- **Changelog:** [CHANGELOG.md](../CHANGELOG.md)
- **GitHub Issues:** https://github.com/jamski105/AcademicAgent/issues

---

**Letzte Aktualisierung:** 2026-02-22 | **Version:** 3.3
