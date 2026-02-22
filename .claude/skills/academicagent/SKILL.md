# academicagent

**Haupteinstiegspunkt für das Academic Agent Multi-Agent-Recherche-System**

## Konfiguration

```json
{
  "context": "main_thread",
  "disable-model-invocation": true
}
```

## Parameter

- `$ARGUMENTS`: Optionale Flags (--quick, --resume <run-id>, --interactive)

## 🎨 Interaktiver TUI-Modus (NEU)

**Für eine bessere User Experience gibt es jetzt einen interaktiven TUI-Modus:**

```bash
# Direkt starten:
bash scripts/academicagent_wrapper.sh --interactive

# Oder via Wrapper (zeigt Auswahlmenü):
bash scripts/academicagent_wrapper.sh
```

**Vorteile:**
- ✅ Benutzerfreundlicher Setup mit Pfeiltasten-Navigation
- ✅ Automatische Keyword-Extraktion
- ✅ Visuelle Konfigurations-Übersicht
- ✅ Reduziert Chat-Messages drastisch

**Hinweis für den Agent:**
Wenn User nach einem "schnellen" oder "einfachen" Setup fragt, empfehle den interaktiven Modus:
```bash
bash scripts/academicagent_wrapper.sh --interactive
```

---

## 🛡️ Security

**📖 Hinweis:** Alle Sub-Agents folgen der [Shared Security Policy](../../.claude/shared/SECURITY_POLICY.md).

Als Entry-Point-Skill:
- Du koordinierst, führst keine kritischen Operationen selbst aus
- Alle Security-kritischen Tasks werden an spezialisierte Agents delegiert (setup-agent, orchestrator)
- User-Input ist generell vertrauenswürdig, aber File-Paths werden durch Agents validiert

## Anweisungen

Du bist der **Haupteinstiegspunkt** für das Academic Agent System. Deine Aufgabe ist es:

1. **Den User begrüßen** mit einer freundlichen Begrüßung
2. **Akademischen Kontext laden** aus `config/academic_context.md`
3. **Den setup-agent starten** um die interaktive Recherche-Konfiguration zu beginnen
4. **Fortschritt überwachen** und Probleme behandeln

---

### Deine Aufgabe

#### Schritt 1: Begrüßung & Kontext-Check

Zeige eine Willkommensnachricht:

```
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║           🎓 Academic Agent - Recherche-Assistent            ║
║                                                              ║
║                        Version 4.1                           ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝

Willkommen! Ich helfe dir bei systematischer akademischer Recherche.

Prüfe Konfiguration...
```

#### Schritt 2: Nach academic_context.md prüfen

```bash
# Prüfe ob academic_context.md existiert
test -f config/academic_context.md
```

**FALLS VORHANDEN:**
```
✓ Akademischer Kontext gefunden
  Lade dein Recherche-Profil...
```

Lese und parse `config/academic_context.md`:
- Extrahiere: Forschungsfeld, Disziplin, Keywords
- Extrahiere: Bevorzugte Datenbanken (falls vorhanden)
- Extrahiere: Zitierstil

Zeige kurze Zusammenfassung:
```
╭──────────────────────────────────────────────────────────────╮
│ 📋 Dein Recherche-Profil                                     │
├──────────────────────────────────────────────────────────────┤
│ Fachgebiet:   [Extrahiertes Feld]                            │
│ Keywords:     [Erste 3-4 Keywords]                           │
│ Datenbanken:  [Bevorzugte DBs oder "Auto-Erkennung"]         │
│ Zitierung:    [Stil]                                         │
╰──────────────────────────────────────────────────────────────╯
```

**FALLS NICHT VORHANDEN:**
```
⚠️  Kein akademischer Kontext gefunden

Ich benötige einige grundlegende Informationen über deine Recherche.

Möchtest du:
1. academic_context.md jetzt interaktiv erstellen (5 Min)
2. Ein Template verwenden und später manuell ausfüllen
3. Mit minimalem Setup fortfahren (zum Testen)
```

Warte auf User-Entscheidung.

**Bei Wahl 1:** Führe User durch Erstellung von `academic_context.md` (stelle 5-7 essentielle Fragen)
**Bei Wahl 2:** Kopiere Template und zeige Pfad
**Bei Wahl 3:** Erstelle minimalen temporären Kontext

#### Schritt 2.5: Browser-Verfügbarkeit sicherstellen (CRITICAL)

**WICHTIG:** Vor dem Start der Recherche muss Chrome mit CDP verfügbar sein!

```bash
# Prüfe ob Chrome mit CDP läuft
bash scripts/cdp_health_check.sh check

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
  echo "✅ Chrome CDP bereit auf Port 9222"
else
  echo "❌ Chrome CDP nicht verfügbar"
  echo ""
  echo "Starte Chrome automatisch..."

  # Auto-Start Chrome
  bash scripts/start_chrome_debug.sh

  # Warte 3 Sekunden
  sleep 3

  # Verifiziere
  bash scripts/cdp_health_check.sh check

  if [ $? -eq 0 ]; then
    echo "✅ Chrome erfolgreich gestartet"
  else
    echo "❌ Chrome konnte nicht gestartet werden"
    echo ""
    echo "Manuelle Schritte:"
    echo "  1. Starte Chrome: bash scripts/start_chrome_debug.sh"
    echo "  2. Verifiziere: curl http://localhost:9222/json/version"
    echo "  3. Starte /academicagent erneut"
    exit 1
  fi
fi
```

**Browser-Status:**
```
✅ Chrome CDP bereit
   Port: 9222
   Version: Chrome/131.0.6778.86

Fahre fort mit Setup...
```

#### Schritt 2.6: Permission & Workflow-Info (WICHTIG)

**WICHTIG:** Informiere den User über den bevorstehenden Workflow:

```
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║              🔒 WORKFLOW-INFORMATIONEN                       ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝

Dieser Workflow nutzt mehrere spezialisierte Sub-Agents:

  • setup-agent      - Interaktive Recherche-Konfiguration
  • orchestrator     - Koordination aller Phasen
  • browser-agent    - Automatisierte Datenbanksuche
  • scoring-agent    - Paper-Ranking
  • extraction-agent - Zitat-Extraktion

⚠️  WICHTIG:
    • Browser-Agent kann während der Suche Login-Prompts
      für DBIS/Datenbanken zeigen - halte Uni-Zugangsdaten bereit.
    • Die Run-Struktur wird automatisch erstellt, um
      Permission-Prompts zu minimieren.
    • Alle Agents arbeiten im runs/ Verzeichnis.

✓ Bereit zum Start

```

**Hinweis:** Die vollständige Run-Struktur wird vom setup-agent automatisch erstellt.

#### Schritt 2.7: Session-Wide Permission Request (KRITISCH)

**WICHTIG:** Frage User EINMALIG um Genehmigung für alle Sub-Agent-Operations:

Verwende das AskUserQuestion-Tool:

```
AskUserQuestion(
  questions=[{
    "question": "Dieser Workflow spawnt mehrere Sub-Agents (setup, orchestrator, browser, scoring, extraction). Alle Sub-Agents automatisch genehmigen?",
    "header": "Permissions",
    "multiSelect": false,
    "options": [
      {
        "label": "Ja - Alle Sub-Agents auto-genehmigen (Empfohlen)",
        "description": "Reduziert Permission-Prompts drastisch. Sub-Agents arbeiten nur im runs/ Verzeichnis und sind durch Auto-Permission-System geschützt."
      },
      {
        "label": "Nein - Jeden Agent einzeln bestätigen",
        "description": "Du wirst bei jedem Agent-Spawn gefragt. Empfohlen nur für Tests oder wenn du jeden Schritt kontrollieren möchtest."
      }
    ]
  }]
)
```

**Verarbeite Antwort:**

```python
# Wenn User "Ja" gewählt hat:
if answer == "Ja - Alle Sub-Agents auto-genehmigen (Empfohlen)":
    export CLAUDE_SESSION_AUTO_APPROVE_AGENTS=true
    export ACADEMIC_AGENT_BATCH_MODE=true

    echo "✅ Session-Permission aktiviert"
    echo "   → Sub-Agents werden automatisch genehmigt"
    echo "   → Nur File-Operations außerhalb runs/ erfordern Bestätigung"
    echo ""

# Wenn User "Nein" gewählt hat:
else:
    echo "ℹ️  Interaktiver Modus aktiv"
    echo "   → Du wirst bei jedem Agent-Spawn gefragt"
    echo "   → Erwarte 3-5 Permission-Prompts während der Recherche"
    echo ""
```

**Environment-Variablen für spätere Agents:**

Diese Variablen werden an alle Sub-Agents weitergegeben:
- `CLAUDE_SESSION_AUTO_APPROVE_AGENTS=true` - Signalisiert Auto-Approve-Modus
- `ACADEMIC_AGENT_BATCH_MODE=true` - Aktiviert Batch-Verarbeitung ohne zusätzliche Prompts

**Hinweis:** Selbst im Auto-Approve-Modus sind kritische Operations geschützt:
- Kein Zugriff auf `.env`, `~/.ssh/`, `secrets/`
- Kein Write außerhalb `runs/` ohne explizite Bestätigung
- Gefährliche Bash-Commands (rm -rf, sudo) erfordern Bestätigung

#### Schritt 3: Setup-Agent starten

```
✓ Kontext erfolgreich geladen

Starte interaktives Setup...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Delegiere an setup-agent:**

```bash
# Verwende Task-Tool um setup-agent zu starten
Task(
  subagent_type="setup-agent",
  description="Interaktives Recherche-Setup",
  prompt="Starte interaktiven Dialog für neuen Recherche-Run.

  Akademischer Kontext ist verfügbar unter: config/academic_context.md

  Deine Aufgaben:
  1. Lade und verstehe den akademischen Kontext
  2. Erkenne relevante Datenbanken basierend auf Disziplin
  3. Führe User durch run-spezifische Fragen:
     - Was ist das Ziel für DIESEN Run?
     - Wie viele Zitationen werden benötigt?
     - Spezifische Keywords für diesen Run?
     - Such-Intensitätslevel?
     - Zeitraum?
  4. Generiere run_config.json mit iterativer Suchstrategie
  5. Übergabe an Orchestrator

  Verwende den neuen iterativen Datenbanksuche-Ansatz:
  - Starte mit Top 5 Datenbanken
  - Erweitere automatisch bei Bedarf
  - Stoppe früh wenn Ziel erreicht oder 2 leere Iterationen

  Sei konversationell und hilfsbereit!"
)
```

#### Schritt 4: Überwache & Behandle Ergebnisse

Nachdem setup-agent fertig ist, wird er entweder:

**A) Erfolg - Konfig erstellt:**
```
✓ Recherche-Konfiguration abgeschlossen!

  Run ID: 2026-02-17_14-30-00
  Konfig: runs/2026-02-17_14-30-00/run_config.json

  Starte Recherche-Orchestrator...
```

Delegiere an Orchestrator (siehe nächster Schritt)

**B) User hat abgebrochen:**
```
Recherche-Setup vom User abgebrochen.

Möchtest du:
1. Von vorne beginnen
2. Einen vorherigen Run fortsetzen
3. Beenden
```

**C) Fehler:**
```
⚠️  Setup hat ein Problem festgestellt: [Fehlermeldung]

Fehlerbehebung:
[Vorschläge basierend auf Fehler]

Erneut versuchen? (Ja/Nein)
```

#### Schritt 5: Übergabe an Orchestrator (mit Live-Status-Monitoring)

Falls Konfig erfolgreich erstellt wurde:

**OPTIONAL: tmux Live-Monitoring Setup**

Frage User ob Live-Monitoring gewünscht ist:

```
╭───────────────────────────────────────────────────────────╮
│ 💡 Live-Status-Monitoring verfügbar!                      │
├───────────────────────────────────────────────────────────┤
│ Du kannst den Recherche-Fortschritt in Echtzeit           │
│ verfolgen mit einem Split-Screen-Dashboard.               │
│                                                           │
│ Features:                                                 │
│  ✓ Echtzeit Phase-Updates                                 │
│  ✓ Iterations-Tracking (Phase 2)                          │
│  ✓ Budget-Monitoring                                      │
│  ✓ Live-Logs                                              │
│  ✓ Progress-Bars                                          │
│                                                           │
│ Möchtest du das Live-Dashboard aktivieren?                │
│  1) Ja - Starte mit tmux Split-Screen (empfohlen)         │
│  2) Nein - Normale Ausführung ohne Live-Monitoring        │
╰───────────────────────────────────────────────────────────╯

Deine Wahl [1-2]:
```

**WENN User "Ja" wählt (Option 1):**

```bash
# Prüfe ob tmux verfügbar ist
if ! command -v tmux &> /dev/null; then
    echo "⚠️  tmux nicht installiert. Installiere mit:"
    echo "   macOS: brew install tmux"
    echo "   Ubuntu/Debian: apt install tmux"
    echo ""
    echo "Fahre mit normaler Ausführung fort..."
    TMUX_AVAILABLE=false
else
    TMUX_AVAILABLE=true
fi

if [ "$TMUX_AVAILABLE" = true ] && [ -z "$TMUX" ]; then
    echo "🖥️  Starte tmux für Live-Status-Monitoring..."

    RUN_ID="[run-id vom Setup]"
    SESSION_NAME="academic_${RUN_ID//[^a-zA-Z0-9]/_}"  # Sanitize für tmux

    # Erstelle tmux Session mit Split-Screen
    tmux new-session -d -s "$SESSION_NAME"

    # Split vertical (50:50)
    tmux split-window -h -t "$SESSION_NAME"

    # Links: Orchestrator-Agent (Main Process)
    tmux send-keys -t "$SESSION_NAME:0.0" \
        "cd $(pwd) && echo 'Starte Orchestrator-Agent...' && sleep 2" C-m

    # Rechts: Status Watcher
    tmux send-keys -t "$SESSION_NAME:0.1" \
        "cd $(pwd) && bash scripts/status_watcher.sh $RUN_ID" C-m

    # Setze Pane-Titel (optional, wenn tmux-Versionen es unterstützen)
    tmux select-pane -t "$SESSION_NAME:0.0" -T "Orchestrator"
    tmux select-pane -t "$SESSION_NAME:0.1" -T "Live Status"

    # Attach zur Session
    echo "✅ tmux Session erstellt: $SESSION_NAME"
    echo "   Linkes Panel: Orchestrator-Agent"
    echo "   Rechtes Panel: Live-Status-Dashboard"
    echo ""
    echo "Hinweis: Zum Beenden: Strg+B, dann 'X' drücken"
    echo ""

    # Attach (blockiert bis Session beendet wird)
    tmux attach -t "$SESSION_NAME"

    # Nach detach: Cleanup
    echo "🧹 Räume tmux Session auf..."
    tmux kill-session -t "$SESSION_NAME" 2>/dev/null

    exit 0
fi
```

**WENN User "Nein" wählt ODER tmux nicht verfügbar:**

Informiere User über alternative Monitoring-Option:

```
ℹ️  Alternative: Öffne ein zweites Terminal und führe aus:
   python3 scripts/live_monitor.py runs/[run-id]

   Oder: Manuelles Tail auf State-File:
   watch -n 3 'jq . runs/[run-id]/metadata/research_state.json'

Fahre fort mit normaler Ausführung...
```

**Starte Orchestrator-Agent:**

```bash
# Starte Orchestrator-Agent mit der generierten Konfig
Task(
  subagent_type="orchestrator-agent",
  description="Recherche-Pipeline ausführen",
  prompt="Führe die vollständige Recherche-Pipeline aus.

  Run ID: [run-id vom Setup]
  Konfig: runs/[run-id]/run_config.json

  Verwende die iterative Datenbanksuche-Strategie aus der Konfig.

  WICHTIG - Live-Status-Updates:
  - Schreibe research_state.json NACH JEDER PHASE
  - Schreibe research_state.json NACH JEDER ITERATION (Phase 2)
  - Update phase_2_state für Iterations-Tracking
  - Update budget_tracking nach jedem Agent-Spawn

  Phasenablauf:
  1. Datenbank-Identifikation (oder überspringe falls bereits ausgewählt)
  2. Suchstring-Generierung
  3. Iterative Datenbanksuche (NEU: adaptive 5-DB-Iterationen)
  4. Screening & Ranking
  5. PDF-Download
  6. Zitat-Extraktion
  7. Finalisierung

  Wichtig:
  - Chrome läuft bereits (falls Setup es gestartet hat)
  - Verwende run_config.json als Wahrheitsquelle
  - Implementiere iterative Suche mit vorzeitiger Terminierung
  - Speichere State nach jeder Iteration
  - Behandle Terminierungsbedingungen (Erfolg, vorzeitiger Stopp, erschöpft)
  "
)
```

#### Schritt 6: Finale Zusammenfassung

Nachdem Orchestrator fertig ist:

```
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║              ✓ RECHERCHE ABGESCHLOSSEN!                      ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝

╭──────────────────────────────────────────────────────────────╮
│ 📊 Ergebnis-Zusammenfassung                                  │
├──────────────────────────────────────────────────────────────┤
│ Quellen gefunden:    [X]                                     │
│ Zitate extrahiert:   [Y]                                     │
│ Gesamtdauer:         [Z] Minuten                             │
│                                                              │
│ Iterationen:         [N]                                     │
│ Verwendete DBs:      [Liste]                                 │
│ Top Performer:       [Top 3 DBs mit Anzahlen]                │
╰──────────────────────────────────────────────────────────────╯

📁 Deine Dateien sind bereit:

   📄 Zitatbibliothek:         runs/[run-id]/outputs/quote_library.json
   📚 Annotierte Bibliographie: runs/[run-id]/outputs/Annotated_Bibliography.md
   📚 BibTeX-Bibliographie:     runs/[run-id]/outputs/bibliography.bib
   📊 Such-Report:             runs/[run-id]/outputs/search_report.md
   📁 PDFs:                    runs/[run-id]/downloads/

Nächste Schritte:
1. Öffne quote_library.json um deine Zitate zu prüfen
2. Importiere bibliography.bib in dein LaTeX/Word-Dokument
3. Prüfe search_report.md für Einblicke

Möchtest du:
1. Eine weitere Recherche starten
2. Diese Recherche erweitern (mehr Quellen)
3. Detaillierten Report ansehen
4. Beenden
```

---

### Spezielle Flags

#### `--quick` oder `--fast`

```bash
/academicagent --quick
```

Verwendet "Schneller Zitat-Modus":
- 5-8 Quellen statt 18-27
- 2-3 Datenbanken
- ~30-45 Min
- Einzelne Iteration erwartet

#### `--resume <run-id>`

```bash
/academicagent --resume 2026-02-17_14-30-00
```

Setze unterbrochene Recherche fort:
1. Lade vorhandene run_config.json
2. Prüfe research_state.json
3. Validiere State
4. Setze von letzter abgeschlossener Phase fort
5. Überspringe setup-agent, gehe direkt zum Orchestrator

---

### Fehlerbehandlung

**Chrome läuft nicht:**
```
⚠️  Chrome mit Remote-Debugging nicht erkannt

Starte Chrome automatisch...
[Führe start_chrome_debug.sh aus]

✓ Chrome bereit auf Port 9222
```

**DBIS-Login erforderlich:**
```
⚠️  DBIS erfordert Authentifizierung

Bitte:
1. Wechsle zum Chrome-Fenster
2. Logge dich mit deinen Uni-Zugangsdaten ein
3. Drücke ENTER wenn fertig

[Warte auf User]

✓ Fahre fort...
```

**Konfig-Validierung fehlgeschlagen:**
```
⚠️  Konfigurationsfehler: [Details]

[Zeige welches Feld ungültig ist]

Optionen:
1. Automatisch korrigieren (empfohlen)
2. Manuell bearbeiten
3. Von vorne beginnen
```

---

### Integration mit bestehendem System

Dieser Skill ersetzt den vorherigen Workflow:

**Alt:** `/setup` → generiert Konfig → `/orchestrator` mit Konfig

**Neu:** `/academicagent` → setup-agent (generiert run_config.json) → orchestrator (iterative Ausführung)

**Vorteile:**
- Einzelner Einstiegspunkt ✓
- Integrierte Fehlerbehandlung ✓
- Bessere UX mit Fortschrittsverfolgung ✓
- Automatisches Kontext-Laden ✓
- Iterative Datenbanksuche ✓

---

### Wichtige Hinweise

- Du läufst im **Main-Thread** - verwende Task() für Delegation
- Setup-agent und Orchestrator sind **autonom** - sie kehren zurück wenn fertig
- Du bist der **Koordinator** - behandle High-Level-Flow und Fehler
- Zeige immer **Fortschritt** und **Status** dem User
- Sei **freundlich** und **hilfsbereit** in allen Nachrichten
- Verwende **Boxen und Formatierung** für bessere Terminal-UX

---

### Beispiel-Flow

```
User: /academicagent

Du: [Willkommensnachricht]
Du: [Lade academic_context.md]
Du: [Zeige Profil-Zusammenfassung]
Du: [Starte setup-agent mit Task()]

     [Setup-agent läuft interaktiv...]
     [Generiert run_config.json]
     [Gibt Erfolg zurück]

Du: [Zeige Konfig-Zusammenfassung]
Du: [Starte orchestrator mit Task()]

     [Orchestrator läuft Phasen...]
     [Iterative DB-Suche...]
     [Gibt Ergebnisse zurück]

Du: [Zeige finale Zusammenfassung]
Du: [Biete nächste Schritte an]
```

---

**Ende des academicagent Skills**
