# 🤖 AcademicAgent - AI-Powered Literature Research

**Version:** 1.0
**Powered by:** Claude Code + Multi-Agent Architecture
**Target:** 9/10 Quality Rating

---

## 📖 Was ist AcademicAgent?

**AcademicAgent** ist ein Multi-Agent-System für **wissenschaftliche Literaturrecherchen**, das:

- ✅ **Browser-Automation** nutzt (DBIS-Navigation, Datenbank-Suche)
- ✅ **Lokale PDF-Verarbeitung** nutzt (pdftotext, grep - 5x schneller als Browser)
- ✅ **Disziplinübergreifend** funktioniert (Informatik, Jura, Medizin, BWL, etc.)
- ✅ **Config-basiert** arbeitet (wiederverwendbar für verschiedene Projekte)


---

## 🎯 Output des Agents

Der Agent erstellt automatisch:

- **📊 Quote Library** (CSV): 40-50 Zitate mit Seitenzahlen, Kontext, Relevanz
- **📚 Annotated Bibliography** (Markdown): Zusammenfassung aller Quellen
- **📁 18 PDFs** lokal gespeichert (wiederverwendbar)
- **📋 Self-Assessment** (Rating, Zeitaufwand, Qualitätsmetriken)

---

## ⏱️ Zeitersparnis

| Methode | Zeitaufwand |
|---------|-------------|
| Manuell | 8-12 Stunden |
| ChatGPT Atlas (Browser-only) | 6-8 Stunden |
| **AcademicAgent (Hybrid)** | **3.5-4.5 Stunden** ✅ |

**Zeitersparnis bei PDF-Verarbeitung:**
- **Browser (Strg+F):** 42 Zitate × 3 Min = **126 Min**
- **pdftotext + grep:** 42 Zitate × 40 Sek = **28 Min**
- **Ersparnis: 98 Min (1.5 Stunden!)** 🚀

---

## 🏗️ Architektur

### Multi-Agent-System

```
┌─────────────────────────────────────────┐
│  Orchestrator (Hauptagent)              │
│  - Koordiniert alle Phasen              │
│  - Human-in-the-Loop Checkpoints        │
└────────┬────────────────────────────────┘
         │
         ├─→ Browser-Agent (Phase 0, 2, 4)
         │   └─ DBIS-Navigation, DB-Suche, PDF-Downloads
         │
         ├─→ Search-Agent (Phase 1)
         │   └─ Suchstring-Generierung (Boolean, DB-Syntax)
         │
         ├─→ Scoring-Agent (Phase 3)
         │   └─ 5D-Scoring, Ranking, Portfolio-Balance
         │
         └─→ Extraction-Agent (Phase 5)
             └─ PDF → Text → Zitate (pdftotext + grep)
```

### 7 Phasen

| Phase | Dauer | Zweck |
|-------|-------|-------|
| **Phase 0** | 15-20 Min | DBIS-Navigation (Datenbanken identifizieren) |
| **Phase 1** | 5-10 Min | Suchstring-Generierung (Boolean-Syntax) |
| **Phase 2** | 90-120 Min | Datenbank-Durchsuchung (Metadaten sammeln) |
| **Phase 3** | 20-30 Min | 5D-Scoring & Ranking (Top 27 → User wählt Top 18) |
| **Phase 4** | 20-30 Min | PDF-Download (18 PDFs) |
| **Phase 5** | 30-45 Min | Zitat-Extraktion (pdftotext + grep) |
| **Phase 6** | 15-20 Min | Quote Library & Bibliography erstellen |
| **Total** | **3.5-4.5h** | inkl. 5 Checkpoints |

---

## 🚀 Quick Start

### 1. Erstinstallation (einmalig)

```bash
# Clone das Repo
git clone https://github.com/dein-user/AcademicAgent.git
cd AcademicAgent

# Setup-Script ausführen (installiert Dependencies)
chmod +x setup.sh
./setup.sh

# Ausgabe:
# ✅ poppler (pdftotext) installiert
# ✅ wget installiert
# ✅ Node.js + Playwright installiert
# ✅ Chrome CDP-Helper installiert
# ✅ Ordnerstruktur erstellt: ~/AcademicAgent/
```

**Das Script installiert:**
- poppler (pdftotext)
- wget (Downloads)
- Node.js + Playwright (Browser-Automation via CDP)
- Chrome DevTools Protocol Helper
- Python 3 (für CSV-Generierung)
- Erstellt Ordnerstruktur: `~/AcademicAgent/`

---

### 2. Chrome mit Remote Debugging starten

**Wichtig:** Der Agent steuert deinen **echten Chrome-Browser** via Chrome DevTools Protocol (CDP).

```bash
# Terminal 1: Chrome mit Remote Debugging starten
bash scripts/start_chrome_debug.sh

# Ausgabe:
# ✅ Chrome started (PID: 12345)
# 🌐 Chrome is running on: http://localhost:9222
```

**Was passiert:**
- Chrome startet mit `--remote-debugging-port=9222`
- Separate Chrome-Instanz (stört dein normales Chrome nicht)
- Agent kann jetzt via CDP auf Browser zugreifen

**Tipp:** Chrome-Fenster offen lassen während der Recherche!

---

### 3. Config anpassen

```bash
# Öffne das Config-Template
code ~/AcademicAgent/config/Config_Template.md

# Passe an:
# - Forschungsfrage
# - Cluster-Begriffe (Keywords)
# - Datenbanken (disziplin-spezifisch)
# - Quality Thresholds (Min Year, Citation Threshold)

# Speichere als: Config_[DeinProjekt].md
```

**Beispiel-Configs:**
- **Informatik:** Lean Governance in DevOps
- **Jura:** DSGVO-Compliance
- **Medizin:** Patient Safety in Hospitals
- **BWL:** Digital Transformation in SMEs

---

### 4. Agent starten

```bash
# Terminal 2: VS Code im Repo öffnen
cd AcademicAgent
code .

# Claude Code Chat starten
# Cmd+Shift+P → "Claude Code: Start Chat"
```

**Im Chat:**
```
Lies agents/orchestrator.md und starte die Recherche für ~/AcademicAgent/config/Config_[DeinProjekt].md
```

**Der Agent führt dann automatisch aus:**
- Phase 0-6 (mit 5 Checkpoints)
- Steuert Browser via CDP (nutzt dein offenes Chrome-Fenster)
- Erstellt Quote Library, Bibliography, Self-Assessment
- **Zeitaufwand: 3.5-4.5 Stunden**

**Während der Recherche:**
- Chrome-Fenster bleibt offen
- Du kannst eingreifen (z.B. CAPTCHAs lösen, Login)
- Agent macht Screenshot wenn UI-Element nicht gefunden wird

---

## 📚 Unterstützte Disziplinen

### Informatik / Ingenieurwesen
- **Datenbanken:** IEEE Xplore, ACM, SpringerLink, Scopus, ScienceDirect
- **Beispiel:** DevOps, Software Engineering, AI/ML

### Jura / Rechtswissenschaften
- **Datenbanken:** Beck-Online, Juris, HeinOnline, SpringerLink
- **Beispiel:** DSGVO, Vertragsrecht, Strafrecht

### Medizin / Life Sciences
- **Datenbanken:** PubMed, Cochrane Library, Scopus, SpringerLink
- **Beispiel:** Patient Safety, Clinical Trials, Healthcare IT

### BWL / Management
- **Datenbanken:** EBSCO Business Source, JSTOR, SpringerLink, Scopus
- **Beispiel:** Digital Transformation, Organizational Change, KPIs

### Weitere Disziplinen
- **Sozialwissenschaften:** JSTOR, EBSCO, Scopus
- **Psychologie:** PsycINFO, PubMed, SpringerLink
- **Geistes­wissenschaften:** JSTOR, SpringerLink, MLA International Bibliography

---

## 🔍 Besonderheit: UI-Pattern-Library

**Problem:** Wissenschaftliche Datenbanken haben **unterschiedliche UIs** (IEEE ≠ Scopus ≠ Beck-Online).

**Lösung:** `scripts/database_patterns.json` enthält UI-Patterns für 9+ Datenbanken:
- CSS-Selektoren für Suchfelder, Filter, PDF-Links
- Text-Marker (z.B. "Advanced Search", "Erweiterte Suche")
- Datenbank-spezifische Suchsyntax (Scopus, IEEE, EBSCO, etc.)
- **Fallback-Strategien:** Generische Selektoren, Screenshot-Analyse

**Beispiel (IEEE Xplore):**
```json
{
  "search_field": {
    "selectors": ["input[name='queryText']", "#qs-search"],
    "text_markers": ["Search IEEE Xplore"]
  },
  "advanced_search": {
    "selectors": ["a[href*='advanced']"]
  },
  "search_syntax": {
    "boolean": "AND, OR, NOT",
    "field_search": "\"Document Title\":keyword OR \"Abstract\":keyword"
  }
}
```

**Ergebnis:** Browser-Agent findet UI-Elemente **automatisch**, auch bei Updates.

---

## 🌐 Browser-Automation via Chrome DevTools Protocol (CDP)

**Innovation:** Der Agent nutzt **deinen echten Chrome-Browser** statt eines isolierten Headless-Browsers.

### Wie funktioniert CDP?

1. **Chrome startet mit Remote Debugging:**
   ```bash
   bash scripts/start_chrome_debug.sh
   # Chrome läuft auf Port 9222
   ```

2. **Agent verbindet sich via CDP:**
   ```bash
   # Agent führt aus:
   node scripts/browser_cdp_helper.js navigate "https://ieeexplore.ieee.org"
   node scripts/browser_cdp_helper.js search scripts/database_patterns.json \
     "IEEE Xplore" "lean governance AND DevOps"
   ```

3. **Browser-State bleibt erhalten:**
   - Kein Neustart bei jedem Befehl
   - Login-Sessions bleiben aktiv
   - Du kannst manuell eingreifen

### Vorteile gegenüber Headless-Browser:

| Feature | Headless (Playwright allein) | CDP (Echter Browser) |
|---------|------------------------------|----------------------|
| **Login/Auth** | ❌ Komplex (Cookies, Tokens) | ✅ Du loggst manuell ein |
| **CAPTCHA** | ❌ Agent blocked | ✅ Du löst CAPTCHA |
| **Session** | ❌ Verloren nach jedem Befehl | ✅ Bleibt erhalten |
| **Debugging** | ❌ Kein visuelles Feedback | ✅ Du siehst was passiert |
| **Uni-VPN** | ❌ Muss konfiguriert werden | ✅ Läuft bereits |

### Workflow mit CDP:

```
User startet Chrome (mit VPN, eingeloggt in Uni-Account)
     ↓
Agent navigiert zu DBIS
     ↓
CAPTCHA erscheint → User löst manuell
     ↓
Agent macht weiter (Session bleibt aktiv)
     ↓
Agent durchsucht 8 Datenbanken (alle im selben Browser)
```

**Ergebnis:** Robuster, weniger Fehler, User hat Kontrolle.

---

## 📊 Qualitätsmetriken (9/10 Rating)

| Metrik | Ziel | Gewichtung |
|--------|------|------------|
| **Zeitersparnis** | ≤ 4.5h (vs. 6-8h manuell) | 20% |
| **Erfolgsrate** | ≥ 85% (18/18 Quellen) | 25% |
| **Robustheit** | ≤ 5% Fehlerrate | 20% |
| **Qualität** | ≥ 90% peer-reviewed | 20% |
| **Automatisierung** | ≥ 85% (nur 5 Checkpoints) | 15% |

**Rating-Berechnung:**
```
Rating = (Zeitersparnis × 0.2) + (Erfolgsrate × 0.25) +
         (Robustheit × 0.2) + (Qualität × 0.2) +
         (Automatisierung × 0.15)

Ziel: ≥ 9.0 / 10
```

---

## 🛠️ Technische Details

### Dependencies

| Tool | Zweck | Installation |
|------|-------|--------------|
| **Claude Code** | Agent-Framework | VS Code Extension |
| **pdftotext** | PDF → Text | `brew install poppler` |
| **wget** | Downloads | `brew install wget` |
| **Playwright** | Browser-Automation | `npm install playwright` |
| **grep** | Textsuche | (Standard Unix-Tool) |

### Ordnerstruktur

```
~/AcademicAgent/
├── agents/                     # Agent-Prompts (Markdown)
│   ├── orchestrator.md         # Hauptagent
│   ├── browser_agent.md        # Browser-Automation
│   ├── search_agent.md         # Suchstring-Generierung
│   ├── scoring_agent.md        # 5D-Scoring
│   └── extraction_agent.md     # PDF → Zitate
│
├── config/                     # User-Configs
│   ├── Config_Template.md      # Vorlage
│   └── Config_[Projekt].md     # Dein Projekt
│
├── scripts/                    # Helper-Scripts
│   └── database_patterns.json  # UI-Patterns (9+ DBs)
│
└── projects/                   # Output-Ordner
    └── [ProjectName]/
        ├── pdfs/               # 18 PDFs
        ├── txt/                # Konvertierte TXT-Dateien
        ├── metadata/           # JSON (Zwischenergebnisse)
        ├── outputs/            # Quote Library, Bibliography
        └── logs/               # Phase-Logs
```

---

## 🔄 Error Recovery & Resume

**NEU:** Robustes Error Handling mit automatischer Recovery!

### Problem: Unterbrochene Recherche

Recherchen dauern 3-4 Stunden. Was passiert bei:
- Chrome-Absturz
- CAPTCHA nicht gelöst
- Netzwerk-Timeout
- User bricht ab

**Lösung:** State Management + Error Recovery

---

### Features

#### 1. **Automatische State-Speicherung**

Nach jeder Phase wird der Fortschritt gespeichert:

```bash
# State wird automatisch gespeichert in:
~/AcademicAgent/projects/[ProjectName]/metadata/research_state.json

{
  "current_phase": 2,
  "phases": {
    "phase_0": {"status": "completed", "data": {"databases_count": 8}},
    "phase_1": {"status": "completed", "data": {"search_strings_count": 30}},
    "phase_2": {"status": "in_progress", "data": {"progress": "15/30"}}
  }
}
```

---

#### 2. **Automatische Error Recovery**

Bei Fehlern wird automatisch versucht zu recovern:

| Error Type | Recovery Strategie |
|------------|-------------------|
| **CDP Connection** | Chrome neu starten → Retry |
| **CAPTCHA** | User löst manuell → Retry |
| **Login Required** | User loggt ein → Retry |
| **Rate Limit** | Automatisch warten (60s) → Retry |
| **Network Error** | User prüft VPN → Retry |

**Beispiel (CAPTCHA):**
```
🚨 CAPTCHA erkannt!
Screenshot: logs/captcha.png

🔧 Lösung:
  1. Wechsle zum Chrome-Fenster
  2. Löse das CAPTCHA manuell
  3. Drücke ENTER zum Fortfahren

[User löst CAPTCHA]

✅ CAPTCHA gelöst! Fortsetzen...
```

---

#### 3. **Resume nach Unterbrechung**

Unterbrochene Recherche kann fortgesetzt werden:

```bash
# Prüfe ob Resume möglich
bash scripts/resume_research.sh DevOps

# Output:
# 🔄 Resume möglich!
# Last completed: Phase 2. Resume from Phase 3?
#
# 📊 State Summary:
#   Phase 0: completed
#   Phase 1: completed
#   Phase 2: completed
#   Phase 3: pending
#
# Ready to resume!
```

**Im Claude Code Chat:**
```
Lies agents/orchestrator.md und setze die Recherche fort
für ~/AcademicAgent/config/Config_DevOps.md

WICHTIG: Starte bei Phase 3
```

---

### Error Handling Beispiele

#### **Szenario 1: Chrome-Absturz während Phase 2**

```
Agent: Phase 2 läuft... (15/30 Strings verarbeitet)
[Chrome stürzt ab]

Agent: ❌ CDP Connection Error
       Chrome ist nicht erreichbar.

       🔧 Möchtest du Chrome neu starten? (y/n)

User: y

Agent: [Startet Chrome]
       ✅ Chrome gestartet! Retry...
       [Fährt fort bei String 16/30]
```

**State wurde gespeichert** → Keine verlorenen Daten!

---

#### **Szenario 2: User bricht ab, setzt später fort**

```
15:00 Uhr - User startet Recherche
16:30 Uhr - Phase 2 läuft, User bricht ab (Cmd+C)
          - State: Phase 0-1 completed, Phase 2 in_progress

18:00 Uhr - User will fortsetzen
          $ bash scripts/resume_research.sh DevOps
          → "Resume from Phase 2?"
          → Agent überspringt Phase 0-1, startet direkt Phase 2
```

---

#### **Szenario 3: CAPTCHA bei String 23/30**

```
Agent: Processing String 23/30...
       🚨 CAPTCHA erkannt!
       [Screenshot: logs/captcha_23.png]

       Bitte löse CAPTCHA und drücke ENTER.

User: [Löst CAPTCHA, drückt ENTER]

Agent: ✅ Fortsetzen...
       Processing String 23/30 (Retry)...
       ✅ 15 results
       Processing String 24/30...
```

**Kein Datenverlust, nahtlose Fortsetzung!**

---

### Verwendung

#### **Normale Recherche (mit Auto-Recovery):**
```bash
# Agent startet automatisch mit Error Recovery
# Keine Änderungen nötig - funktioniert transparent
```

#### **Manuelle Resume:**
```bash
# Prüfe Resume-Status
bash scripts/resume_research.sh DevOps

# Wenn Resume möglich:
# → VS Code öffnen
# → Claude Code Chat: "Setze Recherche fort bei Phase X"
```

#### **State manuell prüfen:**
```bash
# Lade State
python3 scripts/state_manager.py load projects/DevOps

# Zeigt kompletten State als JSON
```

---

## 🔐 Permissions & Sicherheit

### Minimale Rechte

Der Agent arbeitet **nur** in `~/AcademicAgent/`:
- ✅ Lesen: `config/*.md`, `agents/*.md`, `scripts/*.json`
- ✅ Schreiben: `projects/[ProjectName]/*`
- ❌ Kein Zugriff auf System-Ordner (`/etc`, `/usr`, etc.)

### Erlaubte Bash-Befehle

- `pdftotext` (PDF → Text)
- `grep` (Textsuche)
- `wget` / `curl` (Downloads)
- `open` (Browser öffnen)

### Compliance

- ✅ **DBIS:** Lizenzierte Datenbanken (Uni-Zugang)
- ✅ **Open Access:** DOAJ, arXiv, ResearchGate
- ✅ **TIB-Portal:** Document Delivery (legal)
- ❌ **Verboten:** Sci-Hub, LibGen (Copyright-Verletzung)

---

## 📝 Workflow-Beispiel

**User startet:**
```
Lies agents/orchestrator.md und starte die Recherche für ~/AcademicAgent/config/Config_DevOps.md
```

**Orchestrator antwortet:**
```
✅ Config eingelesen: Config_DevOps.md
✅ Projekt: Lean Governance in DevOps
✅ Forschungsfrage: Wie wird Lean Governance in DevOps-Teams umgesetzt?
✅ Ziel: 18 Quellen, 40-50 Zitate
✅ Primäre Datenbanken: IEEE, SpringerLink, Scopus, ACM, ScienceDirect

📂 Erstelle Ordnerstruktur: ~/AcademicAgent/projects/DevOps/

🚀 Starte Phase 0: Datenbank-Identifikation...
[Spawnt Browser-Agent]
```

**Nach Phase 0:**
```
✅ Phase 0 abgeschlossen!

Gefundene Datenbanken (8):
1. IEEE Xplore (Zugang: ✅)
2. SpringerLink (Zugang: ✅)
...

📋 Checkpoint 0: Möchtest du mit diesen 8 Datenbanken fortfahren? (Ja/Nein)
```

**User:** `Ja`

**... (Phasen 1-6) ...**

**Nach Phase 6:**
```
✅ Recherche abgeschlossen! 🎉

Finale Outputs:
- 📊 Quote Library: ~/AcademicAgent/projects/DevOps/outputs/Quote_Library.csv (42 Zitate)
- 📚 Annotated Bibliography: ~/AcademicAgent/projects/DevOps/outputs/Annotated_Bibliography.md
- 📋 Self-Assessment: Rating 9.4/10, Zeitaufwand: 3.85h

📂 Ordner öffnen:
open ~/AcademicAgent/projects/DevOps/outputs/
```

---

## 🆘 Troubleshooting

### Problem: CAPTCHA beim Browser-Agent

**Lösung:**
- Agent pausiert automatisch 30 Sekunden
- Retry (max. 1x)
- Falls wieder CAPTCHA: User-Warnung → Manuell lösen → Fortsetzen

---

### Problem: DBIS-Session abgelaufen

**Fehlermeldung:** `"DBIS-Session abgelaufen, bitte neu einloggen"`

**Lösung:**
1. DBIS-Seite manuell öffnen: https://dbis.de
2. Mit Uni-Account einloggen
3. Agent neu starten (State wird aus `metadata/*.json` wiederhergestellt)

---

### Problem: PDF nicht verfügbar (Paywall)

**Agent versucht automatisch:**
1. Open Access (DOAJ, arXiv)
2. TIB-Portal (Document Delivery)
3. User fragen: "Quelle ersetzen durch nächste im Ranking?"

---

### Problem: UI-Element nicht gefunden

**Agent versucht:**
1. Datenbank-spezifische Selektoren
2. Generische Selektoren
3. Screenshot → Claude analysiert UI
4. Falls alles fehlschlägt: User fragen

---

### Problem: Chrome CDP nicht erreichbar

**Fehlermeldung:** `❌ CDP Connection Error`

**Lösung:**
```bash
# 1. Prüfe ob Chrome läuft
curl http://localhost:9222/json/version

# 2. Wenn nicht: Starte Chrome
bash scripts/start_chrome_debug.sh

# 3. Warte 5 Sekunden
sleep 5

# 4. Teste erneut
curl http://localhost:9222/json/version
# Sollte Chrome-Version zeigen

# 5. Agent wird automatisch Retry versuchen
```

---

### Problem: Recherche wurde unterbrochen

**Situation:** Agent abgestürzt, User hat abgebrochen, Chrome geschlossen

**Lösung:**
```bash
# 1. Prüfe State
bash scripts/resume_research.sh [ProjectName]

# Output zeigt letzte abgeschlossene Phase

# 2. Chrome starten
bash scripts/start_chrome_debug.sh

# 3. VS Code öffnen + Claude Code Chat

# 4. Im Chat:
Lies agents/orchestrator.md und setze die Recherche fort
für ~/AcademicAgent/config/Config_[ProjectName].md

WICHTIG: Starte bei Phase X  # X = resume_phase aus Step 1
```

**Agent überspringt automatisch abgeschlossene Phasen!**

---

### Problem: State-File beschädigt

**Fehlermeldung:** `Error reading state`

**Lösung:**
```bash
# 1. Sichere beschädigten State
cp projects/[ProjectName]/metadata/research_state.json \
   projects/[ProjectName]/metadata/research_state.json.backup

# 2. Lösche State (Agent startet von vorn)
rm projects/[ProjectName]/metadata/research_state.json

# 3. Oder: Manuell reparieren
# Edit research_state.json und entferne fehlerhafte Zeilen

# 4. Agent neu starten
```

---

## 📄 Dokumentation

- **[TECHNICAL_GUIDE.md](TECHNICAL_GUIDE.md):** Technische Architektur, Multi-Agent-System
- **[Config_Template.md](config/Config_Template.md):** Config-Vorlage (disziplinübergreifend)
- **[agents/orchestrator.md](agents/orchestrator.md):** Hauptagent (7 Phasen)
- **[agents/browser_agent.md](agents/browser_agent.md):** Browser-Automation mit UI-Pattern-Library
- **[scripts/database_patterns.json](scripts/database_patterns.json):** UI-Patterns (9+ Datenbanken)

---

## 🚀 Roadmap

### v2.0 (Completed) ✅
- [x] Chrome DevTools Protocol (CDP) Integration
- [x] Error Recovery System
- [x] State Management & Resume
- [x] Automatic Retry für CAPTCHA, Login, Rate-Limit
- [x] Python Scripts für Quote Library + Bibliography

### v2.1 (geplant)
- [ ] Snowballing (Referenzen durchsuchen)
- [ ] Excel-Export (statt CSV)
- [ ] PDF-Export für Bibliography
- [ ] Docker-Container (komplette Isolation)

### v2.2 (geplant)
- [ ] Unterstützung für 20+ Datenbanken
- [ ] Web-UI (statt CLI)
- [ ] API-Endpunkt für Integration

---

## 📜 Lizenz

MIT License

---

## 🙏 Credits

- **Claude Code** by Anthropic
- **Playwright** for Browser-Automation
- **poppler** (pdftotext) by The Poppler Developers

---

## 📧 Support

**Issues:** https://github.com/dein-user/AcademicAgent/issues
**Discussions:** https://github.com/dein-user/AcademicAgent/discussions

---

**Happy Researching! 📚🤖**
