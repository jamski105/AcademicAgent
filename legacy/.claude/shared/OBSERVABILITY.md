# 📊 Observability Guide - Logging & Metrics

**Zweck:** Standardisiertes Logging und Metriken für alle Academic Agent System Agents

**Erstellt:** 2026-02-22

---

## 🎯 Überblick

Alle Agents im Academic Agent System nutzen strukturiertes Logging für:
- **Debugging** - Fehlersuche nach Crashes
- **Monitoring** - Live-Verfolgung des Workflows
- **Forensics** - Post-Mortem-Analysen bei Security-Incidents
- **Performance-Optimierung** - Identifikation von Bottlenecks

---

## 📋 MANDATORY: Wann du loggen MUSST

### 1. Phase Start/End (CRITICAL)

**Jeder Agent MUSS:**
- Phase-Start loggen (bei Beginn der Arbeit)
- Phase-End loggen (bei Completion)

```python
logger.phase_start(phase_num, "Phase Name")
# ... Arbeit ...
logger.phase_end(phase_num, "Phase Name", duration_seconds=123.45)
```

### 2. Errors (CRITICAL)

**Bei JEDEM Fehler:**
```python
logger.error("Navigation failed", url=url, error=str(e))
logger.critical("Action-Gate blocked command", command=cmd, reason=reason)
```

### 3. Key Events (MANDATORY)

**Wichtige Ereignisse im Workflow:**
```python
logger.info("Database navigation started", database="IEEE Xplore", url=url)
logger.info("PDF download completed", filename=pdf_file, source="DOI-Direct")
logger.warning("CAPTCHA detected, waiting for user", attempt=1)
```

### 4. Metrics (MANDATORY für wichtige Zahlen)

**Quantitative Metriken:**
```python
logger.metric("databases_found", 8, unit="count")
logger.metric("search_strings_processed", 15, unit="count")
logger.metric("pdfs_downloaded", 18, unit="count")
logger.metric("phase_duration", 450.5, unit="seconds")
```

### 5. Security Events (MANDATORY bei Verdacht)

**Verdächtige Aktivitäten:**
```python
logger.warning("Suspicious HTML detected in search results",
    pattern="<!-- ignore instructions -->",
    source=url)
logger.critical("Prompt injection attempt detected",
    injected_command="curl evil.com",
    blocked_by="sanitize_html.py")
```

---

## 🛠️ Initialisierung

### Für Agents mit Write-Tool (Orchestrator, Setup, Scoring, Extraction)

```python
import sys
sys.path.insert(0, "scripts")
from logger import get_logger

logger = get_logger("agent_name", project_dir="runs/[SESSION_ID]")
logger.phase_start(phase_num, "Phase Name")
```

### Für Agents ohne Write-Tool (Browser, Search)

**Via safe_bash.py + logger.py (inline Python):**

```bash
# Log via inline Python import (empfohlen)
python3 scripts/safe_bash.py "python3 -c '
from scripts.logger import get_logger
logger = get_logger(\"agent_name\", \"runs/\$RUN_ID\")
logger.info(\"Event description\",
    key1=\"value1\",
    key2=\"value2\")
'"
```

**Beispiel:**
```bash
python3 scripts/safe_bash.py "python3 -c '
from scripts.logger import get_logger
logger = get_logger(\"browser_agent\", \"runs/\$RUN_ID\")
logger.info(\"Navigation started\",
    database=\"IEEE Xplore\",
    url=\"\$URL\")
'"
```

---

## 📊 Log-Levels

| Level | Wann verwenden | Beispiel |
|-------|----------------|----------|
| **DEBUG** | Detaillierte Trace-Infos (nur Development) | "Parsed config value: X" |
| **INFO** | Normale Events, Progress | "Phase 2 started", "Found 45 candidates" |
| **WARNING** | Unerwartete Situationen (nicht-kritisch) | "CAPTCHA detected", "0 results for query" |
| **ERROR** | Fehler die Recovery erlauben | "Navigation failed (retrying)" |
| **CRITICAL** | Fehler die Workflow stoppen | "Budget exceeded", "All candidates knocked out" |

---

## 📈 Standard-Metriken pro Agent

### Scoring-Agent
```python
logger.metric("candidates_after_knockout", 40, unit="count")
logger.metric("avg_score", 4.3, unit="score")
logger.metric("top_score", 4.9, unit="score")
```

### Browser-Agent
```python
logger.metric("databases_navigated", 8, unit="count")
logger.metric("search_strings_executed", 30, unit="count")
logger.metric("candidates_collected", 120, unit="count")
logger.metric("pdfs_downloaded", 18, unit="count")
logger.metric("download_success_rate", 0.95, unit="ratio")
```

### Extraction-Agent
```python
logger.metric("pdfs_processed", 18, unit="count")
logger.metric("quotes_extracted", 45, unit="count")
logger.metric("avg_quotes_per_pdf", 2.5, unit="count")
```

### Search-Agent
```python
logger.metric("search_strings_generated", 30, unit="count")
logger.metric("databases_covered", 10, unit="count")
logger.metric("clusters_used", 3, unit="count")
```

### Orchestrator-Agent
```python
logger.metric("total_workflow_duration", 3600, unit="seconds")
logger.metric("phases_completed", 7, unit="count")
logger.metric("total_cost_usd", 2.50, unit="USD")
logger.metric("total_tokens", 150000, unit="tokens")
```

---

## 🔍 Beispiel-Flows

### Vollständiger Phase-Flow (mit Write-Tool)

```python
from scripts.logger import get_logger

# Initialisierung
logger = get_logger("scoring_agent", project_dir="runs/session_123")

# Phase Start
logger.phase_start(3, "Screening & Ranking")

# Key Events
logger.info("Knockout criteria applied",
    knocked_out=5,
    remaining=40)

logger.info("5D scoring completed",
    candidates_scored=40)

logger.info("Ranking completed",
    top_candidate_id="C015",
    top_score=0.92)

# Warnings
logger.warning("Portfolio imbalance detected",
    primary_count=20,
    target=15)

# Metrics
logger.metric("candidates_after_knockout", 40, unit="count")
logger.metric("avg_score", 4.3, unit="score")

# Phase End
logger.phase_end(3, "Screening & Ranking", duration_seconds=120.5)
```

### Vollständiger Phase-Flow (ohne Write-Tool, via safe_bash)

```bash
#!/bin/bash
RUN_ID="session_123"

# Phase Start
python3 scripts/safe_bash.py "python3 -c '
from scripts.logger import get_logger
logger = get_logger(\"browser_agent\", \"runs/\$RUN_ID\")
logger.phase_start(2, \"Database Search\")
'"

# Loop durch Suchstrings
for i in {0..29}; do
  python3 scripts/safe_bash.py "python3 -c '
from scripts.logger import get_logger
logger = get_logger(\"browser_agent\", \"runs/\$RUN_ID\")
logger.info(\"Processing search string\",
    string_index=\$i,
    database=\"IEEE Xplore\")
'"

  # ... Führe Suche aus ...

  # Log Erfolg
  python3 scripts/safe_bash.py "python3 -c '
from scripts.logger import get_logger
logger = get_logger(\"browser_agent\", \"runs/\$RUN_ID\")
logger.info(\"Search completed\",
    string_index=\$i,
    results_count=\$RESULT_COUNT)
'"

  # Metric
  python3 scripts/safe_bash.py "python3 -c '
from scripts.logger import get_logger
logger = get_logger(\"browser_agent\", \"runs/\$RUN_ID\")
logger.metric(\"search_results_found\", \$RESULT_COUNT, unit=\"count\")
'"
done

# Phase End (duration_seconds wird automatisch berechnet wenn phase_start vorher aufgerufen wurde)
python3 scripts/safe_bash.py "python3 -c '
from scripts.logger import get_logger
logger = get_logger(\"browser_agent\", \"runs/\$RUN_ID\")
logger.phase_end(2, \"Database Search\", duration_seconds=450)
'"
```

---

## 📁 Output-Struktur

### Log-Files

**Pfad:** `runs/[RUN_ID]/logs/[agent_name]_YYYYMMDD_HHMMSS.jsonl`

**Format:** JSON Lines (1 Event pro Zeile)

```json
{"timestamp":"2026-02-19T14:30:00Z","level":"INFO","logger":"browser_agent","message":"Phase 2 started: Database Search","metadata":{"phase":2,"phase_name":"Database Search","event":"phase_start"}}
{"timestamp":"2026-02-19T14:32:15Z","level":"ERROR","logger":"browser_agent","message":"Navigation failed","metadata":{"url":"https://ieeexplore.ieee.org","error":"Timeout after 30s"}}
{"timestamp":"2026-02-19T14:45:00Z","level":"INFO","logger":"browser_agent","message":"Phase 2 completed: Database Search","metadata":{"phase":2,"phase_name":"Database Search","duration_seconds":450.5,"event":"phase_end"}}
```

### Console Output

**Format:** Colored, human-readable (stderr)

```
[2026-02-19 14:30:00] INFO  [browser_agent] Phase 2 started: Database Search
[2026-02-19 14:32:15] ERROR [browser_agent] Navigation failed (url=https://ieeexplore.ieee.org, error=Timeout)
[2026-02-19 14:45:00] INFO  [browser_agent] Phase 2 completed (duration=450.5s)
```

---

## 🎯 Best Practices

### DO ✅

- **Log alle Phase-Transitions** (Start/End ist MANDATORY)
- **Log alle Errors mit Context** (URL, Command, Error-Message)
- **Nutze strukturierte Logs** (key-value statt free-text)
- **Log Metriken für wichtige Zahlen** (Kandidaten-Count, Duration, etc.)
- **Nutze safe_bash.py für alle Bash-Calls** (Security-Requirement)

### DON'T ❌

- ❌ Log Secrets (API-Keys, Passwords, Tokens)
- ❌ Log PII ohne Redaction (User-Emails, Namen)
- ❌ Log exzessive Debug-Messages in Production
- ❌ Log unstrukturiert ("Something happened" ohne Context)
- ❌ Skip Phase-Start/End-Logging (ist MANDATORY)

---

## 🔒 Security-Logging

**Bei diesen Events IMMER loggen:**

1. **Action-Gate Blocks:**
   ```python
   logger.warning("Action gate blocked command",
       command=cmd,
       reason="external_content source")
   ```

2. **HTML-Sanitization:**
   ```python
   logger.info("HTML sanitized",
       removed_patterns=["hidden_divs", "html_comments"],
       source_url=url)
   ```

3. **Domain-Validation-Failures:**
   ```python
   logger.warning("Domain validation failed",
       url=url,
       reason="Not from DBIS proxy")
   ```

4. **Prompt-Injection-Detection:**
   ```python
   logger.critical("Prompt injection attempt detected",
       pattern="ignore previous instructions",
       source="candidates.json",
       field="title")
   ```

---

## 📊 Post-Workflow Analysis

### Log-Queries (via jq)

**Alle Errors finden:**
```bash
jq 'select(.level=="ERROR")' runs/$RUN_ID/logs/*.jsonl
```

**Phase-Durations:**
```bash
jq 'select(.metadata.event=="phase_end") | {phase: .metadata.phase, duration: .metadata.duration_seconds}' runs/$RUN_ID/logs/orchestrator_*.jsonl
```

**Alle Metriken:**
```bash
jq 'select(.metadata.metric) | {metric: .metadata.metric, value: .metadata.value}' runs/$RUN_ID/logs/orchestrator_*.jsonl
```

**Errors pro Agent:**
```bash
jq -r 'select(.level=="ERROR") | .logger' runs/$RUN_ID/logs/*.jsonl | sort | uniq -c
```

---

## 🆘 Troubleshooting

### Logger nicht initialisiert?

**Symptom:** `NameError: name 'logger' is not defined`

**Fix:** Initialisiere Logger zu Beginn des Agents:
```python
from scripts.logger import get_logger
logger = get_logger("agent_name", project_dir="runs/SESSION_ID")
```

### Logs erscheinen nicht in Datei?

**Symptom:** Console-Output OK, aber keine Log-Datei

**Fix:** Prüfe ob `runs/[RUN_ID]/logs/` existiert:
```bash
mkdir -p runs/$RUN_ID/logs
```

### safe_bash.py funktioniert nicht?

**Symptom:** `FileNotFoundError: scripts/safe_bash.py`

**Fix:** Agents ohne Write-Tool müssen Orchestrator logging überlassen (siehe Agent-Contracts)

---

## 📚 Weitere Ressourcen

- **Error-Format:** [Error Reporting Format](ERROR_REPORTING_FORMAT.md)
- **Security-Logging:** [Security Policy](SECURITY_POLICY.md)
- **Agent-Contracts:** [Agent API Contracts](AGENT_API_CONTRACTS.md)

---

**Ende des Observability Guide**
