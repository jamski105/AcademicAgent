# Technical Details: Run 20260223_095905 (Part 2/3)

## Database Selector Analysis

### Expected Selectors (Planned)

**ACM Digital Library:**
```javascript
{
  "search_input": "input[name='AllField']",
  "search_button": "button[type='submit']",
  "result_item": ".issue-item__content",
  "title": ".issue-item__title",
  "authors": ".issue-item__authors",
  "year": ".issue-item__year",
  "abstract": ".abstractSection"
}
```
**Status:** ❌ Not used - "Selectors outdated"

**IEEE Xplore:**
```javascript
{
  "search_input": "input[name='queryText']",
  "search_button": "button.Search",
  "result_item": ".List-results-items",
  "title": "h2.article-title",
  "authors": ".author",
  "year": ".description span",
  "abstract": ".abstract-text"
}
```
**Status:** ❌ Not used - "Selectors outdated"

**Scopus:**
```javascript
{
  "search_input": "textarea#searchfield",
  "search_button": "button#submit",
  "result_item": "tr.searchArea",
  "title": "a.resultsLink",
  "authors": ".previewAuthor",
  "year": ".ddmPubYr",
  "abstract": ".abstract"
}
```
**Status:** ❌ Not used - "Selectors outdated"

**SpringerLink:**
```javascript
{
  "search_input": "input#query",
  "search_button": "button[type='submit']",
  "result_item": ".content-item",
  "title": "h3.title",
  "authors": ".authors",
  "year": ".year",
  "abstract": ".abstract"
}
```
**Status:** ❌ Not used - "Selectors outdated"

**Web of Science:**
```javascript
{
  "search_input": "input#value(input1)",
  "search_button": "button#searchBtn",
  "result_item": ".search-results-item",
  "title": ".title",
  "authors": ".authors",
  "year": ".year",
  "abstract": ".abstract"
}
```
**Status:** ❌ Not used - "Selectors outdated"

---

### Actual Selectors Used (Google Scholar)

**Google Scholar:**
```javascript
{
  "search_input": "input[name='q']",
  "search_button": "button[type='submit']",
  "result_item": ".gs_r.gs_or.gs_scl",
  "title": "h3.gs_rt",
  "authors": ".gs_a",
  "year": "extracted from .gs_a text",
  "abstract": ".gs_rs",
  "url": "h3.gs_rt a[href]"
}
```
**Status:** ✅ Used successfully

**Why Google Scholar Worked:**
- Simpler HTML structure
- Stable selectors (unchanged for years)
- No authentication required
- No rate limiting (for low traffic)

---

## Search String Analysis

### Boolean Syntax by Database

**ACM Format (Not Used):**
```
(Title:"Lean Governance" OR Abstract:"Lean Governance")
AND (Title:DevOps OR Abstract:DevOps)
```

**IEEE Format (Not Used):**
```
("Document Title":"Lean Governance" OR "Abstract":"Lean Governance")
AND ("Document Title":DevOps OR "Abstract":DevOps)
```

**Scopus Format (Not Used):**
```
TITLE-ABS-KEY("Lean Governance" OR "Agile Governance")
AND TITLE-ABS-KEY(DevOps)
AND PUBYEAR > 2018
```

**Google Scholar Format (Actually Used):**
```
"Lean Governance" DevOps
"Agile Governance" "Continuous Compliance"
DevOps Guardrails "Compliance Automation"
```

**Simplification Impact:**
- Lost Boolean precision (AND/OR operators)
- Lost field-specific search (Title vs. Abstract)
- Lost advanced filters (PUBYEAR, etc.)
- Gained: Simplicity and reliability

---

## PDF Download Failure Analysis

### Failure Case 1: ResearchGate (403 Forbidden)

**Papers Affected:**
- Young et al. (2025) - Bridging Performance Gaps
- Khan & Hussain - Data Governance

**Technical Details:**
```http
GET https://www.researchgate.net/...pdf HTTP/1.1
User-Agent: python-requests/2.31.0
Accept: */*

HTTP/1.1 403 Forbidden
Content-Type: text/html
X-Content-Type-Options: nosniff
```

**Root Cause:**
- ResearchGate detects automated requests
- Checks User-Agent header
- Requires cookies from browser session
- May use CAPTCHA/reCAPTCHA

**Attempted Fixes:**
1. Custom User-Agent → Still 403
2. Browser automation → Still 403 (headless detection?)
3. HTTP + Browser hybrid → Still 403

**Why It Failed:**
- ResearchGate has sophisticated bot detection
- Headless browser fingerprinting
- No session cookies from manual login

---

### Failure Case 2: ProQuest (401 Unauthorized)

**Paper Affected:**
- Greene (2020) - IT Governance for DevOps Teams

**Technical Details:**
```http
GET https://www.proquest.com/docview/... HTTP/1.1

HTTP/1.1 401 Unauthorized
WWW-Authenticate: None
Location: /login
```

**Root Cause:**
- Institutional paywall
- Requires university network or VPN
- No public access

**Why It Failed:**
- No institutional credentials provided
- No proxy configuration
- Expected failure

---

### Failure Case 3: JavaScript Download (No Trigger)

**Paper Affected:**
- Whitcombe (2026) - Data Driven Change Control

**Technical Details:**
```javascript
// Page uses JavaScript to generate download
<button onclick="downloadPDF()">Download</button>

function downloadPDF() {
  // Generates PDF server-side
  // Returns blob via XHR
  // Triggers download via JS
}
```

**Why It Failed:**
- No direct PDF URL
- Click event didn't trigger download
- Playwright waited for download event that never fired
- Timeout after 120 seconds

**Attempted Fixes:**
1. Click button → No download
2. Wait for 'download' event → Timeout
3. Extract XHR request → Blocked by CORS

---

### Failure Case 4: Server-Side PDF Generation

**Paper Affected:**
- Batmetan (2025) - Agile IT Governance

**Technical Details:**
```
URL pattern: /article/view/260
Expected: /article/download/260.pdf
Actual: Server generates PDF on-demand (slow)
```

**Why It Failed:**
- PDF generation takes 10-15 seconds
- Our timeout: 5 seconds
- No progress indication
- Connection reset

---

### Success Case: Preprints.org

**Paper:**
- Peerzada (2025) - Agile Governance

**Why It Worked:**
```http
GET https://www.preprints.org/.../download_pub HTTP/1.1

HTTP/1.1 200 OK
Content-Type: application/pdf
Content-Length: 1262592
Content-Disposition: attachment; filename="preprint.pdf"
```

**Success Factors:**
- Direct PDF URL
- No authentication
- No bot detection
- Standard HTTP download
- Fast response (<2 seconds)

---

## 5D Scoring Algorithm

### Scoring Dimensions

**1. Relevance (Weight: 40%)**
```python
def calculate_relevance(paper, research_question):
    # Keyword matching
    title_match = count_keywords_in_text(paper.title, keywords)
    abstract_match = count_keywords_in_text(paper.abstract, keywords)

    # Semantic similarity (if available)
    semantic_score = cosine_similarity(
        embed(research_question),
        embed(paper.abstract)
    )

    # Combine
    relevance = (
        title_match * 0.3 +
        abstract_match * 0.4 +
        semantic_score * 0.3
    ) * 100

    return min(relevance, 100)
```

**Actual Results:**
- Average: 84/100
- Range: 70-95
- Method: Keyword counting only (no embeddings used)

---

**2. Quality (Weight: 10%)**
```python
def calculate_quality(paper):
    score = 0

    # Peer review status
    if paper.peer_reviewed:
        score += 30

    # Citation count
    if paper.citations >= 100:
        score += 30
    elif paper.citations >= 50:
        score += 20
    elif paper.citations >= 10:
        score += 10

    # Publication venue
    if paper.venue_rank == "A":
        score += 20
    elif paper.venue_rank == "B":
        score += 10

    # Author reputation
    if paper.h_index_first_author >= 20:
        score += 20

    return min(score, 100)
```

**Actual Results:**
- Average: 57/100
- Range: 40-70
- Problem: Missing citation data (Google Scholar limitation)

---

**3. Recency (Weight: 30%)**
```python
def calculate_recency(paper, current_year=2026, range_start=2019):
    year = paper.year
    max_age = current_year - range_start  # 7 years
    age = current_year - year

    if age < 0:  # Future publication
        return 100

    recency = max(0, (1 - age / max_age)) * 100
    return recency
```

**Actual Results:**
- Average: 82/100
- Range: 55-100
- Best: 2025-2026 papers (95-100)
- Worst: 2020 paper (55)

---

**4. Accessibility (Weight: 10%)**
```python
def calculate_accessibility(paper):
    score = 0

    # Open access
    if paper.open_access:
        score += 50

    # PDF available
    if paper.pdf_url:
        score += 30

    # Preprint available
    if paper.preprint_url:
        score += 20

    return min(score, 100)
```

**Actual Results:**
- Average: 84/100
- Range: 70-95
- All papers had URLs, most had PDFs (claimed)

---

**5. Utility (Weight: 10%)**
```python
def calculate_utility(paper):
    score = 50  # Base score

    # Contains framework/model
    if "framework" in paper.abstract.lower():
        score += 15

    # Contains case study
    if "case study" in paper.abstract.lower():
        score += 15

    # Contains implementation details
    if any(word in paper.abstract.lower()
           for word in ["implementation", "tool", "method"]):
        score += 10

    # Contains evaluation/empirical data
    if any(word in paper.abstract.lower()
           for word in ["evaluation", "empirical", "results"]):
        score += 10

    return min(score, 100)
```

**Actual Results:**
- Average: 81/100
- Range: 64-90
- Method: Keyword-based heuristic

---

**Total Score Calculation:**
```python
total_score = (
    relevance * 0.40 +
    quality * 0.10 +
    recency * 0.30 +
    accessibility * 0.10 +
    utility * 0.10
)
```

**Top Scores:**
1. Peerzada (2025): 85/100
2. Young et al. (2025): 83/100
3. Whitcombe (2026): 81/100

---

**End of Part 2**
**Continue to TECHNICAL_DETAILS_Part3.md**
