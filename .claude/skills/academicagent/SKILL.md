# academicagent

**Haupteinstiegspunkt für das Academic Agent Multi-Agent-Recherche-System**
**Version:** 2.0.0 (Refactored 2026-02-23)

## Konfiguration

```json
{
  "context": "main_thread",
  "disable-model-invocation": true
}
```

## Parameter

- `$ARGUMENTS`: Optionale Flags (--quick, --resume <run-id>, --interactive)

---

## 🎨 Interaktiver TUI-Modus (Empfohlen!)

**Für bessere UX:**

```bash
bash scripts/academicagent_wrapper.sh --interactive
```

**Vorteile:** Benutzerfreundlicher Setup, automatische Keyword-Extraktion, reduziert Chat-Messages.

**Hinweis:** Wenn User nach "schnellem Setup" fragt, empfehle interaktiven Modus!

---

## 📊 WORKFLOW-ÜBERSICHT

```
╭──────────────────────────────────────────────────────────────╮
│ 📊 7-PHASEN RECHERCHE-WORKFLOW                               │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Setup → Orchestrator → [Phase 0-6] → Finalisierung         │
│    ↓         ↓              ↓             ↓                  │
│  Config   State Mgmt    Sub-Agents   Bibliography           │
│                                                              │
│  Phase 0: DBIS-Navigation (browser-agent)                    │
│  Phase 1: Suchstrings (search-agent)                         │
│  Phase 2: Datenbanksuche (browser-agent, 30x iterativ)      │
│  Phase 3: Ranking (scoring-agent)                            │
│  Phase 4: PDF-Download (browser-agent)                       │
│  Phase 5: Zitat-Extraktion (extraction-agent)               │
│  Phase 6: Finalisierung (orchestrator)                       │
│                                                              │
╰──────────────────────────────────────────────────────────────╯

Geschätzte Dauer:
- Quick Mode:    30-45 Min
- Standard Mode: 1.5-2 Std
- Deep Mode:     3-4 Std
```

---

## 🛡️ Security

**Siehe:** Shared Security Policy (in .claude/shared/SECURITY_POLICY.md falls vorhanden)

Als Entry-Point:
- Koordination, keine kritischen Operationen selbst
- Security-Tasks an spezialisierte Agents delegiert
- User-Input vertrauenswürdig, File-Paths werden validiert

---

## 🎯 DEINE AUFGABE

### Schritt 1: Begrüßung & Kontext-Check

Zeige Willkommensnachricht:

```
╔══════════════════════════════════════════════════════════════╗
║           🎓 Academic Agent - Recherche-Assistent            ║
║                        Version 4.1                           ║
╚══════════════════════════════════════════════════════════════╝

Willkommen! Ich helfe dir bei systematischer akademischer Recherche.
```

Prüfe `config/academic_context.md`:

```bash
test -f config/academic_context.md
```

**FALLS VORHANDEN:** Lade und parse Kontext (Forschungsfeld, Keywords, Datenbanken).

**FALLS NICHT:**
```
⚠️  Kein akademischer Kontext gefunden
   Erstelle config/academic_context.md oder nutze interaktiven Modus:
   bash scripts/academicagent_wrapper.sh --interactive
```

### Schritt 2: Browser-Verfügbarkeit prüfen

```bash
curl -s http://localhost:9222/json/version || echo "Chrome CDP nicht erreichbar"
```

**FALLS NICHT:** Zeige Anleitung:
```
🌐 Chrome CDP erforderlich für Browser-Automatisierung

Starte Chrome:
  bash scripts/start_chrome_debug.sh

Verifiziere:
  curl -s http://localhost:9222/json/version
```

### Schritt 3: Workflow-Info & Mode-Auswahl

Zeige Workflow-Übersicht (ASCII-Diagram oben).

Frage User nach Mode (falls nicht via Flag):

```
Wähle Recherche-Modus:
1. Quick (5 DBs, 15 Quellen, ~30 Min)
2. Standard (15 DBs, 30 Quellen, ~2 Std) [Empfohlen]
3. Deep (30 DBs, 50 Quellen, ~4 Std)
```

### Schritt 4: Permission-Setup

**Vereinfachte Permission-Frage:**

```
🔐 Session-Permissions für Sub-Agents

Option 1: Auto-Approve (Empfohlen)
  Agents dürfen automatisch spawnen (schneller Workflow)

Option 2: Manual
  Du wirst bei jedem Agent-Spawn gefragt (volle Kontrolle)

Wähle Option 1 oder 2?
```

**WENN Auto-Approve:**
```bash
export CLAUDE_SESSION_AUTO_APPROVE_AGENTS=true
echo "✅ Session-Permission aktiviert"
```

### Schritt 5: Live-Monitoring (Optional)

**OPTIONAL - Frage User:**

```
🖥️  Live-Status-Dashboard aktivieren? [Ja/Nein]

Ja: Zeigt Live-Updates in tmux (empfohlen für längere Runs)
Nein: Alternative Monitoring via scripts/live_monitor.py
```

**WENN Ja:**
```bash
bash scripts/setup_tmux_monitor.sh $RUN_ID
```

**Details:** Siehe [scripts/setup_tmux_monitor.sh](../../../scripts/setup_tmux_monitor.sh)

### Schritt 6: Setup-Agent spawnen

```bash
export CURRENT_AGENT="setup-agent"

Task(
  subagent_type="setup-agent",
  prompt="Interaktiver Setup für Run $RUN_ID, Mode: $MODE"
)
```

**Setup-Agent übernimmt:**
- Interaktive Konfiguration
- run_config.json erstellen
- research_state.json initialisieren
- Übergabe an orchestrator-agent

### Schritt 7: Orchestrator-Übergabe

**Setup-Agent gibt RUN_ID zurück. Dann:**

```bash
export CURRENT_AGENT="orchestrator-agent"

Task(
  subagent_type="orchestrator-agent",
  prompt="Starte 7-Phasen-Workflow für Run $RUN_ID"
)
```

**Ab hier:** Orchestrator übernimmt alle 7 Phasen.

### Schritt 8: Finalisierung & Ausgabe

**Nach Orchestrator-Completion:**

Lade Ergebnisse:
```bash
jq . runs/$RUN_ID/metadata/citations.json
cat runs/$RUN_ID/bibliography.md
```

Zeige Zusammenfassung:
```
╔══════════════════════════════════════════════════════════════╗
║                ✅ RECHERCHE ABGESCHLOSSEN                     ║
╚══════════════════════════════════════════════════════════════╝

📊 Statistiken:
   Datenbanken durchsucht: X
   Kandidaten gefunden:    Y
   PDFs heruntergeladen:   Z
   Zitate extrahiert:      N

📁 Output:
   runs/$RUN_ID/bibliography.md
   runs/$RUN_ID/pdfs/
   runs/$RUN_ID/metadata/

⏱️  Dauer: [calculated]
```

---

## 🚨 ERROR HANDLING

### Chrome nicht erreichbar
```
❌ Chrome CDP nicht verfügbar

Lösung:
  bash scripts/start_chrome_debug.sh
  # Dann Skill neu starten
```

### academic_context.md fehlt
```
⚠️  Kein akademischer Kontext

Lösung:
  bash scripts/academicagent_wrapper.sh --interactive
  # Oder manuell erstellen: config/academic_context.md
```

### Konfigurations-Fehler
```
❌ Invalide Konfiguration

Prüfe:
  - config/academic_context.md (Syntax)
  - runs/$RUN_ID/run_config.json (JSON valid)
```

### Agent-Spawn fehlgeschlagen
```
❌ Agent konnte nicht gestartet werden

Debug:
  - Prüfe Agent-Name (setup-agent, orchestrator-agent, etc.)
  - Prüfe .claude/agents/ (Agent existiert?)
  - Logs: runs/$RUN_ID/orchestrator.log
```

**Retry Logic:** Siehe [shared/EXECUTION_PATTERNS.md](../../../shared/EXECUTION_PATTERNS.md)

---

## 🔧 ADVANCED: Resume & Debugging

### Resume fehlgeschlagener Run

```bash
# Via Skill
/academicagent --resume run_20260223_143052

# Oder direkt
bash scripts/academicagent_wrapper.sh --resume run_20260223_143052
```

### Logs anschauen

```bash
# Orchestrator Log
tail -f runs/$RUN_ID/orchestrator.log

# Research State
watch -n 5 "jq . runs/$RUN_ID/research_state.json"

# Live Monitor
python3 scripts/live_monitor.py $RUN_ID
```

### Debugging

```bash
# Prüfe Phase-Outputs
ls -lh runs/$RUN_ID/metadata/

# Validiere JSON
jq empty runs/$RUN_ID/metadata/candidates.json

# Prüfe PDFs
ls -lh runs/$RUN_ID/pdfs/
```

---

## 📚 REFERENZEN

**Shared Documentation:**
- [EXECUTION_PATTERNS.md](../../../shared/EXECUTION_PATTERNS.md) - Action-First, Retry Logic
- [PHASE_EXECUTION_TEMPLATE.md](../../../shared/PHASE_EXECUTION_TEMPLATE.md) - Phase-Workflow-Details
- [ORCHESTRATOR_BASH_LIB.sh](../../../shared/ORCHESTRATOR_BASH_LIB.sh) - Helper Functions

**Agents:**
- [setup-agent.md](../../agents/setup-agent.md) - Setup & Config
- [orchestrator-agent.md](../../agents/orchestrator-agent.md) - Haupt-Koordinator
- [browser-agent.md](../../agents/browser-agent.md) - Web-Automatisierung
- [search-agent.md](../../agents/search-agent.md) - Suchstring-Generation
- [scoring-agent.md](../../agents/scoring-agent.md) - 5D-Scoring
- [extraction-agent.md](../../agents/extraction-agent.md) - Zitat-Extraktion

**Scripts:**
- [setup_tmux_monitor.sh](../../../scripts/setup_tmux_monitor.sh) - Live-Monitoring
- [academicagent_wrapper.sh](../../../scripts/academicagent_wrapper.sh) - TUI-Wrapper
- [start_chrome_debug.sh](../../../scripts/start_chrome_debug.sh) - Chrome CDP Start

---

## 📖 ZUSAMMENFASSUNG - Quick Reference

**1. Begrüßung** → Zeige Willkommensnachricht + Workflow-Diagram

**2. Kontext-Check** → `config/academic_context.md` vorhanden?

**3. Browser-Check** → Chrome CDP auf Port 9222?

**4. Mode-Auswahl** → Quick/Standard/Deep

**5. Permission-Setup** → Auto-Approve oder Manual?

**6. Live-Monitoring** → tmux oder live_monitor.py?

**7. Setup-Agent** → Spawn für interaktive Config

**8. Orchestrator** → Spawn für 7-Phasen-Workflow

**9. Finalisierung** → Zeige Statistiken + Output-Pfade

**10. Error Handling** → Siehe Error-Section oben

---

**Best Practice:** Bei Unsicherheit → Empfehle interaktiven TUI-Modus!

```bash
bash scripts/academicagent_wrapper.sh --interactive
```

---

**Version History:**
- 2.0.0 (2026-02-23): Refactoring - Modularisierung, tmux externalisiert, vereinfachter Permission-Dialog
- 1.x: Original Version (659 Zeilen)
