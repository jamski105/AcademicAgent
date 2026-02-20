# 🚨 Unified Error Reporting Format

**Letzte Aktualisierung:** 2026-02-19

---

## Übersicht

Alle Agents MÜSSEN Fehler im **standardisierten JSON-Format** melden um konsistentes Error-Handling zu ermöglichen.

---

## Standard Error Format (JSON)

```json
{
  "error": {
    "type": "CAPTCHADetected",
    "severity": "warning",
    "phase": 2,
    "agent": "browser-agent",
    "message": "CAPTCHA detected at IEEE Xplore search page",
    "recovery": "user_intervention",
    "context": {
      "url": "https://ieeexplore.ieee.org/search",
      "screenshot": "runs/session_id/logs/error_005.png",
      "search_string": "(lean governance OR agile governance) AND DevOps",
      "database": "IEEE Xplore"
    },
    "timestamp": "2026-02-19T14:30:00Z",
    "run_id": "project_20260219_140000"
  }
}
```

---

## Error Types (Taxonomy)

### Navigation & Browser Errors

- `NavigationTimeout` - Navigation exceeded timeout (30s)
- `CAPTCHADetected` - CAPTCHA challenge encountered
- `LoginRequired` - Database requires authentication
- `PageLoadError` - Page failed to load (HTTP error)
- `CDPConnectionLost` - Chrome DevTools Protocol disconnected
- `DomainBlocked` - Domain not on whitelist

### Search & Extraction Errors

- `SearchTimeout` - Search query timed out
- `NoResultsFound` - Search returned 0 results (not error, just info)
- `ParsingError` - Failed to parse search results HTML
- `ExtractionFailed` - Could not extract metadata from page
- `InvalidSelector` - UI selector not found

### File & Data Errors

- `FileNotFound` - Required file missing
- `CorruptFile` - File exists but corrupted/unreadable
- `ValidationError` - JSON schema validation failed
- `SanitizationFailed` - HTML sanitization detected critical content
- `PDFExtractionFailed` - pdftotext failed (corrupt PDF or OCR needed)

### Security Errors

- `ActionGateBlocked` - Command blocked by action gate
- `PromptInjectionDetected` - Injection pattern found in external content
- `UnauthorizedAccess` - Attempted access to restricted path
- `SecretLeakage` - Attempted to log/expose secrets

### Budget & Resource Errors

- `BudgetExceeded` - Cost limit reached
- `QuotaExceeded` - API rate limit or quota hit
- `DiskSpaceError` - Insufficient disk space
- `MemoryError` - Out of memory

### Configuration Errors

- `ConfigMissing` - Required config file not found
- `ConfigInvalid` - Config file has invalid format/values
- `StateCorrupt` - research_state.json is corrupted

---

## Severity Levels

| Severity | Description | Orchestrator Action |
|----------|-------------|---------------------|
| `info` | Informational (e.g., 0 results) | Log, continue |
| `warning` | Non-critical (e.g., CAPTCHA, retry possible) | Log, retry or ask user |
| `error` | Significant (e.g., validation failed) | Log, skip item, continue phase |
| `critical` | Fatal (e.g., budget exceeded, security breach) | Log, **STOP WORKFLOW**, alert user |

---

## Recovery Strategies

| Recovery | Description | Implementation |
|----------|-------------|----------------|
| `retry` | Auto-retry with backoff | Retry up to 3x with exponential backoff |
| `skip` | Skip this item, continue | Move to next search string / PDF / database |
| `user_intervention` | Requires user action | Pause, display error, wait for user (e.g., CAPTCHA, login) |
| `fallback` | Use alternative method | Try Open Access, manual download, etc. |
| `abort` | Cannot continue | Stop workflow, save state, exit |

---

## Error Logging

### Log Format

```python
# Via logger.py
from scripts.logger import get_logger

logger = get_logger("browser_agent", "runs/session_id")

# Log error in structured format
logger.error(
    "Error occurred during navigation",
    error_type="NavigationTimeout",
    severity="warning",
    phase=2,
    recovery="retry",
    context={
        "url": url,
        "timeout_seconds": 30,
        "attempt": 2
    }
)
```

### Error File Output

Zusätzlich zu Logs, kritische Fehler in separate Error-Datei:

```bash
# runs/[run_id]/errors/phase_2_error_001.json
{
  "error": { ... },
  "stacktrace": "...",
  "system_info": {
    "python_version": "3.11.5",
    "os": "macOS 14.2",
    "chrome_version": "131.0.6778"
  }
}
```

---

## Error Handling Examples

### Example 1: CAPTCHA (Warning, User-Intervention)

```bash
# Browser-agent detects CAPTCHA
python3 scripts/safe_bash.py "python3 -c '
import json
from scripts.logger import get_logger

logger = get_logger(\"browser_agent\", \"runs/\$RUN_ID\")

error = {
    \"error\": {
        \"type\": \"CAPTCHADetected\",
        \"severity\": \"warning\",
        \"phase\": 2,
        \"agent\": \"browser-agent\",
        \"message\": \"CAPTCHA detected at IEEE Xplore\",
        \"recovery\": \"user_intervention\",
        \"context\": {
            \"url\": \"https://ieeexplore.ieee.org\",
            \"screenshot\": \"runs/\$RUN_ID/logs/captcha_001.png\"
        },
        \"timestamp\": \"$(date -u +\"%Y-%m-%dT%H:%M:%SZ\")\",
        \"run_id\": \"\$RUN_ID\"
    }
}

# Log error
logger.error(\"CAPTCHA detected\",
    error_type=\"CAPTCHADetected\",
    recovery=\"user_intervention\",
    url=\"https://ieeexplore.ieee.org\")

# Write error file
with open(\"runs/\$RUN_ID/errors/phase_2_captcha.json\", \"w\") as f:
    json.dump(error, f, indent=2)

print(json.dumps(error))
'"

# User-Benachrichtigung
echo "🚨 CAPTCHA detected!"
echo "   Please solve CAPTCHA in browser window"
echo "   Screenshot: runs/\$RUN_ID/logs/captcha_001.png"
echo ""
echo "Press ENTER when done..."
read

# Retry nach User-Intervention
```

### Example 2: Validation Error (Error, Skip)

```bash
# Validation failed for agent output
python3 scripts/validate_json.py --file metadata/candidates.json --schema schemas/candidates_schema.json

if [ $? -ne 0 ]; then
  # Validation failed - log error
  python3 scripts/safe_bash.py "python3 -c '
from scripts.logger import get_logger
import json

logger = get_logger(\"orchestrator\", \"runs/\$RUN_ID\")

error = {
    \"error\": {
        \"type\": \"ValidationError\",
        \"severity\": \"error\",
        \"phase\": 2,
        \"agent\": \"browser-agent\",
        \"message\": \"Agent output failed JSON schema validation\",
        \"recovery\": \"skip\",
        \"context\": {
            \"file\": \"metadata/candidates.json\",
            \"schema\": \"schemas/candidates_schema.json\"
        },
        \"timestamp\": \"$(date -u +\"%Y-%m-%dT%H:%M:%SZ\")\",
        \"run_id\": \"\$RUN_ID\"
    }
}

logger.error(\"Validation failed\", error_type=\"ValidationError\", recovery=\"skip\")

with open(\"runs/\$RUN_ID/errors/validation_error.json\", \"w\") as f:
    json.dump(error, f, indent=2)
'"

  # Recovery: Skip this output, continue
  echo "⚠️  Skipping invalid output, continuing workflow..."
fi
```

### Example 3: Budget Exceeded (Critical, Abort)

```bash
# Budget check fails
python3 scripts/budget_limiter.py check --run-id $RUN_ID

if [ $? -eq 2 ]; then
  # Critical error - budget exceeded
  python3 scripts/safe_bash.py "python3 -c '
from scripts.logger import get_logger
import json

logger = get_logger(\"orchestrator\", \"runs/\$RUN_ID\")

error = {
    \"error\": {
        \"type\": \"BudgetExceeded\",
        \"severity\": \"critical\",
        \"phase\": 3,
        \"agent\": \"orchestrator\",
        \"message\": \"Research budget exceeded, cannot continue\",
        \"recovery\": \"abort\",
        \"context\": {
            \"max_budget_usd\": 10.0,
            \"current_cost_usd\": 10.25,
            \"percent_used\": 102.5
        },
        \"timestamp\": \"$(date -u +\"%Y-%m-%dT%H:%M:%SZ\")\",
        \"run_id\": \"\$RUN_ID\"
    }
}

logger.critical(\"Budget exceeded\",
    error_type=\"BudgetExceeded\",
    recovery=\"abort\",
    current_cost=10.25)

with open(\"runs/\$RUN_ID/errors/budget_exceeded.json\", \"w\") as f:
    json.dump(error, f, indent=2)

print(json.dumps(error))
'"

  # Abort workflow
  echo "❌ CRITICAL: Budget exceeded!"
  echo "   Cannot continue research."
  echo "   Increase budget or start new run."
  exit 1
fi
```

---

## Error Recovery Decision Tree

```
Error Detected
    │
    ├─ Severity = info → Log → Continue
    │
    ├─ Severity = warning
    │   ├─ Recovery = retry → Retry (3x max) → If fails → user_intervention
    │   └─ Recovery = user_intervention → Pause → Wait for user → Continue
    │
    ├─ Severity = error
    │   ├─ Recovery = skip → Log → Skip item → Continue with next
    │   └─ Recovery = fallback → Try alternative method → If fails → skip
    │
    └─ Severity = critical
        └─ Recovery = abort → Log → Save state → Exit workflow
```

---

## Integration mit Orchestrator

Der Orchestrator muss Error-Responses von Sub-Agents verarbeiten:

```bash
# Nach Task()-Call
AGENT_OUTPUT=$(Task browser-agent ...)

# Check if error returned
if echo "$AGENT_OUTPUT" | grep -q '"error"'; then
  # Parse error
  ERROR_TYPE=$(echo "$AGENT_OUTPUT" | jq -r '.error.type')
  SEVERITY=$(echo "$AGENT_OUTPUT" | jq -r '.error.severity')
  RECOVERY=$(echo "$AGENT_OUTPUT" | jq -r '.error.recovery')

  # Handle based on severity
  case $SEVERITY in
    critical)
      echo "❌ CRITICAL ERROR: $ERROR_TYPE"
      echo "   Aborting workflow..."
      exit 1
      ;;
    error)
      echo "❌ ERROR: $ERROR_TYPE"
      echo "   Recovery: $RECOVERY"
      # Apply recovery strategy
      ;;
    warning)
      echo "⚠️  WARNING: $ERROR_TYPE"
      # Continue with caution
      ;;
  esac
fi
```

---

## Checkliste für Error-Implementierung

Bei jedem neuen Error in Agent-Code:

- [ ] Error-Type aus Taxonomy gewählt
- [ ] Severity korrekt gesetzt
- [ ] Recovery-Strategy definiert
- [ ] Context-Felder gefüllt (URL, file, etc.)
- [ ] Error geloggt via logger.error/critical
- [ ] Error-File geschrieben (bei critical/error)
- [ ] Orchestrator kann Error verarbeiten

---

**Ende des Unified Error Reporting Format**
