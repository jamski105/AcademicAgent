# 🐛 Academic Agent - Problem-Tracking & Fix-Prompts

> **Format**: Jedes Problem enthält eine Beschreibung, Status und einen Fix-Prompt
>
> **WICHTIG**: Die Status-Übersicht befindet sich immer **ganz unten** in diesem Dokument und muss bei Änderungen aktualisiert werden!

---

## 📋 TODO-Liste

### 1. Setup-Agent bleibt stehen ❌

**Status**: Offen
**Priorität**: Hoch
**Betroffene Komponente**: `setup-agent`, `/academicagent` Skill

**Problem-Beschreibung**:
Der Setup-Agent startet erfolgreich, bleibt dann aber stehen ohne weitere Interaktion. Der Agent spawnt, zeigt "Done (2 tool uses · 11.4k tokens · 1m 29s)", aber wartet dann auf User-Input ohne dass klar ist, wo/wie dieser gegeben werden soll.

**Symptome**:
```
⏺ setup-agent(Interaktives Recherche-Setup)
  ⎿  Done (2 tool uses · 11.4k tokens · 1m 29s)

⏺ Der Setup-Agent hat erfolgreich gestartet und führt dich nun durch die interaktive Konfiguration.
  Nächster Schritt: Beantworte die Frage des Setup-Agents zu deiner konkreten Forschungsfrage...
```

**Root Cause**:
- Setup-Agent sollte eigentlich AskUserQuestion verwenden, um Fragen zu stellen
- Stattdessen "Done" ohne sichtbare Fragen
- Kommunikation zwischen Main Thread und Sub-Agent funktioniert nicht richtig

**Fix-Prompt**:
```
Problem: Der setup-agent im /academicagent Skill bleibt nach dem Spawn stehen und zeigt nur "Done", ohne die interaktiven Fragen zu stellen.

Aufgabe:
1. Öffne agents/setup_agent.py
2. Analysiere, warum der Agent keine AskUserQuestion-Calls macht oder diese nicht sichtbar sind
3. Stelle sicher, dass der Agent die Fragen korrekt an den User weiterleitet
4. Teste, ob die Fragen im Main Thread ankommen und angezeigt werden

Mögliche Ursachen:
- Agent verwendet print() statt AskUserQuestion
- Agent-Output wird nicht korrekt zurückgegeben
- Der Agent terminiert zu früh

Bitte behebe das Problem so, dass die interaktiven Fragen beim User ankommen.
```

---

### 2. TUI startet nicht automatisch / funktioniert nicht in Claude Code ❌

**Status**: Offen
**Priorität**: Mittel
**Betroffene Komponente**: `scripts/academicagent_wrapper.sh`, TUI-Modus

**Problem-Beschreibung**:
Der TUI-Modus (Terminal User Interface) kann nicht in Claude Code ausgeführt werden. Der Wrapper erkennt questionary als nicht installiert (obwohl Installation erfolgreich), und TUI-basierte interaktive Eingaben funktionieren grundsätzlich nicht in Claude Code's eingebettetem Terminal.

**Symptome**:
```bash
❌ TUI-Modus kann nicht in Claude Code ausgeführ werden
Error: Exit code 1

\033[1;33m⚠️   questionary nicht installiert\033[0m
```

**Root Cause**:
1. TUI benötigt echtes TTY (Terminal)
2. Claude Code's embedded terminal unterstützt keine interaktiven TUI-Prompts (questionary/prompt_toolkit)
3. Wrapper-Script versucht trotzdem, TUI zu starten

**Fix-Prompt**:
```
Problem: Der TUI-Modus im academicagent_wrapper.sh kann nicht in Claude Code gestartet werden und gibt irreführende Fehlermeldungen.

Aufgabe:
1. Öffne scripts/academicagent_wrapper.sh
2. Füge eine Erkennung hinzu, ob das Script in einem echten Terminal (TTY) oder in Claude Code läuft
3. Wenn kein TTY verfügbar ist:
   - Zeige klare Warnung: "TUI-Modus erfordert echtes Terminal. Bitte außerhalb von Claude Code ausführen."
   - Biete Fallback an: Chat-basiertes Setup verwenden
4. Verhindere den Versuch, questionary zu installieren, wenn ohnehin kein TTY verfügbar ist

Test:
- Führe Script in Claude Code aus → sollte klare Warnung zeigen
- Führe Script in echtem Terminal aus → sollte TUI korrekt starten

Bitte implementiere die TTY-Erkennung und sinnvolle Fallbacks.
```

---

### 3. Optionen werden nicht/unvollständig angezeigt im Chat ❌

**Status**: Offen
**Priorität**: Hoch
**Betroffene Komponente**: `setup-agent`, AskUserQuestion-Integration

**Problem-Beschreibung**:
Wenn der Setup-Agent im Chat-Modus läuft, werden die Auswahloptionen für Forschungsfrage, Recherche-Modus etc. nicht oder nur unvollständig angezeigt. Der User sieht nur Text wie "Welche Forschungsfrage möchtest du verwenden?" aber keine konkreten Optionen zur Auswahl.

**Symptome**:
```
⏺ Der Setup-Agent wartet jetzt auf deine Antwort.
  Welche Forschungsfrage möchtest du verwenden?
  Du kannst einfach die Nummer (1, 2 oder 3) schreiben...

  [Aber Optionen 1, 2, 3 werden nie gezeigt]
```

**Root Cause**:
- Setup-Agent gibt Optionen zurück, aber diese werden nicht an AskUserQuestion weitergeleitet
- Oder: Agent-Output wird nicht korrekt geparsed im Main Thread
- AskUserQuestion-Tool wird vom Sub-Agent nicht richtig verwendet

**Fix-Prompt**:
```
Problem: Der setup-agent zeigt im Chat-Modus die Auswahloptionen nicht an. User sieht Fragen, aber keine konkreten Antwortmöglichkeiten.

Aufgabe:
1. Öffne agents/setup_agent.py
2. Stelle sicher, dass der Agent AskUserQuestion korrekt verwendet mit options-Array
3. Prüfe, ob die Agent-Response korrekt formatiert ist
4. Teste, ob die Optionen im Main Thread ankommen und als Auswahl angezeigt werden

Beispiel für korrektes AskUserQuestion:
{
  "questions": [{
    "question": "Welche Forschungsfrage möchtest du verwenden?",
    "header": "Frage",
    "options": [
      {"label": "Option 1: ...", "description": "Beschreibung"},
      {"label": "Option 2: ...", "description": "Beschreibung"}
    ],
    "multiSelect": false
  }]
}

Bitte stelle sicher, dass der setup-agent AskUserQuestion mit vollständigen options verwendet, nicht nur print().
```

---

### 4. Agent-Verschachtelungsproblem (zu viele Ebenen) ❌

**Status**: Offen
**Priorität**: Kritisch
**Betroffene Komponente**: `/academicagent` Skill, `orchestrator-agent`, Agent-Architektur

**Problem-Beschreibung**:
Die aktuelle Architektur spawnt zu viele verschachtelte Agent-Ebenen:
- Ebene 1: Claude Code
- Ebene 2: /academicagent Skill
- Ebene 3: setup-agent (via Task tool)
- Ebene 4: orchestrator-agent (via Task tool)
- Ebene 5: ❌ browser-agent, scoring-agent, extraction-agent (können nicht mehr gespawnt werden)

**Fehlermeldung**:
```
Error: nested sessions are not supported
Orchestrator-Agent kann keine weiteren Sub-Agents spawnen
```

**Root Cause**:
- Claude Code hat Limits für Agent-Verschachtelungstiefe
- Orchestrator sitzt zu tief in der Hierarchie (Ebene 4)
- Kann daher keine weiteren Task()-Calls für browser/scoring/extraction machen

**Fix-Prompt**:
```
Problem: Die Agent-Hierarchie im /academicagent Skill ist zu tief verschachtelt. Der orchestrator-agent kann keine Sub-Agents (browser, scoring, extraction) mehr spawnen.

Aufgabe - Architektur-Refactoring:
1. Öffne skills/academicagent/academicagent.prompt.md
2. Ändere die Architektur wie folgt:

VORHER (funktioniert nicht):
/academicagent → setup-agent (Task) → orchestrator-agent (Task) → ❌ weitere Agents

NACHHER (soll funktionieren):
/academicagent → orchestrator-agent (Task direkt) → browser/scoring/extraction (Task)

3. Konkrete Änderungen:
   - Entferne setup-agent als separaten Task-Spawn
   - Integriere Setup-Logik direkt in /academicagent Main Thread (mit AskUserQuestion)
   - Spawne orchestrator-agent direkt von /academicagent (Ebene 2 statt Ebene 4)
   - Orchestrator kann dann problemlos seine Sub-Agents spawnen (Ebene 3)

4. Setup-Flow vereinfachen:
   - /academicagent fragt User-Fragen direkt mit AskUserQuestion
   - Generiert run_config.json selbst
   - Spawnt dann orchestrator mit fertiger Config

Bitte refactore die Architektur, um eine Verschachtelungsebene einzusparen.
```

---

### 5. orchestrator-agent hängt bei "Verarbeite Inputs..." ⏳

**Status**: Offen
**Priorität**: Hoch
**Betroffene Komponente**: `orchestrator-agent`

**Problem-Beschreibung**:
Der orchestrator-agent spawnt erfolgreich, zeigt dann aber nur "Verarbeite Inputs..." und terminiert nicht bzw. läuft endlos.

**Symptome**:
```
⏺ orchestrator-agent(Starte 7-Phasen Workflow)
  ⎿  Running (45s elapsed)
  Verarbeite Inputs...
  [Agent hängt hier]
```

**Root Cause**:
- Vermutlich Endlos-Schleife oder blockierender Call
- Agent wartet auf Input, der nie kommt
- Oder: Verschachtelungsproblem verhindert weitere Tool-Calls

**Fix-Prompt**:
```
Problem: Der orchestrator-agent startet, zeigt "Verarbeite Inputs..." und hängt dann ohne weiteren Output.

Aufgabe:
1. Öffne agents/orchestrator_agent.py
2. Analysiere die Startup-Logik:
   - Was macht der Agent beim "Verarbeite Inputs..."?
   - Gibt es blockierende Calls?
   - Wartet er auf externen Input?
3. Füge Debug-Logging hinzu, um zu sehen wo der Agent hängt
4. Stelle sicher, dass der Agent entweder:
   - Erfolgreich die Sub-Agents spawnt
   - Oder: Fehler klar zurückgibt

Teste mit:
- Vereinfachter Test-Config (nur 1 Quelle, Quick-Modus)
- Prüfe, ob Agent bis zum browser-agent-Spawn kommt

Bitte behebe das Hängen-Problem im Orchestrator.
```

---

### 6. Live Monitor - Automatisches Chrome-Fenster statt Terminal-Befehl ❌

**Status**: Offen
**Priorität**: Mittel
**Betroffene Komponente**: Live Monitor, `scripts/live_monitor.py`, Orchestrator

**Problem-Beschreibung**:
Der aktuelle Live Monitor erfordert, dass der User einen Terminal-Befehl kopiert und manuell in einem neuen Terminal-Fenster ausführt. Dies ist umständlich und nicht benutzerfreundlich.

**Aktuelles Verhalten**:
```
⏺ Live Monitor verfügbar
  Kopiere folgenden Befehl und führe ihn in einem neuen Terminal aus:
  python scripts/live_monitor.py --run-id=run_xyz
```

**Gewünschtes Verhalten**:
- Chrome-Fenster öffnet sich automatisch
- Live Monitor wird direkt im Browser angezeigt
- Keine manuelle Kopier-/Terminal-Aktion nötig
- Automatische Integration in den Workflow

**Root Cause**:
- Live Monitor läuft als separater Python-Prozess
- Keine automatische Browser-Integration
- User muss manuell Terminal-Befehle ausführen

**Fix-Prompt**:
```
Problem: Der Live Monitor erfordert manuelles Kopieren und Ausführen eines Terminal-Befehls. Dies soll automatisiert werden - stattdessen soll sich ein Chrome-Fenster automatisch öffnen.

Aufgabe - Live Monitor Automatisierung:

1. Analysiere die aktuelle Live-Monitor-Implementierung:
   - Öffne scripts/live_monitor.py
   - Verstehe, wie der Monitor aktuell gestartet wird
   - Prüfe, wo im Orchestrator der Monitor-Befehl ausgegeben wird

2. Implementiere automatisches Browser-Opening:
   - Live Monitor soll automatisch im Hintergrund starten
   - Verwende Python's webbrowser.open() oder subprocess für Chrome
   - Chrome-Fenster soll sich automatisch mit der Monitor-URL öffnen

3. Entferne die manuelle Kopier-Anweisung:
   - Lösche Output wie "Kopiere folgenden Befehl..."
   - Zeige stattdessen: "✅ Live Monitor geöffnet in Chrome"

4. Browser-Integration:
   - Live Monitor soll einen lokalen HTTP-Server starten (z.B. Port 8000)
   - Server läuft im Hintergrund (subprocess/daemon)
   - Chrome öffnet automatisch `http://localhost:8000?run_id=xyz`
   - Optional: CDP-Chrome verwenden (bereits läuft auf Port 9222)

5. Cleanup-Handling:
   - Server soll beim Workflow-Ende automatisch stoppen
   - Oder: Server läuft weiter, aber nur für aktiven Run

Technische Ansätze:
Option A: Separater HTTP-Server (Flask/SimpleHTTPServer)
Option B: CDP-Chrome Tab öffnen und HTML rendern
Option C: Datei-basiert (HTML schreiben + file:// URL öffnen)

Bitte implementiere die automatische Browser-Integration für den Live Monitor.
```

---

### 7. Agent & Skill Prompt-Qualität Validierung ✅

**Status**: ✅ Gelöst (2026-02-23)
**Priorität**: Mittel
**Betroffene Komponente**: Alle Agents & Skills (setup, orchestrator, browser, scoring, extraction, /academicagent)

**Problem-Beschreibung**:
Es existiert keine systematische Bewertung der Prompt-Qualität für alle Agents und Skills. Unklar ist, welche Prompts gut strukturiert sind und welche umstrukturiert werden sollten.

**Ziel**:
Eine Bewertungsmatrix (Skala 0-10) für alle Agents und Skills erstellen:
- **0** = Perfekt, keine Änderung nötig
- **10** = Sofort umstrukturieren/ändern
- **5** = Mittlerer Handlungsbedarf

Bewertung soll umfassen:
- setup-agent.py
- orchestrator-agent.py
- browser-agent.py
- scoring-agent.py
- extraction-agent.py
- /academicagent Skill
- academicagent_wrapper.sh

Für jeden Score: Begründung, warum dieser Wert vergeben wurde.

**Fix-Prompt**:
```
Problem: Keine systematische Bewertung der Prompt-Qualität für Agents und Skills vorhanden.

Aufgabe - Prompt-Qualität Validierung & Bewertung:

1. Erstelle eine Bewertungsmatrix (0-10 Skala) für folgende Komponenten:
   - setup-agent
   - orchestrator-agent
   - browser-agent
   - scoring-agent
   - extraction-agent
   - /academicagent Skill (skills/academicagent/academicagent.prompt.md)
   - academicagent_wrapper.sh

2. Bewertungsskala:
   - 0 = Perfekt, keine Änderung nötig
   - 10 = Sofort umstrukturieren/ändern
   - 5 = Mittlerer Handlungsbedarf

3. Für jeden Score bitte angeben:
   - Status-Emoji (🟢 = 0-3, 🟡 = 4-5, 🟠 = 6-7, 🔴 = 8-10)
   - Begründung (Was ist gut? Was ist schlecht?)
   - Konkrete Änderungsempfehlung (falls Score > 2)

4. Erstelle eine Tabellen-Matrix mit:
   - Komponente | Score | Status | Begründung | Änderungsempfehlung

5. Füge eine Ziel-Analyse hinzu:
   - Wie würde der Score nach Refactoring aussehen?
   - Was ist der Gesamt-Impact (Durchschnitt vorher/nachher)?

Bitte analysiere alle Prompt-Dateien und erstelle die vollständige Bewertungsmatrix.
```

**Lösung (2026-02-23)**:
✅ Vollständige Bewertungsmatrix erstellt in: `PROMPT_QUALITY_ASSESSMENT.md`
- Alle 7 Komponenten systematisch validiert
- Scores von 1-7/10 vergeben (Durchschnitt: 3.3/10)
- Detaillierte Analysen mit Refactoring-Empfehlungen
- Validierungs-Report bestätigt Assessments
- Hauptprobleme: orchestrator-agent (7/10), browser-agent (4/10), academicagent Skill (5/10)

**Ergebnis**:
- scoring-agent.md: Beste Datei (1/10) 🟢
- Refactoring-Aufwand: 3-4 Wochen @ 20h/Woche
- Quick Win: orchestrator-agent Refactoring = 50% Impact

---

## 📊 Status-Übersicht

| Problem | Status | Priorität | Komponente |
|---------|--------|-----------|------------|
| #1: Setup-Agent bleibt stehen | ❌ Offen | Hoch | setup-agent |
| #2: TUI startet nicht in Claude Code | ❌ Offen | Mittel | wrapper script |
| #3: Optionen nicht angezeigt | ❌ Offen | Hoch | setup-agent |
| #4: Agent-Verschachtelung | ❌ Offen | **Kritisch** | Architektur |
| #5: Orchestrator hängt | ❌ Offen | Hoch | orchestrator-agent |
| #6: Live Monitor Auto-Chrome | ❌ Offen | Mittel | live_monitor.py |
| #7: Prompt-Qualität Validierung | ✅ Gelöst | Mittel | Alle Agents/Skills |

**Gesamt**: 7 Probleme | 1 Gelöst | 6 Offen

---

## 🎯 Empfohlene Fix-Reihenfolge

1. **Kritisch - Problem #4**: Agent-Verschachtelung beheben (Architektur-Refactoring)
   - Blockt alle anderen Features
   - Orchestrator muss Sub-Agents spawnen können

2. **Hoch - Problem #1**: Setup-Agent Interaction fixen
   - Nach Architektur-Fix: Setup in Main Thread integrieren
   - AskUserQuestion korrekt verwenden

3. **Hoch - Problem #3**: Optionen-Anzeige fixen
   - Sollte durch #1 gelöst werden
   - Falls nicht: Separater Fix nötig

4. **Hoch - Problem #5**: Orchestrator-Hängen beheben
   - Nach #4: Sollte durch reduzierte Verschachtelung gelöst sein
   - Falls nicht: Debug-Logging hinzufügen

5. **Mittel - Problem #6**: Live Monitor Auto-Chrome
   - UX-Verbesserung, nicht kritisch
   - Nach Core-Fixes implementieren

6. **Mittel - Problem #2**: TUI-TTY-Erkennung
   - Nice-to-have für bessere UX
   - Nicht kritisch für Core-Funktionalität

7. **Mittel - Problem #7**: Prompt-Qualität Validierung
   - Kann parallel zu anderen Fixes laufen
   - Hilft bei langfristiger Code-Qualität

---

## ➕ Neue Probleme hinzufügen

**Format für neue Probleme**:

```markdown
### X. [Kurzer Titel] ❌

**Status**: Offen / In Bearbeitung / Gelöst
**Priorität**: Niedrig / Mittel / Hoch / Kritisch
**Betroffene Komponente**: [Datei/Agent/Script]

**Problem-Beschreibung**:
[Detaillierte Beschreibung des Problems]

**Symptome**:
```
[Fehlermeldungen, Logs, Output-Beispiele]
```

**Root Cause**:
[Vermutete Ursache / Analyse]

**Fix-Prompt**:
```
Problem: [Knappe Zusammenfassung]

Aufgabe:
1. [Schritt 1]
2. [Schritt 2]
...

Bitte behebe das Problem.
```
```

---

**Letzte Aktualisierung**: 2026-02-23 - Problem #7 gelöst (Prompt-Qualität Validierung abgeschlossen)
