# Academic Agent v2.3+ - Agent Prompts

Agent-Definitionen für Claude Code

---

## 📋 Active Agents (5)

### 1. linear_coordinator.md ✅
**Model:** Sonnet 4.6
**Role:** Master Orchestrator
**Status:** ACTIVE
**Description:** Orchestriert 6-Phasen Workflow, spawnt Subagenten, ruft Python-Module via Bash auf

### 2. query_generator.md ✅
**Model:** Haiku 4.5
**Role:** Query Expansion
**Status:** ACTIVE
**Description:** Expandiert User-Query zu API-spezifischen Boolean-Queries (CrossRef, OpenAlex, S2)

### 3. llm_relevance_scorer.md ✅
**Model:** Haiku 4.5
**Role:** Semantic Relevance Scoring
**Status:** ACTIVE
**Description:** Bewertet Papers semantisch (0-1 Score), batch-processing, JSON I/O

### 4. quote_extractor.md ✅
**Model:** Haiku 4.5
**Role:** Quote Extraction
**Status:** ACTIVE
**Description:** Extrahiert 2-3 relevante Zitate pro Paper (≤25 Wörter), mit Context-Window

### 5. dbis_browser.md ✅
**Model:** Sonnet 4.6
**Role:** Browser Automation (Chrome MCP)
**Status:** ACTIVE
**Description:** PDF-Download via institutionellem Zugang (TIB Shibboleth), interaktiver Login

---

## 🗑️ Deprecated Agents (1)

### five_d_scorer.md ⚠️
**Status:** DEPRECATED
**Replaced by:**
- `src/ranking/five_d_scorer.py` (Python CLI) - 5D-Scoring
- `llm_relevance_scorer.md` (Agent) - Semantic Relevance

**Reason:** Aufgeteilt in deterministische Python-Logik und LLM-basierte Semantik

---

## 🏗️ Agent Architecture

```
User → /research
  ↓
SKILL.md spawns:
  ↓
┌─────────────────────────────────────┐
│ linear_coordinator (Sonnet)        │
│                                     │
│ Phase 1: Context Setup              │
│ Phase 2: Query Gen → query_generator│
│ Phase 3: Search → Python CLI        │
│ Phase 4: Ranking → five_d_scorer.py │
│          + llm_relevance_scorer     │
│ Phase 5: PDF → dbis_browser         │
│ Phase 6: Quotes → quote_extractor   │
└─────────────────────────────────────┘
```

---

## 📝 Agent Guidelines

### When to use Agents:
- ✅ Semantic understanding (query expansion, relevance scoring)
- ✅ Creative generation (quote extraction)
- ✅ Complex decision-making (browser automation)
- ✅ Natural language processing

### When to use Python Modules:
- ✅ Deterministic calculations (citations, recency, venue scores)
- ✅ API calls (CrossRef, OpenAlex, Semantic Scholar)
- ✅ Data processing (deduplication, parsing)
- ✅ File I/O (PDF parsing, database operations)

---

## 🔧 Development

### Creating a new Agent:

1. Create `my_agent.md` in this directory
2. Add front matter:
```yaml
---
model: claude-haiku-4-5-20251001
tools: []
---
```
3. Define:
   - Role & Responsibility
   - Input/Output Format (JSON)
   - Workflow/Strategy
   - Examples
4. Spawn from coordinator:
```python
Task(subagent_type="my_agent", prompt="...")
```

### Testing Agents:

```bash
# Integration tests
pytest tests/agents/test_my_agent.py

# E2E test
/research "Test Query"
```

---

## 📖 Documentation

- **Architecture:** `docs/ARCHITECTURE_v2.md`
- **Module Specs:** `docs/MODULE_SPECS_v2.md`
- **Workflow:** `WORKFLOW.md`

---

**Last Updated:** 2026-02-27
