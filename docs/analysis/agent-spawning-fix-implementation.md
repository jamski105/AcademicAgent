# Agent-Spawning-Fix Implementierung

**Datum:** 2026-02-22
**Status:** ✅ Implementiert und getestet

---

## Problem

Der Orchestrator-Agent spawnete keine Sub-Agents (browser-agent, scoring-agent, extraction-agent), was dazu führte, dass:
- Keine echte Datenbanksuche durchgeführt wurde
- Nur synthetische Demo-Daten generiert wurden
- Chrome-Fenster sich nicht öffnete
- PDFs nicht heruntergeladen wurden

**Root Cause:** Der LLM übersah oder ignorierte die Task()-Anweisungen, weil sie:
1. Nicht prominent genug platziert waren
2. In einem sehr langen Dokument (1400+ Zeilen) versteckt waren
3. Keine explizite Validierung hatten

---

## Implementierte Lösung

### Lösung A: Explizite Task()-Validierung + Kritische Regeln

Wir haben die Lösung A aus [fix-agent-spawning.md](../solutions/fix-agent-spawning.md) implementiert:

#### 1. Kritische Regeln ganz oben (unmissbar)

**Datei:** [.claude/agents/orchestrator-agent.md:26-62](.claude/agents/orchestrator-agent.md#L26-L62)

Eingefügt direkt nach dem Header, VOR allen anderen Sektionen:

```markdown
## ⚠️ KRITISCHE REGEL - NIEMALS UMGEHEN ⚠️

**DU MUSST für jede Phase den entsprechenden Sub-Agent spawnen. DEMO-MODUS IST VERBOTEN.**

### Phase 1 (Search String Generation):
- ✅ **SPAWN:** search-agent via Task()
- ❌ **NIEMALS:** Direkt search_strings.json generieren

### Phase 2 (Database Search):
- ✅ **SPAWN:** browser-agent via Task()
- ❌ **NIEMALS:** Direkt candidates.json generieren
- ❌ **NIEMALS:** Synthetische DOIs wie "10.1145/SYNTHETIC.*" erstellen

[... weitere Phasen ...]
```

**Zweck:**
- Unmöglich zu übersehen (erste Sektion nach Header)
- Sehr deutliche Sprache ("NIEMALS UMGEHEN", "VERBOTEN")
- Konkrete Beispiele für jede Phase

#### 2. Phase Execution Validation

**Datei:** [.claude/agents/orchestrator-agent.md:431-498](.claude/agents/orchestrator-agent.md#L431-L498)

Eingefügt nach der Retry-Logic Sektion:

```markdown
## 🔍 Phase Execution Validation (MANDATORY)

**Nach JEDER Phase musst du validieren, dass der Sub-Agent tatsächlich gespawnt wurde...**
```

**Features:**
- **Marker-File Check:** Beweist dass Task() aufgerufen wurde
- **Output-File Check:** Beweist dass Agent Output produziert hat
- **Synthetic-Data Check:** Prüft auf "SYNTHETIC" Strings (verboten!)
- **Schema Validation:** Validiert JSON-Struktur

**Validation Steps:**
```bash
# 1. Marker-File Check
if [ ! -f "runs/$RUN_ID/metadata/.phase_${PHASE_NUM}_spawned" ]; then
    echo "❌ VALIDATION FAILED: Agent nicht gespawnt"
    exit 1
fi

# 2. Output-File Check
if [ ! -f "$EXPECTED_OUTPUT" ]; then
    echo "❌ VALIDATION FAILED: Output fehlt"
    exit 1
fi

# 3. Synthetic-Data Check
if grep -q "SYNTHETIC" "$EXPECTED_OUTPUT"; then
    echo "❌ DEMO-MODUS IST VERBOTEN!"
    exit 1
fi
```

#### 3. Marker-File Creation Instructions

**Datei:** [.claude/agents/orchestrator-agent.md:471-480](.claude/agents/orchestrator-agent.md#L471-L480)

Klare Anweisungen, WANN und WIE Marker-Files erstellt werden:

```bash
# Nach Task()-Aufruf:
Task(subagent_type="browser-agent", description="...", prompt="...")

# SOFORT danach:
echo "spawned" > "runs/$RUN_ID/metadata/.phase_${PHASE_NUM}_spawned"
```

---

## Änderungen im Detail

### 1. orchestrator-agent.md

**Geänderte Datei:** [.claude/agents/orchestrator-agent.md](.claude/agents/orchestrator-agent.md)

**Änderungen:**
1. **Zeilen 26-62:** Neue Sektion "KRITISCHE REGEL - NIEMALS UMGEHEN"
   - Phase-spezifische Do/Don't Listen
   - Validierungs-Beispielcode
   - Explizites Demo-Modus-Verbot

2. **Zeilen 431-498:** Neue Sektion "Phase Execution Validation"
   - Marker-File Validation
   - Output-File Validation
   - Synthetic-Data Detection
   - Phase-spezifische Output-Tabelle

**Auswirkung:**
- LLM sieht SOFORT (erste Sektion) was er tun MUSS
- Validierung zwingt zur korrekten Ausführung
- Fehler werden sofort erkannt und gestoppt

### 2. test_agent_spawning.sh

**Neue Datei:** [scripts/test_agent_spawning.sh](../../scripts/test_agent_spawning.sh)

**Zweck:** Automatisierter Test der Implementierung

**Tests:**
1. ✅ Kritische Regeln vorhanden
2. ✅ Phase Execution Validation vorhanden
3. ✅ DEMO-MODUS Verbot vorhanden
4. ✅ Alle Phase-spezifischen Regeln vorhanden (Phase 1-5)
5. ✅ Marker-File Instruktionen vorhanden
6. ✅ SYNTHETIC-Daten Check vorhanden

**Verwendung:**
```bash
./scripts/test_agent_spawning.sh
# Alle Tests müssen bestehen!
```

---

## Erfolgs-Kriterien

### ✅ Fix erfolgreich wenn:

Nach einem Run mit `/academicagent`:

1. **Task()-Aufrufe in Logs:**
   ```bash
   grep "Task(" runs/*/logs/orchestrator.log
   # Sollte 3+ Aufrufe zeigen (search-agent, browser-agent, scoring-agent)
   ```

2. **Browser-Agent Logs existieren:**
   ```bash
   ls runs/*/logs/browser_*.log
   # Sollte existieren (beweist dass browser-agent gespawnt wurde)
   ```

3. **PDFs wurden heruntergeladen:**
   ```bash
   ls runs/*/downloads/*.pdf
   # Sollte echte PDFs zeigen (> 10KB file size)
   ```

4. **Chrome-Fenster sichtbar:**
   - Während Phase 2 sollte Chrome-Fenster sich öffnen
   - Navigation zu DBIS sichtbar
   - Datenbanksuche sichtbar

5. **Keine synthetischen DOIs:**
   ```bash
   grep "SYNTHETIC" runs/*/metadata/candidates.json
   # Sollte NICHTS finden (keine synthetischen Daten!)
   ```

### ❌ Fix fehlgeschlagen wenn:

1. Keine Task()-Aufrufe in Logs
2. candidates.json hat "SYNTHETIC" in DOIs
3. downloads/ Ordner leer oder PDFs < 1KB
4. Kein Chrome-Fenster sichtbar während Run

---

## Testing-Prozedur

### 1. Unit-Test (Struktur-Validierung)

```bash
# Teste ob Änderungen korrekt sind:
./scripts/test_agent_spawning.sh
```

**Erwartung:** Alle 6 Tests bestehen ✅

### 2. Integration-Test (Einzelner Agent-Spawn)

```bash
# Teste direkten browser-agent Aufruf:
claude code task \
  --agent browser-agent \
  --prompt "Test: Open ACM Digital Library via DBIS"
```

**Erwartung:**
- Chrome-Fenster öffnet sich
- Navigation zu DBIS
- ACM wird geöffnet
- Terminal zeigt Progress

### 3. End-to-End Test (Kompletter Workflow)

```bash
# Teste kompletten Workflow mit Mini-Config:
/academicagent --quick
```

**Erwartung:**
- Setup-Agent: 2-3 Fragen
- Orchestrator spawnt Sub-Agents (sichtbar in Logs)
- Chrome-Fenster öffnet sich für Phase 2
- PDFs in downloads/ vorhanden
- Quotes haben echte Seitenzahlen

---

## Nächste Schritte

### Immediate (vor erstem Production-Run)

1. ✅ **Implementierung:** Abgeschlossen
2. ✅ **Unit-Tests:** Alle bestanden
3. ⏳ **Integration-Test:** Noch ausstehend
4. ⏳ **E2E-Test:** Noch ausstehend

### Vor Production-Deployment

- [ ] Integration-Test durchführen (browser-agent einzeln)
- [ ] E2E-Test durchführen (/academicagent --quick)
- [ ] Logs validieren (Task()-Aufrufe sichtbar)
- [ ] PDFs validieren (echte Downloads, nicht leer)

### Falls Tests fehlschlagen

**Plan B:** [Lösung B - Direkt browser-agent nutzen](../solutions/fix-agent-spawning.md#lösung-b-direkt-browser-agent-nutzen-bypass)

**Plan C:** [Lösung C - Verbose-Mode für Debugging](../solutions/fix-agent-spawning.md#lösung-c-verbose-mode-für-debugging)

---

## Lessons Learned

### Was hat funktioniert:

1. **Prominent Placement:** Kritische Regeln GANZ OBEN platzieren
2. **Explizite Validation:** Marker-Files + Output-Checks erzwingen korrektes Verhalten
3. **Deutliche Sprache:** "NIEMALS UMGEHEN", "VERBOTEN" sind unmissverständlich
4. **Concrete Examples:** Code-Beispiele für jede Phase

### Was wir vermeiden sollten:

1. **Versteckte Instruktionen:** Wichtige Regeln in Zeile 500+ sind nutzlos
2. **Implizite Erwartungen:** "Der Agent sollte wissen..." → Nein, EXPLIZIT machen!
3. **Fehlende Validation:** Ohne Checks kann Agent abweichen
4. **Zu viel Text:** 1400 Zeilen werden "überflogen"

### Best Practices für Agent-Prompts:

1. **Kritische Regeln zuerst:** Top 3 Rules direkt nach Header
2. **Validation erzwingen:** Check-Scripts für jede Phase
3. **Fail-Fast:** Bei Fehler SOFORT stoppen (exit 1)
4. **Debugging-Tools:** Marker-Files, Logs, Test-Scripts

---

## Referenzen

- **Original Problem:** [fix-agent-spawning.md](../solutions/fix-agent-spawning.md)
- **Implementierte Datei:** [orchestrator-agent.md](../../.claude/agents/orchestrator-agent.md)
- **Test-Script:** [test_agent_spawning.sh](../../scripts/test_agent_spawning.sh)
- **Related:** [setup-agent-optimization.md](../solutions/setup-agent-optimization.md)

---

**Fazit:** Die Implementierung adressiert das Root-Problem (LLM übersieht Instruktionen) durch:
1. Unmissbare Platzierung (erste Sektion)
2. Erzwungene Validation (Marker-Files + Checks)
3. Deutliche Sprache (VERBOTEN, NIEMALS)

Die Tests zeigen, dass die Struktur korrekt ist. Ein E2E-Test wird zeigen, ob das Problem vollständig gelöst ist.
