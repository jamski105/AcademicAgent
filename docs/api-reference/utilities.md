# 🛠️ Utilities API Reference

Python-Utility-Module für AcademicAgent.

## cdp_wrapper.py

### CDPClient

**Zweck:** Chrome DevTools Protocol Client für Browser-Automatisierung.

#### Konstruktor

```python
CDPClient(port: int = 9222)
```

**Parameter:**
- `port` - CDP-Port (default: 9222)

**Beispiel:**
```python
from scripts.cdp_wrapper import CDPClient

cdp = CDPClient(port=9222)
```

#### connect()

```python
def connect() → None
```

**Beschreibung:** Verbindet zu Chrome Debug-Port.

**Raises:**
- `CDPConnectionError` - Wenn Verbindung fehlschlägt

**Beispiel:**
```python
cdp = CDPClient()
cdp.connect()
```

#### navigate()

```python
def navigate(url: str) → dict
```

**Beschreibung:** Navigiert zu URL.

**Parameter:**
- `url` - Ziel-URL

**Returns:**
- `dict` - Response mit Status

**Raises:**
- `SecurityError` - Wenn Domain nicht whitelisted
- `CDPError` - Bei Navigation-Fehler

**Beispiel:**
```python
cdp.navigate("https://ieeexplore.ieee.org")
```

#### search_database()

```python
def search_database(
    database_name: str,
    search_string: str
) → list[dict]
```

**Beschreibung:** Führt Suche in Datenbank durch.

**Parameter:**
- `database_name` - Name der Datenbank (muss in `database_disciplines.yaml` existieren)
- `search_string` - Boolean-Suchstring

**Returns:**
- `list[dict]` - Liste von Paper-Metadaten

**Beispiel:**
```python
results = cdp.search_database(
    "IEEE Xplore",
    '"DevOps" AND "Governance"'
)

for paper in results:
    print(paper['title'])
```

#### download_pdf()

```python
def download_pdf(
    url: str,
    output_path: str
) → bool
```

**Beschreibung:** Lädt PDF herunter.

**Parameter:**
- `url` - PDF-URL
- `output_path` - Pfad zum Speichern

**Returns:**
- `bool` - True wenn erfolgreich

**Raises:**
- `DownloadError` - Bei Fehler

**Beispiel:**
```python
success = cdp.download_pdf(
    "https://ieeexplore.ieee.org/stamp/stamp.jsp?arnumber=123",
    "downloads/paper.pdf"
)
```

#### disconnect()

```python
def disconnect() → None
```

**Beschreibung:** Schließt CDP-Verbindung.

**Beispiel:**
```python
cdp.disconnect()
```

---

## cost_tracker.py

### CostTracker

**Zweck:** Tracking von Claude API-Kosten.

#### Konstruktor

```python
CostTracker(run_id: str)
```

**Parameter:**
- `run_id` - Timestamp des Runs (z.B. "2026-02-18_14-30-00")

**Beispiel:**
```python
from scripts.cost_tracker import CostTracker

tracker = CostTracker(run_id="2026-02-18_14-30-00")
```

#### record_llm_call()

```python
def record_llm_call(
    agent_name: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    phase: Optional[str] = None
) → None
```

**Beschreibung:** Recorded einen LLM API-Call.

**Parameter:**
- `agent_name` - Name des Agents (z.B. "browser-agent")
- `model` - Model-Name (z.B. "claude-sonnet-4")
- `input_tokens` - Anzahl Input-Tokens
- `output_tokens` - Anzahl Output-Tokens
- `phase` - Optional: Phase-Name (z.B. "phase_2")

**Beispiel:**
```python
tracker.record_llm_call(
    agent_name="scoring-agent",
    model="claude-sonnet-4",
    input_tokens=5000,
    output_tokens=1500,
    phase="phase_3"
)
```

#### get_total_cost()

```python
def get_total_cost() → float
```

**Beschreibung:** Gibt Gesamtkosten zurück.

**Returns:**
- `float` - Kosten in USD

**Beispiel:**
```python
total = tracker.get_total_cost()
print(f"Total: ${total:.2f}")
```

#### get_breakdown()

```python
def get_breakdown() → dict
```

**Beschreibung:** Gibt detaillierten Kosten-Breakdown.

**Returns:**
```python
{
    "total_usd": 3.45,
    "by_agent": {
        "browser-agent": 1.20,
        "scoring-agent": 0.95,
        ...
    },
    "by_model": {
        "claude-sonnet-4": 2.10,
        "claude-haiku-4": 1.35
    },
    "by_phase": {
        "phase_2": 1.20,
        "phase_3": 0.95,
        ...
    }
}
```

**Beispiel:**
```python
breakdown = tracker.get_breakdown()
print(f"By Agent: {breakdown['by_agent']}")
```

---

## metrics.py

### MetricsCollector

**Zweck:** Sammelt Performance-Metriken.

#### Konstruktor

```python
MetricsCollector(run_id: str)
```

**Beispiel:**
```python
from scripts.metrics import MetricsCollector

metrics = MetricsCollector(run_id="2026-02-18_14-30-00")
```

#### record()

```python
def record(
    metric_name: str,
    value: float,
    unit: Optional[str] = None,
    labels: Optional[dict] = None
) → None
```

**Beschreibung:** Recorded eine Metrik.

**Parameter:**
- `metric_name` - Name der Metrik
- `value` - Wert
- `unit` - Einheit (z.B. "seconds", "count")
- `labels` - Optional: Labels als Dict

**Beispiel:**
```python
metrics.record(
    "papers_found",
    value=52,
    unit="count",
    labels={"database": "IEEE Xplore"}
)
```

#### measure_time()

```python
@contextmanager
def measure_time(
    operation: str,
    labels: Optional[dict] = None
)
```

**Beschreibung:** Context-Manager für Zeit-Messung.

**Beispiel:**
```python
with metrics.measure_time("pdf_download", labels={"file": "paper1.pdf"}):
    download_pdf(...)
```

#### get_summary()

```python
def get_summary() → dict
```

**Beschreibung:** Gibt Metriken-Zusammenfassung.

**Returns:**
```python
{
    "papers_found": {"count": 52, "unit": "count"},
    "pdf_download_duration": {"mean": 5.3, "unit": "seconds"},
    ...
}
```

---

## retry_strategy.py

### retry_with_backoff()

**Zweck:** Decorator für Retry mit Exponential Backoff.

```python
@retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    exceptions: tuple = (Exception,)
)
def function(...):
    ...
```

**Parameter:**
- `max_retries` - Max Anzahl Retries
- `base_delay` - Initial Delay in Sekunden
- `max_delay` - Max Delay
- `exponential_base` - Basis für Exponential (2.0 = verdoppeln)
- `exceptions` - Tuple von Exceptions die retry-ed werden

**Beispiel:**
```python
from scripts.retry_strategy import retry_with_backoff

@retry_with_backoff(max_retries=3, base_delay=2.0)
def flaky_api_call():
    response = requests.get("https://api.example.com")
    return response.json()

# Bei Fehler: Retry nach 2s, 4s, 8s
result = flaky_api_call()
```

### RetryHandler

**Zweck:** Retry-Handler Klasse.

```python
class RetryHandler:
    @staticmethod
    def network_request() → RetryHandler
    @staticmethod
    def file_operation() → RetryHandler
    @staticmethod
    def database_query() → RetryHandler
```

**Vordefinierte Profile:**
- `network_request()` - Für Network-Calls (3 retries, 2s base)
- `file_operation()` - Für File-Ops (5 retries, 0.5s base)
- `database_query()` - Für DB-Queries (4 retries, 1s base)

**Beispiel:**
```python
from scripts.retry_strategy import RetryHandler

handler = RetryHandler.network_request()
result = handler.execute(download_file, url="https://...")
```

---

## safe_bash.py

### safe_bash_execute()

**Zweck:** Führt Bash-Befehl mit Action-Gate-Validierung aus.

```python
def safe_bash_execute(
    command: str,
    source: str = "user",
    user_intent: str = ""
) → subprocess.CompletedProcess
```

**Parameter:**
- `command` - Bash-Befehl
- `source` - "system", "user", oder "external"
- `user_intent` - Beschreibung was User erreichen will

**Returns:**
- `subprocess.CompletedProcess` - Ergebnis

**Raises:**
- `ActionGateError` - Wenn Befehl blockiert wird

**Beispiel:**
```python
from scripts.safe_bash import safe_bash_execute

result = safe_bash_execute(
    "python3 scripts/validate_state.py runs/latest/state.json",
    source="system",
    user_intent="Validate research state"
)

print(result.stdout)
```

### action_gate_validate()

**Zweck:** Validiert Befehl gegen Security-Rules.

```python
def action_gate_validate(
    command: str,
    source: str,
    user_intent: str
) → dict
```

**Returns:**
```python
{
    "allowed": True,
    "reason": ""  # Leer wenn allowed, sonst Grund
}
```

**Beispiel:**
```python
from scripts.safe_bash import action_gate_validate

validation = action_gate_validate(
    "rm -rf /important",
    source="external",
    user_intent=""
)

if not validation['allowed']:
    print(f"Blocked: {validation['reason']}")
```

---

## validate_state.py

### validate_state()

**Zweck:** Validiert Research-State-Integrität.

```python
def validate_state(state_file: str) → dict
```

**Parameter:**
- `state_file` - Pfad zu research_state.json

**Returns:**
```python
{
    "valid": True,
    "current_phase": 3,
    "completed_phases": [0, 1, 2],
    "next_phase": 3,
    "can_resume": True,
    "errors": []
}
```

**Raises:**
- `StateCorruptedError` - Wenn Checksum-Mismatch
- `FileNotFoundError` - Wenn Datei nicht existiert

**Beispiel:**
```python
from scripts.validate_state import validate_state

state = validate_state("runs/2026-02-18_14-30-00/metadata/research_state.json")

if state['can_resume']:
    print(f"Resume from Phase {state['next_phase']}")
```

### save_state()

**Zweck:** Speichert State mit Checksumme.

```python
def save_state(
    state: dict,
    run_dir: str
) → None
```

**Parameter:**
- `state` - State-Dictionary
- `run_dir` - Run-Verzeichnis (z.B. "runs/2026-02-18_14-30-00")

**Beispiel:**
```python
from scripts.validate_state import save_state

state = {
    "version": "3.0",
    "run_id": "2026-02-18_14-30-00",
    "current_phase": 2,
    "completed_phases": [0, 1],
    ...
}

save_state(state, "runs/2026-02-18_14-30-00")
```

---

## Weitere Utilities

### sanitize_html.py

```python
def sanitize_html(
    content: str,
    source: str = "external"
) → str
```

**Beschreibung:** Bereinigt HTML von gefährlichen Elementen.

### validate_domain.py

```python
def is_whitelisted_domain(url: str) → bool
def validate_navigation(url: str) → None  # Raises SecurityError
```

**Beschreibung:** Domain-Whitelisting für Sicherheit.

---

## CLI-Nutzung

Viele Utilities können direkt von CLI aufgerufen werden:

```bash
# State validieren
python3 scripts/validate_state.py runs/[timestamp]/metadata/research_state.json

# Kosten anzeigen
python3 scripts/cost_tracker.py runs/[timestamp]/metadata/llm_costs.jsonl

# Metriken-Summary
python3 scripts/metrics.py summarize runs/[timestamp]/metadata/metrics.jsonl

# Safe Bash (mit Action-Gate)
python3 scripts/safe_bash.py "ls -la"

# CDP-Wrapper
python3 scripts/cdp_wrapper.py navigate "https://example.com"
```

---

## Nächste Schritte

- **[Agents Reference](agents.md)** - Agent-API
- **[Skills Reference](skills.md)** - Orchestrator-API
- **[Developer Guide](../developer-guide/README.md)** - Entwicklung

**[← Zurück zur API Reference](README.md)**
