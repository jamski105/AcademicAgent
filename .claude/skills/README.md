# Skills System - Developer Documentation

**Version:** 2.2
**Audience:** Developers & Contributors

This document explains the internal architecture of the AcademicAgent skill system.

---

## 🏗️ Architecture Overview

The AcademicAgent uses a **two-layer architecture**:

```
User Command (/start-research)
    ↓
.claude/skills/start-research/SKILL.md (Entry Point)
    ↓
.claude/agents/setup-agent.md (Agent Instructions)
    ↓
Claude Code executes agent logic
```

### Layer 1: Skills (Entry Points)

**Location:** `.claude/skills/*/SKILL.md`

**Purpose:**
- User-facing entry point
- Metadata and configuration
- Parameter handling
- Agent invocation

**Format:** Claude Code Skill format with YAML frontmatter

### Layer 2: Agents (System Prompts)

**Location:** `.claude/agents/*.md`

**Purpose:**
- Detailed agent instructions
- Tool usage guidelines
- Error handling logic
- Domain-specific knowledge

**Format:** YAML frontmatter + Markdown instructions

---

## 📁 Directory Structure

```
.claude/
├── skills/                      # User-facing entry points
│   ├── start-research/
│   │   └── SKILL.md            # Main entry point
│   ├── orchestrator/
│   │   └── SKILL.md            # Coordinates all phases
│   ├── setup-agent/
│   │   └── SKILL.md            # Interactive config creation
│   ├── browser-agent/
│   │   └── SKILL.md            # Browser automation
│   ├── search-agent/
│   │   └── SKILL.md            # Search string generation
│   ├── scoring-agent/
│   │   └── SKILL.md            # 5D scoring & ranking
│   └── extraction-agent/
│       └── SKILL.md            # PDF quote extraction
│
└── agents/                      # Agent system prompts
    ├── setup-agent.md          # 663 lines - full instructions
    ├── browser-agent.md        # CDP navigation logic
    ├── search-agent.md         # Boolean query generation
    ├── scoring-agent.md        # 5D ranking algorithm
    └── extraction-agent.md     # PDF processing logic
```

**Key Insight:** Skills (40 lines) are thin wrappers that invoke Agents (600+ lines).

---

## 🔗 How Skills and Agents Connect

### Example: `/browser-agent`

**Step 1: User invokes skill**
```
/browser-agent Navigate to IEEE Xplore
```

**Step 2: Skill file loaded**

`.claude/skills/browser-agent/SKILL.md`:
```markdown
## Configuration

```json
{
  "context": "fork",
  "agent": "browser-agent",
  "disable-model-invocation": true
}
```

## Parameters

- `$ARGUMENTS`: Task description

## Instructions

The browser-agent has access to:
- Read, Grep, Glob
- Bash (for CDP helper scripts)
...
```

**Step 3: Agent file loaded**

Claude Code sees `"agent": "browser-agent"` and loads:

`.claude/agents/browser-agent.md`:
```yaml
---
name: browser-agent
description: Browser automation for database navigation
tools:
  - Read
  - Grep
  - Glob
  - Bash
  - WebFetch
disallowedTools:
  - Write
  - Edit
  - Task
permissionMode: default
---

# Browser-Agent Instructions

You are the Browser-Agent for scientific databases.

Your task:
1. Connect to Chrome via CDP
2. Navigate to databases
3. Execute searches
...
```

**Step 4: Agent executes task**

The agent reads the full instructions from `.claude/agents/browser-agent.md` and executes the user's task.

---

## 📋 Skill Configuration Reference

### Context Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| `main_thread` | Agent runs in main conversation | Orchestrator, start-research (needs Write access) |
| `fork` | Agent runs in isolated subprocess | Worker agents (browser, search, scoring, extraction) |

**Rule:** Only `main_thread` agents can use `Write`, `Edit`, and `Task` tools.

### Agent Configuration

**Key:** `"agent": "browser-agent"`

This tells Claude Code to load the corresponding agent file from `.claude/agents/`.

### Model Invocation

**Key:** `"disable-model-invocation": true`

**Purpose:** Prevents Claude from using the API for simple tasks. The agent uses only tools.

**When to use:** For all skills (reduces cost and latency).

---

## 🔒 Permissions System

### Permission Modes

**Defined in:** `.claude/agents/*.md` frontmatter

```yaml
permissionMode: default  # Ask for approval on sensitive operations
```

### Tool Allowances

**Example from browser-agent:**

```yaml
tools:
  - Read
  - Grep
  - Glob
  - Bash
  - WebFetch
disallowedTools:
  - Write
  - Edit
  - Task
```

**Why disallow Write/Edit for worker agents?**
- Worker agents should return JSON data to orchestrator
- Orchestrator handles all file writes (centralized state management)
- Prevents conflicts and ensures consistency

### Special Cases

**Orchestrator (main_thread):**
```yaml
tools:
  - Read
  - Grep
  - Glob
  - Bash
  - Write      # ✅ Allowed
  - Edit       # ✅ Allowed
  - Task       # ✅ Allowed (to spawn subagents)
```

**Worker agents (fork):**
```yaml
tools:
  - Read
  - Grep
  - Glob
  - Bash
disallowedTools:
  - Write      # ❌ Not allowed
  - Edit       # ❌ Not allowed
  - Task       # ❌ Not allowed (no nesting)
```

---

## 🆕 Adding a New Skill

### Step 1: Create Skill Entry Point

**File:** `.claude/skills/my-new-agent/SKILL.md`

```markdown
# my-new-agent

Brief description of what this skill does

## Configuration

```json
{
  "context": "fork",
  "agent": "my-new-agent",
  "disable-model-invocation": true
}
```

## Parameters

- `$ARGUMENTS`: Task description

## Instructions

This skill delegates to the my-new-agent.

Example usage:
```
/my-new-agent Do something
```
```

### Step 2: Create Agent Instructions

**File:** `.claude/agents/my-new-agent.md`

```yaml
---
name: my-new-agent
description: Short description (appears in listings)
tools:
  - Read
  - Grep
  - Glob
  - Bash
disallowedTools:
  - Write
  - Edit
  - Task
permissionMode: default
---

# My New Agent

You are the My-New-Agent for [purpose].

## Your Task

1. Step 1: Do something
2. Step 2: Do something else
3. Return structured JSON

## Available Tools

- **Read:** Read config files
- **Grep:** Search for patterns
- **Bash:** Run scripts

## Output Format

Return JSON:
```json
{
  "status": "success",
  "data": {...}
}
```

## Error Handling

If errors occur:
1. Try to recover
2. If unrecoverable, return JSON with error details
```

### Step 3: Test the Skill

```bash
# In Claude Code Chat:
/my-new-agent Test task
```

### Step 4: Document It

Add to [SKILLS_USAGE.md](../../SKILLS_USAGE.md):

```markdown
### `/my-new-agent` (Debug)

**Funktion:** Does something useful

**Input:** Task description

**Output:** JSON with results

**Beispiel:**
```
/my-new-agent Analyze something
```
```

---

## 🎭 Agent Design Patterns

### Pattern 1: Read-Only Worker

**Use Case:** Browser, Search, Scoring, Extraction agents

**Characteristics:**
- `context: fork`
- No Write/Edit/Task tools
- Returns JSON to orchestrator
- Orchestrator persists results

**Example:** browser-agent

```yaml
---
name: browser-agent
tools:
  - Read
  - Grep
  - Glob
  - Bash
disallowedTools:
  - Write
  - Edit
  - Task
---
```

### Pattern 2: Coordinator (Orchestrator)

**Use Case:** Orchestrator, start-research

**Characteristics:**
- `context: main_thread`
- Has Write/Edit/Task tools
- Delegates to worker agents
- Manages state and checkpoints

**Example:** orchestrator

```yaml
---
name: orchestrator
tools:
  - Read
  - Write
  - Edit
  - Task
  - Bash
---
```

### Pattern 3: Interactive Setup

**Use Case:** setup-agent

**Characteristics:**
- `context: main_thread` or `fork` (depends on use case)
- Uses interactive dialogs
- Generates configs
- Can spawn orchestrator

**Example:** setup-agent

```yaml
---
name: setup-agent
tools:
  - Read
  - Write
  - Bash
  - Task
---
```

---

## 🔧 Configuration Files

### Skill Metadata

**File:** `.claude/skills/*/SKILL.md`

**Required fields:**
- `context`: "main_thread" or "fork"
- `agent`: Name of agent file (without .md)
- `disable-model-invocation`: true (recommended)

**Optional fields:**
- `parameters`: Parameter descriptions
- `examples`: Usage examples

### Agent Metadata

**File:** `.claude/agents/*.md`

**Required fields:**
- `name`: Agent identifier
- `description`: Short description
- `tools`: List of allowed tools
- `disallowedTools`: List of forbidden tools

**Optional fields:**
- `permissionMode`: "default" or custom
- Additional YAML fields

---

## 🧪 Testing & Debugging

### Manual Testing

```bash
# Test a skill directly
/browser-agent Navigate to IEEE Xplore

# Check what the agent sees
cat .claude/agents/browser-agent.md

# Verify skill configuration
cat .claude/skills/browser-agent/SKILL.md
```

### Debugging Tips

1. **Agent not loading?**
   - Check `"agent": "browser-agent"` matches filename
   - Verify `.claude/agents/browser-agent.md` exists

2. **Permission denied?**
   - Check `disallowedTools` in agent YAML
   - Verify context mode (fork vs main_thread)

3. **Tool not available?**
   - Check `tools:` list in agent YAML
   - Some tools only work in certain contexts

### Logging

**Orchestrator logs:**
```
runs/[Timestamp]/logs/
├── phase_0.log
├── phase_1.log
├── ...
└── cdp_health.log
```

**Agent output:**

Worker agents return JSON to orchestrator:
```json
{
  "status": "success",
  "data": {
    "databases": [...]
  }
}
```

---

## 📊 Agent Hierarchy

```
Orchestrator (main_thread)
    ├─→ setup-agent (fork or main)
    ├─→ browser-agent (fork)
    │       └─→ CDP scripts (bash)
    ├─→ search-agent (fork)
    ├─→ scoring-agent (fork)
    └─→ extraction-agent (fork)
            └─→ pdftotext (bash)
```

**Rules:**
1. Only orchestrator can spawn agents (`Task` tool)
2. Worker agents cannot spawn sub-agents (no nesting)
3. All state management happens in orchestrator
4. Worker agents are stateless (return JSON)

---

## 🔐 Security & Best Practices

### Least Privilege Principle

**Worker agents should have minimal permissions:**
```yaml
tools:
  - Read
  - Grep
  - Glob
  - Bash  # Only if needed for scripts
disallowedTools:
  - Write
  - Edit
  - Task
```

**Why?**
- Prevents accidental file modifications
- Ensures centralized state management
- Easier to reason about system behavior

### State Management

**Centralized in orchestrator:**
```python
python3 scripts/state_manager.py save <run_dir> <phase> <status>
```

**Never in worker agents:**
```yaml
# ❌ Don't do this in worker agents
disallowedTools:
  - Write  # No state writes
```

### Error Recovery

**Worker agents:**
- Return error JSON to orchestrator
- Orchestrator decides how to handle

**Orchestrator:**
- Uses `scripts/error_handler.sh` for recovery
- Saves state after each phase
- Implements retry logic

---

## 📚 Related Documentation

### For Users

- **[SKILLS_USAGE.md](../../SKILLS_USAGE.md)** - User guide for all skills
- **[README.md](../../README.md)** - Project overview
- **[ERROR_RECOVERY.md](../../ERROR_RECOVERY.md)** - Troubleshooting

### For Developers

- **[AGENT_WORKFLOW.md](../../AGENT_WORKFLOW.md)** - Detailed workflow
- **[.claude/agents/](../agents/)** - Agent instructions
- **[scripts/](../../scripts/)** - Helper scripts

---

## 🚀 Future Improvements

### Planned Features

1. **Agent Composition**
   - Allow controlled nesting (max depth 2)
   - Coordinator → Worker → Helper pattern

2. **Dynamic Agent Loading**
   - Load agent instructions from config
   - Database-specific agent variations

3. **Agent Testing Framework**
   - Unit tests for agents
   - Mock CDP responses
   - Automated skill testing

4. **Performance Monitoring**
   - Track agent execution times
   - Identify bottlenecks
   - Optimize slow phases

---

## 💡 Contributing

### Adding a New Database

1. **Add database pattern:**
   ```bash
   # Edit scripts/database_patterns.json
   {
     "MyNewDB": {
       "search_field": "input[name='query']",
       "search_syntax": "boolean",
       ...
     }
   }
   ```

2. **Update browser-agent:**
   ```bash
   # .claude/agents/browser-agent.md
   # Add MyNewDB-specific navigation logic
   ```

3. **Test:**
   ```
   /browser-agent Navigate to MyNewDB and search for "test"
   ```

### Improving an Existing Agent

1. **Find the agent file:**
   ```bash
   .claude/agents/browser-agent.md
   ```

2. **Edit instructions:**
   ```yaml
   # Add new capabilities, improve error handling, etc.
   ```

3. **Test thoroughly:**
   ```
   /browser-agent Test new feature
   ```

4. **Update documentation:**
   ```bash
   # Update SKILLS_USAGE.md with new features
   ```

---

## 🆘 Support

**Issues:** [GitHub Issues](https://github.com/yourusername/AcademicAgent/issues)

**Questions:** Check existing issues or create a new one

---

**Happy Developing! 🛠️🤖**
