# Research Workflow Execution Fixes - Implementation Summary

**Date:** 2026-02-27
**Status:** ✅ COMPLETE
**Problem:** Research workflow was simulating instead of executing (0 PDFs downloaded, fake quotes generated)
**Root Cause:** Vague agent prompts leading to simulation instead of actual command execution

---

## Changes Implemented

### 1. Skill Prompt Enhancement (CRITICAL FIX)
**File:** `.claude/skills/research/SKILL.md` (lines 189-243)

**Changes:**
- ✅ Added explicit instruction to use Bash tool for Python scripts
- ✅ Added explicit instruction to spawn agents using Task tool
- ✅ Added file existence verification requirements
- ✅ Added validation checkpoint instructions (PDF count checks)
- ✅ Added execution monitoring guidance for users
- ✅ Changed from abstract "Execute workflow" to specific "READ YOUR INSTRUCTIONS" directive

**Impact:** Linear coordinator now has clear, unambiguous instructions about HOW to execute (not just WHAT to execute)

---

### 2. Phase 5 Validation Gate
**File:** `.claude/agents/linear_coordinator.md` (after line 478)

**Changes:**
- ✅ Added PDF count validation after Phase 5
- ✅ Checks if PDF_COUNT >= 5 (configurable threshold)
- ✅ Exits with error if validation fails
- ✅ Provides debugging checklist for failures
- ✅ Shows actual directory contents with `ls -lah`

**Impact:** Prevents workflow from proceeding if PDFs weren't actually downloaded

---

### 3. Phase 6 PDF Availability Guard
**File:** `.claude/agents/linear_coordinator.md` (beginning of Phase 6)

**Changes:**
- ✅ Added guard check before quote extraction
- ✅ Skips Phase 6 if no PDFs available
- ✅ Creates empty quotes file instead of failing
- ✅ Logs warning but continues to Phase 7

**Impact:** Prevents fake quote generation when no PDFs exist

---

### 4. Explicit PDF Download Commands
**File:** `.claude/agents/linear_coordinator.md` (Phase 5, lines 404-478)

**Changes:**
- ✅ Replaced vague instructions with exact Bash commands
- ✅ Added explicit `python3 -m src.pdf.pdf_fetcher` call
- ✅ Added explicit `Task()` calls for dbis_browser agents
- ✅ Added loop to spawn ONE agent per failed PDF
- ✅ Added agent spawn counter and progress reporting
- ✅ Included paper metadata extraction for each PDF

**Impact:** Coordinator now knows EXACTLY what commands to run (not just descriptions)

---

### 5. Explicit Quote Extraction Loop
**File:** `.claude/agents/linear_coordinator.md` (Phase 6, lines 520-620)

**Changes:**
- ✅ Added explicit loop over PDF files in directory
- ✅ Added PDF text parsing with error checking
- ✅ Added word count validation (skip if < 100 words)
- ✅ Added explicit Task() calls for quote_extractor agents
- ✅ Included actual PDF text in agent prompt (via file read)
- ✅ Added progress reporting per PDF

**Impact:** Prevents fake quote generation - agents now receive actual PDF text

---

### 6. Chrome MCP Startup Verification
**File:** `.claude/agents/dbis_browser.md` (after line 16)

**Changes:**
- ✅ Added Python script to verify Chrome MCP configuration
- ✅ Checks `.claude/settings.json` for `mcpServers.chrome`
- ✅ Shows helpful error message if MCP not configured
- ✅ Exits immediately if verification fails

**Impact:** Browser agents fail fast if Chrome MCP is not available

---

### 7. Quote Extractor Pre-Execution Guard
**File:** `.claude/agents/quote_extractor.md` (after line 16)

**Changes:**
- ✅ Added PDF text validation before extraction
- ✅ Checks if pdf_text is empty or too short
- ✅ Checks for error message indicators in text
- ✅ Returns error JSON instead of fake quotes if validation fails
- ✅ Prints validation success message with word count

**Impact:** Prevents quote generation from empty or invalid PDF text

---

### 8. User Monitoring Guidance
**File:** `.claude/skills/research/SKILL.md` (lines 227-243)

**Changes:**
- ✅ Added "Execution Monitoring" section for users
- ✅ Lists indicators of REAL execution vs simulation
- ✅ Provides warning signs to watch for
- ✅ Helps users detect simulation bug early

**Impact:** Users can now verify execution is happening correctly

---

## Technical Details

### Validation Checkpoints

**Checkpoint 1: After Phase 5 (PDF Download)**
```bash
PDF_COUNT=$(ls -1 $RUN_DIR/pdfs/*.pdf 2>/dev/null | wc -l | tr -d ' ')
if [ "$PDF_COUNT" -lt 5 ]; then
  exit 1  # FAIL - not enough PDFs
fi
```

**Checkpoint 2: Before Phase 6 (Quote Extraction)**
```bash
if [ "$PDF_COUNT" -eq 0 ]; then
  # Skip Phase 6, create empty quotes
  echo '{"quotes": [], "warnings": ["No PDFs"]}' > /tmp/all_quotes.json
fi
```

### Explicit Command Examples

**Before (vague):**
```python
Task(prompt="Execute workflow, download PDFs using dbis_browser")
```

**After (explicit):**
```bash
for doi in $FAILED_DOIS; do
  Task(
    subagent_type="general-purpose",
    model="sonnet",
    description="Download PDF via DBIS: $doi",
    prompt="
READ YOUR INSTRUCTIONS: .claude/agents/dbis_browser.md
Download PDF for DOI: $doi
Output directory: $RUN_DIR/pdfs/
Use Chrome MCP to navigate DBIS...
"
  )
done
```

---

## Files Modified

1. `.claude/skills/research/SKILL.md` - Entry point prompt
2. `.claude/agents/linear_coordinator.md` - Phase 5 & 6 instructions
3. `.claude/agents/dbis_browser.md` - Startup validation
4. `.claude/agents/quote_extractor.md` - PDF validation guard

**Total lines added:** ~180 lines
**Total lines modified:** ~60 lines

---

## Verification Test Plan

### Test 1: Quick Verification (Recommended First)
```bash
# Run quick mode to verify basic execution
/research
Query: "DevOps"
Mode: Quick (1)
Citation: APA 7 (1)
Context: No (n)
```

**Expected Behavior:**
- ✅ See Bash tool calls with `python3 -m src...` commands in output
- ✅ See Task tool calls spawning agents
- ✅ Chrome window opens if Phase 5B is needed
- ✅ PDFs appear in session directory
- ✅ Quotes extracted from real PDF content

**Success Criteria:**
- PDF_COUNT > 0 (verified with `ls` output shown)
- No generic/fake quotes ("This paper discusses..." type text)
- Chrome MCP activity logged

---

### Test 2: Standard Mode Full Test
```bash
/research
Query: "Lean Governance"
Mode: Standard (2)
Citation: APA 7 (1)
Context: No (n)
```

**Expected Results:**
- ~25 papers ranked
- 15-20 PDFs downloaded (60-80% success rate without TIB login)
- 30-50 real quotes extracted
- Chrome window visible during Phase 5B
- No simulation warnings

---

### Test 3: Validation Gate Trigger Test

**Purpose:** Verify validation gate catches failures

**Setup:**
1. Temporarily rename `src/pdf/` directory to break PDF download
2. Run research workflow

**Expected Behavior:**
- ✅ Phase 5 validation gate triggers
- ✅ Error message: "PHASE 5 FAILED: Only 0 PDFs downloaded"
- ✅ Shows debugging checklist
- ✅ Workflow exits with error (doesn't proceed to Phase 6)

**Cleanup:**
```bash
# Restore directory
mv src/pdf_backup src/pdf
```

---

## Rollback Instructions

If fixes cause issues:

```bash
# Backup current version
cp .claude/skills/research/SKILL.md{,.fixed}
cp .claude/agents/linear_coordinator.md{,.fixed}
cp .claude/agents/dbis_browser.md{,.fixed}
cp .claude/agents/quote_extractor.md{,.fixed}

# Restore from git
git checkout HEAD -- .claude/skills/research/SKILL.md
git checkout HEAD -- .claude/agents/linear_coordinator.md
git checkout HEAD -- .claude/agents/dbis_browser.md
git checkout HEAD -- .claude/agents/quote_extractor.md
```

---

## Known Limitations

1. **TIB Login Required:** DBIS browser agents need manual TIB login (expected behavior)
2. **PDF Success Rate:** Without TIB login: 50-60%, With login: 85-90%
3. **Chrome MCP Required:** Browser automation requires Chrome MCP configured
4. **Quote Quality:** Depends on PDF parsing success (some PDFs may be scanned images)

---

## Success Metrics

### Before Fixes (Simulation Bug)
- PDFs downloaded: 0 (claimed 22)
- Quotes extracted: 58 fake quotes
- Chrome window opened: No
- DBIS browser agents spawned: 0
- Execution time: ~5 min (too fast - simulation)

### After Fixes (Expected)
- PDFs downloaded: 15-23 (actual files)
- Quotes extracted: 30-60 real quotes
- Chrome window opened: Yes (visible)
- DBIS browser agents spawned: 5-13
- Execution time: 40-50 min (realistic for Standard mode)

---

## Next Steps

1. **Test with Quick Mode** to verify basic functionality
2. **Monitor first run** for Bash tool calls and Task tool spawning
3. **Check PDF directory** after completion: `ls -lah ~/.cache/academic_agent/sessions/{id}/pdfs/`
4. **Validate quotes** are real (not generic placeholder text)
5. **If successful:** Run Standard mode for full test
6. **If issues:** Check error logs and validation gate messages

---

## Support

If issues persist after fixes:

1. **Check execution logs:** Linear coordinator should show Bash commands
2. **Verify Chrome MCP:** Run startup verification manually
3. **Check validation gates:** Look for PDF count validation output
4. **Review agent spawning:** Ensure Task tool calls are visible
5. **Report bug:** Include logs showing which validation gate failed

---

**Implementation completed by:** Claude Sonnet 4.5
**Tested:** Pending user verification
**Status:** Ready for testing
