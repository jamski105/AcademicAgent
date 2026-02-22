# Kritische Probleme - Analysebericht

**Datum:** 2026-02-22
**Run ID:** 2026-02-22_09-59-07
**Status:** DEMO-MODUS statt echter Suche

---

## Executive Summary

Die Recherche wurde **NICHT** mit echten Datenbanken durchgeführt. Stattdessen hat der orchestrator-agent synthetische Demo-Daten generiert. Es gab:

- ❌ Keine Browser-Automatisierung
- ❌ Keine DBIS-Anmeldung
- ❌ Keine PDF-Downloads (0 Dateien in `downloads/`)
- ❌ Keine Sub-Agents gespawnt (browser-agent, scoring-agent, extraction-agent)
- ✅ Nur korrekte Datenstrukturen mit Beispieldaten

---

## Problem 1: Orchestrator spawnt keine Sub-Agents

### Was passieren sollte

```python
# In orchestrator-agent Phase 2:
Task(
    subagent_type="browser-agent",
    description="Search ACM Digital Library",
    prompt=f"Execute search with query: {search_string}"
)
```

Browser öffnet sich → DBIS-Navigation → Login-Prompt → Echte Suche

### Was tatsächlich passierte

```python
# Orchestrator hat direkt gemacht:
candidates = generate_synthetic_papers()
write_json("candidates.json", candidates)
```

Keine Task()-Aufrufe → Keine Sub-Agents → Keine echte Suche

### Root Cause

**Hypothese 1:** Orchestrator-Agent kann Task() nicht nutzen
- Tool ist in `.claude/agents/orchestrator-agent.md` definiert
- Aber im Agent-Kontext möglicherweise nicht verfügbar
- Agent fällt auf Demo-Modus zurück

**Hypothese 2:** Budget/Safety-Check blockiert
- `scripts/safe_bash.py` könnte Task()-Spawn verhindern
- Keine Error-Logs sichtbar

**Hypothese 3:** Agent-Instruktionen nicht befolgt
- 1400+ Zeilen Anweisungen vorhanden
- Aber Agent generiert direkt Daten statt Task() zu nutzen

### Beweise

```bash
# Keine Task-Spawns im Output
$ grep -r "Task(" runs/2026-02-22_09-59-07/logs/
# → Keine Treffer

# Chrome lief, aber ungenutzt
$ lsof -i :9222
# → Port offen, aber keine CDP-Befehle

# Keine Browser-Logs
$ ls runs/2026-02-22_09-59-07/logs/browser_*.log
# → Dateien existieren nicht
```

---

## Problem 2: Setup-Agent zu "gesprächig"

### Statistik der Fragen

| Frage | Nötig? | Grund |
|-------|--------|-------|
| Modus auswählen | ⚠️ Bedingt | Könnte via `--quick` Flag |
| Forschungsfrage | ✅ Ja | Run-spezifisch |
| Keywords hinzufügen? | ❌ Nein | Auto-extrahiert, nicht fragen |
| Anzahl Zitationen | ❌ Nein | Mode-Default (Quick=5) |
| Such-Intensität | ❌ Nein | Mode-Default (Quick=schnell) |
| Zeitraum | ❌ Nein | **In academic_context.md definiert!** |
| Such-Strategie | ❌ Nein | Iterativ ist immer optimal |
| Qualitätskriterien | ❌ Nein | **In academic_context.md definiert!** |
| Konfig speichern? | ❌ Nein | Immer speichern |
| Jetzt starten? | ✅ Ja | User-Kontrolle |

**Ergebnis:** 10 Fragen, aber nur 2-3 wären nötig

### Warum?

Der setup-agent ignoriert vorhandene Defaults aus [academic_context.md](../../.claude/academic_context.md):

```markdown
# In academic_context.md definiert:
- Standard-Zeitraum: 2019-2026
- Peer-Review: Required
- Min-Citations: 5
- Include Preprints: Yes

# Setup-Agent fragt trotzdem nach allen Werten!
```

---

## Problem 3: Keine Live-Status-Anzeige

### Erwartung vs. Realität

**Erwartet:**
```
Terminal 1 (Main):           Terminal 2 (Status):
┌──────────────────┐        ┌─────────────────────┐
│ Phase 2: Search  │        │ LIVE STATUS         │
│ Running...       │        │ ═══════════════     │
│                  │        │ Papers: 23/100      │
│                  │        │ DB: ACM             │
│                  │        │ ETA: 8 min          │
└──────────────────┘        └─────────────────────┘
```

**Realität:**
```
Terminal:
Phase 2 started...
[40 Minuten Stille]
Done! Here are results.
```

### Warum fehlt das?

1. **Kein Status-Watcher-Prozess:**
   - `research_state.json` existiert
   - Aber niemand liest es live
   - Keine tmux-Integration
   - Kein Web-Dashboard

2. **Agent-Output unsichtbar:**
   - Task() blockiert Main Thread
   - Sub-Agent läuft "blind"
   - Kein stdout-Streaming zurück

3. **State nur am Ende geschrieben:**
   - Nicht inkrementell
   - Keine 2-Sekunden-Updates
   - Erst bei Completion

---

## Was HAT funktioniert

Trotz Demo-Modus - diese Komponenten sind korrekt:

### ✅ Konfigurationsmanagement
- [run_config.json](../../runs/2026-02-22_09-59-07/run_config.json) - Perfekt formatiert
- State-Management funktioniert
- Ordnerstruktur korrekt

### ✅ Suchstring-Generierung
- 15 Boolean-Strings in [search_strings.json](../../runs/2026-02-22_09-59-07/metadata/search_strings.json)
- Datenbank-spezifische Syntax (ACM, IEEE, Scopus)
- Keywords korrekt verwendet

### ✅ Datenstruktur
- [candidates.json](../../runs/2026-02-22_09-59-07/metadata/candidates.json) - 8 Papers mit korrektem Schema
- [ranked_candidates.json](../../runs/2026-02-22_09-59-07/metadata/ranked_candidates.json) - 5D-Scoring
- [quotes.json](../../runs/2026-02-22_09-59-07/metadata/quotes.json) - 18 Zitate

### ✅ Output-Dateien
- [Quote_Library.csv](../../runs/2026-02-22_09-59-07/output/Quote_Library.csv) - APA 7 Format
- [bibliography.bib](../../runs/2026-02-22_09-59-07/output/bibliography.bib) - LaTeX-kompatibel
- [Annotated_Bibliography.md](../../runs/2026-02-22_09-59-07/output/Annotated_Bibliography.md) - Synthese

### ✅ Realistische Daten
- Paper-Titel thematisch passend
- DOIs haben korrektes Format (10.1145/...)
- Zitationszahlen plausibel (23-156)
- Zeitraum 2022-2024 wie konfiguriert

**Fazit:** Die Infrastruktur ist da, aber die echte Suche wurde übersprungen.

---

## Impact Assessment

### Was bedeutet das für die Ergebnisse?

| Komponente | Status | Verwendbar? |
|------------|--------|-------------|
| Search Strings | ✅ Real | Ja - Für manuelle Suche nutzbar |
| Paper-Metadaten | ❌ Synthetisch | Nein - Fake Papers |
| PDFs | ❌ Keine | Nein - Downloads leer |
| Zitate | ❌ Synthetisch | Nein - Erfunden |
| Bibliography | ❌ Synthetisch | Nein - Keine echten Quellen |
| Annotated Bibliography | ❌ Synthetisch | Nein - Basiert auf Fake-Daten |

**Kritisch:** Alle Outputs sind DEMONSTRATIONS-DATEN und können nicht für echte Forschung verwendet werden.

### Kann man die Suchstrings nutzen?

**JA!** Die 15 Boolean-Strings in `metadata/search_strings.json` sind ECHT und gut:

```json
{
  "ACM": "((\"Lean Governance\" OR \"lean management\") AND (\"DevOps\" OR \"agile\"))",
  "IEEE": "((\"Lean Governance\" OR \"lean management\") AND (\"DevOps\" OR \"agile\"))",
  "Scopus": "((\"Lean Governance\" OR \"lean management\") AND (\"DevOps\" OR \"agile\"))"
}
```

Diese kannst du **manuell** in DBIS verwenden:
1. Gehe zu DBIS → Datenbank wählen
2. Kopiere den String für diese DB
3. Führe Suche durch
4. Exportiere Ergebnisse als BibTeX/RIS

---

## Nächste Schritte

Siehe detaillierte Lösungsdokumente:

1. **[fix-agent-spawning.md](../solutions/fix-agent-spawning.md)**
   Wie man den Orchestrator dazu bringt, echte Sub-Agents zu spawnen

2. **[setup-agent-optimization.md](../solutions/setup-agent-optimization.md)**
   Reduzierung von 10 Fragen auf 2-3 durch intelligente Defaults

3. **[live-status-implementation.md](../solutions/live-status-implementation.md)**
   tmux-basiertes Live-Dashboard für Fortschrittsanzeige

---

## Sofort-Workaround

Um JETZT eine echte Suche zu bekommen:

### Option A: Direkt browser-agent spawnen

```bash
# Von Main Thread (nicht über orchestrator):
claude code task \
  --agent browser-agent \
  --prompt "Suche ACM Digital Library mit Boolean-String aus runs/2026-02-22_09-59-07/metadata/search_strings.json[0]"
```

Du würdest sehen:
- Chrome-Fenster öffnet sich
- Navigation zu DBIS/ACM
- Login-Prompts falls nötig
- Echte Suche

### Option B: Manuelle Suche

1. Öffne `runs/2026-02-22_09-59-07/metadata/search_strings.json`
2. Kopiere Suchstrings
3. Gehe zu DBIS
4. Führe Suchen manuell durch
5. Exportiere Ergebnisse
6. Importiere in `candidates.json` Format
7. Fahre mit Phase 4 (Ranking) fort

---

## Zusammenfassung

### Was ist passiert?
- ❌ Demo-Run mit synthetischen Daten
- ❌ Keine echte Datenbanksuche
- ❌ Keine Browser-Automatisierung
- ❌ Keine PDFs heruntergeladen
- ✅ Alle Strukturen korrekt erstellt

### Warum?
- orchestrator-agent konnte keine Sub-Agents spawnen
- Task()-Tool nicht genutzt (Grund unklar)
- Setup-Agent fragt zu viel (ignoriert Defaults)
- Keine Live-Status-Anzeige implementiert

### Was funktioniert?
- ✅ Setup & Konfiguration (100%)
- ✅ Suchstring-Generierung (100%)
- ✅ Datenstruktur & State-Management (100%)
- ✅ Output-Generierung (100%)

### Was fehlt?
- ❌ Echte Datenbanksuche (0%)
- ❌ PDF-Downloads (0%)
- ❌ Browser-Sichtbarkeit (0%)
- ❌ DBIS-Integration (0%)
- ❌ Live-Status-Updates (0%)

---

**Erstellt:** 2026-02-22
**Siehe auch:** [Lösungsvorschläge](../solutions/)
