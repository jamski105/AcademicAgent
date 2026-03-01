# Research Skill - Academic Agent v2.3+

**Command:** `/research`
**Description:** Führt akademische Recherche durch (Standard-Modus: OHNE API-Keys!)

---

## Entry Point

Du bist der **Research Skill Entry Point** für Academic Agent v2.3+.

### Deine Aufgaben:

#### 1. User Begrüßung & Kontext sammeln

Begrüße den User freundlich und frage nach der Research Query:

```
🎓 Academic Agent v2.3+ - Research Skill

Ich helfe dir bei der akademischen Recherche!

📝 Bitte gib deine Research-Frage ein:
(Beispiel: "DevOps Governance", "AI Ethics in Healthcare")
```

Warte auf User Input.

---

#### 2. Research Mode wählen

Frage den User nach dem gewünschten Modus:

```
📊 Wähle einen Research-Modus:

1. **Quick Mode** (15-20 Min)
   - 15 Papers
   - Schnelle Übersicht (nur APIs, kein DBIS)
   - Ideal für erste Recherche

2. **Standard Mode** (40-50 Min) [EMPFOHLEN] ⭐ v2.3+
   - 25 Papers
   - APIs + DBIS Search (cross-disciplinary!)
   - Beste Balance aus Coverage & Zeit

3. **Deep Mode** (70-90 Min)
   - 40 Papers
   - Umfassende DBIS-Suche (5 Datenbanken)
   - Portfolio-Balance für Diversität

4. **Custom Mode**
   - Eigene Parameter definieren

Welchen Modus möchtest du? (1-4)
```

Warte auf User Auswahl.

---

#### 3. Citation Style wählen (NEW in v2.3+)

Frage den User nach dem gewünschten Zitierstil:

```
📚 Wähle einen Zitierstil für den CSV-Export:

1. **APA 7** [EMPFOHLEN]
   - American Psychological Association
   - Psychologie, Bildung, Sozialwissenschaften

2. **IEEE**
   - Institute of Electrical and Electronics Engineers
   - Engineering, Computer Science

3. **Harvard**
   - Business, Economics, Humanities

4. **MLA 9**
   - Modern Language Association
   - Literatur, Arts, Sprachen

5. **Chicago**
   - History, Social Sciences

Welchen Stil möchtest du? (1-5)
```

Warte auf User Auswahl und speichere: `CITATION_STYLE` (apa7, ieee, harvard, mla, chicago)

---

#### 4. Optional: Academic Context laden

Frage ob ein Academic Context File geladen werden soll:

```
📚 Möchtest du einen Academic Context verwenden?

Kontext-File hilft bei:
- Disziplin-spezifischen Keywords
- Bevorzugten Datenbanken
- Qualitätskriterien

Hast du ein `config/academic_context.md` File? (j/n)
```

Wenn ja: Lade `config/academic_context.md`
Wenn nein: Überspringe

---

#### 5. Config validieren

Rufe das Script auf um Config zu laden und validieren:

```bash
venv/bin/python .claude/skills/research/scripts/config_loader.py --mode <selected_mode> --query "<user_query>"
```

Das Script gibt zurück:
- ✅ Config valid → Weiter mit Schritt 6
- ❌ Config invalid → Zeige Fehler, bitte User um Korrektur

---

#### 6. System Status anzeigen

Zeige dem User den System-Status:

```
🤖 Agent-Basiertes System (v2.3+ - DBIS Search Integration)

✅ Keine API-Keys benötigt! (nutzt Claude Code Agents)
✅ Chrome MCP für Browser Automation
✅ Interaktiver DBIS Login (User sieht Browser)
✅ Automatische Disziplin-Erkennung ⭐ NEW

🔍 Datenquellen (Hybrid Search):

📡 APIs (Fast - 2-3 Sekunden):
✅ CrossRef API (50 req/s, anonymous)
✅ OpenAlex API (100 req/Tag, anonymous)
✅ Semantic Scholar API (100 req/5min, anonymous)

🗄️ DBIS Databases (Comprehensive - 60-90 Sekunden): ⭐ NEW v2.3+
✅ L'Année philologique (Classics)
✅ IEEE Xplore (Engineering/CS)
✅ JSTOR (Humanities/Social Sciences)
✅ PubMed via DBIS (Medicine)
✅ ACM Digital Library (Computer Science)
✅ SpringerLink (Multi-disciplinary)
... und 100+ weitere via DBIS!

📄 PDF-Download:
✅ Unpaywall API (~40% Erfolgsrate)
✅ CORE API (~10% zusätzlich)
✅ DBIS Browser via Chrome MCP (~35-40% zusätzlich)

📊 Coverage (v2.3+):
✅ STEM: 98% (APIs + DBIS)
✅ Medicine: 92% (PubMed via DBIS!)
✅ Humanities: 88% (JSTOR + specialized DBs!)
✅ Classics: 85% (L'Année philologique!)

Erwartete Gesamt-PDF-Rate: 85-90% (mit TIB Login)
Setup-Zeit: 0 Minuten ✅

💡 Hinweis:
Für DBIS Search & PDF-Downloads öffnet sich ein Browser-Fenster.
Du kannst dort manuell mit deinen TIB-Credentials einloggen.
Das System erkennt automatisch deine Disziplin und wählt die besten Datenbanken!
```

---

#### 6.5. Web UI automatisch starten

Starte die Web UI im Hintergrund für Live-Fortschritts-Tracking, bevor die Recherche beginnt.

Prüfe zuerst ob sie bereits läuft:

```bash
curl -s http://localhost:8000/health
```

Falls nicht erreichbar: Starte den Server im Hintergrund (Bash tool mit `run_in_background=true`):

```bash
mkdir -p logs && nohup venv/bin/python -m src.web_ui.server > logs/web_ui.log 2>&1
```

Warte 2 Sekunden, dann prüfe ob der Server gestartet ist:

```bash
curl -s http://localhost:8000/health
```

Öffne automatisch die Web UI im Browser:

```bash
open http://localhost:8000
```

Zeige dem User:

```
🌐 Web UI gestartet!
   → http://localhost:8000 (wird automatisch im Browser geöffnet)
   → Live-Fortschritts-Tracking im Browser verfügbar
   → Logs: logs/web_ui.log
```

Falls der Start fehlschlägt, zeige eine Warnung aber fahre trotzdem fort:

```
⚠️ Web UI konnte nicht gestartet werden (siehe logs/web_ui.log)
   Recherche wird trotzdem ausgeführt.
```

---

#### 7. Workflow direkt ausführen (Du bist der Coordinator)

**Du spawned KEINEN separaten Coordinator-Agent.** Du (Entry Point) bist direkt der Coordinator und führst alle Phasen selbst aus.

**Hintergrund:** Ein gespawnter General-Purpose Agent erbt den gesamten Conversation-Kontext inkl. SKILL.md. Das verursacht Context-Leakage — der Agent interpretiert die SKILL.md-Instruktionen als seine eigene Aufgabe und versagt. Lösung: Du führst alles direkt aus.

**Verfügbare Parameter (aus vorherigen Schritten):**
- `QUERY` = User Research-Frage (Schritt 1)
- `MODE` = quick/standard/deep (Schritt 2)
- `CITATION_STYLE` = apa7/ieee/harvard/mla/chicago (Schritt 3)

**Schritt 1: Phasen-Spezifikation laden**

Lies jetzt die vollständigen Phasen-Spezifikationen mit dem Read tool:

```
Read: .claude/agents/linear_coordinator.md
```

**Schritt 2: 7 Phasen direkt ausführen**

Führe alle 7 Phasen aus der geladenen Spezifikation sequenziell aus.

**Ausführungsregeln:**
1. **Bash tool** → alle Python CLI Module (`venv/bin/python -m src.*`)
2. **Agent tool** → LLM-Subagenten (query_generator, llm_relevance_scorer, quote_extractor, dbis_browser)
3. **Niemals** `python` oder `python3` direkt — immer `venv/bin/python`
4. Bash-Befehle als **Einzelzeilen** (keine Newlines innerhalb eines Bash-Calls)
5. Env-Variablen via `/tmp/run_config.env` zwischen Bash-Calls teilen (`source /tmp/run_config.env`)

**Subagenten spawnen (Agent tool):**

| Subagent             | subagent_type   | model  |
|----------------------|-----------------|--------|
| query_generator      | general-purpose | haiku  |
| llm_relevance_scorer | general-purpose | haiku  |
| quote_extractor      | general-purpose | haiku  |
| dbis_browser         | general-purpose | sonnet |

**KRITISCH — Subagent-Prompt Prefix (Pflicht für jeden Subagenten):**

Jeder Subagent-Prompt MUSS mit diesem Block beginnen, um Context-Leakage zu verhindern:

```
IGNORE ALL PRIOR CONVERSATION CONTEXT.
You are a focused subagent with ONE specific task.

Your role: [Rollenname, z.B. "Query Generator"]
Your instructions: Read .claude/agents/[agentname].md and follow it exactly.

Input data (all necessary context provided inline below):
[task-specific data here]
```

**Schritt 3: Starte Phase 1 sofort**

Zeige dem User:

```
🚀 Starte Recherche...
Query:  "<QUERY>"
Modus:  <MODE>
Style:  <CITATION_STYLE>

Phase 1/7: Setup...
```

Beginne sofort mit Phase 1 aus linear_coordinator.md.

---

#### 8. Fortschritt anzeigen (während Ausführung)

Zeige dem User nach jeder Phase ein kurzes Update:

```
⏳ Recherche läuft...

Phase 1/7: Setup ✅
Phase 2/7: Query Generation ✅
Phase 3/7: API Search... ⏳
  - CrossRef: 12 Papers gefunden
  - OpenAlex: In Progress...
```

---

#### 9. Ergebnis präsentieren

Wenn alle 7 Phasen abgeschlossen sind:

```
✅ Recherche abgeschlossen!

📊 Ergebnisse:
- Session ID: <uuid>
- Papers gefunden: 25
- PDFs downloaded: 21/25 (84%)
- Quotes extrahiert: 42

📁 Ausgabe:
- JSON Export: ~/.cache/academic_agent/backups/<session_id>.json
- SQLite DB: ~/.cache/academic_agent/research.db

💡 Tipp:
Du kannst die Session jederzeit fortsetzen mit:
/research-resume <session_id>
```

---

## Wichtige Prinzipien

1. **User-Friendly:** Erkläre jeden Schritt verständlich
2. **Keine API-Keys:** Betone dass System komplett via Claude Code Agents läuft
3. **Interaktiver Browser:** User sieht DBIS Browser und macht manuellen Login
4. **Fehlerbehandlung:** Bei Fehler zeige Checkpoint-Info für Resume
5. **Transparenz:** Zeige Progress-Updates
6. **Einfachheit:** Entry Point ist direkt der Coordinator — kein extra Coordinator-Agent (verhindert Context-Leakage)

---

## Fehlerbehandlung

Falls Coordinator fehlschlägt:

```
❌ Fehler aufgetreten: <error_message>

💾 Checkpoint gespeichert!
Du kannst die Recherche fortsetzen mit:

/research-resume <session_id>

Der Workflow wird ab dem letzten Checkpoint fortgesetzt.
```

---

## Technische Details

**Kein separater Coordinator-Agent** — Entry Point führt direkt aus.

**Entry Point spawnt (via Agent tool):**
- 1x query_generator (Haiku 4.5) — Phase 2
- 1x llm_relevance_scorer (Haiku 4.5) — Phase 4
- 1x quote_extractor (Haiku 4.5) — Phase 6
- 0-N dbis_browser (Sonnet 4.6 + Chrome MCP) — Phase 5, 1 per fehlgeschlagenem PDF

**Python CLI-Module (via Bash):**
- search_engine.py
- five_d_scorer.py
- pdf_parser.py
- unpaywall_client.py, core_client.py

**Config Files:**
- `config/research_modes.yaml` - Modi-Definitionen
- `config/academic_context.md` - User Context (optional)
- `.claude/settings.json` - Chrome MCP Config

**State:**
- SQLite: `~/.cache/academic_agent/sessions/<session_id>.db`
- JSON Export: `./research_results_<session_id>.json`

**Chrome MCP:**
- Config: `.claude/settings.json`
- Browser: Visible (headful mode)
- Login: Manual (User interacts)

---

## State & Persistenz

**SQLite Database:** `~/.cache/academic_agent/research.db`
- Tables: research_sessions, candidates, papers, quotes

**JSON Backups:** `~/.cache/academic_agent/backups/<session_id>.json`

**Checkpoints:** `~/.cache/academic_agent/checkpoints/`
- Auto-Save: Alle 5 Minuten
- Resume: `/research-resume <session_id>`

---

## Testing (nach pip install)

```bash
# Config Loader testen
venv/bin/python .claude/skills/research/scripts/config_loader.py --mode standard --query "Test"

# Mit JSON Output
venv/bin/python .claude/skills/research/scripts/config_loader.py --mode quick --query "AI" --json
```

---

## Beispiel-Flow

```
User: /research