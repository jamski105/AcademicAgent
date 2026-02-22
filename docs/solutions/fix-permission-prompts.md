# Lösung: Zu viele Permission-Prompts

**Problem:** User muss ständig bestätigen:
- Dokumente erstellen/bearbeiten
- Responses zum Agenten durchreichen
- Neue Agents starten

**Ziel:** Auto-Permission für runs/ Ordner und Agent-Operationen

---

## Problem-Analyse

### Warum so viele Prompts?

**Claude Code hat standardmäßig Permission-Guards für:**

1. **File-Operationen:**
   - Write/Edit außerhalb bekannter Ordner
   - Löschen von Dateien
   - Erstellen neuer Ordner

2. **Agent-Kommunikation:**
   - Task()-Spawn erfordert Permission
   - Agent-zu-Agent Messages
   - User-Input durchreichen zu Agent

3. **Bash-Commands:**
   - Gefährliche Commands (rm, mv, etc.)
   - Network-Zugriffe
   - Long-running processes

---

## Wo ist das definiert?

### Academic Agent Auto-Permission

Das System HAT bereits Auto-Permission-Konzept:

```bash
# In orchestrator-agent.md Zeile 570-620:

## Auto-Permission System

Agents haben AUTOMATISCH Permission für:

✅ Lesen aller Files in runs/$RUN_ID/
✅ Schreiben in runs/$RUN_ID/
✅ Bash-Commands via safe_bash.py
✅ CDP-Zugriffe (Browser-Automatisierung)

KEINE Permission nötig für:
- candidates.json schreiben
- PDFs in downloads/ speichern
- Logs in logs/ schreiben
- State-Updates

CURRENT_AGENT Environment-Variable:
export CURRENT_AGENT="browser-agent"

Wird genutzt für:
- Tracking welcher Agent aktiv ist
- Auto-Permission-Entscheidungen
- Logging
```

### Aber: Claude Code ignoriert das?

**Mögliche Gründe:**

1. **CURRENT_AGENT nicht gesetzt:**
   - Environment-Variable fehlt
   - Claude Code prüft sie nicht
   - Nur für Logging genutzt, nicht für Permissions

2. **runs/ Ordner nicht in Claude Code Whitelist:**
   - Claude Code kennt nur: `.git/`, `node_modules/`, etc.
   - `runs/` ist custom und nicht auto-erlaubt

3. **Agent-to-Agent Prompts:**
   - Claude Code SDK erfordert explizite Permission
   - Keine Auto-Approve für Task()-Spawns

---

## Lösungen

### Lösung 1: Claude Code Settings anpassen

```json
// .vscode/settings.json oder ~/.claude/config.json

{
  "claude.autoApprove": {
    "write": [
      "runs/**/*",
      "docs/**/*",
      ".claude/templates/**/*"
    ],
    "read": [
      "**/*"  // Alles lesen erlaubt
    ],
    "bash": {
      "safe_commands": [
        "jq",
        "grep",
        "find",
        "ls",
        "cat",
        "curl",
        "python3 scripts/*.py"
      ],
      "allowed_patterns": [
        "^cd runs/.*",
        "^mkdir -p runs/.*",
        "^python3 scripts/safe_bash\\.py.*"
      ]
    },
    "agents": {
      "auto_spawn": [
        "orchestrator-agent",
        "browser-agent",
        "scoring-agent",
        "extraction-agent",
        "search-agent",
        "setup-agent"
      ],
      "auto_forward_responses": true
    }
  }
}
```

**Problem:** Diese API existiert möglicherweise nicht in Claude Code

### Lösung 2: Wrapper-Script mit --yes Flag

```bash
#!/bin/bash
# scripts/auto_approve_wrapper.sh

# Setze Environment für Auto-Approve
export CLAUDE_AUTO_APPROVE_WRITE="runs/**,docs/**"
export CLAUDE_AUTO_APPROVE_AGENTS="*-agent"
export CLAUDE_AUTO_FORWARD_RESPONSES="true"

# Run mit Auto-Flags
claude code task \
  --agent "$1" \
  --prompt "$2" \
  --auto-approve-writes \
  --auto-approve-agents \
  --yes
```

Nutze in academicagent Skill:

```bash
# Statt:
Task(orchestrator-agent, ...)

# Nutze:
bash scripts/auto_approve_wrapper.sh orchestrator-agent "..."
```

**Problem:** --auto-approve Flags existieren möglicherweise nicht

### Lösung 3: Pre-Create alle Files

Wenn Claude Code erlaubt, **bestehende** Files zu bearbeiten ohne Prompt:

```bash
# In academicagent Skill BEFORE spawning orchestrator:

echo "📁 Erstelle Output-Struktur..."

# Pre-create alle Files die beschrieben werden
touch "runs/$RUN_ID/metadata/candidates.json"
touch "runs/$RUN_ID/metadata/ranked_candidates.json"
touch "runs/$RUN_ID/metadata/quotes.json"
touch "runs/$RUN_ID/metadata/research_state.json"
touch "runs/$RUN_ID/output/Quote_Library.csv"
touch "runs/$RUN_ID/output/bibliography.bib"
touch "runs/$RUN_ID/output/Annotated_Bibliography.md"

# Pre-create Log-Files
for agent in orchestrator browser scoring extraction; do
    touch "runs/$RUN_ID/logs/${agent}_agent.log"
done

echo "✓ Struktur erstellt - Agents können ohne Permission schreiben"
```

**Vorteil:** Edit statt Write erfordert oft weniger Permissions

### Lösung 4: Single JSON statt viele Files

**Problem:** 20 Files = 20 Permission-Prompts

**Lösung:** Alles in einem File

```json
// runs/<run-id>/state.json

{
  "config": { ... },
  "candidates": [ ... ],
  "ranked": [ ... ],
  "quotes": [ ... ],
  "state": { ... },
  "logs": {
    "orchestrator": [ ... ],
    "browser": [ ... ]
  }
}
```

Agents schreiben nur EINE Datei → nur 1 Permission nötig

```bash
# Agents nutzen jq für Updates:
jq '.candidates += [new_paper]' state.json > tmp && mv tmp state.json
```

### Lösung 5: Trust Mode für runs/ Ordner

```bash
# In .claude/academic_context.md ergänzen:

## Permission Settings

**WICHTIG:** Dieses Projekt nutzt den `runs/` Ordner für Output.

Bitte aktiviere "Trust Mode" für diesen Ordner:

1. VSCode: Workspace als "Trusted" markieren
2. Claude Code: `runs/` in Auto-Approve Liste
3. Oder: Nutze Environment-Variable:

```bash
export CLAUDE_TRUST_WORKSPACE=true
export CLAUDE_AUTO_APPROVE_RUNS_FOLDER=true
```

Agents dürfen OHNE Bestätigung:
- In runs/<run-id>/ schreiben
- PDFs nach runs/<run-id>/downloads/ laden
- Logs in runs/<run-id>/logs/ schreiben
```

---

## Agent-Spawning-Permissions

### Problem: Task() erfordert Permission

**Warum?**
- Spawning von Agents = Code-Execution
- Security-Feature von Claude Code
- Verhindert ungewollte Agent-Spawns

**Lösungen:**

#### Option A: Pre-Approve in academicagent Skill

```bash
# In .claude/skills/academicagent.sh:

# User-Frage VOR orchestrator-spawn:
echo "Der Orchestrator wird folgende Agents spawnen:"
echo "  • browser-agent (für Datenbanksuche)"
echo "  • scoring-agent (für Paper-Ranking)"
echo "  • extraction-agent (für Zitat-Extraktion)"
echo ""
read -p "Alle Agents erlauben? [J/n] " APPROVE

if [[ "$APPROVE" =~ ^[Nn] ]]; then
    echo "Abgebrochen."
    exit 1
fi

export APPROVED_AGENTS="orchestrator-agent,browser-agent,scoring-agent,extraction-agent"
```

#### Option B: Session-wide Permission

```bash
# Bei Start von /academicagent:

claude code config set \
  --session \
  --key "auto_approve_agents" \
  --value "orchestrator-agent,browser-agent,scoring-agent,extraction-agent"

# Nur für diese Session gültig
```

#### Option C: .claude/permissions.json

```json
// .claude/permissions.json

{
  "agents": {
    "auto_approve": [
      {
        "pattern": "*-agent",
        "scope": "runs/**",
        "reason": "Academic Agent Workflow"
      }
    ]
  },
  "files": {
    "auto_write": [
      "runs/**/*"
    ]
  }
}
```

---

## Response-Forwarding-Problem

### Problem: Agent fragt User, aber Response muss approved werden

**Scenario:**
```
browser-agent: ⚠️  DBIS erfordert Login

Bitte:
1. Wechsle zu Chrome
2. Logge dich ein
3. Drücke ENTER

[Warte auf User-Input...]

Claude Code: "Agent wartet auf Input. Durchreichen? [Ja/Nein]"
```

Das ist nervig weil es **erwartet** ist!

**Lösung:**

#### Option A: Batch-Approve bei Agent-Start

```bash
# Wenn orchestrator spawnt:
echo "⚠️  HINWEIS: Agents können um Login bitten"
echo "Dein Input wird automatisch durchgereicht."
echo ""

export CLAUDE_AUTO_FORWARD_AGENT_PROMPTS=true
```

#### Option B: Pre-Warn User

```bash
# In setup-agent:

echo "╔══════════════════════════════════════╗"
echo "║   WICHTIG: Datenbank-Authentifizierung  ║"
echo "╚══════════════════════════════════════╝"
echo ""
echo "Während der Suche kann DBIS Login-Prompts zeigen."
echo "Der browser-agent wird dann PAUSIEREN und dich benachrichtigen."
echo ""
echo "Bitte halte deine Uni-Zugangsdaten bereit."
echo ""
read -p "Verstanden? [ENTER]"

# Jetzt ist User vorbereitet und erwartet Prompts
```

---

## Empfohlene Kombination

### Quick Fix (sofort machbar):

1. **Lösung 3:** Pre-Create alle Files
2. **Option B (Agent-Spawning):** Session-wide Permission
3. **Option B (Response-Forward):** Pre-Warn User

```bash
# In academicagent Skill:

# 1. Pre-Create Structure
bash scripts/create_run_structure.sh "$RUN_ID"

# 2. Request Session Permission
echo "Dieser Workflow nutzt 3 Sub-Agents."
read -p "Alle Agents auto-approven? [J/n] " APPROVE
if [[ ! "$APPROVE" =~ ^[Nn] ]]; then
    export CLAUDE_SESSION_AUTO_APPROVE_AGENTS=true
fi

# 3. Warn about Prompts
echo "⚠️  Browser-Agent kann Login-Prompts zeigen - bitte bereit halten."
sleep 2

# 4. Run
Task(orchestrator-agent, ...)
```

### Langfristig (SDK-Feature-Request):

```bash
# Wünschenswert in Claude Code SDK:

Task(
    subagent_type="orchestrator-agent",
    auto_approve_subagents=True,  # ← Alle Spawns erlauben
    auto_forward_prompts=True,    # ← User-Input durchreichen
    trusted_workspace=True         # ← runs/ auto-approve
)
```

---

## Zusammenfassung

### Aktuelle Situation
- ❌ 10+ Permission-Prompts pro Run
- ❌ Jeder File-Write erfordert Approval
- ❌ Jeder Agent-Spawn erfordert Approval
- ❌ Jeder User-Input-Forward erfordert Approval

### Nach Fix
- ✅ 1-2 Permissions (zu Beginn)
- ✅ runs/ Ordner ist trusted
- ✅ Agents spawnen automatisch
- ✅ User-Prompts werden durchgereicht

### Implementation
1. Pre-Create File-Struktur (10 min)
2. Session Permission Request (5 min)
3. Pre-Warn Messages (5 min)
4. Teste mit /academicagent --quick (2 min)

**Total:** 22 Minuten Fix-Zeit

---

**Siehe auch:**
- [critical-issues-report-2026-02-22.md](../analysis/critical-issues-report-2026-02-22.md)
- [fix-agent-spawning.md](./fix-agent-spawning.md)
