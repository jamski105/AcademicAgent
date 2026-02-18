# 🏗️ Architektur-Übersicht

Dieses Dokument erklärt die technische Architektur von AcademicAgent im Detail.

## High-Level Architektur

### System-Komponenten

```
┌─────────────────────────────────────────────────────────────┐
│                     Claude Code CLI                         │
│                 (Anthropic Agent SDK)                       │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        │ Skill Invocation
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                 Orchestrator Skill                          │
│         (.claude/skills/academicagent/SKILL.md)             │
│                                                             │
│  Responsibilities:                                          │
│  • Phase Management (0-6)                                   │
│  • Human-in-the-Loop Checkpoints                           │
│  • State Persistence & Recovery                            │
│  • Agent Task Delegation                                    │
│  • Error Handling & Retry Logic                            │
└────┬────────────┬───────────┬──────────┬────────────┬──────┘
     │            │           │          │            │
     │ Task       │ Task      │ Task     │ Task       │ Task
     │            │           │          │            │
     ▼            ▼           ▼          ▼            ▼
┌────────┐  ┌─────────┐  ┌────────┐ ┌────────┐ ┌────────────┐
│ Setup  │  │ Browser │  │ Search │ │ Scoring│ │ Extraction │
│ Agent  │  │ Agent   │  │ Agent  │ │ Agent  │ │ Agent      │
└────────┘  └────┬────┘  └────────┘ └────────┘ └──────┬─────┘
                 │                                      │
                 │ CDP Protocol                         │ pdftotext
                 ▼                                      ▼
          ┌────────────┐                         ┌──────────┐
          │  Chrome    │                         │   PDFs   │
          │  (Debug    │                         │          │
          │   Mode)    │                         └──────────┘
          └────────────┘
                 │
                 │ HTTPS
                 ▼
          ┌────────────┐
          │ Academic   │
          │ Databases  │
          │ (via DBIS) │
          └────────────┘
```

### Datenfluss

```
1. User Invocation
   ↓
2. Orchestrator initializes State
   ↓
3. Phase 0: Browser-Agent → DBIS → Database List
   ↓ (User Checkpoint)
4. Phase 1: Search-Agent → Search Strings
   ↓ (User Checkpoint)
5. Phase 2: Browser-Agent → Iterative DB Search → Candidates
   ↓
6. Phase 3: Scoring-Agent → 5D Scoring → Ranked Candidates
   ↓ (User Checkpoint: Select Top 18)
7. Phase 4: Browser-Agent → Download PDFs
   ↓
8. Phase 5: Extraction-Agent → Extract Quotes
   ↓ (User Checkpoint: Validate Quotes)
9. Phase 6: Generate Outputs (BibTeX, JSON, Markdown)
   ↓ (User Checkpoint: Final Confirmation)
10. Complete!
```

---

## Der 7-Phasen-Workflow (Technisch)

### Phase 0: DBIS-Navigation

**Verantwortlich:** `browser-agent`

**Input:**
```json
{
  "research_question": "...",
  "keywords": ["primary", "secondary"],
  "disciplines": ["Computer Science"]
}
```

**Prozess:**

1. **Load Curated Databases**
   ```python
   # Von config/database_disciplines.yaml
   curated_dbs = load_databases_for_disciplines(["Computer Science"])
   # Ergebnis: [ACM, IEEE, DBLP, arXiv, Scopus, ...]
   ```

2. **Navigate DBIS Portal**
   ```python
   cdp.navigate("https://dbis.ur.de")
   cdp.search_database(
       query=f"{keywords[0]} {disciplines[0]}",
       filters={"access": "licensed", "type": "full-text"}
   )
   ```

3. **Parse & Score Results**
   ```python
   for result in dbis_results:
       description = result['description']
       relevance_score = calculate_relevance(description, keywords)
       if relevance_score >= 60:
           discovered_dbs.append(result)
   ```

4. **Merge & Deduplicate**
   ```python
   all_dbs = curated_dbs + discovered_dbs
   all_dbs = deduplicate_by_name(all_dbs)
   all_dbs = sort_by_priority(all_dbs)
   ```

**Output:**
```json
{
  "databases": [
    {
      "name": "ACM Digital Library",
      "url": "https://dl.acm.org",
      "priority": 1,
      "source": "curated"
    },
    {
      "name": "CiteSeerX",
      "url": "https://citeseerx.ist.psu.edu",
      "priority": 2,
      "source": "dbis_discovered",
      "relevance_score": 76
    }
  ]
}
```

**Checkpoint:** User validates database list.

### Phase 1: Suchstring-Generierung

**Verantwortlich:** `search-agent`

**Input:**
```json
{
  "databases": [...],
  "keywords": {
    "primary": ["Lean Governance", "DevOps"],
    "secondary": ["Continuous Delivery", "Agile"]
  }
}
```

**Prozess:**

1. **Load Database-Specific Syntax**
   ```python
   # Jede DB hat eigene Suchsyntax
   SYNTAX_RULES = {
       "IEEE Xplore": {
           "operators": ["AND", "OR", "NOT"],
           "phrase_delimiter": '"',
           "field_search": '("Document Title":term)',
           "max_query_length": 500
       },
       "ACM Digital Library": {
           "operators": ["AND", "OR", "NOT"],
           "field_search": '[[Title: term]]',
           "max_query_length": 1000
       },
       "PubMed": {
           "operators": ["AND", "OR", "NOT"],
           "field_search": 'term[TIAB]',
           "mesh_terms": True
       }
   }
   ```

2. **Generate Query per Database**
   ```python
   def generate_search_string(db_name, keywords):
       syntax = SYNTAX_RULES[db_name]

       # Primary keywords (required)
       primary_clauses = []
       for kw in keywords['primary']:
           # Synonyms expansion
           synonyms = get_synonyms(kw)
           clause = f'({kw} OR {" OR ".join(synonyms)})'
           primary_clauses.append(clause)

       # Combine with AND
       query = f"{syntax['operators'][0].join(primary_clauses)}"

       # Add secondary (optional boost)
       if keywords['secondary']:
           secondary = f"({' OR '.join(keywords['secondary'])})"
           query = f"({query}) AND ({secondary})"

       # Apply field restrictions (title/abstract)
       if syntax.get('field_search'):
           query = apply_field_search(query, syntax)

       # Truncate if too long
       if len(query) > syntax['max_query_length']:
           query = truncate_query(query, syntax['max_query_length'])

       return query
   ```

3. **Validate Queries**
   ```python
   for db, query in search_strings.items():
       if not validate_syntax(query, db):
           raise InvalidQueryError(f"Invalid syntax for {db}: {query}")
   ```

**Output:**
```json
{
  "search_strings": {
    "IEEE Xplore": '("Lean Governance" OR "Lean Management") AND (DevOps OR "Continuous Delivery")',
    "ACM Digital Library": '[[Title: Lean Governance]] OR [[Abstract: DevOps Continuous Delivery]]',
    "PubMed": '(Lean Governance[TIAB] OR Lean Management[TIAB]) AND (DevOps[TIAB] OR Agile[TIAB])'
  }
}
```

**Checkpoint:** User approves search strings.

### Phase 2: Iterative Datenbanksuche

**Verantwortlich:** `browser-agent`

**Input:**
```json
{
  "databases": [...],
  "search_strings": {...},
  "config": {
    "databases_per_iteration": 5,
    "target_candidates": 50,
    "max_iterations": 5
  }
}
```

**Algorithmus:**

```python
candidates = []
iteration = 0

while iteration < max_iterations:
    iteration += 1

    # Select next batch of databases
    batch = databases[iteration*dbs_per_iter : (iteration+1)*dbs_per_iter]

    for db in batch:
        try:
            # Navigate to database
            cdp.navigate(db['url'])

            # Handle login if required
            if requires_login(db):
                wait_for_manual_login()

            # Execute search
            search_query = search_strings[db['name']]
            results = cdp.search_database(db['name'], search_query)

            # Parse results
            for result in results:
                candidate = parse_paper_metadata(result)
                candidates.append(candidate)

            # Log progress
            logger.info(f"{db['name']}: {len(results)} papers found")

        except Exception as e:
            logger.error(f"{db['name']} failed: {e}")
            # Continue with next database

    # Check if target reached
    if len(candidates) >= target_candidates:
        logger.info(f"Target reached: {len(candidates)} >= {target_candidates}")
        break

# Save candidates
save_candidates(candidates, run_dir)
```

**CDP Search Implementation:**

```python
def search_database(db_name, search_string):
    # Database-specific selectors
    SELECTORS = {
        "IEEE Xplore": {
            "search_input": "input[name='queryText']",
            "search_button": "button[type='submit']",
            "result_item": "div.List-results-items",
            "title": "h2.result-item-title",
            "abstract": "div.abstract-text",
            "metadata": "div.description"
        },
        "ACM Digital Library": {
            "search_input": "input#acm-search-input",
            "search_button": "button.search-button",
            "result_item": "li.search__item",
            ...
        }
    }

    selectors = SELECTORS[db_name]

    # Enter search query
    cdp.fill(selectors['search_input'], search_string)
    cdp.click(selectors['search_button'])

    # Wait for results
    cdp.wait_for_selector(selectors['result_item'], timeout=30)

    # Parse results
    results = []
    result_elements = cdp.query_selector_all(selectors['result_item'])

    for elem in result_elements:
        result = {
            'title': cdp.get_text(elem, selectors['title']),
            'abstract': cdp.get_text(elem, selectors['abstract']),
            'metadata': cdp.get_text(elem, selectors['metadata']),
            'url': cdp.get_attribute(elem, 'href'),
            'database': db_name
        }
        results.append(result)

    return results
```

**Output:**
```json
{
  "candidates": [
    {
      "title": "Lean Governance in DevOps Teams",
      "authors": ["Smith, J.", "Miller, A."],
      "year": 2023,
      "venue": "IEEE TSE",
      "abstract": "...",
      "url": "https://...",
      "doi": "10.1109/...",
      "database": "IEEE Xplore",
      "pdf_url": "https://..."
    },
    ...
  ],
  "metadata": {
    "total_candidates": 52,
    "databases_searched": 10,
    "iterations": 2
  }
}
```

### Phase 3: 5D-Bewertung & Ranking

**Verantwortlich:** `scoring-agent`

**5D-Score-Berechnung:**

```python
def calculate_5d_score(candidate):
    """
    Berechnet den 5D-Score für einen Kandidaten.

    Returns:
        dict: {
            'score': 0-100,
            'breakdown': {
                'citations': 0-20,
                'recency': 0-20,
                'relevance': 0-25,
                'quality': 0-20,
                'open_access': 0-15
            }
        }
    """
    scores = {}

    # 1. Citations (20%)
    citations = candidate.get('citations', 0)
    if citations == 0:
        scores['citations'] = 0
    elif citations < 10:
        scores['citations'] = citations * 0.5  # 0-5
    elif citations < 50:
        scores['citations'] = 5 + (citations - 10) * 0.125  # 5-10
    elif citations < 100:
        scores['citations'] = 10 + (citations - 50) * 0.1  # 10-15
    elif citations < 300:
        scores['citations'] = 15 + (citations - 100) * 0.015  # 15-18
    else:
        scores['citations'] = min(20, 18 + (citations - 300) * 0.001)  # 18-20

    # 2. Recency (20%)
    current_year = datetime.now().year
    year = candidate.get('year', current_year - 20)
    year_diff = current_year - year
    scores['recency'] = max(0, 20 - (year_diff * 1))  # -1 point per year

    # 3. Relevance (25%)
    scores['relevance'] = calculate_relevance_score(
        title=candidate['title'],
        abstract=candidate.get('abstract', ''),
        keywords=config['keywords']
    )

    # 4. Quality (20%)
    scores['quality'] = calculate_quality_score(
        venue=candidate.get('venue', ''),
        venue_type=candidate.get('venue_type', 'unknown')
    )

    # 5. Open Access (15%)
    if candidate.get('pdf_url'):
        if is_open_access(candidate['pdf_url']):
            scores['open_access'] = 15  # Gold OA
        else:
            scores['open_access'] = 9   # PDF available via institution
    else:
        scores['open_access'] = 0

    total_score = sum(scores.values())

    return {
        'score': round(total_score, 2),
        'breakdown': scores
    }

def calculate_relevance_score(title, abstract, keywords):
    """
    Berechnet Relevanz-Score basierend auf Keyword-Matches.
    """
    score = 0
    title_lower = title.lower()
    abstract_lower = abstract.lower()

    # Primary keywords in title (highest weight)
    for kw in keywords['primary']:
        if kw.lower() in title_lower:
            score += 8  # max 8 points per primary keyword

    # Primary keywords in abstract
    for kw in keywords['primary']:
        if kw.lower() in abstract_lower:
            score += 4  # max 4 points per primary keyword

    # Secondary keywords
    for kw in keywords.get('secondary', []):
        if kw.lower() in title_lower:
            score += 3
        elif kw.lower() in abstract_lower:
            score += 1

    # Cap at 25
    return min(25, score)

def calculate_quality_score(venue, venue_type):
    """
    Berechnet Qualitäts-Score basierend auf Venue-Ranking.
    """
    # Load rankings from database
    rankings = load_venue_rankings()

    if venue in rankings:
        rank = rankings[venue]

        # CORE rankings für Conferences
        if rank['type'] == 'conference':
            if rank['core'] == 'A*':
                return 20
            elif rank['core'] == 'A':
                return 17
            elif rank['core'] == 'B':
                return 13
            elif rank['core'] == 'C':
                return 9

        # Scimago/IF für Journals
        elif rank['type'] == 'journal':
            if rank['quartile'] == 'Q1':
                return 20
            elif rank['quartile'] == 'Q2':
                return 16
            elif rank['quartile'] == 'Q3':
                return 12
            elif rank['quartile'] == 'Q4':
                return 8

    # Unknown venue
    return 5
```

**Ranking:**

```python
# Sort candidates by score
ranked_candidates = sorted(
    candidates,
    key=lambda c: c['score'],
    reverse=True
)

# Top 27 (1.5x target of 18)
top_27 = ranked_candidates[:27]
```

**Output:**
```json
{
  "ranked_candidates": [
    {
      "rank": 1,
      "title": "...",
      "score": 92,
      "breakdown": {
        "citations": 19,
        "recency": 19,
        "relevance": 25,
        "quality": 20,
        "open_access": 9
      },
      ...
    },
    ...
  ]
}
```

**Checkpoint:** User selects Top 18 from Top 27.

### Phases 4-6: Download, Extraction, Finalization

(Siehe [User Guide Workflow](../user-guide/02-basic-workflow.md) für Details)

---

## State-Management

### State-Datei-Format

```json
{
  "version": "3.0",
  "run_id": "2026-02-18_14-30-00",
  "current_phase": 3,
  "completed_phases": [0, 1, 2],
  "pending_phases": [3, 4, 5, 6],
  "config": {
    "research_question": "...",
    "keywords": {...},
    "disciplines": [...]
  },
  "phase_outputs": {
    "phase_0": {
      "databases": [...],
      "completed_at": "2026-02-18T14:45:00Z"
    },
    "phase_1": {
      "search_strings": {...},
      "completed_at": "2026-02-18T14:55:00Z"
    },
    "phase_2": {
      "candidates_count": 52,
      "iterations": 2,
      "completed_at": "2026-02-18T17:10:00Z"
    }
  },
  "checksum": "sha256:abc123..."
}
```

### State-Persistence

```python
def save_state(state, run_dir):
    """
    Speichert State mit Checksumme für Integritätsprüfung.
    """
    state_file = f"{run_dir}/metadata/research_state.json"

    # Calculate checksum
    state_str = json.dumps(state, sort_keys=True)
    checksum = hashlib.sha256(state_str.encode()).hexdigest()
    state['checksum'] = f"sha256:{checksum}"

    # Backup existing state
    if os.path.exists(state_file):
        backup_file = f"{state_file}.backup_phase_{state['current_phase']}"
        shutil.copy(state_file, backup_file)

    # Write new state atomically
    temp_file = f"{state_file}.tmp"
    with open(temp_file, 'w') as f:
        json.dump(state, f, indent=2)

    os.rename(temp_file, state_file)

    logger.info(f"State saved: Phase {state['current_phase']}, checksum: {checksum[:8]}...")
```

### State-Validierung

```python
def validate_state(state_file):
    """
    Validiert State-Datei-Integrität.
    """
    with open(state_file) as f:
        state = json.load(f)

    # Extract checksum
    stored_checksum = state.pop('checksum')

    # Recalculate
    state_str = json.dumps(state, sort_keys=True)
    calculated_checksum = f"sha256:{hashlib.sha256(state_str.encode()).hexdigest()}"

    # Compare
    if stored_checksum != calculated_checksum:
        raise StateCorruptedError("Checksum mismatch")

    return state
```

---

## Agent-Hierarchie & Kommunikation

### Orchestrator-Agent Pattern

```
┌────────────────────────────────────────────────┐
│           Orchestrator (Main Agent)            │
│                                                │
│  def orchestrate_research():                   │
│      phase = load_or_init_state()              │
│                                                │
│      while phase <= 6:                         │
│          if phase == 0:                        │
│              databases = task(browser_agent)   │
│              checkpoint(databases)             │
│          elif phase == 1:                      │
│              strings = task(search_agent)      │
│              checkpoint(strings)               │
│          ...                                   │
│                                                │
│          save_state(phase)                     │
│          phase += 1                            │
│                                                │
│      generate_outputs()                        │
└────────────────────────────────────────────────┘
         │ Task               │ Task
         ▼                    ▼
    ┌──────────┐         ┌──────────┐
    │ Browser  │         │  Search  │
    │  Agent   │         │  Agent   │
    └──────────┘         └──────────┘
```

### Task Delegation

```markdown
<!-- In Orchestrator SKILL.md -->

## Phase 0: DBIS Navigation

Use the Task tool to invoke browser-agent:

{
  "description": "Navigate DBIS and find databases",
  "prompt": "Navigate to DBIS portal. Search for databases matching keywords: ${keywords}. Return list of relevant databases with URLs and relevance scores.",
  "subagent_type": "browser-agent"
}

Wait for result. Result will contain JSON with databases.
```

### Agent Response Format

```json
{
  "status": "success",
  "phase": 0,
  "output": {
    "databases": [...]
  },
  "metrics": {
    "duration_seconds": 1234,
    "tokens_used": 50000,
    "cost_usd": 0.85
  },
  "logs": "Navigated to DBIS. Found 11 databases..."
}
```

---

## CDP-Integration

### CDP-Wrapper-Architektur

```python
class CDPClient:
    """
    Wrapper um Chrome DevTools Protocol.

    Abstrahiert Browser-Automatisierung und fügt:
    - Error handling & retry logic
    - Logging & metrics
    - Security validations
    - Domain whitelisting
    """

    def __init__(self, port=9222):
        self.port = port
        self.connection = None
        self.session_id = None

    def connect(self):
        """Verbindet zu Chrome Debug-Port."""
        try:
            response = requests.get(f"http://localhost:{self.port}/json")
            targets = response.json()

            # Nutze ersten verfügbaren Tab
            for target in targets:
                if target['type'] == 'page':
                    self.session_id = target['id']
                    self.ws_url = target['webSocketDebuggerUrl']
                    break

            # Öffne WebSocket
            self.connection = websocket.create_connection(self.ws_url)
            logger.info(f"Connected to Chrome on port {self.port}")

        except Exception as e:
            raise CDPConnectionError(f"Failed to connect: {e}")

    def navigate(self, url):
        """
        Navigiert zu URL mit Domain-Validierung.
        """
        # Security: Validate domain
        if not is_whitelisted_domain(url):
            raise SecurityError(f"Domain not whitelisted: {url}")

        # Send CDP command
        command = {
            "id": self._next_id(),
            "method": "Page.navigate",
            "params": {"url": url}
        }

        self._send(command)
        result = self._receive()

        # Wait for page load
        self.wait_for_page_load()

        logger.info(f"Navigated to: {url}")
        return result

    def search_database(self, database_name, search_string):
        """
        Datenbank-spezifische Suche.
        """
        # Load database configuration
        db_config = load_database_config(database_name)

        # Navigate to database
        self.navigate(db_config['url'])

        # Fill search field
        self.fill(db_config['selectors']['search_input'], search_string)

        # Click search button
        self.click(db_config['selectors']['search_button'])

        # Wait for results
        self.wait_for_selector(db_config['selectors']['result_item'])

        # Parse results
        results = self.parse_search_results(db_config['selectors'])

        logger.info(f"{database_name}: {len(results)} results found")
        return results

    def download_pdf(self, url, output_path):
        """
        Lädt PDF herunter mit Retry-Logic.
        """
        @retry_with_backoff(max_retries=3)
        def _download():
            self.navigate(url)

            # Wait for PDF to load
            time.sleep(2)

            # Get PDF binary
            pdf_data = self._get_pdf_content()

            # Save to file
            with open(output_path, 'wb') as f:
                f.write(pdf_data)

        _download()
        logger.info(f"Downloaded PDF: {output_path}")
```

### Domain-Whitelisting

```python
# scripts/validate_domain.py

WHITELISTED_DOMAINS = [
    # Academic Databases
    "dl.acm.org",
    "ieeexplore.ieee.org",
    "springer.com",
    "sciencedirect.com",
    "arxiv.org",
    "scholar.google.com",
    ...

    # DBIS & Proxies
    "dbis.ur.de",
    "eaccess.ub.tum.de",
    "ezproxy.*",  # Wildcard für Uni-Proxies
]

def is_whitelisted_domain(url):
    """
    Prüft ob Domain auf Whitelist.

    Special case: DBIS Proxy Mode
    - URLs via DBIS Proxy werden automatisch erlaubt
    """
    parsed = urlparse(url)
    domain = parsed.netloc.lower()

    # Direct match
    if domain in WHITELISTED_DOMAINS:
        return True

    # Wildcard match (e.g. ezproxy.*)
    for pattern in WHITELISTED_DOMAINS:
        if '*' in pattern:
            regex = pattern.replace('*', '.*')
            if re.match(regex, domain):
                return True

    # DBIS Proxy Mode
    if 'dbis.ur.de/DB=' in url or 'eaccess' in domain:
        return True

    return False
```

---

## Sicherheits-Framework

### Action-Gate

```python
# scripts/safe_bash.py

def safe_bash_execute(command, source="user", user_intent=""):
    """
    Führt Bash-Befehl nur aus wenn durch Action-Gate validiert.
    """
    # Validate command
    validation = action_gate_validate(
        command=command,
        source=source,
        user_intent=user_intent
    )

    if not validation['allowed']:
        raise ActionGateError(f"Command blocked: {validation['reason']}")

    # Execute
    result = subprocess.run(
        command,
        shell=True,
        capture_output=True,
        text=True,
        timeout=120
    )

    return result

def action_gate_validate(command, source, user_intent):
    """
    Validiert Befehl gegen Security-Rules.
    """
    # Rule 1: No network commands without explicit intent
    network_commands = ['curl', 'wget', 'ssh', 'scp', 'rsync']
    if any(cmd in command for cmd in network_commands):
        if source == "external" and "network" not in user_intent.lower():
            return {
                'allowed': False,
                'reason': 'Network command from external source without explicit intent'
            }

    # Rule 2: No destructive file operations
    destructive_commands = ['rm -rf', 'format', 'mkfs', 'dd']
    if any(cmd in command for cmd in destructive_commands):
        return {
            'allowed': False,
            'reason': 'Destructive command not allowed'
        }

    # Rule 3: No privilege escalation
    if 'sudo' in command or 'su -' in command:
        return {
            'allowed': False,
            'reason': 'Privilege escalation not allowed'
        }

    # Rule 4: Scope restriction
    if source == "external":
        # External content kann nur in /tmp oder runs/ schreiben
        allowed_paths = ['/tmp', runs_dir()]
        if not any(path in command for path in allowed_paths):
            return {
                'allowed': False,
                'reason': 'Write outside allowed paths'
            }

    return {'allowed': True}
```

---

## Performance & Optimierungen

### Iterative Search Performance

**Alte Implementierung (V2.0):**
```python
# Alle Datenbanken im Voraus durchsuchen
for db in all_databases:  # z.B. 20 Datenbanken
    search(db)

# Ergebnis: 20 DBs durchsucht, 4 Stunden, $6
```

**Neue Implementierung (V3.0):**
```python
# Iterativ bis Ziel erreicht
iteration = 0
while candidates < target and iteration < max_iterations:
    batch = databases[iteration*5:(iteration+1)*5]
    for db in batch:
        search(db)
    if candidates >= target:
        break  # Stopp!
    iteration += 1

# Ergebnis: 10 DBs durchsucht, 2.5 Stunden, $3.50
```

**Performance-Gewinn:**
- ⚡ 42% schneller
- 💰 40% günstiger
- 🎯 Höhere Relevanz (beste DBs zuerst)

### Caching & Memoization

```python
# Cache für Venue-Rankings (teuer zu fetchen)
@lru_cache(maxsize=1000)
def get_venue_ranking(venue_name):
    return fetch_from_ranking_api(venue_name)

# Cache für DBIS-Abfragen
@lru_cache(maxsize=100)
def search_dbis(query):
    return fetch_from_dbis(query)
```

---

## Nächste Schritte

- **[Agent-Entwicklung](02-agent-development.md)** - Neue Agents schreiben
- **[Datenbanken hinzufügen](03-adding-databases.md)** - Neue DBs integrieren
- **[Testing](04-testing.md)** - Tests schreiben

**[← Zurück zum Developer Guide](README.md)**
