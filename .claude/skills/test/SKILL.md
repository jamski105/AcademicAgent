# Test Mode Skill - Academic Agent v2.3

**Command:** `/test`
**Purpose:** Test system functionality and collect feedback for debugging

---

## Mission

You are the **Test Mode Coordinator** for Academic Agent v2.3.

Your job is to:
1. **Test each system component** systematically
2. **Collect detailed feedback** (success/failure/errors)
3. **Generate a test report** for the developer
4. **Identify issues** and suggest fixes

---

## Test Workflow

### Phase 1: Environment Check

```bash
# Check Python
python3 --version

# Check venv
source venv/bin/activate 2>&1 || echo "⚠️  venv not activated"

# Check dependencies
python3 -c "import yaml, sqlalchemy, pymupdf, rich; print('✅ Core deps OK')" 2>&1

# Check Chrome MCP
npx -y @eddym06/custom-chrome-mcp@latest --version 2>&1 | head -1

# Check config files
ls -la config/*.yaml | wc -l
```

**Expected:** Python 3.11+, venv active, all deps installed, Chrome MCP working, 5 config files

**Feedback:**
- ✅ Environment ready
- ⚠️ Missing dependencies
- ❌ Critical error

---

### Phase 2: Config Validation

```bash
# Test orchestrator
python3 -m src.search.dbis_search_orchestrator --test 2>&1

# Test discipline classifier
python3 -m src.classification.discipline_classifier \
  --query "Lateinische Metrik" \
  --test 2>&1
```

**Expected:** Both tests pass, discovery mode activated for Rechtswissenschaft

**Feedback:**
- ✅ Config loads correctly
- ⚠️ Warnings (non-critical)
- ❌ Config errors (module not found, syntax error, etc.)

---

### Phase 3: Agent Spawn Test

Test spawning each agent individually:

```markdown
# Test 1: query_generator
Task(subagent_type="query_generator", prompt='{
  "user_query": "DevOps Governance",
  "research_mode": "quick"
}')

# Test 2: discipline_classifier
Task(subagent_type="discipline_classifier", prompt='{
  "user_query": "Mietrecht Kündigungsfristen",
  "expanded_queries": ["Tenant law termination periods"]
}')

# Test 3: llm_relevance_scorer
Task(subagent_type="llm_relevance_scorer", prompt='{
  "user_query": "DevOps",
  "papers": [
    {
      "title": "DevOps Governance Framework",
      "abstract": "This paper presents a governance framework for DevOps...",
      "authors": ["Smith, J."],
      "year": 2023
    }
  ]
}')
```

**Feedback for each:**
- ✅ Agent spawned successfully
- ✅ Agent returned valid JSON
- ⚠️ Agent timeout (increase timeout_seconds?)
- ⚠️ Agent returned invalid format
- ❌ Agent not found (name mismatch?)
- ❌ Agent crashed (check error message)

---

### Phase 4: DBIS Selector Validation (Manual)

**Instructions for user:**

```
1. Open browser: https://dbis.ur.de/dbis/dbliste.php?bib_id=ubtib&lett=f&sGeb=9.1
2. Open DevTools (F12) → Console
3. Test selectors:

// Database entries
document.querySelectorAll("tr[id^='db_']")
// Should find 20+ elements

// Database names
document.querySelector("td.td2 a")
// Should find first database name

// Traffic lights
document.querySelector("img[src*='dbis_']")
// Should find ampel image
```

**User Response Required:**
- How many databases found? ___
- Selectors work? (Yes/No) ___
- If No, describe HTML structure: ___

---

### Phase 5: Mini Research Test (Quick Mode)

```
Run a quick test research:
User Query: "DevOps Governance"
Mode: Quick (15 papers, ~20 min, APIs only - NO DBIS)
```

**Monitor:**
- Phase 1: Context Setup ✓
- Phase 2: Query Generation (query_generator agent)
- Phase 2a: Discipline Classification (discipline_classifier)
- Phase 3: API Search ONLY (CrossRef, OpenAlex, S2)
- Phase 4: Ranking (5D + llm_relevance_scorer)
- Phase 5: PDF Download (Unpaywall + CORE, NO dbis_browser)
- Phase 6: Quote Extraction (quote_extractor)
- Phase 7: Export

**Feedback:**
For each phase:
- ✅ Phase completed
- ⚠️ Phase had warnings (describe)
- ❌ Phase failed (error message)

---

### Phase 6: DBIS Discovery Test (CRITICAL)

```
Run DBIS Discovery test:
User Query: "Mietrecht Kündigungsfristen"
Mode: Standard (25 papers, DBIS enabled)
```

**Monitor DBIS Search Phase:**
```
Phase 3 - Track 2: DBIS Search
  → Orchestrator prepares config
  → dbis_search agent spawned
  → Discovery Mode activated? (Yes/No)
  → Browser opens? (Yes/No)
  → DBIS page loads? (Yes/No)
  → Databases scraped? (Yes/No)
  → How many databases found? ___
  → TOP 5 selected? (list them): ___
  → Searches each database? (Yes/No)
  → Papers found? (count): ___
  → Errors? (describe): ___
```

**Feedback:**
- ✅ Discovery worked perfectly
- ⚠️ Discovery found databases but had issues (describe)
- ❌ Discovery failed completely (error)

---

## Test Report Generation

After all phases, create a test report:

```markdown
# Test Report - Academic Agent v2.3

**Date:** {date}
**Tester:** {your name}
**Duration:** {total time}

## Summary
- Environment: ✅/⚠️/❌
- Config: ✅/⚠️/❌
- Agent Spawning: ✅/⚠️/❌
- DBIS Selectors: ✅/⚠️/❌
- Mini Research: ✅/⚠️/❌
- DBIS Discovery: ✅/⚠️/❌

## Detailed Feedback

### Phase 1: Environment
Status: ✅/⚠️/❌
Issues: {describe any issues}
Suggestions: {how to fix}

### Phase 2: Config
Status: ✅/⚠️/❌
Issues: {describe}
Suggestions: {fixes}

### Phase 3: Agent Spawning
query_generator: ✅/⚠️/❌ {notes}
discipline_classifier: ✅/⚠️/❌ {notes}
llm_relevance_scorer: ✅/⚠️/❌ {notes}

### Phase 4: DBIS Selectors
Selectors work: Yes/No
Databases found: {count}
Issues: {describe}
HTML structure notes: {if selectors don't work}

### Phase 5: Mini Research
Duration: {time}
Papers found: {count}
PDFs downloaded: {count}
Quotes extracted: {count}
Errors: {list}

### Phase 6: DBIS Discovery
Discovery activated: Yes/No
Databases found: {count}
Databases selected: {list}
Papers from DBIS: {count}
Issues: {describe}

## Critical Bugs
{list any show-stoppers}

## Warnings
{list non-critical issues}

## Success Stories
{list what worked well}

## Recommendations
{list improvements}
```

Save report to: `runs/test_report_{timestamp}.md`

---

## Feedback Collection Format

**For Developer (Jonas):**

After each test run, collect:

```json
{
  "test_run_id": "test_{timestamp}",
  "version": "v2.3",
  "environment": {
    "os": "{OS}",
    "python_version": "{version}",
    "node_version": "{version}",
    "chrome_installed": true/false
  },
  "results": {
    "environment_check": {
      "status": "pass/warn/fail",
      "details": "{details}",
      "errors": ["{error messages}"]
    },
    "config_validation": {
      "orchestrator_test": "pass/fail",
      "discipline_classifier_test": "pass/fail",
      "errors": []
    },
    "agent_spawning": {
      "query_generator": "pass/fail",
      "discipline_classifier": "pass/fail",
      "llm_relevance_scorer": "pass/fail",
      "errors": []
    },
    "dbis_selectors": {
      "manual_test_completed": true/false,
      "databases_found": {count},
      "selectors_work": true/false,
      "issues": "{description}"
    },
    "mini_research": {
      "completed": true/false,
      "duration_minutes": {time},
      "papers_found": {count},
      "pdfs_downloaded": {count},
      "quotes_extracted": {count},
      "errors": []
    },
    "dbis_discovery": {
      "completed": true/false,
      "discovery_activated": true/false,
      "databases_found": {count},
      "databases_selected": ["{list}"],
      "papers_from_dbis": {count},
      "errors": []
    }
  },
  "critical_bugs": ["{list}"],
  "warnings": ["{list}"],
  "recommendations": ["{list}"]
}
```

Save to: `runs/feedback_{timestamp}.json`

---

## Usage

```bash
# In Claude Code:
/test

# Or with specific phase:
/test phase=dbis_discovery

# Or quick validation only:
/test quick
```

---

## Notes for Tester

- **Be patient:** Full test takes 30-60 minutes
- **Take notes:** Describe errors in detail
- **Screenshots:** Take screenshots of DBIS page for selector validation
- **Logs:** Check `runs/test_*/session_log.txt` for detailed errors
- **Don't skip phases:** Each phase tests different components

---

**Ready to test!** 🧪
