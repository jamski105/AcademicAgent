# Academic Agent v2.2 - Installation Guide

**Aktualisiert:** 2026-02-27 (v2.2 - DBIS Search Integration)
**Python Version:** 3.11+
**Platform:** macOS, Linux, Windows

**New in v2.2:** No additional dependencies required! DBIS search uses existing Chrome MCP.

---

## 🚀 Quick Start (Automatisch via setup.sh)

### Ein Befehl Installation

```bash
git clone <repo-url>
cd AcademicAgent
./setup.sh
```

**Das macht setup.sh:**
1. ✅ Python 3.11+ Check
2. ✅ Dependencies installieren system-weit (requirements-v2.txt)
3. ✅ Chrome MCP Server installieren (npm)
4. ✅ NLTK Data downloaden
5. ✅ Cache Directories erstellen
6. ✅ .claude/settings.json konfigurieren

**Dauer:** ~5-8 Minuten (je nach Internet)

**Hinweis:** Dependencies werden system-weit mit `pip3 install --user` installiert.
Kein virtuelles Environment nötig!

---

## 📦 Was wird installiert?

### Python Dependencies

```bash
# Core
anthropic>=0.40.0        # ← OPTIONAL (nur für lokale Tests)
httpx, aiohttp, requests

# Database
sqlalchemy>=2.0.0
pydantic>=2.10.0

# PDF Processing
pymupdf>=1.24.0          # PDF Text Extraction

# CLI UI
rich>=13.9.0
click>=8.1.0

# Utils
tenacity>=9.0.0          # Retry Logic
cachetools>=5.3.0
pyyaml>=6.0.1

# Testing
pytest>=8.3.0
pytest-asyncio>=0.24.0
```

**Wichtig:** Playwright ist jetzt **OPTIONAL** (DEPRECATED → Chrome MCP)

### Chrome MCP Server (NEU!)

```bash
npm install -g @eddym06/custom-chrome-mcp
```

**Wofür?**
- Browser Automation für DBIS PDF-Downloads
- Ersetzt Playwright Python-Code
- Nutzt natives Chrome/Chromium

---

## ⚙️ Konfiguration

### 1. Chrome MCP (.claude/settings.json)

**Wird automatisch von setup.sh erstellt:**

```json
{
  "mcpServers": {
    "chrome": {
      "command": "npx",
      "args": ["-y", "@eddym06/custom-chrome-mcp@latest"],
      "env": {
        "CHROME_PATH": "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
      }
    }
  }
}
```

**Chrome Path automatisch erkannt für:**
- macOS: `/Applications/Google Chrome.app`
- Linux: `/usr/bin/google-chrome` oder `/usr/bin/chromium`
- Windows: `C:\Program Files\Google\Chrome\Application\chrome.exe`

### 2. Research Modes (config/research_modes.yaml)

**Bereits im Repo, keine Änderung nötig:**

```yaml
modes:
  quick:
    max_papers: 15
    estimated_duration_min: 20

  standard:  # Empfohlen
    max_papers: 25
    estimated_duration_min: 35

  deep:
    max_papers: 40
    estimated_duration_min: 60
```

### 3. Academic Context (Optional)

**Optional:** `config/academic_context.md` anpassen:

```markdown
## Disziplin
Computer Science / Software Engineering

## Keywords
- DevOps
- Continuous Integration

## Bevorzugte Datenbanken
- IEEE Xplore
- ACM Digital Library
```

### 4. DBIS Credentials (Optional für 85-90% PDF Rate)

```bash
export TIB_USERNAME="your_tib_username"
export TIB_PASSWORD="your_tib_password"
```

**Falls kein TIB Account:**
- PDF-Download Rate: ~50% (Unpaywall + CORE)
- Mit TIB: ~85-90% (+ DBIS Browser)

---

## ✅ Installation Verifizieren

### 1. Python Environment Test

```bash
python3 --version  # ≥ 3.11
python3 -m pip list | grep httpx
python3 -c "import httpx, pydantic, pymupdf, rich; print('✓ Core packages OK')"
```

### 2. Chrome MCP Test

```bash
npx @eddym06/custom-chrome-mcp --version
```

### 3. Unit Tests (Optional)

```bash
pytest tests/unit/ -v
```

### 4. Erster Research Test

```bash
/research "Test Query"
```

---

## 🛠️ Manuelle Installation (Falls setup.sh nicht läuft)

### Schritt 1: Upgrade pip

```bash
python3 -m pip install --upgrade pip setuptools wheel --user
```

### Schritt 2: Python Dependencies (System-weit)

```bash
python3 -m pip install -r requirements-v2.txt --user
```

**Hinweis:** Mit `--user` werden Packages im User-Verzeichnis installiert:
- macOS: `~/Library/Python/3.x/lib/python/site-packages`
- Linux: `~/.local/lib/python3.x/site-packages`
- Windows: `%APPDATA%\Python\Python3x\site-packages`

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

# Chrome MCP installieren
npm install -g @eddym06/custom-chrome-mcp
```

### Schritt 4: .claude/settings.json erstellen

```bash
cat > .claude/settings.json <<EOF
{
  "mcpServers": {
    "chrome": {
      "command": "npx",
      "args": ["-y", "@eddym06/custom-chrome-mcp@latest"],
      "env": {
        "CHROME_PATH": "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
      }
    }
  }
}
EOF
```

### Schritt 5: Cache Directories

```bash
mkdir -p ~/.cache/academic_agent/pdfs
mkdir -p ~/.cache/academic_agent/http_cache
```

---

## 🚨 Troubleshooting

### Problem: setup.sh Permission Denied

```bash
chmod +x setup.sh
./setup.sh
```

### Problem: Python Version zu alt

```bash
# macOS: Homebrew
brew install python@3.11

# Linux: pyenv
pyenv install 3.11.0
pyenv global 3.11.0
```

### Problem: Chrome MCP startet nicht

```bash
# Check Node.js Version
node --version  # ≥ 18.0.0

# Reinstall
npm uninstall -g @eddym06/custom-chrome-mcp
npm install -g @eddym06/custom-chrome-mcp@latest
```

### Problem: Chrome nicht gefunden

```bash
# Chrome installieren
# macOS:
brew install --cask google-chrome

# Linux:
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo dpkg -i google-chrome-stable_current_amd64.deb

# Oder Chromium:
sudo apt-get install chromium-browser
```

### Problem: DBIS Login funktioniert nicht

**Manueller Login:**
1. dbis_browser Agent öffnet Browser (sichtbar!)
2. User sieht Shibboleth Login-Page
3. Manuell einloggen (Username/Password)
4. Agent erkennt erfolgreichen Login
5. Agent lädt PDF herunter

---

## 🎯 Nächste Schritte

Nach erfolgreicher Installation:

1. **First Run:**
```bash
/research "Your first research question"
```

2. **Mode Selection:**
- Start mit **Standard Mode** (empfohlen)

3. **DBIS Browser:**
- Browser öffnet sich automatisch bei PDF-Download
- TIB Login manuell durchführen
- Agent wartet auf Completion

4. **Results:**
- Gespeichert in `~/.cache/academic_agent/sessions/`
- JSON Export verfügbar

---

## 📚 Siehe auch

- [WORKFLOW.md](./WORKFLOW.md) - User Journey & Development
- [ARCHITECTURE_v2.md](./docs/ARCHITECTURE_v2.md) - System Design
- [MODULE_SPECS_v2.md](./docs/MODULE_SPECS_v2.md) - Module Details
