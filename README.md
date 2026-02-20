# 🎓 AcademicAgent

**Version:** 3.3 (Validation-Gate & MANDATORY Encryption Edition)
**Autonomes akademisches Literatur-Recherche-System**

> ⚠️ **WICHTIG: macOS ONLY**
>
> Dieses System ist **ausschließlich für macOS** entwickelt und getestet.
> - Erfordert macOS-spezifische Pfade (`/Applications/Google Chrome.app`)
> - Nutzt macOS-spezifische Befehle (`stat -f`, `lsof`, `open`)
> - Homebrew als Paketmanager
>
> **Linux/Windows werden NICHT unterstützt.**

AcademicAgent ist ein Claude-basierter Forschungsassistent, der den gesamten Literaturrecherche-Prozess automatisiert - von der Datenbanksuche bis zur Zitat-Extraktion. Er liefert 18 hochwertige Veröffentlichungen mit zitierfähigen Zitaten in 3,5-4 Stunden.

---

## 🌟 Hauptfunktionen

- **Vollständig autonom**: 7-Phasen-Workflow mit minimaler menschlicher Aufsicht
- **Intelligente Datenbankauswahl**: 30 kuratierte Top-Datenbanken + dynamische DBIS-Erkennung
- **5D-Bewertungssystem**: Zitationen, Aktualität, Relevanz, Journalqualität, Open Access
- **Iterative Suche**: Durchsucht jeweils 5 Datenbanken bis Ziel erreicht (40% weniger Datenbanken, 42% schneller)
- **PDF-Extraktion**: Natives `pdftotext` - 5x schneller als browserbasierte Extraktion
- **Zitatbibliothek**: Strukturiertes JSON mit Seitenzahlen und Relevanzscores
- **Fehlerwiederherstellung**: Automatisches State-Management mit Fortsetzungsfähigkeit
- **Sicherheit**: Defense-in-Depth mit Validation-Gate, Encryption-at-Rest, Retry-Enforcement (9.8/10 Score)

---

## 🚀 Schnellstart

### Voraussetzungen

- **macOS** (10.15 Catalina oder neuer empfohlen)
- Google Chrome Browser
- Universitäts-VPN-Zugang (für lizenzierte Datenbanken)
- Homebrew Paketmanager (wird automatisch installiert falls nicht vorhanden)

### Installation

```bash
# Repository klonen
git clone https://github.com/jamski105/AcademicAgent.git
cd AcademicAgent

# Setup ausführen (installiert alle Abhängigkeiten)
bash setup.sh

# Chrome mit Remote-Debugging starten
bash scripts/start_chrome_debug.sh
```

### Deine erste Recherche

```bash
# VS Code öffnen
code .

# Claude Code Chat starten
# Cmd+Shift+P → "Claude Code: Start Chat"

# Im Chat:
/academicagent
```

Das war's! Der Agent wird:
1. Dich durch die Erstellung einer Recherche-Konfiguration führen
2. Datenbanken über DBIS durchsuchen
3. Kandidaten mit 5D-Bewertung ranken
4. Die Top 18 PDFs herunterladen
5. Relevante Zitate extrahieren
6. Bibliographie generieren

**Geschätzte Zeit:** 3,5-4 Stunden (größtenteils automatisiert)

---

## 📋 Skills-Übersicht

### Haupt-Skill

| Skill | Beschreibung | Wann verwenden |
|-------|-------------|----------------|
| **`/academicagent`** | Haupt-Orchestrator - führt alle 7 Phasen aus | Immer für neue Recherchen |

### Debug-Skills (Optional)

| Skill | Beschreibung | Wann verwenden |
|-------|-------------|----------------|
| `/setup-agent` | Interaktive Konfig-Generierung | Konfigs erstellen ohne Recherche zu starten |
| `/browser-agent` | Browser-Automatisierungs-Tests | CDP/UI-Navigationsprobleme debuggen |
| `/search-agent` | Boolean-Suchstring-Tests | Query-Generierung debuggen |
| `/scoring-agent` | 5D-Ranking-Tests | Kandidaten-Ranking debuggen |
| `/extraction-agent` | PDF-Extraktions-Tests | Zitat-Extraktion debuggen |

---

## 🎯 Der 7-Phasen-Workflow

Der Orchestrator verwaltet alle Phasen automatisch mit 5 menschlichen Checkpoints:

| Phase | Name | Dauer | Checkpoint | Beschreibung |
|-------|------|-------|------------|--------------|
| **0** | DBIS-Navigation | 15-20 Min | ✅ | Navigation zu Datenbanken über DBIS-Portal |
| **1** | Suchstring-Generierung | 5-10 Min | ✅ | Boolean-Queries aus Keywords generieren |
| **2** | Datenbanksuche | 90-120 Min | ❌ | Iterative Suche (jeweils 5 DBs) |
| **3** | 5D-Bewertung & Ranking | 20-30 Min | ✅ | Kandidaten ranken, Top 27 auswählen → User wählt 18 |
| **4** | PDF-Download | 20-30 Min | ❌ | Ausgewählte Papers herunterladen |
| **5** | Zitat-Extraktion | 30-45 Min | ✅ | Relevante Zitate mit Seitenzahlen extrahieren |
| **6** | Finalisierung | 15-20 Min | ✅ | Bibliographie und Ausgaben generieren |

### Checkpoints (Human-in-the-Loop)

- **Checkpoint 0:** Datenbankliste validieren
- **Checkpoint 1:** Suchstrings freigeben
- **Checkpoint 3:** Top 18 aus Top 27 Kandidaten auswählen
- **Checkpoint 5:** Zitatqualität prüfen
- **Checkpoint 6:** Finale Ausgaben bestätigen

---

## 💾 Ausgabe-Struktur

```
runs/
└── 2026-02-18_14-30-00/
    ├── downloads/              # 18 PDF-Dateien
    ├── metadata/
    │   ├── research_state.json # Fortsetzungs-State
    │   ├── candidates.json     # Gerankte Kandidaten
    │   ├── search_strings.json # Generierte Queries
    │   └── config.md           # Recherche-Konfiguration
    ├── outputs/
    │   ├── quote_library.json  # Extrahierte Zitate
    │   ├── bibliography.bib    # BibTeX-Zitationen
    │   └── summary.md          # Recherche-Zusammenfassung
    └── logs/
        ├── phase_*.log         # Phasen-Ausführungslogs
        └── cdp_health.log      # Browser-Monitoring-Logs
```

---

## 🗃️ Datenbank-Strategie V3.0

### Kuratierte Top-Datenbanken

AcademicAgent verwendet eine kuratierte Liste von TOP-Datenbanken pro Disziplin:

**Interdisziplinär (Top 10):**
- Web of Science, Scopus, Google Scholar, JSTOR
- SpringerLink, ScienceDirect, PubMed, arXiv
- BASE, CORE

**Informatik:**
- ACM Digital Library, IEEE Xplore, DBLP
- arXiv, Scopus

**Wirtschaft & BWL:**
- WISO, Statista, Business Source Elite
- EconBiz, RePEc, SSRN, Scopus

**Jura:**
- juris, beck-online, Wolters Kluwer Online
- Staudinger BGB, HeinOnline, Westlaw

### DBIS Dynamische Erkennung

Zusätzlich zur kuratierten Liste erkennt der Agent dynamisch weitere Datenbanken über DBIS:

1. Durchsucht DBIS mit Recherche-Keywords + Disziplin
2. Bewertet Ergebnisse nach Beschreibungs-Relevanz (0-100)
3. Fügt Datenbanken mit Score ≥ 60 zur Suchliste hinzu
4. Integriert sich mit iterativer Suchstrategie

**Ergebnis:** 40% weniger durchsuchte Datenbanken, 42% schnellere Ausführung, höhere Relevanz

---

## 🔄 Iterative Suchstrategie

Anstatt alle Datenbanken im Voraus zu durchsuchen, sucht der Agent iterativ:

```
Phase 2: Datenbanksuche (Iterativ)
├─ Iteration 1: Top 5 Datenbanken → 23 Kandidaten
├─ Check: Ziel erreicht? (Ziel: 50) → NEIN
├─ Iteration 2: Nächste 5 Datenbanken → 51 Kandidaten (gesamt)
└─ Check: Ziel erreicht? → JA → Vorzeitig stoppen
```

**Vorteile:**
- Stoppt wenn genügend Kandidaten gefunden wurden
- Spart Zeit bei weniger relevanten Datenbanken
- Priorisiert hochwertige Quellen

---

## 🧠 5D-Bewertungssystem

Jeder Kandidat wird über 5 Dimensionen bewertet:

| Dimension | Gewichtung | Beschreibung |
|-----------|------------|--------------|
| **Zitationen** | 20% | Google Scholar Zitationsanzahl (normalisiert) |
| **Aktualität** | 20% | Publikationsjahr (2024 = 100, verfällt 5 Pkte/Jahr) |
| **Relevanz** | 25% | Keyword-Match in Titel/Abstract |
| **Journalqualität** | 20% | Impact Factor / Konferenz-Rang |
| **Open Access** | 15% | PDF öffentlich verfügbar |

**Finaler Score:** 0-100 Punkte

**Beispiel:**
```json
{
  "title": "Lean Governance in DevOps Teams",
  "score": 87,
  "breakdown": {
    "citations": 18,    // 350 Zitationen → 18 Pkt
    "recency": 19,      // 2023 → 19 Pkt
    "relevance": 23,    // Starker Keyword-Match → 23 Pkt
    "quality": 18,      // Top-Konferenz → 18 Pkt
    "open_access": 9    // PDF verfügbar → 9 Pkt
  }
}
```

---

## 🛠️ Konfiguration

### Eine Recherche-Konfiguration erstellen

Konfigurationen werden in [config/](config/) als Markdown-Dateien gespeichert. Erstelle eine über:

```bash
# Option 1: Interaktives Setup (empfohlen)
# In Claude Code Chat:
/academicagent
# Agent führt dich durch die Konfig-Erstellung

# Option 2: Manuelles Setup
/setup-agent
# Erstellt Konfig ohne Recherche zu starten

# Option 3: Beispiel-Template verwenden
cp config/.example/academic_context_cs_example.md config/my_research.md
# Manuell bearbeiten
```

### Konfig-Struktur

```markdown
# Recherche-Konfiguration

## Forschungsfrage
Wie ermöglichen Lean-Prinzipien Governance in DevOps-Teams?

## Keywords
- Primär: Lean Governance, DevOps
- Sekundär: Continuous Delivery, Agile Teams
- Verwandt: IT Governance, Process Automation

## Ziel-Disziplinen
- Informatik
- Software Engineering
- Business Management

## Suchparameter
- Jahresbereich: 2015-2024
- Sprachen: Englisch, Deutsch
- Dokumenttypen: Journal-Artikel, Konferenz-Papers

## Qualitätsfilter
- Min. Zitationen: 10
- Open Access bevorzugt: Ja
- Zielanzahl: 18 Papers
```

Siehe [config/academic_context.md](config/academic_context.md) für vollständiges Template.

---

## 🔄 Fehlerwiederherstellung & Fortsetzung

### Nach Unterbrechung fortsetzen

Falls die Recherche unterbrochen wird (Absturz, Terminal geschlossen, etc.):

```bash
# 1. State validieren
python3 scripts/validate_state.py runs/[Timestamp]/metadata/research_state.json

# Ausgabe zeigt:
# ✅ State gültig
# Zuletzt abgeschlossen: Phase 2
# Nächste: Phase 3
# Checksum: OK

# 2. Chrome neu starten
bash scripts/start_chrome_debug.sh

# 3. In VS Code fortsetzen
code .
# In Claude Code Chat:
/academicagent

# Agent setzt automatisch bei Phase 3 fort
```

### Häufige Probleme

Siehe [ERROR_RECOVERY.md](ERROR_RECOVERY.md) für detailliertes Troubleshooting:

- **CDP-Verbindungsfehler** - Chrome antwortet nicht
- **CAPTCHA-Erkennung** - Manuelle Lösung erforderlich
- **Login erforderlich** - Universitäts-Authentifizierung nötig
- **Rate Limits** - Automatischer Retry mit Backoff
- **Netzwerkfehler** - VPN/Verbindungsprobleme
- **State-Korruption** - Wiederherstellungsverfahren

### CDP-Health-Monitor

Der Orchestrator überwacht automatisch die Chrome-Gesundheit alle 5 Minuten:
- Prüft CDP-Verbindung (Port 9222)
- Überwacht Speichernutzung (warnt bei >2GB)
- Startet Chrome bei Absturz automatisch neu
- Loggt in `runs/[Timestamp]/logs/cdp_health.log`

---

## 🛡️ Sicherheit

AcademicAgent ist gegen Prompt-Injection-Angriffe gehärtet. Wichtige Maßnahmen:

- **Instruktions-Hierarchie**: Externe Inhalte werden nur als DATEN behandelt
- **Input-Sanitierung**: HTML-Bereinigung, Injection-Pattern-Erkennung
- **⭐ NEW: Safe-Bash-Wrapper**: Framework-enforced Action-Gate für alle Bash-Aufrufe
- **⭐ NEW: PDF Security Validator**: Deep Analysis mit Metadata-Stripping, Redundancy-Detection, Structure-Validation
- **Action Gate**: Validiert Tool-Aufrufe vor Ausführung (Source-Tracking: system/user/external_content)
- **Domain-Whitelist**: Nur akademische Datenbanken erlaubt (über DBIS Proxy-Mode)
- **Least Privilege**: Beschränkter Dateisystem- und Netzwerkzugriff
- **Reader/Actor-Trennung**: Read-only-Agents können keine Befehle ausführen
- **⭐ NEW: CDP Fallback Manager**: Auto-Recovery bei Chrome-Ausfällen mit Playwright Headless Fallback
- **⭐ NEW: Budget Limiter**: Token-Budget-Enforcement (warnt bei 80%, stoppt bei 100%)
- **⭐ NEW: Encryption at Rest Docs**: Empfehlungen für FileVault/LUKS Disk-Encryption

**Sicherheits-Score:** 9.5/10 (95% der Maßnahmen implementiert, +5% durch neue Features)

Siehe [SECURITY.md](SECURITY.md) für vollständige Sicherheitsdokumentation und Red-Team-Tests.

---

## 📊 Typische Recherche-Session

```
User startet Recherche (00:00)
  ↓
/academicagent
  ↓
Interaktive Konfig-Erstellung (00:00 - 00:10)
  → Forschungsfrage, Keywords, Filter
  ↓
[Checkpoint 0] Datenbanken validieren (00:15)
  → Agent zeigt: 8 kuratierte + 3 DBIS entdeckte = 11 Datenbanken
  → User genehmigt
  ↓
[Checkpoint 1] Suchstrings prüfen (00:25)
  → Agent zeigt Boolean-Queries für jede Datenbank
  → User genehmigt
  ↓
Phase 2 läuft automatisch (00:25 - 02:30)
  → Iteration 1: Top 5 Datenbanken → 23 Kandidaten
  → Iteration 2: Nächste 5 Datenbanken → 52 Kandidaten → STOPP
  ↓
[Checkpoint 3] Top 18 aus Top 27 auswählen (02:30)
  → Agent rankt alle Kandidaten nach 5D-Score
  → Zeigt Top 27 mit Scores
  → User wählt Top 18
  ↓
Phase 4 läuft automatisch (02:30 - 03:00)
  → Lädt 18 PDFs nach runs/[Timestamp]/downloads/
  ↓
Phase 5 läuft automatisch (03:00 - 03:45)
  → Extrahiert Zitate aus allen PDFs mit pdftotext
  → 40-50 relevante Zitate mit Seitenzahlen
  ↓
[Checkpoint 5] Zitatqualität prüfen (03:45)
  → Agent zeigt Beispielzitate
  → User genehmigt
  ↓
Phase 6 läuft automatisch (03:45 - 04:00)
  → Generiert bibliography.bib (BibTeX)
  → Generiert quote_library.json
  → Generiert summary.md
  ↓
[Checkpoint 6] Ausgaben bestätigen (04:00)
  → Agent zeigt Ausgabe-Pfade
  → User genehmigt
  ↓
✅ Recherche abgeschlossen! (04:00)
```

**Gesamte aktive Zeit:** ~15-20 Minuten (Checkpoints + Konfig)
**Gesamte verstrichene Zeit:** ~4 Stunden (größtenteils automatisiert)

---

## 🎨 Architektur

### Agent-Struktur

```
Orchestrator (/academicagent)
├── Phase 0: DBIS-Navigation
│   ├── Task: browser-agent
│   └── Entdeckt Datenbanken über DBIS
├── Phase 1: Suchstring-Generierung
│   ├── Task: search-agent
│   └── Erstellt Boolean-Queries
├── Phase 2: Datenbanksuche (Iterativ)
│   ├── Task: browser-agent (Schleife)
│   └── Durchsucht 5 DBs pro Iteration
├── Phase 3: 5D-Bewertung & Ranking
│   ├── Task: scoring-agent
│   └── Rankt alle Kandidaten
├── Phase 4: PDF-Download
│   ├── Task: browser-agent
│   └── Lädt ausgewählte Papers herunter
├── Phase 5: Zitat-Extraktion
│   ├── Task: extraction-agent
│   └── Extrahiert Zitate mit pdftotext
└── Phase 6: Finalisierung
    ├── Python-Scripte
    └── Generiert Ausgaben
```

### Tools & Technologien

- **Browser-Steuerung**: Chrome DevTools Protocol (CDP) via Playwright
- **PDF-Verarbeitung**: `pdftotext` (poppler-utils) + `grep`
- **State-Management**: JSON-Dateien mit SHA-256-Checksummen
- **Datenbank-Erkennung**: DBIS-Portal + WebFetch
- **Logging**: Strukturierte Logs pro Phase (JSON)
- **Sicherheit**: Domain-Validierung, Input-Sanitierung, Action-Gating

---

## 🧪 Testing & Validierung

### Chrome-CDP-Verbindung testen

```bash
# Chrome starten
bash scripts/start_chrome_debug.sh

# 3 Sekunden warten
sleep 3

# Verbindung testen
curl http://localhost:9222/json/version
# Sollte Chrome-Versionsinformationen zurückgeben
```

### Sicherheitstests ausführen

```bash
# Vollständige Red-Team-Testsuite ausführen
bash tests/red_team/run_tests.sh

# Erwartet: 6/10 automatisierte Tests bestehen (60%)
# 4/10 erfordern manuelle Verifikation
```

### Recherche-State validieren

```bash
# State-Datei-Integrität prüfen
python3 scripts/validate_state.py runs/[Timestamp]/metadata/research_state.json

# Zeigt:
# - Aktuelle Phase
# - Zuletzt abgeschlossene Phase
# - Nächste ausstehende Phase
# - Checksum-Verifizierung
# - Fortsetzungsfähigkeit
```

### Unit-Tests ausführen

```bash
# Test-Dependencies installieren
pip install -r tests/requirements-test.txt

# Unit-Tests ausführen
python3 -m pytest tests/unit/ -v

# Mit Coverage-Report
python3 -m pytest tests/unit/ -v --cov=scripts --cov-report=term
```

**Test-Coverage:**
- `test_action_gate.py` - Action-Gate-Validierungslogik (18 Tests)
- `test_validate_domain.py` - Domain-Validierung und DBIS-Proxy-Mode (16 Tests)
- `test_sanitize_html.py` - HTML-Sanitierung und Injection-Erkennung (14 Tests)
- `test_retry_strategy.py` - Retry-Handler und Backoff-Strategien (15 Tests)

### CI/CD Pipeline

Das Projekt verwendet GitHub Actions für automatisierte Tests:

```bash
# Workflow wird automatisch ausgeführt bei:
# - Push zu main/develop
# - Pull Requests zu main
```

**Pipeline-Jobs:**
1. **setup-test** - Installiert Python, Node.js, System-Dependencies
2. **unit-tests** - Führt pytest mit Coverage aus
3. **security-tests** - Red-Team-Tests (90% Pass-Rate erforderlich)
4. **script-validation** - Python/Bash-Syntax-Checks
5. **secrets-scan** - Scannt nach API-Keys und Secrets
6. **build-validation** - Prüft Dateistruktur und Agent-Configs
7. **status-report** - Aggregiert Ergebnisse

Siehe [.github/workflows/ci.yml](.github/workflows/ci.yml) für Details.

### Git-Hooks Setup

Pre-Commit-Hook für Secret-Scanning installieren:

```bash
# Hook installieren
bash scripts/setup_git_hooks.sh

# Testet automatisch bei jedem Commit:
# - API-Keys (ANTHROPIC_API_KEY, etc.)
# - Passwörter und Tokens
# - Sensitive Dateien (.env, *.pem, SSH-Keys)
# - Große Dateien (>10 MB Warnung)
```

---

## 🔧 Erweiterte Nutzung

### Von spezifischer Phase fortsetzen

```bash
# In Claude Code Chat:
/academicagent

# Bei Aufforderung Run-Verzeichnis angeben:
runs/2026-02-18_14-30-00

# Agent lädt State und fragt:
# "State zeigt Phase 2 abgeschlossen. Von Phase 3 fortsetzen?"
# → ja
```

### Benutzerdefinierte Datenbank hinzufügen

**Hinweis:** Die Datenbank-Konfiguration erfolgt derzeit über die DBIS-Integration. Für custom databases kontaktiere die Maintainer oder öffne ein GitHub Issue mit deinem Datenbank-Vorschlag.

Zukünftige Version wird `config/databases.yaml` unterstützen:

```yaml
# Coming soon in v3.2
- name: Benutzerdefinierte Datenbank
  disciplines:
    - Deine Disziplin
  url: custom-db.com
  access: Subscription
  base_score: 85
```

### Iterative Suchparameter anpassen

Bearbeite Konfig um Suchverhalten zu ändern:

```markdown
## Suchparameter
- Databases Per Iteration: 5    # Auf 3 oder 10 ändern
- Target Candidates: 50          # Zielanzahl ändern
- Max Iterations: 5              # Maximale Iterationen begrenzen
- Min Candidates Per DB: 3       # Unproduktive DBs überspringen
```

### Zitatbibliothek nach Word exportieren

**Option 1: Pandoc (manuell)**

```bash
# Konvertiere BibTeX zu Word
pandoc runs/[Timestamp]/outputs/bibliography.bib \
  -o bibliography.docx \
  --citeproc
```

**Option 2: JSON Export (coming soon)**

Zukünftige Version wird `scripts/export_quotes.py` enthalten:
```bash
# Coming in v3.2
python3 scripts/export_quotes.py \
  runs/[Timestamp]/outputs/quote_library.json \
  output.docx
```

### Utility-Scripts verwenden

#### Kosten-Tracking

Trackt Claude API-Token-Usage und Kosten:

```bash
# Kosten für eine Recherche anzeigen
python3 scripts/cost_tracker.py runs/[Timestamp]/metadata/llm_costs.jsonl

# Ausgabe:
# 📊 Kostenübersicht
# Gesamt: $2.45
# Nach Agent: browser-agent ($0.89), scoring-agent ($0.67), ...
# Nach Modell: claude-opus-4 ($1.23), claude-sonnet-4 ($1.22)
```

In Agent-Code verwenden:

```python
from scripts.cost_tracker import CostTracker

tracker = CostTracker(run_id="2026-02-18_14-30-00")
tracker.record_llm_call(
    agent_name="scoring-agent",
    model="claude-sonnet-4",
    input_tokens=5000,
    output_tokens=1500,
    phase="phase_3"
)
```

#### Performance-Metrics

Sammelt strukturierte Metriken:

```bash
# Metriken anzeigen
jq '.' runs/[Timestamp]/metadata/metrics.jsonl

# Aggregierte Zusammenfassung
python3 scripts/metrics.py summarize runs/[Timestamp]/metadata/metrics.jsonl
```

In Agent-Code verwenden:

```python
from scripts.metrics import MetricsCollector

metrics = MetricsCollector(run_id="2026-02-18_14-30-00")

# Einfache Metrik
metrics.record("papers_found", 52, unit="count", labels={"database": "IEEE"})

# Zeitmessung
with metrics.measure_time("pdf_download", labels={"file": "paper1.pdf"}):
    download_pdf()
```

#### Retry-Strategien

Exponential Backoff für fehleranfällige Operationen:

```python
from scripts.retry_strategy import retry_with_backoff, RetryHandler

# Als Decorator
@retry_with_backoff(max_retries=3, base_delay=2.0)
def flaky_api_call():
    response = requests.get("https://api.example.com")
    return response.json()

# Als Handler mit Profil
handler = RetryHandler.network_request()  # Vorkonfiguriert für Network
result = handler.execute(download_file, url="https://...")
```

#### CDP-Wrapper

Sichere Browser-Automatisierung ohne direkte CDP-Aufrufe:

```python
from scripts.cdp_wrapper import create_cdp_client

cdp = create_cdp_client()
result = cdp.navigate("https://ieeexplore.ieee.org")
html = cdp.get_html()
cdp.screenshot("/tmp/page.png")

# Datenbank-Suche
search_result = cdp.search_database(
    database_name="IEEE Xplore",
    search_string="(DevOps) AND (Governance)"
)
print(f"Gefunden: {search_result.papers_found} Papers")
```

#### Sichere Bash-Ausführung

Erzwingt Action-Gate-Validierung vor Bash-Befehlen:

```bash
# Via CLI
python3 scripts/safe_bash.py "python3 scripts/validate_state.py runs/latest/state.json"

# Dry-Run (validiert ohne Ausführung)
python3 scripts/safe_bash.py --dry-run "curl https://example.com"
# Output: ❌ BLOCKIERT: Network request ohne Action-Gate-Freigabe
```

In Agent-Code verwenden:

```python
from scripts.safe_bash import safe_bash_execute

try:
    result = safe_bash_execute(
        command="python3 scripts/process_data.py",
        source="system",
        user_intent="Datenverarbeitung für Phase 3"
    )
    print(result.stdout)
except SafeBashError as e:
    print(f"Befehl blockiert: {e}")
```

---

## 📖 Dokumentation

### 📚 Für Nutzer (Studierende & Forscher)

**[User Guide](docs/user-guide/README.md)** - Vollständiger Guide für Endnutzer

- [Erste Schritte](docs/user-guide/01-getting-started.md) - Installation & erste Recherche
- [Grundlegender Workflow](docs/user-guide/02-basic-workflow.md) - 7-Phasen-Workflow verstehen
- [Konfiguration erstellen](docs/user-guide/03-configuration.md) - Optimale Konfigs erstellen
- [Ergebnisse verstehen](docs/user-guide/04-understanding-results.md) - 5D-Bewertungssystem & Outputs
- [Probleme lösen](docs/user-guide/05-troubleshooting.md) - Troubleshooting & Fehlerbehandlung
- [Best Practices](docs/user-guide/06-best-practices.md) - Tipps für optimale Recherchen

### 🛠️ Für Entwickler & Contributors

**[Developer Guide](docs/developer-guide/README.md)** - Guide für Entwickler

- [Architektur-Übersicht](docs/developer-guide/01-architecture.md) - System-Design & Datenfluss
- [Agent-Entwicklung](docs/developer-guide/02-agent-development.md) - Neue Agents erstellen
- [Datenbanken hinzufügen](docs/developer-guide/03-adding-databases.md) - Neue DBs integrieren
- [Testing-Guide](docs/developer-guide/04-testing.md) - Unit-, Integration- & E2E-Tests
- [Security-Considerations](docs/developer-guide/05-security.md) - Sichere Entwicklung
- [Contribution-Guide](docs/developer-guide/06-contribution-guide.md) - Zum Projekt beitragen

### 📖 Technische Referenz

**[API Reference](docs/api-reference/README.md)** - Detaillierte API-Dokumentation

- [Agents](docs/api-reference/agents.md) - Agent-Definitionen & Prompts
- [Skills](docs/api-reference/skills.md) - Orchestrator-Skill Dokumentation
- [Utilities](docs/api-reference/utilities.md) - Python-Module Referenz

### 🔒 Sicherheit & Fehlerbehebung

- **[ERROR_RECOVERY.md](ERROR_RECOVERY.md)** - Umfassender Fehlerbehandlungs-Guide
- **[SECURITY.md](SECURITY.md)** - Sicherheitshärtung & Red-Team-Tests
- **[PRIVACY.md](PRIVACY.md)** - Datenschutzrichtlinie & GDPR-Compliance
- **[docs/THREAT_MODEL.md](docs/THREAT_MODEL.md)** - Bedrohungsmodell & Sicherheitsanalyse

### ⚙️ Konfiguration & Technisches

- **[docs/DBIS_USAGE.md](docs/DBIS_USAGE.md)** - Technische DBIS-Integration (für Agents)
- **[UPGRADE.md](UPGRADE.md)** - Upgrade-Anleitung zwischen Versionen
- **[CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)** - Community-Verhaltenskodex

---

## 🤝 Beitragen

Beiträge sind willkommen!

### ✅ Kürzlich Implementiert (v3.0)

Die folgenden Infrastruktur-Verbesserungen wurden bereits umgesetzt:
- ✅ CI/CD-Pipeline mit GitHub Actions (7 automatisierte Jobs)
- ✅ Unit-Tests mit pytest (50+ Tests, Coverage-Tracking)
- ✅ Kosten-Tracking für Claude API-Nutzung
- ✅ Performance-Metriken-System (strukturiertes Logging)
- ✅ Retry-Mechanismen mit Exponential Backoff
- ✅ Threat-Model und Sicherheitsanalyse
- ✅ CDP-Wrapper für sichere Browser-Automatisierung
- ✅ Git-Hooks für Secret-Scanning

### 🎯 Offene Verbesserungsbereiche

1. **Datenbank-Abdeckung**
   - Disziplin-spezifische Datenbanken hinzufügen (z.B. PsycINFO, ERIC, MedLine)
   - DBIS-Relevanz-Scoring mit ML verbessern
   - Alternative Zugangsmethoden für Paywall-Datenbanken

2. **Bewertungsalgorithmus**
   - H-Index für Journalqualität integrieren
   - Domain-spezifisches Relevanz-Scoring (trainiert auf Fachbegriffen)
   - Automatische Duplikatserkennung zwischen Datenbanken

3. **Internationalisierung**
   - Mehrsprachige Suchstrings (automatische Übersetzung)
   - Unterstützung nicht-englischer Datenbanken (z.B. CNKI für Chinesisch)
   - Lokalisierte Konfigurations-Templates

4. **Ausgabeformate**
   - Zitierstile (APA, MLA, Chicago, IEEE)
   - Export zu Zotero, Mendeley, EndNote (RIS/BibTeX-Import)
   - Annotierte Bibliographie-Generierung

5. **Benutzeroberfläche**
   - Webbasierte Konfigurations-UI (React/Next.js)
   - Echtzeit-Fortschritts-Dashboard mit Streaming-Updates
   - Visuelle Zitat-Bibliothek mit Highlighting

---

## 🐛 Bekannte Einschränkungen

1. **DBIS-Abhängigkeit**: Benötigt universitären DBIS-Zugang
2. **Manueller Login**: Einige Datenbanken benötigen menschliche Authentifizierung
3. **CAPTCHA-Handling**: Erfordert manuelle Lösung
4. **Rate Limits**: Aggressive Suche kann Rate Limits auslösen
5. **PDF-Extraktion**: Qualität hängt von PDF-Textebene ab

---

## 📄 Lizenz

MIT License - Siehe LICENSE-Datei für Details

---

## 🙏 Danksagungen

- **Anthropic** - Claude Code und Agent SDK
- **DBIS** - Database Information System (Universität Regensburg)
- **Poppler** - PDF-Textextraktions-Bibliothek
- **Playwright** - Chrome DevTools Protocol Client

---

## 🤖 ChatGPT-Konfigurationsgenerator

Du kannst ChatGPT verwenden, um deine Recherche-Konfiguration automatisch zu erstellen. Kopiere den folgenden Prompt und füge ihn in ChatGPT ein:

```text
Du bist ein akademischer Konfigurationsassistent für AcademicAgent, ein autonomes Literatur-Recherche-System.

DEINE AUFGABE:
Erstelle basierend auf den Angaben des Nutzers eine vollständige Recherche-Konfiguration im Markdown-Format.

KONFIGURATIONS-STRUKTUR:
Eine AcademicAgent-Konfiguration muss folgende Abschnitte enthalten:

# Recherche-Konfiguration

## Forschungsfrage
[Eine präzise, forschungsleitende Frage]

## Keywords
- Primär: [Haupt-Schlagwörter, die das Kernthema definieren]
- Sekundär: [Ergänzende Begriffe, die den Kontext erweitern]
- Verwandt: [Synonyme, verwandte Konzepte, alternative Begriffe]

## Ziel-Disziplinen
[Wissenschaftliche Disziplinen, z.B. Informatik, BWL, Jura, Psychologie]

## Suchparameter
- Jahresbereich: [z.B. 2015-2024]
- Sprachen: [z.B. Englisch, Deutsch]
- Dokumenttypen: [z.B. Journal-Artikel, Konferenz-Papers, Dissertationen]

## Qualitätsfilter
- Min. Zitationen: [z.B. 10]
- Open Access bevorzugt: [Ja/Nein]
- Zielanzahl: [Standard: 18 Papers]

ITERATIVE SUCHPARAMETER (Optional):
## Erweiterte Suchparameter
- Databases Per Iteration: [Standard: 5]
- Target Candidates: [Standard: 50]
- Max Iterations: [Standard: 5]
- Min Candidates Per DB: [Standard: 3]

ANWEISUNGEN:
1. Frage den Nutzer nach:
   - Thema, Forschungsfrage oder Gliederung
   - Akademischer Kontext (Studiengang, Seminar, etc.)
   - Zeitrahmen und Umfang
   - Sprachpräferenzen

2. Generiere basierend darauf:
   - Eine präzise Forschungsfrage
   - 3 Kategorien von Keywords (Primär, Sekundär, Verwandt) mit je 3-5 Begriffen
   - Passende Ziel-Disziplinen
   - Sinnvolle Suchparameter und Qualitätsfilter

3. Gib die Konfiguration als kopierbaren Markdown-Block aus

4. Erkläre kurz, wie die Konfiguration verwendet wird:
   "Speichere diese Konfiguration als `config/deine_recherche.md` im AcademicAgent-Verzeichnis und starte dann `/academicagent` in Claude Code."

BEISPIEL-INTERAKTION:
Nutzer: "Ich schreibe eine Bachelorarbeit über KI-Ethik in autonomen Fahrzeugen"
Assistent: [Generiert vollständige Konfiguration mit passenden Keywords wie "AI Ethics", "Autonomous Vehicles", "Moral Decision Making", etc.]

JETZT: Frage den Nutzer nach seinem Thema/seiner Forschungsfrage!
```

**Verwendung:**

1. Kopiere den obigen Prompt in ChatGPT
2. Beschreibe dein Forschungsthema, deine Gliederung oder Forschungsfrage
3. ChatGPT generiert eine fertige Konfigurationsdatei
4. Speichere die Ausgabe als `config/deine_recherche.md`
5. Starte `/academicagent` in Claude Code

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/jamski105/AcademicAgent/issues)
- **Diskussionen**: [GitHub Discussions](https://github.com/jamski105/AcademicAgent/discussions)
- **Dokumentation**: Siehe Docs in diesem Repository

---

## 🔄 Versionshistorie

- **v3.1** (2026-02-19) - Security-Hardening, macOS-Only, Script-Robustheit
  - ✅ Safe-Bash Wrapper, PDF Security Validator, CDP Fallback Manager
  - ✅ Budget Limiter, Encryption at Rest Docs
  - ✅ Alle Scripts mit `set -euo pipefail`
  - ✅ TTY-Checks, Cleanup-Traps, bc-Fallbacks
  - ⚠️ Linux-Support entfernt (macOS-only)
- **v3.0** (2026-02-18) - Datenbank-Strategie V3.0 mit dynamischer DBIS-Erkennung
- **v2.5** (Vorherig) - Iterative Datenbanksuche
- **v2.0** (Vorherig) - 5D-Bewertungssystem
- **v1.0** (Vorherig) - Erstes Release

Siehe [UPGRADE.md](UPGRADE.md) für Migrations-Anleitung.

---

**Viel Erfolg bei der Recherche! 📚🤖**
