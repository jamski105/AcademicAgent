# 🚀 Erste Schritte mit AcademicAgent

In dieser Anleitung lernst du, wie du AcademicAgent installierst und deine erste Literaturrecherche durchführst.

## Voraussetzungen prüfen

Bevor du startest, stelle sicher, dass du folgendes hast:

### ✅ System-Anforderungen

- **Betriebssystem:** macOS oder Linux
- **Browser:** Google Chrome (wird automatisch installiert falls nicht vorhanden)
- **Netzwerk:** Universitäts-VPN-Zugang für lizenzierte Datenbanken

### ✅ Accounts & Zugänge

- **Claude API Key:** Du brauchst einen API-Schlüssel von Anthropic
  - Registriere dich auf [console.anthropic.com](https://console.anthropic.com)
  - Erstelle einen API-Key unter "API Keys"
  - Notiere dir den Key (beginnt mit `sk-ant-...`)

- **Universitäts-VPN:** Zugang zum VPN deiner Universität
  - Für Zugriff auf lizenzierte Datenbanken (IEEE, Springer, etc.)
  - Muss während der Recherche aktiv sein

- **DBIS-Zugang:** Zugang zum Database Information System deiner Uni
  - In der Regel automatisch mit Uni-Login verfügbar
  - DBIS-Portal: [dbis.ur.de](https://dbis.ur.de)

---

## Installation

### Schritt 1: Repository klonen

Öffne ein Terminal und führe folgende Befehle aus:

```bash
# Repository klonen
git clone https://github.com/yourusername/AcademicAgent.git

# In das Verzeichnis wechseln
cd AcademicAgent
```

### Schritt 2: Setup-Script ausführen

Das Setup-Script installiert alle benötigten Abhängigkeiten automatisch:

```bash
# Setup ausführen (kann 5-10 Minuten dauern)
bash setup.sh
```

**Was installiert das Setup-Script?**
- Python 3.10+ und benötigte Pakote
- Node.js und Claude Code CLI
- Poppler (für PDF-Textextraktion)
- Playwright (für Browser-Automatisierung)
- Chrome mit Remote-Debugging-Support

**Hinweis:** Du wirst möglicherweise nach deinem Administrator-Passwort gefragt.

### Schritt 3: API-Key konfigurieren

Nach der Installation musst du deinen Claude API Key konfigurieren:

```bash
# API-Key in Umgebungsvariable speichern
echo 'export ANTHROPIC_API_KEY="sk-ant-dein-key-hier"' >> ~/.zshrc

# Oder für Bash-Nutzer:
echo 'export ANTHROPIC_API_KEY="sk-ant-dein-key-hier"' >> ~/.bashrc

# Terminal neu laden
source ~/.zshrc  # oder source ~/.bashrc
```

**Sicherheitshinweis:** Teile deinen API-Key niemals mit anderen oder committe ihn nicht in Git!

---

## Chrome mit Remote-Debugging starten

AcademicAgent steuert Chrome über das Chrome DevTools Protocol (CDP). Dafür muss Chrome im Debug-Modus laufen:

```bash
# Chrome im Debug-Modus starten
bash scripts/start_chrome_debug.sh
```

**Was passiert?**
- Chrome öffnet sich in einem separaten Fenster
- Eine Meldung erscheint: "Chrome wird remote gesteuert"
- Der Browser läuft auf Port 9222 für CDP-Verbindungen

**Wichtig:**
- Lasse dieses Chrome-Fenster während der Recherche offen
- Schließe es nicht manuell
- Du kannst es im Hintergrund laufen lassen

### Verbindung testen

Um zu prüfen, ob Chrome korrekt läuft:

```bash
# CDP-Verbindung testen
curl http://localhost:9222/json/version
```

Du solltest eine JSON-Antwort mit Chrome-Versionsinformationen sehen:
```json
{
   "Browser": "Chrome/121.0.6167.85",
   "Protocol-Version": "1.3",
   "webSocketDebuggerUrl": "ws://localhost:9222/devtools/browser/..."
}
```

---

## VS Code öffnen und Claude Code starten

### Schritt 1: Projekt in VS Code öffnen

```bash
# VS Code öffnen
code .
```

### Schritt 2: Claude Code Chat starten

In VS Code:
1. Drücke **Cmd+Shift+P** (Mac) oder **Ctrl+Shift+P** (Windows/Linux)
2. Tippe "Claude Code: Start Chat"
3. Drücke Enter

Ein Chat-Panel öffnet sich rechts in VS Code.

---

## Deine erste Recherche

Jetzt bist du bereit für deine erste Literaturrecherche!

### Schritt 1: AcademicAgent starten

Im Claude Code Chat-Panel, tippe:

```
/academicagent
```

Drücke Enter.

### Schritt 2: Interaktive Konfiguration

Der Agent führt dich durch einen interaktiven Setup-Prozess:

#### Frage 1: Forschungsfrage
```
Agent: Was ist deine Forschungsfrage?

Beispiel-Antwort:
"Wie ermöglichen Lean-Prinzipien Governance in DevOps-Teams?"
```

#### Frage 2: Primary Keywords
```
Agent: Welche Haupt-Keywords beschreiben dein Thema? (kommagetrennt)

Beispiel-Antwort:
"Lean Governance, DevOps, Agile Teams"
```

#### Frage 3: Secondary Keywords
```
Agent: Optionale sekundäre Keywords? (kommagetrennt, oder Enter zum Überspringen)

Beispiel-Antwort:
"Continuous Delivery, Process Automation, IT Governance"
```

#### Frage 4: Disziplinen
```
Agent: Welche akademischen Disziplinen sind relevant? Wähle aus:
1. Informatik
2. Wirtschaft & BWL
3. Jura
4. Medizin
5. Psychologie
6. Interdisziplinär

Beispiel-Antwort:
"1,2" (für Informatik und Wirtschaft)
```

#### Frage 5: Jahresbereich
```
Agent: Welcher Zeitraum soll durchsucht werden?

Beispiel-Antwort:
"2015-2024" (Standard)
```

#### Frage 6: Sprachen
```
Agent: Welche Sprachen? (kommagetrennt)

Beispiel-Antwort:
"Englisch, Deutsch"
```

#### Frage 7: Zielanzahl
```
Agent: Wie viele Papers möchtest du am Ende? (Standard: 18)

Beispiel-Antwort:
"18" (empfohlen für Bachelor/Master-Arbeiten)
```

### Schritt 3: Konfig-Bestätigung

Der Agent zeigt dir eine Zusammenfassung:

```markdown
# Deine Recherche-Konfiguration

## Forschungsfrage
Wie ermöglichen Lean-Prinzipien Governance in DevOps-Teams?

## Keywords
- Primär: Lean Governance, DevOps, Agile Teams
- Sekundär: Continuous Delivery, Process Automation, IT Governance

## Disziplinen
- Informatik
- Wirtschaft & BWL

## Parameter
- Zeitraum: 2015-2024
- Sprachen: Englisch, Deutsch
- Zielanzahl: 18 Papers

Sieht das gut aus? (ja/nein)
```

Antworte mit "ja" um fortzufahren.

### Schritt 4: Recherche läuft automatisch

Ab jetzt läuft der Prozess größtenteils automatisch! Der Agent wird:

1. **Phase 0 (15-20 Min):** Datenbanken über DBIS finden
   - **→ CHECKPOINT:** Du validierst die gefundenen Datenbanken

2. **Phase 1 (5-10 Min):** Boolean-Suchstrings generieren
   - **→ CHECKPOINT:** Du genehmigst die Suchstrings

3. **Phase 2 (90-120 Min):** Datenbanken durchsuchen
   - Läuft automatisch, keine Eingabe nötig
   - Du kannst in dieser Zeit andere Dinge tun

4. **Phase 3 (20-30 Min):** Kandidaten bewerten und ranken
   - **→ CHECKPOINT:** Du wählst Top 18 aus Top 27 Kandidaten

5. **Phase 4 (20-30 Min):** PDFs herunterladen
   - Läuft automatisch

6. **Phase 5 (30-45 Min):** Zitate extrahieren
   - Läuft automatisch
   - **→ CHECKPOINT:** Du prüfst Zitatqualität

7. **Phase 6 (15-20 Min):** Bibliographie generieren
   - **→ CHECKPOINT:** Du bestätigst die finalen Ausgaben

**Gesamtdauer:** ~3,5-4 Stunden (deine aktive Zeit: ~15-20 Minuten)

---

## Was passiert während der Recherche?

### Automatische Phasen

Während die automatischen Phasen laufen:
- **Chrome läuft im Hintergrund** und durchsucht Datenbanken
- **Du kannst andere Dinge tun** (E-Mails checken, Kaffee holen, etc.)
- **VS Code zeigt Fortschritt** im Chat-Panel
- **Logs werden geschrieben** nach `runs/[Timestamp]/logs/`

### Checkpoints (Human-in-the-Loop)

Bei Checkpoints wirst du aktiv:
- **Benachrichtigung** im Chat-Panel
- **Agent wartet auf deine Bestätigung**
- **Du prüfst die Ergebnisse** und gibst Feedback
- **Dann geht es automatisch weiter**

---

## Deine Ergebnisse finden

Nach Abschluss findest du alle Ergebnisse in:

```
runs/2026-02-18_14-30-00/  (Timestamp variiert)
├── downloads/              # 18 PDF-Dateien
├── outputs/
│   ├── quote_library.json  # Extrahierte Zitate mit Seitenzahlen
│   ├── bibliography.bib    # BibTeX-Zitationen
│   └── summary.md          # Recherche-Zusammenfassung
├── metadata/
│   ├── config.md           # Deine Recherche-Konfiguration
│   └── candidates.json     # Alle gefundenen Kandidaten mit Scores
└── logs/                   # Detaillierte Logs für Debugging
```

### Die wichtigsten Dateien:

1. **`outputs/bibliography.bib`**
   - Alle 18 Papers im BibTeX-Format
   - Direkt in LaTeX/Word importierbar
   - Enthält Titel, Autoren, Jahr, DOI, etc.

2. **`outputs/quote_library.json`**
   - 40-50 relevante Zitate aus den Papers
   - Mit Seitenzahlen und Relevanz-Scores
   - Strukturiert nach Themen

3. **`downloads/*.pdf`**
   - Die 18 heruntergeladenen PDF-Dateien
   - Benannt nach: `Autor_Jahr_Titel.pdf`

4. **`outputs/summary.md`**
   - Überblick über die Recherche
   - Statistiken (Anzahl gefundener Papers, Datenbanken, etc.)
   - Empfehlungen für nächste Schritte

---

## Nächste Schritte

Glückwunsch zu deiner ersten Recherche! 🎉

**Was du jetzt tun kannst:**

1. **[Ergebnisse verstehen](04-understanding-results.md)**
   - Lerne das 5D-Bewertungssystem verstehen
   - Wie du die Zitatbibliothek nutzt

2. **[Best Practices](06-best-practices.md)**
   - Tipps für bessere Recherche-Ergebnisse
   - Keyword-Strategien

3. **Weitere Recherchen durchführen**
   - Einfach erneut `/academicagent` ausführen
   - Neue Konfiguration erstellen

4. **Probleme?**
   - Siehe [Troubleshooting-Guide](05-troubleshooting.md)

---

## Häufige Fragen (FAQ)

### Muss ich die ganze Zeit am Computer bleiben?

**Nein!** Nur bei Checkpoints (~15-20 Minuten aktive Zeit). Den Rest der Zeit läuft alles automatisch im Hintergrund.

### Kann ich die Recherche unterbrechen?

**Ja!** Der State wird automatisch gespeichert. Du kannst jederzeit:
1. Terminal schließen
2. Später erneut `/academicagent` ausführen
3. Agent fragt ob du fortsetzen möchtest

Siehe [Troubleshooting: Recherche fortsetzen](05-troubleshooting.md#recherche-fortsetzen).

### Wie viel kostet eine Recherche?

Die Kosten hängen von der Claude API-Nutzung ab:
- **Typisch:** $2-4 pro Recherche
- **Abhängig von:** Anzahl Datenbanken, Papers, Seitenlänge der PDFs
- **Tracking:** Siehe `runs/[Timestamp]/metadata/llm_costs.jsonl`

### Brauche ich wirklich VPN?

**Ja, für lizenzierte Datenbanken!** Viele akademische Datenbanken (IEEE Xplore, SpringerLink, etc.) sind nur über Universitätsnetzwerke zugänglich. Ohne VPN:
- Open-Access-Datenbanken funktionieren (arXiv, CORE, BASE)
- Lizenzierte Datenbanken werden blockiert oder erfordern Login

### Funktioniert es auch auf Windows?

Aktuell nur **macOS und Linux** vollständig unterstützt. Windows-Support ist geplant (WSL2 funktioniert möglicherweise).

---

**[Weiter zu: Grundlegender Workflow →](02-basic-workflow.md)**
