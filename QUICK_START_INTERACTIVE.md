# 🚀 Quick Start - Interactive Mode (v2.1)

**NEU:** Interaktiver Dialog statt manueller Config-Erstellung!

---

## 🎯 Was ist neu?

**Version 2.1 bringt:**
- ✅ **Interaktiver Setup-Dialog**: Kein Config-File mehr nötig!
- ✅ **7 Recherche-Modi**: Von Quick Quote (30 Min) bis Survey (6h)
- ✅ **Smart Chrome Setup**: Automatische DBIS-Prüfung
- ✅ **Strukturiertes Logging**: Besseres Debugging
- ✅ **Verbessertes Error Handling**: Automatische Recovery

---

## ⚡ 3-Schritte-Start

### Schritt 1: Smart Chrome Setup (einmalig)

```bash
cd ~/AcademicAgent
bash scripts/smart_chrome_setup.sh
```

**Was passiert:**
1. Chrome startet mit Remote Debugging (Port 9222)
2. DBIS öffnet sich automatisch
3. Du loggst dich ein (falls nötig)
4. Setup verifiziert Zugang

**Ausgabe:**
```
✅ Chrome started (PID: 12345)
✅ CDP connection working
✅ DBIS access verified
```

**Hinweis:** Chrome-Fenster offen lassen!

---

### Schritt 2: VS Code öffnen

```bash
cd ~/AcademicAgent
code .
```

Starte Claude Code Chat:
- **VSCode:** Cmd+Shift+P → "Claude Code: Start Chat"

---

### Schritt 3: Interaktiven Dialog starten

Im Claude Code Chat:

```
Start interactive research setup
```

**Oder ausführlicher:**

```
Lies agents/interactive_setup_agent.md und starte den interaktiven Dialog für meine Recherche.
```

---

## 💬 Was passiert im Dialog?

### Phase 1: Kontext verstehen

```
Agent: Hi! Ich bin dein Research-Assistent. 🤖

Erzähl mir kurz:
1. Was schreibst du gerade?
2. An welcher Stelle steckst du?
3. Was brauchst du konkret?
```

**Beispiel-Antworten:**
- "Ich schreibe meine Masterarbeit über DevOps und brauche 1-2 Zitate"
- "Ich starte gerade mit einem Paper über AI-Testing"
- "Ich brauche Quellen für mein Related Work Kapitel über Microservices"

---

### Phase 2: Modus-Auswahl

Basierend auf deiner Antwort schlägt der Agent einen Modus vor:

```
Agent: Basierend auf deiner Beschreibung schlage ich den Quick Quote Mode vor.

Das bedeutet:
- ⏱️ Dauer: 30-45 Min
- 📚 Quellen: 5-8
- 🎯 Fokus: Gezielte Zitate finden

Passt das, oder soll ich einen anderen Modus verwenden?
```

**Verfügbare Modi:**

| Modus | Dauer | Quellen | Wann nutzen? |
|-------|-------|---------|--------------|
| **Quick Quote** | 30-45 Min | 5-8 | 1-3 spezifische Zitate |
| **Deep Research** | 3.5-4.5h | 18-27 | Umfassende Literature Review |
| **Chapter Support** | 1.5-2h | 8-12 | Quellen für ein Kapitel |
| **Citation Expansion** | 1-1.5h | 10-15 | Snowballing von Papers |
| **Trend Analysis** | 1-1.5h | 8-12 | Neueste Entwicklungen |
| **Controversy Mapping** | 2-2.5h | 12-18 | Pro/Contra-Positionen |
| **Survey/Overview** | 5-6h | 30-50 | Systematischer Review |

---

### Phase 3: Keywords & Disziplin

```
Agent: Was ist deine Forschungsfrage?

Du: "Wie wird Lean Governance in DevOps umgesetzt?"

Agent: Ich habe folgende Keywords identifiziert:

Cluster 1 (Hauptkonzept):
- lean governance
- lightweight governance
- agile governance

Cluster 2 (Kontext):
- DevOps
- continuous delivery
- CI/CD

Passen diese Keywords?
```

Du kannst:
- ✅ Bestätigen
- ➕ Hinzufügen
- ➖ Entfernen
- ✏️ Ändern

---

### Phase 4: Datenbanken

```
Agent: In welcher Disziplin recherchierst du?

1. Informatik / Software Engineering
2. Jura / Rechtswissenschaften
3. Medizin / Life Sciences
4. BWL / Management
5. Ingenieurwesen
6. Sozialwissenschaften
7. Geisteswissenschaften
8. Andere

Du: 1

Agent: Basierend auf Informatik empfehle ich:
- IEEE Xplore
- ACM Digital Library
- SpringerLink
- Scopus
- ScienceDirect

Möchtest du diese nutzen? (Ja/Anpassen)
```

---

### Phase 5: Quality-Filter

```
Agent: Lass uns noch die Qualitäts-Filter festlegen:

Zeitraum:
- Ab welchem Jahr? [Vorschlag: 2015]

Zitationen:
- Minimum an Citations? [Vorschlag: 50]

Dokumenttyp:
- Nur Peer-Reviewed? [Vorschlag: Ja]
```

---

### Phase 6: Bestätigung & Start

```
Agent: Perfekt! Hier ist deine Recherche-Konfiguration:

📋 Zusammenfassung:
- Modus: Quick Quote Mode
- Dauer: 30-45 Min
- Quellen: 5-8

Forschungsfrage: "Wie wird Lean Governance in DevOps umgesetzt?"
Keywords: [Liste]
Datenbanken: [Liste]

Alles korrekt? (Ja/Nein/Ändern)

Du: Ja

Agent: 🚀 Starte Setup...

[1/3] Chrome-Check... ✅
[2/3] DBIS-Zugang... ✅
[3/3] Config erstellen... ✅

🎉 Setup abgeschlossen!
Übergebe jetzt an Orchestrator...
```

---

## 📊 Während der Recherche

### Was du siehst

Der Agent zeigt dir den Fortschritt:

```
✅ Phase 0: DBIS-Navigation (15 Min)
   → 8 Datenbanken gefunden

⏳ Phase 1: Suchstring-Generierung (5 Min)
   → 15 Suchstrings erstellt

⏳ Phase 2: Datenbank-Durchsuchung (30 Min)
   → IEEE Xplore: 12 results
   → ACM: 8 results
   → SpringerLink: 15 results
```

### Wenn Fehler auftreten

**Beispiel: CAPTCHA**
```
⚠️ CAPTCHA detected. Please:
  1. Switch to Chrome window
  2. Solve the CAPTCHA
  3. Press ENTER when done

[Du löst CAPTCHA]

✅ Continuing...
```

**Beispiel: Login**
```
⚠️ Login required. Please:
  1. Switch to Chrome window
  2. Log in with your credentials
  3. Press ENTER when done

[Du loggst dich ein]

✅ Login verified. Continuing...
```

---

## 📁 Ergebnisse

Nach Abschluss findest du:

```
~/AcademicAgent/projects/[ProjectName]/
├── pdfs/                   # 5-8 PDFs (je nach Modus)
├── outputs/
│   ├── Quote_Library.csv   # Alle Zitate mit Kontext
│   └── Annotated_Bibliography.md
└── logs/                   # Strukturierte Logs (JSON)
```

**Quote Library (CSV):**
- ID, APA-7 Zitat, Datenbank, DOI
- Zitat-Text, Seite, Kontext
- Relevanz-Score

**Annotated Bibliography (Markdown):**
- Zusammenfassung aller Quellen
- Kategorisiert nach Relevanz

---

## 🔄 Resume nach Unterbrechung

Falls die Recherche unterbrochen wurde:

```bash
# Prüfe Resume-Status
bash scripts/resume_research.sh [ProjectName]

# Output zeigt:
🔄 Resume möglich!
Last completed: Phase 2. Resume from Phase 3?

Ready to resume!
```

Im Claude Code Chat:

```
Setze die Recherche fort für [ProjectName]
```

Der Agent überspringt automatisch abgeschlossene Phasen!

---

## 💡 Tipps & Tricks

### Für Quick Quote Mode

**Tipp 1:** Sei sehr spezifisch in deiner Forschungsfrage
```
❌ "Microservices"
✅ "Vorteile von Microservices gegenüber Monolithen bei Skalierung"
```

**Tipp 2:** Wähle nur 2-3 relevanteste Datenbanken

### Für Deep Research Mode

**Tipp 1:** Plane 4-5 Stunden ein (inkl. Checkpoints)

**Tipp 2:** Nutze alle empfohlenen Datenbanken

### Für Trend Analysis Mode

**Tipp 1:** Setze Min Year auf letztes Jahr
```
Min Year: 2025 (für cutting-edge research)
```

**Tipp 2:** Inkludiere Preprints (arXiv, bioRxiv)

### Für Citation Expansion Mode

**Tipp 1:** Starte mit 3-5 hochwertigen Papers

**Tipp 2:** Nutze Scopus oder Web of Science (haben Citation-Graphs)

---

## 🆘 Troubleshooting

### Chrome startet nicht

```bash
# Kill existing Chrome
lsof -ti:9222 | xargs kill -9

# Neu starten
bash scripts/smart_chrome_setup.sh
```

### CDP Connection Error

```bash
# Teste CDP
curl http://localhost:9222/json/version

# Sollte Chrome-Version zeigen
# Falls nicht: Chrome neu starten
```

### Dialog startet nicht

```
# Stelle sicher, dass Chrome läuft
lsof -i:9222

# Falls nicht:
bash scripts/smart_chrome_setup.sh
```

### DBIS-Login funktioniert nicht

**Lösung:**
1. Öffne Chrome manuell: `open -a "Google Chrome" https://dbis.ur.de`
2. Logge dich mit Uni-Account ein
3. Zurück zum Chat, ENTER drücken

---

## 📚 Weitere Dokumentation

- **[README.md](README.md)**: Vollständige System-Übersicht
- **[agents/interactive_setup_agent.md](agents/interactive_setup_agent.md)**: Detaillierter Dialog-Flow
- **[ERROR_RECOVERY_GUIDE.md](ERROR_RECOVERY_GUIDE.md)**: Error Handling & Resume

---

## 🎉 Erfolgsmetriken

Nach der Recherche zeigt der Agent:

```
🎉 Recherche abgeschlossen!

Ergebnisse:
- 📊 8 Quellen gefunden
- 📄 12 Zitate extrahiert
- ⏱️ Dauer: 38 Min (geplant: 30-45 Min)

Files:
- Quote Library: projects/DevOps/outputs/Quote_Library.csv
- Bibliography: projects/DevOps/outputs/Annotated_Bibliography.md
- PDFs: projects/DevOps/pdfs/ (8 files)

Nächste Schritte:
1. Öffne Quote Library in Excel
2. Markiere relevante Zitate
3. Kopiere in deine Arbeit
```

---

## 🚀 Los geht's!

**3 Schritte:**

1. **Terminal:**
   ```bash
   bash scripts/smart_chrome_setup.sh
   ```

2. **VS Code:**
   ```bash
   code ~/AcademicAgent
   ```

3. **Claude Code Chat:**
   ```
   Start interactive research setup
   ```

**Das war's!** Der Agent führt dich durch den Rest. 🎉

---

**Happy Researching! 📚🤖**

*Version 2.1 - Interactive Mode*
