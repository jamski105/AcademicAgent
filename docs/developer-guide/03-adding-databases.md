# 🗄️ Datenbanken hinzufügen

Dieser Guide erklärt wie man neue akademische Datenbanken zu AcademicAgent hinzufügt.

## Überblick

Um eine neue Datenbank hinzuzufügen brauchst du:

1. **Datenbank-Eintrag** in `config/database_disciplines.yaml`
2. **Browser-Selektoren** für Such- und Ergebnis-Elemente
3. **Suchstring-Syntax-Rules** für Query-Generierung
4. **(Optional) Download-Strategie** für PDF-Zugriff

---

## Schritt 1: Datenbank-Eintrag erstellen

### YAML-Struktur

```yaml
# config/database_disciplines.yaml

- name: Name der Datenbank
  disciplines:
    - Disziplin 1
    - Disziplin 2
  url: https://database-url.com
  access: Subscription | Open Access | Hybrid
  api_available: true | false
  base_score: 70-95
  priority: 1-3
  notes: "Beschreibung der Datenbank"
  selectors:
    search_input: "CSS selector"
    search_button: "CSS selector"
    result_item: "CSS selector"
    title: "CSS selector"
    abstract: "CSS selector"
    authors: "CSS selector"
    year: "CSS selector"
    pdf_link: "CSS selector"
  syntax:
    operators:
      - "AND"
      - "OR"
      - "NOT"
    phrase_delimiter: '"'
    field_search_template: '({field}:{term})'
    max_query_length: 500
```

### Beispiel: IEEE Xplore

```yaml
- name: IEEE Xplore
  disciplines:
    - Informatik
    - Elektrotechnik
    - Ingenieurwissenschaften
  url: https://ieeexplore.ieee.org
  access: Subscription
  api_available: true
  base_score: 93
  priority: 1
  notes: "Premier database for electrical engineering and computer science"

  selectors:
    search_input: "input[name='queryText']"
    search_button: "button[type='submit'].search-button"
    result_item: "div.List-results-items xpl-results-item"
    title: "h2.result-item-title a"
    abstract: "div.abstract-text"
    authors: "p.author span"
    year: "div.description span.text"
    pdf_link: "a.pdf-link"
    doi: "a.stats-document-abstract-doi"

  syntax:
    operators:
      - "AND"
      - "OR"
      - "NOT"
    phrase_delimiter: '"'
    field_search_template: '("Document Title":{term})'
    max_query_length: 500

  pdf_download:
    method: direct_link
    requires_login: true
    login_selector: "a.sign-in-link"
```

### Feld-Erklärungen

| Feld | Beschreibung | Werte |
|------|--------------|-------|
| `name` | Offizieller Name | String |
| `disciplines` | Relevante Fachbereiche | Liste |
| `url` | Startseite URL | URL |
| `access` | Zugangsart | Subscription / Open Access / Hybrid |
| `api_available` | Hat die DB eine API? | Boolean |
| `base_score` | Initial-Score für Priorisierung | 70-95 |
| `priority` | Suchpriorität | 1 (highest) - 3 (lowest) |
| `notes` | Beschreibung | String |

---

## Schritt 2: Selektoren finden

### Mit Browser DevTools

1. **Öffne Datenbank** in Chrome
2. **Öffne DevTools** (F12 oder Cmd+Option+I)
3. **Führe Testsuche durch** mit einem Keyword
4. **Inspect Elemente:**

#### Search Input

```javascript
// Im DevTools Console:
document.querySelector('input[type="search"]')
document.querySelector('input[name="query"]')
document.querySelector('#search-field')

// Finde das Element das funktioniert
```

#### Search Button

```javascript
document.querySelector('button[type="submit"]')
document.querySelector('.search-button')
document.querySelector('#search-btn')
```

#### Result Items

```javascript
// Liste aller Ergebnis-Container
document.querySelectorAll('.result-item')
document.querySelectorAll('article.paper')
document.querySelectorAll('div[data-result-id]')
```

#### Title, Abstract, etc.

```javascript
// Innerhalb eines Result Items:
let result = document.querySelector('.result-item')

result.querySelector('.title')
result.querySelector('h2 a')
result.querySelector('.abstract-text')
result.querySelector('.authors')
```

### Beispiel-Session

```javascript
// 1. Öffne: https://dl.acm.org
// 2. In Console:

// Test Search Input
let searchInput = document.querySelector('input#acm-search-input')
searchInput.value = "machine learning"
console.log("Search input works:", searchInput.value)

// Test Search Button
let searchBtn = document.querySelector('button.search-button')
searchBtn.click()

// Warte bis Ergebnisse laden...

// Test Result Items
let results = document.querySelectorAll('li.search__item')
console.log(`Found ${results.length} results`)

// Test Title Extraction
let firstTitle = results[0].querySelector('.issue-item__title a')
console.log("First title:", firstTitle.textContent)
```

### Selektoren dokumentieren

```yaml
selectors:
  # Beschreibe was jeder Selektor macht
  search_input: "input#acm-search-input"  # Main search field on homepage
  search_button: "button.search-button"   # Submit button next to search
  result_item: "li.search__item"          # Container for each result
  title: ".issue-item__title a"           # Title link (relative to result_item)
  abstract: ".issue-item__abstract"       # Abstract text
  authors: ".issue-item__loa span"        # Author names
  year: ".issue-item__detail span"        # Publication year
  pdf_link: "a.pdf-link"                  # Link to PDF
```

---

## Schritt 3: Suchstring-Syntax definieren

### Syntax-Rules

Jede Datenbank hat eigene Boolean-Suchsyntax:

**IEEE Xplore:**
```
("Term 1" OR "Term 2") AND ("Term 3")
```

**ACM Digital Library:**
```
[[Title: term1]] OR [[Abstract: term2]]
```

**PubMed:**
```
(term1[TIAB] OR term2[TIAB]) AND term3[MeSH]
```

### Syntax-Konfiguration

```yaml
syntax:
  # Boolean Operators
  operators:
    - "AND"
    - "OR"
    - "NOT"

  # Wie werden Phrasen gekennzeichnet?
  phrase_delimiter: '"'  # IEEE, ACM: "phrase"

  # Feld-spezifische Suche (optional)
  field_search_template: '("Document Title":{term})'
  # {term} wird ersetzt durch Suchbegriff

  # Maximale Query-Länge
  max_query_length: 500

  # Spezielle Features (optional)
  supports_wildcards: true      # term* findet terms, terminator, etc.
  wildcard_char: "*"
  proximity_search: true        # "term1 NEAR/5 term2"
  proximity_operator: "NEAR"
```

### Beispiel-Generierung

```python
# In search-agent

def generate_search_string(database, keywords):
    syntax = database['syntax']

    # Primary Keywords (alle mit OR verbunden)
    primary_terms = []
    for kw in keywords['primary']:
        # Add phrase delimiters
        term = f'{syntax["phrase_delimiter"]}{kw}{syntax["phrase_delimiter"]}'
        primary_terms.append(term)

    primary_query = f' {syntax["operators"][1]} '.join(primary_terms)  # OR

    # Secondary Keywords
    if keywords.get('secondary'):
        secondary_terms = []
        for kw in keywords['secondary']:
            term = f'{syntax["phrase_delimiter"]}{kw}{syntax["phrase_delimiter"]}'
            secondary_terms.append(term)

        secondary_query = f' {syntax["operators"][1]} '.join(secondary_terms)  # OR

        # Combine: (primary) AND (secondary)
        query = f'({primary_query}) {syntax["operators"][0]} ({secondary_query})'
    else:
        query = primary_query

    # Apply field search if available
    if syntax.get('field_search_template'):
        # Fokus auf Title + Abstract
        title_query = syntax['field_search_template'].replace('{field}', 'Title').replace('{term}', query)
        abstract_query = syntax['field_search_template'].replace('{field}', 'Abstract').replace('{term}', query)
        query = f'{title_query} {syntax["operators"][1]} {abstract_query}'

    # Truncate if too long
    if len(query) > syntax['max_query_length']:
        query = query[:syntax['max_query_length']]

    return query
```

---

## Schritt 4: PDF-Download-Strategie

### Download-Methoden

#### 1. Direct Link

PDF ist direkt über Link verfügbar:

```yaml
pdf_download:
  method: direct_link
  requires_login: false
  pdf_link_selector: "a.pdf-link"
```

```python
# In browser-agent
pdf_url = result.querySelector('a.pdf-link').href
download_file(pdf_url, output_path)
```

#### 2. Click-to-Download

PDF öffnet sich nach Klick:

```yaml
pdf_download:
  method: click_download
  requires_login: true
  pdf_button_selector: "button.download-pdf"
  wait_for_download: 5  # seconds
```

```python
# In browser-agent
cdp.click('button.download-pdf')
time.sleep(5)  # Warte auf Download
# PDF landet in Downloads-Ordner
```

#### 3. Via DOI Resolver

Paper-Seite hat DOI, PDF über DOI-Resolver:

```yaml
pdf_download:
  method: doi_resolver
  requires_login: false
  doi_selector: "a.stats-document-abstract-doi"
```

```python
# In browser-agent
doi = result.querySelector('a.stats-document-abstract-doi').textContent
doi = clean_doi(doi)  # Entferne Präfixe

# Versuche Open Access Repositories
pdf_url = try_resolve_doi(doi, sources=['unpaywall', 'core', 'arxiv'])

if pdf_url:
    download_file(pdf_url, output_path)
else:
    # Fallback: Via Uni-Proxy
    pdf_url = f"https://doi.org/{doi}"
    download_via_proxy(pdf_url, output_path)
```

#### 4. API-basiert

Datenbank hat API:

```yaml
pdf_download:
  method: api
  api_endpoint: "https://api.database.com/papers/{id}/pdf"
  requires_api_key: true
```

```python
# In browser-agent
paper_id = extract_id_from_url(result_url)

headers = {'Authorization': f'Bearer {API_KEY}'}
response = requests.get(
    f'https://api.database.com/papers/{paper_id}/pdf',
    headers=headers
)

with open(output_path, 'wb') as f:
    f.write(response.content)
```

---

## Schritt 5: Testing

### Manual Testing

```bash
# 1. Teste Selektoren manuell in Browser DevTools
# Siehe "Schritt 2"

# 2. Teste Suchstring-Generierung
python3 tests/manual/test_search_string.py \
  --database "New Database" \
  --keywords "keyword1,keyword2"

# Expected output:
# Generated: ("keyword1" OR "keyword2") AND ...

# 3. Teste Browser-Navigation
python3 scripts/cdp_wrapper.py navigate "https://new-database.com"
python3 scripts/cdp_wrapper.py search "test query"

# 4. Teste PDF-Download
python3 scripts/cdp_wrapper.py download_pdf \
  "https://new-database.com/paper/123" \
  "/tmp/test.pdf"
```

### Automated Testing

```python
# tests/integration/test_database_integration.py

def test_new_database_search():
    """Test search functionality for new database."""

    # Load database config
    db = load_database_config("New Database")

    # Connect to Chrome
    cdp = CDPClient()
    cdp.connect()

    # Navigate
    cdp.navigate(db['url'])

    # Search
    cdp.fill(db['selectors']['search_input'], "test query")
    cdp.click(db['selectors']['search_button'])

    # Wait for results
    cdp.wait_for_selector(db['selectors']['result_item'], timeout=10)

    # Parse results
    results = cdp.query_selector_all(db['selectors']['result_item'])

    assert len(results) > 0, "No results found"

    # Check first result
    first_result = results[0]
    title = cdp.get_text(first_result, db['selectors']['title'])

    assert title, "Could not extract title"
    assert len(title) > 10, "Title too short"

def test_pdf_download():
    """Test PDF download for new database."""

    db = load_database_config("New Database")
    cdp = CDPClient()
    cdp.connect()

    # Navigate to a known paper URL (use test paper)
    test_paper_url = "https://new-database.com/paper/test-123"
    cdp.navigate(test_paper_url)

    # Download PDF
    pdf_path = "/tmp/test_paper.pdf"
    cdp.download_pdf(test_paper_url, pdf_path)

    # Validate
    assert os.path.exists(pdf_path), "PDF not downloaded"
    assert os.path.getsize(pdf_path) > 1000, "PDF too small (likely error page)"

    # Validate PDF content
    text = extract_text_from_pdf(pdf_path)
    assert len(text) > 100, "PDF has no readable text"
```

### Integration mit CI/CD

```yaml
# .github/workflows/database-tests.yml

name: Database Integration Tests

on: [push, pull_request]

jobs:
  test-new-database:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v2

      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.10

      - name: Install dependencies
        run: |
          pip install -r tests/requirements-test.txt

      - name: Start Chrome in debug mode
        run: |
          google-chrome --remote-debugging-port=9222 --headless &
          sleep 5

      - name: Run database tests
        run: |
          pytest tests/integration/test_new_database.py -v
```

---

## Schritt 6: Dokumentation

### Update database_disciplines.yaml

Füge vollständigen Eintrag hinzu mit allen Feldern.

### Update DBIS_USAGE.md

```markdown
## Neue Datenbank: [Name]

### Besonderheiten

- [Besonderheit 1]
- [Besonderheit 2]

### Login-Anforderungen

[Beschreibung wenn Login nötig]

### Rate Limits

[Beschreibung von Rate Limits]

### Bekannte Probleme

- [Problem 1]: [Workaround]
- [Problem 2]: [Workaround]
```

### Update README.md

Füge Datenbank zur Liste hinzu.

---

## Häufige Probleme

### Problem: Selektoren ändern sich

**Ursache:** Datenbank-Website hat Update erhalten

**Lösung:**
```yaml
# Versionierte Selektoren
selectors_v2:  # Neue Selektoren nach Update
  search_input: "input#new-search-field"
  ...

# Automatische Erkennung
selector_detection:
  - try: selectors_v2
  - fallback: selectors_v1
```

### Problem: CAPTCHA-Blocking

**Ursache:** Datenbank erkennt Bot

**Lösung:**
```yaml
rate_limiting:
  requests_per_minute: 5
  delay_between_requests: 15  # seconds
  retry_after_captcha: manual  # Pause und warte auf User
```

### Problem: Login-Popup

**Ursache:** Subscription-Datenbank verlangt Login

**Lösung:**
```yaml
login:
  required: true
  method: shibboleth  # oder saml, oauth
  detection: "div.login-required"
  instructions: "Please log in via your institution"
```

---

## Best Practices

### 1. Robuste Selektoren

❌ **Fragil:**
```yaml
title: "div:nth-child(3) > h2"  # Bricht bei kleinsten Änderungen
```

✅ **Robust:**
```yaml
title: "h2.paper-title, h2[data-title], .result-item h2"  # Multiple Fallbacks
```

### 2. Timeout-Handling

```yaml
timeouts:
  page_load: 30
  search_results: 15
  pdf_download: 60
```

### 3. Logging

```python
logger.info(f"[{db_name}] Starting search")
logger.info(f"[{db_name}] Found {len(results)} results")
logger.error(f"[{db_name}] Failed: {error}")
```

---

## Checkliste: Neue Datenbank

- [ ] Datenbank-Eintrag in `database_disciplines.yaml` erstellt
- [ ] Selektoren mit DevTools gefunden und getestet
- [ ] Suchstring-Syntax dokumentiert
- [ ] PDF-Download-Methode implementiert
- [ ] Manual Tests durchgeführt
- [ ] Automated Tests geschrieben
- [ ] Dokumentation aktualisiert
- [ ] Pull Request erstellt

---

**[← Zurück zum Developer Guide](README.md) | [Weiter zu: Testing →](04-testing.md)**
