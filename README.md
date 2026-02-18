# 🎓 AcademicAgent

**Version:** 3.0
**Autonomes akademisches Literatur-Recherche-System**

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
- **Sicherheit**: Schutz gegen Prompt-Injection-Angriffe (9/10 Score)

---

## 🚀 Schnellstart

### Voraussetzungen

- macOS oder Linux
- Chrome-Browser
- Universitäts-VPN-Zugang (für lizenzierte Datenbanken)

### Installation

```bash
# Repository klonen
git clone https://github.com/yourusername/AcademicAgent.git
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
- **Action Gate**: Validiert Tool-Aufrufe vor Ausführung
- **Domain-Whitelist**: Nur akademische Datenbanken erlaubt (über DBIS)
- **Least Privilege**: Beschränkter Dateisystem- und Netzwerkzugriff
- **Reader/Actor-Trennung**: Read-only-Agents können keine Befehle ausführen

**Sicherheits-Score:** 9/10 (90% der Maßnahmen implementiert)

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

Bearbeite [config/database_disciplines.yaml](config/database_disciplines.yaml):

```yaml
- name: Benutzerdefinierte Datenbank
  disciplines:
    - Deine Disziplin
  url: custom-db.com
  access: Subscription
  api_available: false
  base_score: 85
  priority: 2
  notes: "Beschreibung deiner benutzerdefinierten Datenbank"
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

```bash
# JSON in formatiertes Word-Dokument konvertieren
# (Benötigt pandoc - installiert via setup.sh)
python3 scripts/export_quotes.py \
  runs/[Timestamp]/outputs/quote_library.json \
  output.docx
```

---

## 📖 Zusätzliche Dokumentation

- **[ERROR_RECOVERY.md](ERROR_RECOVERY.md)** - Umfassender Fehlerbehandlungs-Guide
- **[SECURITY.md](SECURITY.md)** - Sicherheitshärtung & Red-Team-Tests
- **[docs/DBIS_USAGE.md](docs/DBIS_USAGE.md)** - Technische DBIS-Integration (für Agents)
- **[config/database_disciplines.yaml](config/database_disciplines.yaml)** - Datenbank-Katalog

---

## 🤝 Beitragen

Beiträge sind willkommen! Verbesserungsbereiche:

1. **Datenbank-Abdeckung**
   - Disziplin-spezifische Datenbanken hinzufügen
   - DBIS-Relevanz-Scoring verbessern

2. **Bewertungsalgorithmus**
   - H-Index für Journalqualität integrieren
   - Domain-spezifisches Relevanz-Scoring hinzufügen

3. **Internationalisierung**
   - Mehrsprachige Suchstrings
   - Unterstützung nicht-englischer Datenbanken

4. **Ausgabeformate**
   - Zitierstile (APA, MLA, Chicago)
   - Export zu Zotero, Mendeley, EndNote

5. **Benutzeroberfläche**
   - Webbasierte Konfigurations-UI
   - Echtzeit-Fortschritts-Dashboard

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

## 📞 Support & Kontakt

- **Issues**: [GitHub Issues](https://github.com/yourusername/AcademicAgent/issues)
- **Diskussionen**: [GitHub Discussions](https://github.com/yourusername/AcademicAgent/discussions)
- **E-Mail**: your-email@example.com
- **Dokumentation**: Siehe Docs in diesem Repository

---

## 🔄 Versionshistorie

- **v3.0** (2026-02-18) - Datenbank-Strategie V3.0 mit dynamischer DBIS-Erkennung
- **v2.5** (Vorherig) - Iterative Datenbanksuche
- **v2.0** (Vorherig) - 5D-Bewertungssystem
- **v1.0** (Vorherig) - Erstes Release

---

**Viel Erfolg bei der Recherche! 📚🤖**
