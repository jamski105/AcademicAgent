# Academic Agent v2.3 - Setup Guide

**Vollständige Schritt-für-Schritt Anleitung für neue Nutzer**

**Version:** v2.3 (DBIS Auto-Discovery)
**Datum:** 2026-02-27
**Geschätzte Setup-Zeit:** 10-15 Minuten

---

## 📋 Übersicht

Nach diesem Setup kannst du:
- ✅ `/research` Command in Claude Code ausführen
- ✅ Cross-disciplinary academic research (92%+ coverage)
- ✅ DBIS Auto-Discovery (automatisch 10-30 Datenbanken pro Fachgebiet)
- ✅ PDFs herunterladen (85-90% success rate)
- ✅ Quotes extrahieren mit AI
- ✅ Exportieren in 5 Formaten (JSON, CSV, Markdown, BibTeX)

---

## ⚙️ Systemanforderungen

### Minimale Requirements:
- **Python:** 3.11 oder höher
- **Node.js:** 18.0 oder höher (für Chrome MCP)
- **Chrome/Chromium:** Installiert
- **Git:** Für Repository Clone
- **Speicher:** ~500 MB für Dependencies
- **Internet:** Für API-Zugriffe und DBIS

### Empfohlene Requirements:
- **RAM:** 4 GB+ (für Browser Automation)
- **CPU:** Multi-core (für parallele Searches)
- **OS:** macOS, Linux, oder Windows (WSL empfohlen)

---

## 🚀 Quick Start (Automatisch)

### Option A: Ein-Befehl Installation (Empfohlen)

```bash
# 1. Repository klonen
git clone <repo-url>
cd AcademicAgent

# 2. Setup ausführen (macht ALLES automatisch!)
./setup.sh

# 3. Virtual Environment aktivieren
source venv/bin/activate

# 4. Fertig! Test mit:
/research "DevOps Governance"
```

**Das macht `setup.sh` für dich:**
- ✅ Python 3.11+ Check
- ✅ Virtual Environment erstellen
- ✅ Python Dependencies installieren (~5 min)
- ✅ Node.js Check
- ✅ Chrome MCP Server installieren
- ✅ Chrome/Chromium Path erkennen
- ✅ `.claude/settings.json` automatisch erstellen
- ✅ NLTK Data downloaden
- ✅ Cache Directories erstellen
- ✅ Optional: Unit Tests ausführen

**Dauer:** ~5-8 Minuten (abhängig von Internet)

---

## 🔧 Manuelle Installation (Falls setup.sh nicht funktioniert)

### Schritt 1: Python Virtual Environment

```bash
# Virtual Environment erstellen
python3 -m venv venv

# Aktivieren
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Pip upgraden
pip install --upgrade pip setuptools wheel
```

### Schritt 2: Python Dependencies installieren

```bash
pip install -r requirements-v2.txt
```

**Wichtige Dependencies:**
- `httpx`, `aiohttp`, `requests` - HTTP Clients
- `sqlalchemy`, `pydantic` - Database & Data Validation
- `pymupdf` - PDF Text Extraction
- `rich`, `click` - CLI UI
- `pyyaml` - Config Loading
- `tenacity` - Retry Logic
- `pytest` - Testing

**Installation dauert:** ~3-5 Minuten

### Schritt 3: Node.js & Chrome MCP

```bash
# Node.js installieren (falls nicht vorhanden)

# macOS:
brew install node

# Linux:
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# Windows:
# Download von https://nodejs.org

# Chrome MCP Server installieren
npm install -g @eddym06/custom-chrome-mcp@latest

# Version checken
node --version  # Should be 18+
npx @eddym06/custom-chrome-mcp --version
```

### Schritt 4: Chrome/Chromium installieren

```bash
# macOS:
brew install --cask google-chrome

# Linux:
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo dpkg -i google-chrome-stable_current_amd64.deb
# ODER Chromium:
sudo apt-get install chromium-browser

# Windows:
# Download from https://www.google.com/chrome/
```

### Schritt 5: .claude/settings.json erstellen

**Automatisch (empfohlen):**
```bash
# setup.sh erstellt das automatisch
./setup.sh
```

**Manuell:**
```bash
# Chrome Path finden
# macOS:
CHROME_PATH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
# Linux:
CHROME_PATH="/usr/bin/google-chrome"  # oder /usr/bin/chromium
# Windows:
CHROME_PATH="C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"

# .claude/settings.json erstellen
mkdir -p .claude
cat > .claude/settings.json <<EOF
{
  "mcpServers": {
    "chrome": {
      "command": "npx",
      "args": ["-y", "@eddym06/custom-chrome-mcp@latest"],
      "env": {
        "CHROME_PATH": "$CHROME_PATH"
      }
    }
  }
}
EOF

echo "✅ .claude/settings.json created"
```

### Schritt 6: Cache Directories erstellen

```bash
mkdir -p ~/.cache/academic_agent/pdfs
mkdir -p ~/.cache/academic_agent/http_cache
mkdir -p ~/.cache/academic_agent/sessions

echo "✅ Cache directories created"
```

---

## ✅ Installation überprüfen

### Check 1: Python Dependencies

```bash
python --version  # ≥ 3.11
pip list | grep -E "pyyaml|sqlalchemy|pymupdf|rich"
```

**Erwartete Output:**
```
Python 3.11.x (oder höher)
PyYAML        6.0.1
SQLAlchemy    2.0.x
PyMuPDF       1.24.x
rich          13.9.x
```

### Check 2: Chrome MCP

```bash
# Version check
npx @eddym06/custom-chrome-mcp --version

# Connection test
timeout 5 npx -y @eddym06/custom-chrome-mcp@latest 2>&1 | head -5
```

### Check 3: Config Files

```bash
ls -la config/*.yaml
# Should show:
# api_config.yaml
# dbis_disciplines.yaml (v2.3 - Discovery!)
# dbis_selectors.yaml (v2.3 - NEW!)
# research_modes.yaml
```

### Check 4: Unit Tests (Optional)

```bash
pytest tests/unit/test_discipline_classifier.py -v
pytest tests/unit/test_dbis_discovery.py -v

# Expected: All tests pass
```

---

## 🎯 Erster Test-Run

### Test 1: Orchestrator Test

```bash
# Test DBIS Discovery Config Generation
python -m src.search.dbis_search_orchestrator --test

# Expected Output:
# ✅ Test Config Generated
# Mode: discovery
# Discovery Enabled: True
```

### Test 2: Research Command (FULL E2E)

```bash
# In Claude Code:
/research "DevOps Governance"
```

**Was passiert:**
1. Mode Selection: Standard Mode (25 papers, ~50 min)
2. Citation Style: APA 7
3. Phase 1: Context Setup ✓
4. Phase 2: Query Generation (query_generator agent)
5. Phase 2a: Discipline Classification → "Informatik"
6. Phase 3: Hybrid Search
   - Track 1: API Search (CrossRef, OpenAlex, S2) ~3 sec
   - Track 2: DBIS Search (~60 sec)
     - **Discovery Mode:** Scraped 20+ databases
     - **Selected TOP 5:** IEEE Xplore, ACM, Springer, etc.
7. Phase 4: Ranking (5D + LLM)
8. Phase 5: PDF Download (85-90%)
9. Phase 6: Quote Extraction
10. Phase 7: Export (JSON, CSV, Markdown, BibTeX)

**Results saved to:**
```
runs/2026-02-27_16-30-00/
├── pdfs/                  # Downloaded PDFs
├── results.json           # Complete results
├── quotes.csv             # Quotes with citations + SOURCE
├── summary.md             # Human-readable summary
├── bibliography.bib       # BibTeX
└── session.db             # SQLite database
```

---

## 🐛 Troubleshooting

### Problem: Python Version zu alt

```bash
python --version  # < 3.11

# Lösung macOS:
brew install python@3.11
# Lösung Linux:
pyenv install 3.11.0
pyenv global 3.11.0
```

### Problem: Chrome MCP startet nicht

```bash
# Check Node.js Version
node --version  # Muss ≥ 18.0.0 sein

# Reinstall Chrome MCP
npm uninstall -g @eddym06/custom-chrome-mcp
npm install -g @eddym06/custom-chrome-mcp@latest

# Test
npx -y @eddym06/custom-chrome-mcp@latest
```

### Problem: Chrome nicht gefunden

```bash
# Check .claude/settings.json
cat .claude/settings.json | grep CHROME_PATH

# Manuell Chrome Path setzen
# Bearbeite .claude/settings.json und setze korrekten Pfad
```

### Problem: "No module named 'yaml'"

```bash
# Virtual Environment aktiviert?
which python  # Sollte venv/bin/python zeigen

# Falls nicht aktiviert:
source venv/bin/activate

# PyYAML installieren
pip install pyyaml
```

### Problem: DBIS Discovery findet keine Datenbanken

```bash
# Check DBIS Selectors (manuell im Browser testen)
open "https://dbis.ur.de/dbis/dbliste.php?bib_id=ubtib&lett=f&sGeb=9.1"

# In Browser Console testen:
document.querySelectorAll("tr[id^='db_']")  # Sollte DB-Einträge finden

# Falls nicht: Selectors anpassen in:
# config/dbis_selectors.yaml
```

### Problem: Timeouts bei DBIS Search

```bash
# Timeout erhöhen in config/dbis_disciplines.yaml:
discovery_defaults:
  timeout_seconds: 60  # Erhöhe auf 60s
```

---

## 🔐 Optional: TIB Credentials (für höhere PDF-Rate)

### Ohne TIB Account:
- PDF Download Rate: ~50% (Unpaywall + CORE)
- DBIS Search: Nur frei zugängliche Datenbanken

### Mit TIB Account:
- PDF Download Rate: **85-90%** (+ DBIS Browser mit TIB-Lizenz)
- DBIS Search: Alle lizenzierten Datenbanken

### Setup:

```bash
# .bashrc / .zshrc editieren:
export TIB_USERNAME="your_username"
export TIB_PASSWORD="your_password"

# Source reload:
source ~/.bashrc  # oder ~/.zshrc

# Verify:
echo $TIB_USERNAME
```

**Wichtig:** Login erfolgt **manuell** im Browser (Agent öffnet Browser, du loggst ein)

---

## 📚 Nächste Schritte

### 1. Erste Research durchführen

```bash
/research "Your research question"
```

**Empfohlene Test-Queries:**
- **Informatik:** "Machine Learning Optimization"
- **Medizin:** "COVID-19 Treatment Protocols"
- **Jura:** "Mietrecht Kündigungsfristen" (testet Discovery!)
- **Klassik:** "Lateinische Metrik Augusteisch"

### 2. Research Modes testen

- **Quick:** 15 papers, ~20 min (nur APIs, kein DBIS)
- **Standard:** 25 papers, ~50 min (APIs + DBIS Discovery) ⭐ Empfohlen
- **Deep:** 40 papers, ~90 min (5+ Datenbanken)

### 3. Citation Styles testen

Verfügbar:
- APA 7 (Psychology, Education)
- IEEE (Engineering, CS)
- Harvard (Business, Economics)
- MLA 9 (Literature, Arts)
- Chicago (History, Social Sciences)

### 4. Output analysieren

```bash
# Results anschauen
cd runs/LATEST/

# JSON
cat results.json | jq '.statistics'

# CSV mit Excel öffnen
open quotes.csv

# Markdown lesen
cat summary.md
```

---

## 🎓 Weitere Dokumentation

- **[README.md](./README.md)** - Features & Quick Start
- **[WORKFLOW.md](./WORKFLOW.md)** - User Journey & Development
- **[INSTALLATION.md](./INSTALLATION.md)** - Detaillierte Install-Infos
- **[ARCHITECTURE_v2.md](./docs/ARCHITECTURE_v2.md)** - System Design
- **[MODULE_SPECS_v2.md](./docs/MODULE_SPECS_v2.md)** - Module Details
- **[DBIS_INTEGRATION.md](./DBIS_INTEGRATION.md)** - DBIS Details
- **[CHANGELOG.md](./CHANGELOG.md)** - Version History

---

## 🆘 Support

**Problem?** Check:
1. [Troubleshooting](#-troubleshooting) section oben
2. [GitHub Issues](https://github.com/yourusername/AcademicAgent/issues)
3. Test logs: `runs/LATEST/session_log.txt`

**Feature Request?** Open ein GitHub Issue!

---

## ✅ Setup Complete Checklist

- [ ] Python 3.11+ installiert
- [ ] Node.js 18+ installiert
- [ ] Chrome/Chromium installiert
- [ ] Virtual Environment erstellt
- [ ] Dependencies installiert (`pip install -r requirements-v2.txt`)
- [ ] Chrome MCP installiert (`npm install -g @eddym06/custom-chrome-mcp`)
- [ ] `.claude/settings.json` erstellt
- [ ] Cache Directories erstellt
- [ ] Unit Tests laufen (`pytest tests/unit/ -v`)
- [ ] Orchestrator Test erfolgreich (`python -m src.search.dbis_search_orchestrator --test`)
- [ ] Erster `/research` Test erfolgreich

**Alle Checkboxen ✅?** → System ist einsatzbereit! 🚀

---

**Academic Agent v2.3 - Powered by AI, built for researchers** 🎓
