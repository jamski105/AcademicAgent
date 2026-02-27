# DBIS Integration Test Plan

**Purpose:** Verify the DBIS-first workflow for PDF downloads

---

## Prerequisites

1. ✅ Chrome MCP server configured in `.claude/settings.json`
2. ✅ `config/dbis_publishers.yaml` exists
3. ✅ User has TIB/Leibniz Uni credentials for DBIS login
4. ✅ Google Chrome installed

---

## Test 1: Basic DBIS Navigation

**Goal:** Verify agent can navigate to DBIS and search for a database

**Steps:**

1. Spawn dbis_browser agent:
```json
{
  "doi": "10.1109/ACCESS.2021.3064112",
  "paper_title": "Test IEEE Paper"
}
```

2. Observe agent actions:
   - ✅ Navigates to https://dbis.ur.de/UBTIB
   - ✅ Searches for "IEEE Xplore"
   - ✅ Finds search results
   - ✅ Extracts resource ID
   - ✅ Takes screenshots

3. Check for errors:
   - ❌ "Unknown tool" errors (indicates tool name mismatch)
   - ❌ "Element not found" (indicates selector issues)
   - ❌ Navigation timeout

**Expected Result:**
- Agent successfully navigates DBIS
- Resource ID cached in `config/dbis_publishers.yaml`
- No critical errors

---

## Test 2: DBIS Login Flow

**Goal:** Verify agent handles login requirement correctly

**Steps:**

1. Clear browser cookies/cache (to force login)

2. Spawn agent with same test DOI

3. Agent should:
   - ✅ Detect login required
   - ✅ Display message: "⚠️ Please log in to DBIS with TIB credentials"
   - ✅ Pause for 60 seconds
   - ✅ Wait for user to log in

4. User logs in manually in browser window

5. Agent continues after login:
   - ✅ Verifies login success
   - ✅ Continues with database search

**Expected Result:**
- Login detected and handled gracefully
- User has time to log in manually
- Agent continues after successful login

---

## Test 3: "Zur Datenbank" Navigation

**Goal:** Verify agent clicks through to publisher with license

**Steps:**

1. Agent should be on DBIS resource page

2. Agent should:
   - ✅ Find "Zur Datenbank" button
   - ✅ Click button
   - ✅ Wait for redirect
   - ✅ Land on publisher site (ieeexplore.ieee.org)
   - ✅ Take screenshot

3. Verify URL changed to publisher

4. Check page content:
   - ✅ No "Sign in" or "Purchase" prompts
   - ✅ PDF access available (indicates license active)

**Expected Result:**
- Redirect successful
- Publisher site loaded
- License active (no paywall)

---

## Test 4: PDF Download

**Goal:** Verify complete workflow from DOI to PDF

**Test Cases:**

### 4.1: IEEE Paper
```json
{
  "doi": "10.1109/ACCESS.2021.3064112",
  "paper_title": "IoT Security Paper"
}
```

**Expected:**
- ✅ DBIS → IEEE Xplore → Paper found → PDF downloaded
- ✅ Returns: `{"status": "success", "pdf_path": "..."}`

### 4.2: ACM Paper
```json
{
  "doi": "10.1145/3377811.3380330",
  "paper_title": "Software Engineering Paper"
}
```

**Expected:**
- ✅ DBIS → ACM Digital Library → Paper found → PDF downloaded

### 4.3: Springer Paper
```json
{
  "doi": "10.1007/978-3-030-45234-6_1",
  "paper_title": "Computer Science Chapter"
}
```

**Expected:**
- ✅ DBIS → SpringerLink → Paper found → PDF downloaded

### 4.4: Elsevier Paper
```json
{
  "doi": "10.1016/j.infsof.2020.106302",
  "paper_title": "Information Science Paper"
}
```

**Expected:**
- ✅ DBIS → ScienceDirect → Paper found → PDF downloaded

---

## Test 5: Error Handling

### 5.1: Database Not Found in DBIS

**Setup:** Use fake/unknown publisher

**Expected:**
- ✅ Agent tries DBIS search
- ✅ No results found
- ✅ Returns error: "Database not found in DBIS"
- ✅ Suggests alternative method

### 5.2: Paper Not Found on Publisher

**Setup:** Use invalid DOI

**Expected:**
- ✅ Agent navigates to publisher
- ✅ DOI search returns no results
- ✅ Agent tries title search
- ✅ Still no results
- ✅ Returns error: "Paper not found"

### 5.3: Session Expired

**Setup:** Wait for DBIS session to expire

**Expected:**
- ✅ Agent detects "anmelden" prompt
- ✅ Informs user session expired
- ✅ Requests re-login
- ✅ Retries after login

### 5.4: Paywall Despite DBIS

**Setup:** Use paper not covered by TIB license

**Expected:**
- ✅ Agent detects "purchase" or "buy" keywords
- ✅ Returns error: "Paywall detected despite DBIS routing"
- ✅ Logs issue for debugging

---

## Test 6: Resource ID Caching

**Goal:** Verify resource IDs are cached for faster subsequent runs

**Steps:**

1. First run with IEEE DOI:
   - ⏱️ Should search DBIS for "IEEE Xplore"
   - ⏱️ Should extract resource ID
   - ✅ Should cache ID in config file

2. Check `config/dbis_publishers.yaml`:
   ```yaml
   IEEE:
     dbis_resource_id: "123456"  # Should be populated
   ```

3. Second run with different IEEE DOI:
   - ⚡ Should skip DBIS search
   - ⚡ Should navigate directly to resource page
   - ⚡ Faster execution

**Expected Result:**
- First run: ~45-60 seconds (with DBIS search)
- Subsequent runs: ~20-30 seconds (direct navigation)

---

## Test 7: Rate Limiting

**Goal:** Verify agent respects DBIS rate limits

**Steps:**

1. Spawn agent multiple times in quick succession

2. Monitor timing between DBIS requests:
   - ✅ At least 1 second between requests
   - ✅ No 429 Too Many Requests errors

3. Check logs for rate limiting messages

**Expected Result:**
- Requests properly spaced
- No rate limit violations

---

## Test 8: Multi-Publisher Batch

**Goal:** Test downloading from multiple publishers in sequence

**Steps:**

1. Prepare list of DOIs from different publishers:
   - IEEE, ACM, Springer, Elsevier

2. Run batch download (via coordinator or loop)

3. Verify for each:
   - ✅ Correct DBIS database selected
   - ✅ Navigation successful
   - ✅ PDF downloaded

**Expected Result:**
- Success rate: 85-90%
- All publishers handled correctly
- Resource IDs cached for each

---

## Performance Metrics

Track these metrics during testing:

| Metric | Target | Actual |
|--------|--------|--------|
| **Overall Success Rate** | 85-90% | ___% |
| **DBIS Navigation Time** | <15s | ___s |
| **PDF Download Time** | <30s total | ___s |
| **Resource ID Cache Hit** | 100% after 1st run | ___% |
| **Error Recovery Rate** | >95% | ___% |

---

## Chrome MCP Tool Validation

Verify these tools are available and working:

```bash
# List available MCP tools
# Check for:
- mcp__chrome__navigate
- mcp__chrome__click
- mcp__chrome__type
- mcp__chrome__screenshot
- mcp__chrome__evaluate
- mcp__chrome__wait
```

If tool names differ, update `.claude/agents/dbis_browser.md` accordingly.

---

## Troubleshooting

### Issue: "Unknown tool: mcp__chrome__navigate"

**Cause:** Tool name mismatch
**Fix:** Check actual tool names from Chrome MCP, update agent

### Issue: "Element not found"

**Cause:** DBIS HTML structure changed or wrong selectors
**Fix:** Take screenshot, inspect page, update selectors in config

### Issue: Agent stuck waiting for login

**Cause:** Login not detected or timeout too short
**Fix:** Increase timeout in config, check login detection logic

### Issue: Paywall still blocking

**Cause:** DBIS routing failed or wrong database
**Fix:** Verify "Zur Datenbank" click successful, check URL after redirect

---

## Success Criteria

✅ All 4 publisher types (IEEE, ACM, Springer, Elsevier) work
✅ DBIS login handled correctly
✅ Resource IDs cached after first run
✅ Error handling graceful
✅ Success rate >85%
✅ No tool name errors
✅ Rate limiting respected
✅ PDF files actually downloaded and valid

---

## Test Execution Log

```
Date: ___________
Tester: ___________

Test 1 (Basic DBIS Navigation): ☐ Pass ☐ Fail
Notes:

Test 2 (DBIS Login Flow): ☐ Pass ☐ Fail
Notes:

Test 3 ("Zur Datenbank"): ☐ Pass ☐ Fail
Notes:

Test 4 (PDF Download): ☐ Pass ☐ Fail
  4.1 IEEE: ☐ Pass ☐ Fail
  4.2 ACM: ☐ Pass ☐ Fail
  4.3 Springer: ☐ Pass ☐ Fail
  4.4 Elsevier: ☐ Pass ☐ Fail
Notes:

Test 5 (Error Handling): ☐ Pass ☐ Fail
Notes:

Test 6 (Caching): ☐ Pass ☐ Fail
Notes:

Test 7 (Rate Limiting): ☐ Pass ☐ Fail
Notes:

Test 8 (Multi-Publisher): ☐ Pass ☐ Fail
Notes:

Overall Result: ☐ Pass ☐ Fail
Success Rate: ___%
```

---

## Next Steps After Testing

If tests pass:
1. ✅ Mark implementation as complete
2. ✅ Update CHANGELOG
3. ✅ Close related issues
4. ✅ Deploy to production

If tests fail:
1. ❌ Document failures
2. ❌ Debug issues
3. ❌ Fix bugs
4. ❌ Retest
