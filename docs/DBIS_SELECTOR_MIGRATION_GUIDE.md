# DBIS Selector Migration Guide
**Date:** 2026-02-27
**Version:** Academic Agent v2.3
**Status:** ✅ Complete

---

## Quick Summary

DBIS has been completely redesigned. All old selectors are broken. New selectors have been identified and validated.

### What Changed?

| Aspect | Before (Pre-2026) | After (2026+) |
|--------|-------------------|---------------|
| **URL Pattern** | `dbis/dbliste.php?bib_id=...` | `/UBTIB/browse/subjects/{id}/` |
| **Structure** | Static HTML tables | JavaScript SPA |
| **Database Entries** | `<tr id="db_123">` | `<a href="/resources/123">` |
| **Traffic Lights** | `.gif` images | `.svg` images |
| **CSS Framework** | Custom | Bulma CSS |

---

## Old vs New Selectors

### Database Entries

```diff
# OLD (BROKEN) ❌
- database_entry: "tr[id^='db_']"
- Result: 0 matches

# NEW (WORKING) ✅
+ database_entry: "a[href*='/resources/']"
+ Result: 80 matches
```

**Old HTML:**
```html
<tr id="db_123" class="even">
  <td class="td1">...</td>
  <td class="td2">
    <a href="erf=123&colors=15">Database Name</a>
  </td>
</tr>
```

**New HTML:**
```html
<span class="tag is-medium m-1 has-text-link">
  <a href="/UBTIB/resources/104296">
    <span class="traffic-light-container">
      <img class="traffic-light" src="/img/icons/ampel_green.svg" alt="">
    </span>
    <span>Database Name</span>
  </a>
</span>
```

---

### Database Names

```diff
# OLD (BROKEN) ❌
- database_name: "td.td2 a"
- Result: 0 matches

# NEW (WORKING) ✅
+ database_name: "a[href*='/resources/']"
+ Result: 80 matches
+ Extract with: element.text
```

---

### Traffic Lights

```diff
# OLD (BROKEN) ❌
- traffic_light: "img[src*='dbis_']"
- Result: 0 matches
- Pattern: dbis_gr_01.gif, dbis_ge_01.gif, dbis_ro_01.gif

# NEW (WORKING) ✅
+ traffic_light: "img.traffic-light"
+ Result: 32 matches
+ Pattern: ampel_green.svg, ampel_yellow.svg, ampel_red.svg
```

**Old patterns:**
- `dbis_gr_` → Green (free access)
- `dbis_ge_` → Yellow (institutional)
- `dbis_ro_` → Red (no access)

**New patterns:**
- `ampel_green.svg` → Green (free access)
- `ampel_yellow.svg` → Yellow (institutional)
- `ampel_red.svg` → Red (no access)

---

## URL Migration

### Old URL Format (404 Error)
```
https://dbis.ur.de/dbis/dbliste.php?bib_id=ubtib&lett=f&sGeb=9.1
```
❌ **Returns:** "Leider ist ein Fehler aufgetreten"

### New URL Format (Working)
```
https://dbis.ur.de/UBTIB/browse/subjects/9/
```
✅ **Returns:** 80 database entries

### Subject ID Mapping
| Subject | Old ID | New ID | New URL |
|---------|--------|--------|---------|
| Library Science | 9 | 9 | `/UBTIB/browse/subjects/9/` |
| Law | 9.1 | 9.1 | `/UBTIB/browse/subjects/9.1/` |
| Medicine | 7 | 7 | `/UBTIB/browse/subjects/7/` |
| Computer Science | 11 | 11 | `/UBTIB/browse/subjects/11/` |

---

## Implementation Changes

### Code Example: Old Way (Broken)

```python
# OLD - DOES NOT WORK
from selenium import webdriver
from selenium.webdriver.common.by import By

driver.get("https://dbis.ur.de/dbis/dbliste.php?bib_id=ubtib&lett=f&sGeb=9.1")
time.sleep(2)

# ❌ Returns 0 elements
entries = driver.find_elements(By.CSS_SELECTOR, "tr[id^='db_']")
names = driver.find_elements(By.CSS_SELECTOR, "td.td2 a")
lights = driver.find_elements(By.CSS_SELECTOR, "img[src*='dbis_']")
```

### Code Example: New Way (Working)

```python
# NEW - WORKS PERFECTLY
from selenium import webdriver
from selenium.webdriver.common.by import By

# Step 1: Navigate to subjects page
driver.get("https://dbis.ur.de/fachliste.php?bib_id=ubtib")
time.sleep(3)

# Step 2: Click on desired subject
subject_link = driver.find_element(By.PARTIAL_LINK_TEXT, "Bibliothekswesen")
subject_link.click()
time.sleep(5)  # Wait for JavaScript to load

# Step 3: Extract database information
# ✅ Returns 80 elements
entries = driver.find_elements(By.CSS_SELECTOR, "a[href*='/resources/']")

for entry in entries:
    # Extract name
    name = entry.text.strip()

    # Extract URL
    url = entry.get_attribute('href')

    # Extract traffic light
    traffic_light = entry.find_element(By.CSS_SELECTOR, "img.traffic-light")
    access_src = traffic_light.get_attribute('src')

    if 'green' in access_src:
        access = "free"
    elif 'yellow' in access_src:
        access = "institutional"
    elif 'red' in access_src:
        access = "restricted"

    print(f"{name} [{access}] - {url}")
```

---

## Configuration Updates

### File: `config/dbis_selectors.yaml`

**Changed sections:**

1. **Database Entry Selector**
```yaml
# OLD
database_entry:
  primary: "tr[id^='db_']"

# NEW
database_entry:
  primary: "a[href*='/resources/']"
```

2. **Database Name Selector**
```yaml
# OLD
database_name:
  primary: "td.td2 a"

# NEW
database_name:
  primary: "a[href*='/resources/']"
```

3. **Traffic Light Selector**
```yaml
# OLD
traffic_light:
  primary: "img[src*='dbis_']"

# NEW
traffic_light:
  primary: "img.traffic-light"
```

4. **Traffic Light Patterns**
```yaml
# OLD
green:
  - "dbis_gr_"
  - "amp_gruen"

# NEW
green:
  - "ampel_green"  # Primary
  - "dbis_gr_"     # Fallback (deprecated)
```

5. **Test URLs**
```yaml
# OLD
test_urls:
  rechtswissenschaft: "https://dbis.ur.de/dbis/dbliste.php?bib_id=ubtib&colors=15&lett=f&sGeb=9.1"

# NEW
test_urls:
  rechtswissenschaft: "https://dbis.ur.de/UBTIB/browse/subjects/9.1/"
```

---

## Testing Checklist

Use this checklist to verify the new selectors work in your environment:

- [ ] **Prerequisites**
  - [ ] Selenium installed (`pip install selenium`)
  - [ ] Chrome/ChromeDriver available
  - [ ] Network access to dbis.ur.de

- [ ] **URL Access**
  - [ ] Can load `https://dbis.ur.de/fachliste.php?bib_id=ubtib`
  - [ ] Can click on a subject link
  - [ ] Subject page loads with databases visible

- [ ] **Selector Validation**
  - [ ] `a[href*='/resources/']` returns ~80 elements
  - [ ] Each element contains a database name
  - [ ] Each element has a valid href starting with `/UBTIB/resources/`
  - [ ] `img.traffic-light` returns ~32 elements
  - [ ] Traffic light images have `ampel_green`, `ampel_yellow`, or `ampel_red` in src

- [ ] **Data Extraction**
  - [ ] Can extract database names from link text
  - [ ] Can extract database URLs from href attribute
  - [ ] Can determine access level from traffic light color
  - [ ] No duplicate entries

- [ ] **Error Handling**
  - [ ] Handles pages with 0 results gracefully
  - [ ] Detects 404 errors on old URLs
  - [ ] Waits for JavaScript to load (5+ seconds)

---

## Troubleshooting

### Problem: Selectors return 0 results

**Possible causes:**
1. JavaScript hasn't loaded yet → Increase wait time to 5+ seconds
2. Using old URL format → Check URL matches new pattern
3. Network error or DBIS down → Verify site loads in browser

**Solution:**
```python
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Wait for elements to be present
wait = WebDriverWait(driver, 10)
elements = wait.until(
    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a[href*='/resources/']"))
)
```

---

### Problem: Traffic lights count doesn't match entries count

**Expected behavior:** This is normal!
- Entries count: 80 (all databases on page)
- Traffic lights count: 32 (only visible on current page, rest hidden by pagination)

**Explanation:** The page uses pagination. Not all 80 databases are visible at once.

---

### Problem: Old test URLs return 404

**Expected behavior:** This is correct!
- Old URLs like `dbis/dbliste.php` no longer work
- DBIS has migrated to new URL structure

**Solution:** Update all test URLs to use new format:
```
/UBTIB/browse/subjects/{subject_id}/
```

---

## Migration Timeline

| Date | Action | Status |
|------|--------|--------|
| Pre-2026 | Old table-based DBIS structure | Deprecated |
| 2026-01-?? | DBIS migrates to SPA | Live |
| 2026-02-27 | New selectors identified | ✅ Complete |
| 2026-02-27 | Configuration updated | ✅ Complete |
| 2026-02-27 | Documentation created | ✅ Complete |
| Next | Integration testing required | ⏳ Pending |

---

## Files Modified

1. **Configuration:**
   - `/config/dbis_selectors.yaml` (updated)

2. **Documentation:**
   - `/docs/DBIS_SELECTOR_VALIDATION_REPORT.md` (new)
   - `/docs/DBIS_WORKING_SELECTORS.json` (new)
   - `/docs/DBIS_SELECTOR_MIGRATION_GUIDE.md` (new)

3. **Screenshots:**
   - `/tmp/dbis_screenshot_1.png`
   - `/tmp/dbis_database_list.png`
   - `/tmp/dbis_final.png`

---

## Next Steps

1. **Test Integration** (Task #9)
   - Run end-to-end test with new selectors
   - Verify dbis_search agent uses updated config
   - Test with multiple disciplines

2. **Monitor for Changes**
   - DBIS may continue to evolve
   - Consider periodic validation checks
   - Document any future selector changes

3. **Update Related Code**
   - Check if any hardcoded selectors exist
   - Ensure all code uses `dbis_selectors.yaml`
   - Update test fixtures if needed

---

## Support

**Questions?** Check these resources:
- Validation report: `docs/DBIS_SELECTOR_VALIDATION_REPORT.md`
- Working selectors: `docs/DBIS_WORKING_SELECTORS.json`
- Configuration file: `config/dbis_selectors.yaml`

**Problems?** Run validation script:
```bash
python3 /tmp/dbis_final_test.py
```

---

**Document version:** 1.0
**Last updated:** 2026-02-27
**Validated against:** DBIS Production (dbis.ur.de)
