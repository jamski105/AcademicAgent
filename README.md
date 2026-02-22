# 🎓 AcademicAgent

**Version:** 4.0
**Autonomes akademisches Literatur-Recherche-System**

> ⚠️ **WICHTIG: Dieses System ist ausschließlich für macOS entwickelt**
>
> - Benötigt macOS-spezifische Pfade (`/Applications/Google Chrome.app`)
> - Nutzt macOS-spezifische Befehle (`stat -f`, `lsof`, `open`)
> - Homebrew als Paketmanager erforderlich
> - **Linux/Windows werden NICHT unterstützt**

> 🤖 **Gebaut für Claude Code**
>
> AcademicAgent ist **ausschließlich für Claude Code** entwickelt und optimiert.
> Die Verwendung mit anderen KI-Systemen wird nicht unterstützt.

---

## Was ist AcademicAgent?

**AcademicAgent** automatisiert den kompletten Literaturrecherche-Prozess für deine akademische Arbeit. Gib deine Forschungsfrage und Keywords ein – der Agent findet, bewertet und liefert dir **18 hochwertige wissenschaftliche Publikationen mit zitierfähigen Zitaten** in 3,5-4 Stunden.

**Das Ergebnis:** Eine fertige BibTeX-Bibliographie, eine strukturierte Zitatbibliothek und 18 heruntergeladene PDFs – bereit für deine Thesis, Hausarbeit oder Paper.

---

## 🌟 Hauptfunktionen

- ✅ **Vollständig autonom**: 7-Phasen-Workflow mit nur 5 menschlichen Checkpoints
- 🎯 **Intelligente Datenbankauswahl**: 30+ kuratierte Top-Datenbanken + dynamische DBIS-Erkennung
- ⭐ **5D-Bewertungssystem**: Bewertet Papers nach Zitationen, Aktualität, Relevanz, Journalqualität & Open Access
- 🔄 **Iterative Suche**: Durchsucht jeweils 5 Datenbanken bis Ziel erreicht (40% weniger DBs, 42% schneller)
- 📄 **Schnelle PDF-Extraktion**: Natives `pdftotext` (5x schneller als Browser-Extraktion)
- 📚 **Zitatbibliothek**: Strukturiertes JSON mit Seitenzahlen und Relevanzscores
- 💾 **Fehlerwiederherstellung**: Automatisches State-Management – setze Recherchen nach Absturz fort
- 🛡️ **Produktionsreife Sicherheit**: Defense-in-Depth mit Validation-Gate (9.8/10 Security-Score)

---

## 🚀 Schnellstart für Anfänger

**Noch nie Terminal benutzt? Kein Problem!** Diese Anleitung führt dich Schritt für Schritt durch die Installation.

### Schritt 1: Terminal öffnen

1. Drücke `Command (⌘) + Space` auf deiner Tastatur
2. Tippe `Terminal` ein
3. Drücke `Enter`

Ein schwarzes oder weißes Fenster öffnet sich – das ist das Terminal. Hier gibst du alle folgenden Befehle ein.

---

### Schritt 2: Homebrew installieren

**Was ist Homebrew?** Ein Paketmanager für macOS – damit installierst du Software über das Terminal.

**Befehl kopieren und ins Terminal einfügen:**

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

- Drücke `Enter`
- Folge den Anweisungen auf dem Bildschirm (eventuell musst du dein macOS-Passwort eingeben)
- Warte, bis "Installation successful" erscheint (dauert 2-5 Minuten)

> 💡 **Tipp:** Falls Homebrew bereits installiert ist, erscheint "Homebrew is already installed". Das ist ok – weiter mit Schritt 3!

---

### Schritt 3: Git installieren

**Was ist Git?** Ein Versionskontrollsystem – damit lädst du den AcademicAgent-Code herunter.

```bash
brew install git
```

- Drücke `Enter`
- Warte, bis die Installation abgeschlossen ist (1-3 Minuten)

**Prüfen ob Git installiert ist:**

```bash
git --version
```

Du solltest etwas wie `git version 2.39.0` sehen.

---

### Schritt 4: Repository klonen

**Jetzt laden wir AcademicAgent herunter!**

```bash
# Wechsle in dein Home-Verzeichnis
cd ~

# Lade AcademicAgent herunter
git clone https://github.com/jamski105/AcademicAgent.git

# Wechsle ins AcademicAgent-Verzeichnis
cd AcademicAgent
```

**Was passiert hier?**
- `cd ~` navigiert zu deinem Home-Ordner (z.B. `/Users/deinname/`)
- `git clone` lädt den AcademicAgent-Code herunter
- `cd AcademicAgent` wechselt in den heruntergeladenen Ordner

> 📁 **AcademicAgent ist jetzt hier:** `~/AcademicAgent`

---

### Schritt 5: Setup ausführen

**Dieser Befehl installiert ALLE benötigten Abhängigkeiten automatisch:**

```bash
bash setup.sh
```

- Drücke `Enter`
- Das Setup prüft:
  - Python 3.9+
  - Node.js
  - Poppler (für PDF-Verarbeitung)
  - Chrome Browser
  - Disk-Verschlüsselung (FileVault)
- Installation dauert 5-10 Minuten

**Bei Fehlern:**
- Das Setup gibt klare Anweisungen, was zu tun ist
- Folge den Hinweisen und führe `bash setup.sh` erneut aus

---

### Schritt 6: Chrome mit Remote-Debugging starten

**AcademicAgent steuert Chrome automatisch – dafür muss Chrome im Debug-Modus laufen:**

```bash
bash scripts/start_chrome_debug.sh
```

- Ein neues Chrome-Fenster öffnet sich
- **WICHTIG:** Schließe dieses Fenster NICHT während der Recherche!

> ⚠️ **Hinweis:** Dieses Chrome-Fenster ist speziell für AcademicAgent. Dein normales Chrome kannst du parallel verwenden.

---

### Schritt 7: Claude Code öffnen und Recherche starten

**Jetzt geht's los!**

```bash
# Claude Code im AcademicAgent-Verzeichnis öffnen
claude .
```

**Oder alternativ:**
- Öffne Claude Code manuell
- Navigiere zum AcademicAgent-Ordner (`~/AcademicAgent`)

**Im Claude Code Chat:**

```
/academicagent
```

- Drücke `Enter`
- Der Agent startet den interaktiven Setup-Dialog
- Beantworte die Fragen zu deinem Forschungsthema
- Der Agent führt dich durch alle 7 Phasen!

---

### ✅ Das war's!

**Der Agent übernimmt jetzt und:**
1. ✅ Führt dich durch die Recherche-Konfiguration (10 Min)
2. 🤖 Durchsucht Datenbanken über DBIS (90-120 Min)
3. ⭐ Bewertet und rankt Kandidaten mit 5D-System (20-30 Min)
4. 📥 Lädt die Top 18 PDFs herunter (20-30 Min)
5. 📝 Extrahiert relevante Zitate (30-45 Min)
6. 📚 Generiert BibTeX-Bibliographie (15 Min)

**Gesamtdauer:** 3,5-4 Stunden (größtenteils automatisiert)

**Ergebnisse findest du hier:** `~/AcademicAgent/runs/[Timestamp]/`

---

### 🆘 Probleme?

Siehe [ERROR_RECOVERY.md](docs/ERROR_RECOVERY.md) für häufige Fehler und Lösungen.

---

## 📊 Der 7-Phasen-Workflow

### Workflow-Übersicht

```
┌─────────────────────────────────────────────────────────────┐
│  START: /academicagent                                      │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
        ┌──────────────────────────────┐
        │  Phase 0: DBIS-Navigation    │  ⏱️  15-20 Min
        │  🌐 Datenbanken entdecken    │
        └──────────────┬───────────────┘
                       ↓
                   ✅ Checkpoint
              "Datenbankliste ok?"
                       ↓
        ┌──────────────────────────────┐
        │  Phase 1: Suchstrings        │  ⏱️  5-10 Min
        │  🔍 Boolean-Queries          │
        └──────────────┬───────────────┘
                       ↓
                   ✅ Checkpoint
              "Suchstrings ok?"
                       ↓
        ┌──────────────────────────────┐
        │  Phase 2: Datenbanksuche     │  ⏱️  90-120 Min
        │  🤖 ITERATIV (5 DBs/Runde)   │
        │  ├─ Iteration 1: 5 DBs       │
        │  ├─ Check: Ziel erreicht?    │
        │  ├─ Iteration 2: 5 DBs       │
        │  └─ Stopp bei 50+ Kandidaten │
        └──────────────┬───────────────┘
                       ↓
        ┌──────────────────────────────┐
        │  Phase 3: 5D-Bewertung       │  ⏱️  20-30 Min
        │  ⭐ Ranking nach 5 Faktoren  │
        └──────────────┬───────────────┘
                       ↓
                   ✅ Checkpoint
        "Wähle 18 aus Top 27 Papers"
                       ↓
        ┌──────────────────────────────┐
        │  Phase 4: PDF-Download       │  ⏱️  20-30 Min
        │  📥 18 Papers herunterladen  │
        └──────────────┬───────────────┘
                       ↓
        ┌──────────────────────────────┐
        │  Phase 5: Zitat-Extraktion   │  ⏱️  30-45 Min
        │  📝 Relevante Zitate finden  │
        └──────────────┬───────────────┘
                       ↓
                   ✅ Checkpoint
              "Zitatqualität ok?"
                       ↓
        ┌──────────────────────────────┐
        │  Phase 6: Finalisierung      │  ⏱️  15-20 Min
        │  📚 BibTeX + Ausgaben        │
        └──────────────┬───────────────┘
                       ↓
                   ✅ Checkpoint
               "Alles fertig?"
                       ↓
        ┌──────────────────────────────┐
        │  ✅ FERTIG!                  │
        │  📂 runs/[Timestamp]/        │
        └──────────────────────────────┘
```

### Phasen-Details

| Phase | Name | Dauer | Typ | Beschreibung |
|-------|------|-------|-----|--------------|
| **0** | DBIS-Navigation | 15-20 Min | ✅ Checkpoint | Entdeckt Datenbanken über DBIS-Portal |
| **1** | Suchstring-Generierung | 5-10 Min | ✅ Checkpoint | Erstellt Boolean-Queries aus Keywords |
| **2** | Datenbanksuche | 90-120 Min | 🤖 Automatisch | Iterative Suche (jeweils 5 DBs) bis Ziel erreicht |
| **3** | 5D-Bewertung | 20-30 Min | ✅ Checkpoint | Rankt Kandidaten, User wählt 18 aus Top 27 |
| **4** | PDF-Download | 20-30 Min | 🤖 Automatisch | Lädt ausgewählte Papers herunter |
| **5** | Zitat-Extraktion | 30-45 Min | ✅ Checkpoint | Extrahiert Zitate mit Seitenzahlen |
| **6** | Finalisierung | 15-20 Min | ✅ Checkpoint | Generiert BibTeX und finale Ausgaben |

**Legende:**
- ✅ **Checkpoint** = Du musst etwas bestätigen oder auswählen
- 🤖 **Automatisch** = Läuft komplett ohne dein Zutun

---

## 📂 Was bekommst du am Ende?

Nach der Recherche findest du alle Ergebnisse in `~/AcademicAgent/runs/[Timestamp]/`:

```
runs/2026-02-18_14-30-00/
│
├── 📥 downloads/                    # Deine 18 PDFs
│   ├── paper_001.pdf
│   ├── paper_002.pdf
│   └── ...
│
├── 📊 metadata/                     # Zwischen-Ergebnisse & State
│   ├── research_state.json          # Für Resume nach Absturz
│   ├── candidates.json              # Alle gefundenen Papers (50+)
│   ├── search_strings.json          # Boolean-Queries pro Datenbank
│   └── config.md                    # Deine Recherche-Konfiguration
│
├── ✨ outputs/                      # DEINE HAUPT-ERGEBNISSE
│   ├── quote_library.json           # Extrahierte Zitate mit Seitenzahlen
│   ├── bibliography.bib             # BibTeX für LaTeX/Word
│   └── summary.md                   # Recherche-Zusammenfassung
│
└── 📋 logs/                         # Ausführungs-Logs
    ├── phase_0.log
    ├── phase_1.log
    └── cdp_health.log
```

**Die wichtigsten Dateien:**
- ✅ `outputs/bibliography.bib` → Kopiere in dein LaTeX-Projekt
- ✅ `outputs/quote_library.json` → 40-50 relevante Zitate mit Seitenzahlen
- ✅ `downloads/*.pdf` → 18 hochwertige Papers

---

## 🗃️ Welche Datenbanken werden durchsucht?

AcademicAgent nutzt zwei Strategien:

### 1. Kuratierte Top-Datenbanken (30+)

**Interdisziplinär:**
- Web of Science, Scopus, Google Scholar, JSTOR, SpringerLink, ScienceDirect, PubMed, arXiv, BASE, CORE

**Informatik & Software Engineering:**
- ACM Digital Library, IEEE Xplore, DBLP, arXiv, Scopus

**Wirtschaft & BWL:**
- WISO, Statista, Business Source Elite, EconBiz, RePEc, SSRN, Scopus

**Jura:**
- juris, beck-online, Wolters Kluwer Online, Staudinger BGB, HeinOnline, Westlaw

### 2. Dynamische DBIS-Erkennung

Zusätzlich durchsucht der Agent **DBIS** (Datenbank-Infosystem) automatisch:

1. Suche in DBIS mit deinen Keywords + Disziplin
2. Bewertung der Ergebnisse (Relevanz-Score 0-100)
3. Datenbanken mit Score ≥ 60 werden zur Liste hinzugefügt
4. Integration in iterative Suche

**Typisches Ergebnis:** 8 kuratierte + 3 DBIS-entdeckte = **11 Datenbanken**

### 🔄 Iterative Suche (NEU!)

**Intelligenter als alte Versionen:** Agent durchsucht nicht mehr ALLE Datenbanken auf einmal!

```
START Phase 2
  ↓
Iteration 1: Durchsuche Top 5 Datenbanken
  → Gefunden: 23 Kandidaten
  ↓
Check: Ziel erreicht? (Ziel: 50 Kandidaten)
  → NEIN, weiter!
  ↓
Iteration 2: Durchsuche nächste 5 Datenbanken
  → Gefunden: 28 neue (Gesamt: 51)
  ↓
Check: Ziel erreicht?
  → JA! Stoppe vorzeitig ✅
```

**Ergebnis:** 40% weniger Datenbanken durchsucht, 42% schneller, gleiche Qualität! 🚀

---

## ⭐ Wie werden Papers bewertet? (5D-System)

Jedes gefundene Paper wird über **5 Dimensionen** bewertet und erhält einen Score von 0-100 Punkten:

| Dimension | Gewicht | Was wird gemessen? | Beispiel |
|-----------|---------|-------------------|----------|
| 🎯 **Relevanz** | 25% | Keyword-Treffer in Titel & Abstract | "DevOps" + "Governance" im Titel = 23 Pkt |
| 📈 **Zitationen** | 20% | Wie oft wurde das Paper zitiert? | 350 Zitationen = 18 Pkt |
| 📅 **Aktualität** | 20% | Publikationsjahr (neuere = besser) | 2023 = 19 Pkt, 2015 = 11 Pkt |
| 🏆 **Journalqualität** | 20% | Impact Factor, Konferenz-Rang | Top-Konferenz (A*) = 18 Pkt |
| 🔓 **Open Access** | 15% | PDF frei verfügbar? | Ja = 15 Pkt, Nein = 0 Pkt |

**Finaler Score = Summe aller Dimensionen (max. 100 Punkte)**

### Beispiel-Bewertung

```json
{
  "title": "Lean Governance in DevOps Teams (2023)",
  "authors": "Schmidt et al.",
  "score": 87,
  "breakdown": {
    "relevance": 23,      // Starke Keyword-Matches
    "citations": 18,      // 350 Zitationen
    "recency": 19,        // Erschienen 2023
    "quality": 18,        // Publiziert in Top-Konferenz
    "open_access": 9      // PDF verfügbar (aber paywall)
  }
}
```

**Score 87/100 = Top 3 Kandidat** ✨

**Nach Phase 3:** Agent zeigt dir die Top 27 Papers sortiert nach Score – du wählst die besten 18 aus!

---

## 📖 Dokumentation & Ressourcen

### 🚨 Fehlerbehandlung & Troubleshooting

**[ERROR_RECOVERY.md](docs/ERROR_RECOVERY.md)**

Umfassender Guide für alle häufigen Probleme:
- **CDP-Verbindungsfehler**: Chrome antwortet nicht mehr → Auto-Restart
- **CAPTCHA erkannt**: Manuell lösen im Browser-Fenster
- **Login erforderlich**: Uni-Authentifizierung durchführen
- **Rate Limits**: Automatischer 60s Backoff
- **Recherche unterbrochen**: State validieren & fortsetzen mit `validate_state.py`

Enthält auch: CDP Health Monitor Anleitung, State-Management Commands, Debug-Tools.

---

### 🛡️ Sicherheit & Datenschutz

**[SECURITY.md](docs/SECURITY.md) - Security Score: 9.8/10**

AcademicAgent ist produktionsreif gehärtet gegen Prompt-Injection-Angriffe:
- ✅ **Validation-Gate**: MANDATORY Output-Validierung für alle Agents
- ✅ **Encryption-at-Rest**: MANDATORY via FileVault (macOS) enforced
- ✅ **Safe-Bash-Wrapper**: Framework-enforced Action-Gate für alle Bash-Aufrufe
- ✅ **PDF Security Validator**: Deep Analysis mit Metadata-Stripping
- ✅ **100% automatisierte Red-Team-Tests** (12/12 Tests)

**[PRIVACY.md](docs/PRIVACY.md) - GDPR-Compliant**

Datenschutzrichtlinie & GDPR-Compliance:
- **Local-First**: Alle Daten bleiben auf deinem Mac
- **Log-Redaction**: Automatische PII/Secret-Redaction in allen Logs
- **Claude API**: Prompts nach 30 Tagen gelöscht
- **Encryption**: FileVault/LUKS empfohlen

**[THREAT_MODEL.md](docs/THREAT_MODEL.md)**

Detailliertes Bedrohungsmodell & Sicherheitsanalyse:
- Angriffsvektoren & Mitigations
- Security Requirements & Compliance (GDPR, ISO 27001)
- Risk Register & Security Audit History

---

### 📁 Projektstruktur

**[PROJEKTSTRUKTUR.md](docs/PROJEKTSTRUKTUR.md)**

Vollständige Übersicht über das Projekt:
- Alle Verzeichnisse & Dateien erklärt
- 40+ Python/Bash-Scripte dokumentiert
- Agent-Definitionen & Skills
- Für Nutzer UND Entwickler

---

## 🔄 Nach Absturz fortsetzen

Falls die Recherche unterbrochen wird:

```bash
# 1. State validieren
python3 scripts/validate_state.py runs/[Timestamp]/metadata/research_state.json

# 2. Chrome neu starten
bash scripts/start_chrome_debug.sh

# 3. Agent fortsetzen
cd ~/AcademicAgent
claude .
# Im Chat: /academicagent
```

Der Agent setzt automatisch bei der letzten abgeschlossenen Phase fort!

**Mehr Details:** Siehe [ERROR_RECOVERY.md](docs/ERROR_RECOVERY.md)

---

## 🔧 Erweiterte Nutzung

**Für Power-User:** Detaillierte Dokumentation zu allen erweiterten Features findest du in [docs/PROJEKTSTRUKTUR.md](docs/PROJEKTSTRUKTUR.md)

**Highlights:**
- Utility-Scripts (Cost-Tracker, Metrics, Retry-Strategien)
- CDP-Wrapper für Browser-Automatisierung
- Safe-Bash für sichere Command-Ausführung
- State-Management & Resume-Funktionen




---

## 📄 Lizenz

MIT License - Siehe LICENSE-Datei für Details

---

## 🤖 ChatGPT Config-Generator (Copy & Paste!)

**Problem:** Die Config-Datei manuell ausfüllen ist mühsam.
**Lösung:** Lass ChatGPT eine fertige Config für dich erstellen!

### Schritt 1: Kopiere diesen Prompt in ChatGPT

```text
Du bist ein Konfigurations-Assistent für AcademicAgent (ein Literatur-Recherche-Tool).

DEINE AUFGABE:
Erstelle eine fertige Config-Datei im EXAKTEN Format von academic_context.md

STRUKTUR (EXAKT SO ÜBERNEHMEN!):

# Wissenschaftlicher Kontext

## 1. Forschungsgebiet
**Hauptdisziplin:**
[Beispiel: Software Engineering, Psychologie, Medizinrecht]

**Spezialisierung/Sub-Bereich:**
[Beispiel: DevOps Governance, Klinische Depressionsforschung]

## 2. Hintergrund der Arbeit
**Art der Arbeit:**
[Beispiel: Masterarbeit, Bachelorarbeit, Dissertation]

**Kontext:**
[2-3 Sätze: Uni, Studiengang, Thema der Arbeit]

**Hauptziel der Arbeit:**
[1-2 Sätze: Was willst du erreichen?]

## 3. Verwendete Methoden/Theorien
**Forschungsmethoden:**
[Liste: z.B. Qualitative Interviews, Experimente, Literature Review]

**Theoretischer Rahmen:**
[Liste: z.B. Grounded Theory, Design Thinking, Lean Principles]

**Technologien/Tools:**
[Liste: z.B. Python, SPSS, Docker, Unity]

## 4. Wichtige Keywords
**Hauptkonzepte:**
[5-8 zentrale Begriffe zu deinem Thema]

**Technische Begriffe:**
[5-8 technische/fachliche Begriffe]

**Zielgruppen/Kontext:**
[3-5 Begriffe: Wer/Was wird untersucht?]

## 5. Bevorzugte Datenbanken (optional)
**Deine bevorzugten Datenbanken:**
[z.B. ACM Digital Library, IEEE Xplore, PubMed]

## 6. Zitationseinstellungen
**Zitationsstil:**
[Zitationsstil]

**Max Wörter pro Zitat:**
[max Wörter pro Zitat]

## 7. Relevante Autoren/Paper (optional)
**Seminal Papers:**
[2-3 wichtige Papers in deinem Feld]

**Wichtige Forscher/Gruppen:**
[2-3 Namen/Institutionen]

## 8. Zeitliche Eingrenzung (Default)
**Standard-Zeitraum:**
2019-2026

## 9. Qualitätsanforderungen (Default)
**Peer-Review erforderlich:**
Ja

**Preprints einbeziehen:**
Ja

**Minimum Citation Count:**
5

## 10. Sprachen
**Bevorzugte Sprachen:**
1. Englisch (primär)
2. Deutsch (sekundär)

---

ANWEISUNGEN:
1. Frage den Nutzer nach: Thema, Studiengang, Art der Arbeit, Forschungsfrage
2. Fülle ALLE Abschnitte aus (nutze die Beispiele als Vorlage)
3. Gib die fertige Config als Markdown-Code-Block aus
4. Am Ende erkläre: "Speichere das als `config/academic_context.md`"

JETZT: Frage den Nutzer nach seinem Thema und berücksichtige dabei Dateien die dir der Nutzer eventuell gegeben hat.
```

### Schritt 2: Beschreibe dein Thema in ChatGPT und gebe ChatGPT im besten Fall deine Gliederung o.ä. mit

Beispiel:
```
"Ich schreibe eine Masterarbeit über Lean Governance in DevOps-Teams.
Studiengang: Wirtschaftsinformatik an der TU München.
Fokus: Wie Lean-Prinzipien Governance-Prozesse verbessern können."
```

### Schritt 3: ChatGPT gibt dir die fertige Config

Kopiere die Ausgabe KOMPLETT!

### Schritt 4: Speichere die Config

**Option A: Mit Terminal (nicht EMPFOHLEN)**

```bash
# Navigiere zum AcademicAgent-Ordner
cd ~/AcademicAgent

# Öffne die Config-Datei im Editor
nano config/academic_context.md

# Füge die ChatGPT-Ausgabe ein (Cmd+V)
# Speichern: Ctrl+O, Enter, Ctrl+X
```

**Option B: Mit Text-Editor (EMPFOHLEN)**

1. Öffne `~/AcademicAgent/config/academic_context.md` in einem Text-Editor
2. Ersetze ALLES mit der ChatGPT-Ausgabe
3. Speichern

### Schritt 5: Starte den Agent

```bash
# Im Terminal
cd ~/AcademicAgent
claude .

# Im Claude Code Chat
/academicagent
```

**Fertig!** Der Agent lädt deine Config und startet die Recherche. ✨

---

## 📄 Lizenz

MIT License - Siehe [LICENSE](LICENSE) für Details.

---

## 📄 Coming Soon

- Agent und Skill Prompts alles auf Deutsch übersetzen.

---


**Viel Erfolg bei deiner Recherche! 📚✨**
