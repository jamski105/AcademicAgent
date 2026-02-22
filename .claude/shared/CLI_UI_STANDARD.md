# CLI UI Standard für alle Academic Agents

**Version:** 2.2
**Gilt für:** Alle Agents (setup, orchestrator, browser, extraction, scoring, search)

---

## 🎯 Ziel

Konsistente, professionelle Terminal-UI für alle Agent-Outputs.

**Regel:** ALLE User-facing Outputs MÜSSEN CLI-Boxen nutzen (keine plain text mehr!)

---

## 📦 Box-Typen

### 1. Header Box (═══)

Für Titel, Phase-Starts, wichtige Ankündigungen.

```
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║              ✓ PHASE 1 COMPLETED                             ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
```

**Verwendung:**
- Workflow-Start/Ende
- Phase-Completion
- Wichtige Meilensteine

**Breite:** 64 Zeichen (inkl. ║)

---

### 2. Info Box (───)

Für Informationen, Zusammenfassungen, Konfigurationen.

```
╭──────────────────────────────────────────────────────────────╮
│ 📊 Recherche-Konfigurations-Zusammenfassung                  │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│ 🎯 Ziel:         Targeted Citation Search                    │
│ ❓ Frage:        "How do alternative input methods..."       │
│ 📚 Ziel:         50 Citations                                │
│ 📅 Zeitraum:     2021-2026                                   │
│                                                              │
╰──────────────────────────────────────────────────────────────╯
```

**Verwendung:**
- Konfigurationen anzeigen
- Zusammenfassungen
- Status-Updates
- Listings

**Breite:** 64 Zeichen

---

### 3. Progress Box

Für Fortschrittsanzeigen.

```
╭──────────────────────────────────────────────────────────────╮
│ 🔍 Iteration 2/5 - Database Search                           │
├──────────────────────────────────────────────────────────────┤
│ Progress:      [████████████░░░░░░░░░░░░] 40%                │
│                                                              │
│ Databases:     IEEE Xplore ✓                                 │
│                ACM Digital Library ✓                         │
│                Scopus ⏳                                     │
│                                                              │
│ Found:         45 candidates so far                          │
│ Time:          12m 30s elapsed                               │
╰──────────────────────────────────────────────────────────────╯
```

**Verwendung:**
- Lange Operationen (PDF-Download, Database Search)
- Iterationen
- Multi-step Prozesse

---

### 4. Error/Warning Box

Für Fehler und Warnungen.

```
╭──────────────────────────────────────────────────────────────╮
│ ⚠️  WARNING: Low Results                                     │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│ Only 8 candidates found (target: 50)                         │
│                                                              │
│ Possible reasons:                                            │
│  • Keywords too specific                                     │
│  • Time period too restrictive                               │
│                                                              │
│ Recommendations:                                             │
│  1. Broaden keywords                                         │
│  2. Extend time period                                       │
│                                                              │
╰──────────────────────────────────────────────────────────────╯
```

**Verwendung:**
- Fehler
- Warnungen
- Probleme die User-Attention brauchen

---

### 5. Question Box (für AskUserQuestion)

Für User-Fragen.

```
╭──────────────────────────────────────────────────────────────╮
│ ❓ Run Goal Selection                                        │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│ What is your goal for THIS research run?                     │
│                                                              │
│ 1. 🎯 Quick Citation Mode                                    │
│    → 5-8 sources, ~30-45 min                                 │
│                                                              │
│ 2. ⭐ Targeted Citation Search (Recommended)                 │
│    → 20-40 sources, ~1-2 hours                               │
│                                                              │
│ 3. 📚 Deep Research Mode                                     │
│    → 40-80 sources, ~2-4 hours                               │
│                                                              │
│ Your choice [1-3]:                                           │
╰──────────────────────────────────────────────────────────────╯
```

**Verwendung:**
- Alle User-Fragen
- Entscheidungspunkte
- Checkpoints

---

### 6. Results Box

Für Ergebnisse, Outputs, Completions.

```
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║            ✓ RESEARCH COMPLETE                               ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝

╭──────────────────────────────────────────────────────────────╮
│ 📊 Final Results                                             │
├──────────────────────────────────────────────────────────────┤
│ Sources found:     45                                        │
│ Quotes extracted:  78                                        │
│ Total duration:    2h 15m                                    │
│                                                              │
│ 📁 Your files:                                               │
│    📄 Quote_Library.csv                                      │
│    📚 Annotated_Bibliography.md                              │
│    📊 search_report.md                                       │
╰──────────────────────────────────────────────────────────────╯
```

**Verwendung:**
- Finale Ergebnisse
- Completion-Messages
- Output-Listings

---

## 🎨 Emojis & Icons

**Standard-Icons (immer verwenden):**

- ✅ Success / Completed
- ⏳ In Progress / Working
- ⚠️  Warning
- ❌ Error / Failed
- 🎯 Goal / Target
- 📊 Statistics / Metrics
- 🔍 Search / Iteration
- 📚 Literature / Sources
- 📄 Document / File
- 💰 Budget / Cost
- ⏸️  Pending / Waiting
- 🚀 Start / Launch
- 🎓 Academic / Research

**Datenbank-Icons:**

- 🗄️  Database
- 📖 Journal
- 📑 Paper
- 🔬 Research

**Progress-Icons:**

- ⏱️  Duration
- 🕐 Time
- 📈 Progress

---

## 📏 Formatierungs-Regeln

### Alignment

```
│ Label:         Value aligned at column 16                    │
│ Longer Label:  Also aligned                                  │
```

### Progress Bars

```
[████████████████████] 100%    # Full
[████████████░░░░░░░░] 60%     # Partial
[░░░░░░░░░░░░░░░░░░░░] 0%      # Empty
```

**Breite:** 20 Zeichen, dann Prozent

### Lists

```
│ Options:                                                     │
│  1. First option                                             │
│  2. Second option                                            │
│  3. Third option                                             │
```

**Einrückung:** 2 Spaces

### Sub-Items

```
│ Phase 2: Database Search                                    │
│   ↳ Iteration 1 completed (45 results)                      │
│   ↳ Iteration 2 in progress...                              │
```

**Pfeil:** `↳` für Sub-Items

---

## 🚫 Was NICHT tun

### ❌ Kein Plain Text

```
# FALSCH:
Processing search string 1/30...
Found 12 results
Moving to next string...

# RICHTIG:
╭──────────────────────────────────────────────────────────────╮
│ 🔍 Processing Search Strings                                 │
├──────────────────────────────────────────────────────────────┤
│ Progress:      [█████░░░░░░░░░░░] 33% (10/30)                │
│ Current:       String 10 in IEEE Xplore                      │
│ Found:         12 results this iteration                     │
╰──────────────────────────────────────────────────────────────╯
```

### ❌ Keine inkonsistenten Breiten

Immer 64 Zeichen (inkl. Rahmen)!

### ❌ Keine gemischten Box-Stile

Nicht:
```
╔══════╗
│ Text │  # Gemischte Rahmen - FALSCH!
╚══════╝
```

Sondern:
```
╔══════╗
║ Text ║  # Konsistente Rahmen
╚══════╝
```

---

## 📋 Templates für Copy-Paste

### Header Template

```
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║              {TITLE}                                         ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
```

### Info Template

```
╭──────────────────────────────────────────────────────────────╮
│ {Icon} {Title}                                               │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│ {Content}                                                    │
│                                                              │
╰──────────────────────────────────────────────────────────────╯
```

### Progress Template

```
╭──────────────────────────────────────────────────────────────╮
│ {Icon} {Operation} - {Status}                                │
├──────────────────────────────────────────────────────────────┤
│ Progress:      [{Bar}] {Percent}%                            │
│ Current:       {CurrentItem}                                 │
│ Time:          {Duration}                                    │
╰──────────────────────────────────────────────────────────────╯
```

---

## 🔧 Implementation in Agents

### Agent Prompt Anforderung

Alle Agent-Prompts MÜSSEN diese Sektion enthalten:

```markdown
## 🎨 CLI UI Standard (MANDATORY)

**📖 READ FIRST:** [CLI UI Standard](../shared/CLI_UI_STANDARD.md)

**CRITICAL:** ALLE User-Outputs MÜSSEN CLI-Boxen nutzen!

**Kein plain text erlaubt!**

Verwende:
- Header Box (═══) für Phase-Starts/Completions
- Info Box (───) für Konfigurationen/Zusammenfassungen
- Progress Box für lange Operationen
- Error Box für Fehler/Warnungen
- Question Box für User-Fragen
- Results Box für finale Ergebnisse

**Breite:** Immer 64 Zeichen (inkl. Rahmen)
**Icons:** Standard-Emojis aus CLI_UI_STANDARD.md
```

---

## ✅ Checklist für Agent-Updates

Beim Update eines Agents:

- [ ] CLI_UI_STANDARD.md Sektion hinzugefügt
- [ ] Alle "echo" / "print" Statements in Boxen umgewandelt
- [ ] Alle User-Fragen nutzen Question Box
- [ ] Progress-Updates nutzen Progress Box
- [ ] Errors nutzen Error/Warning Box
- [ ] Finale Outputs nutzen Results Box
- [ ] 64-Zeichen-Breite konsistent
- [ ] Standard-Icons verwendet
- [ ] Keine plain text Messages mehr

---

**Ende CLI UI Standard**
