# Orchestrator Execution Patterns

**Version:** 1.0.0 (2026-02-23)
**Last Updated:** Refactoring Phase 1
**Purpose:** Single-Source-of-Truth für kritische Ausführungs-Patterns

---

## 1. Action-First Pattern (MANDATORY für ALLE Phasen)

### Regel

**NIEMALS Text VOR Tool-Call ausgeben!**

**Order:**
1. **Execute Tool-Call FIRST** (no text before)
2. **Wait for Tool-Result** (blocking)
3. **THEN write summary text** (1-2 sentences max)
4. **IMMEDIATELY continue** to next phase (no delays)

---

### ✅ CORRECT Example

```
[Tool-Call sofort ohne Text davor]

[Tool-Result abwarten]

Phase 0 abgeschlossen. 15 Datenbanken gefunden. Starte Phase 1.
```

**Flow:**
- NO introduction text
- NO "Let me..."
- NO "I will now..."
- **SOFORT Tool-Call**

---

### ❌ WRONG Example

```
Ich starte jetzt Phase 0. Zuerst navigiere ich zu DBIS...

[Tool-Call]

[Tool-Result]

Phase 0 abgeschlossen.
```

**Problem:** Text VOR Tool-Call = Regelverstoß!

---

## 2. Retry Logic (für Tool-Calls und Agent-Spawns)

### Standard-Retry-Parameter

```bash
MAX_RETRIES=3
INITIAL_BACKOFF=5
MAX_BACKOFF=60
BACKOFF_MULTIPLIER=2
```

### Retry-Strategie

**When to Retry:**
- CDP connection lost (browser-agent)
- Network timeout (WebFetch)
- Agent spawn failed (Task tool error)
- File write errors (transient)

**When NOT to Retry:**
- Validation errors (invalid input)
- Security violations
- User cancellation
- Logic errors (bugs)

### Pattern

```bash
retry_with_backoff() {
    local command=$1
    local max_retries=${2:-3}
    local backoff=${3:-5}

    for i in $(seq 1 $max_retries); do
        if eval "$command"; then
            return 0
        fi

        if [ $i -lt $max_retries ]; then
            echo "⚠️  Retry $i/$max_retries nach ${backoff}s..."
            sleep $backoff
            backoff=$((backoff * 2))
            [ $backoff -gt 60 ] && backoff=60
        fi
    done

    return 1
}
```

**Usage:**
```bash
retry_with_backoff "curl -s https://dbis.uni-regensburg.de" 3 5
```

---

## 3. Validation Gate (für Phase-Outputs)

### Purpose
Sicherstellen, dass jede Phase valide Outputs produziert bevor die nächste startet.

### Standard-Checks

1. **File Existence**
   ```bash
   [ -f "runs/$RUN_ID/metadata/databases.json" ] || exit 1
   ```

2. **JSON Schema Validation**
   ```bash
   jq empty "runs/$RUN_ID/metadata/databases.json" 2>/dev/null || exit 1
   ```

3. **Minimum Content**
   ```bash
   count=$(jq 'length' "runs/$RUN_ID/metadata/databases.json")
   [ "$count" -ge 3 ] || exit 1
   ```

4. **Required Fields**
   ```bash
   jq -e '.[] | select(.database_name and .url)' file.json >/dev/null
   ```

### Pattern

```bash
validate_phase_output() {
    local phase=$1
    local run_id=$2
    local file="runs/$run_id/metadata/phase${phase}_output.json"

    # Existence check
    [ -f "$file" ] || {
        echo "❌ Phase $phase: Output-File fehlt"
        return 1
    }

    # JSON validity
    jq empty "$file" 2>/dev/null || {
        echo "❌ Phase $phase: Invalides JSON"
        return 1
    }

    # Content check (phase-specific)
    local count=$(jq 'length' "$file")
    [ "$count" -gt 0 ] || {
        echo "❌ Phase $phase: Leeres Output"
        return 1
    }

    echo "✅ Phase $phase: Validation passed ($count items)"
    return 0
}
```

---

## 4. Continuous Flow Pattern

### Regel
**Keine Delays zwischen Phasen!**

Nach Abschluss einer Phase:
1. Validiere Output (Validation Gate)
2. Update research_state.json
3. **SOFORT** nächste Phase starten

**VERBOTEN:**
- `sleep` zwischen Phasen
- "Warte auf User-Input" (außer bei Errors)
- "Pausiere für X Sekunden"

### Pattern

```bash
# Phase N abgeschlossen
echo "✅ Phase $N abgeschlossen"

# Validation
validate_phase_output $N $RUN_ID || exit 1

# State update
jq ".phases[$N].status = \"completed\"" research_state.json > tmp && mv tmp research_state.json

# SOFORT Phase N+1 starten (kein sleep!)
[Tool-Call für Phase N+1]
```

---

## 5. State Management Pattern

### research_state.json Structure

```json
{
  "run_id": "run_20260223_143052",
  "mode": "standard",
  "started_at": "2026-02-23T14:30:52Z",
  "phases": {
    "0": {"status": "completed", "started_at": "...", "completed_at": "..."},
    "1": {"status": "in_progress", "started_at": "..."},
    "2": {"status": "pending"}
  },
  "current_phase": 1,
  "checkpoints": [
    {"phase": 0, "timestamp": "...", "output": "metadata/databases.json"}
  ]
}
```

### Update-Pattern

```bash
# Phase starten
jq ".phases[\"$PHASE\"].status = \"in_progress\" | \
    .phases[\"$PHASE\"].started_at = \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\" | \
    .current_phase = $PHASE" research_state.json > tmp && mv tmp research_state.json

# Phase abschließen
jq ".phases[\"$PHASE\"].status = \"completed\" | \
    .phases[\"$PHASE\"].completed_at = \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\" | \
    .checkpoints += [{\"phase\": $PHASE, \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\", \"output\": \"$OUTPUT_FILE\"}]" \
    research_state.json > tmp && mv tmp research_state.json
```

---

## 6. Error Handling Pattern

### Error Categories

**1. Recoverable Errors (Retry)**
- CDP connection lost
- Network timeouts
- Transient file I/O errors

**2. Critical Errors (Abort)**
- Invalid configuration
- Security violations
- Missing prerequisites
- Data corruption

### Pattern

```bash
handle_error() {
    local error_type=$1
    local error_msg=$2
    local phase=$3
    local run_id=$4

    case "$error_type" in
        recoverable)
            echo "⚠️  Recoverable Error: $error_msg"
            echo "   Versuche Recovery..."
            return 0
            ;;
        critical)
            echo "❌ CRITICAL ERROR: $error_msg"
            jq ".phases[\"$phase\"].status = \"failed\" | \
                .phases[\"$phase\"].error = \"$error_msg\"" \
                runs/$run_id/research_state.json > tmp && mv tmp runs/$run_id/research_state.json
            exit 1
            ;;
    esac
}
```

---

## 7. Checkpoint System

### Purpose
Ermöglicht Resume bei Unterbrechung/Fehler.

### Pattern

```bash
create_checkpoint() {
    local phase=$1
    local run_id=$2
    local output_file=$3

    local checkpoint_dir="runs/$run_id/checkpoints"
    mkdir -p "$checkpoint_dir"

    # Save checkpoint metadata
    cat > "$checkpoint_dir/phase${phase}.json" <<EOF
{
  "phase": $phase,
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "output_file": "$output_file",
  "hash": "$(sha256sum runs/$run_id/$output_file | cut -d' ' -f1)"
}
EOF

    echo "💾 Checkpoint Phase $phase gespeichert"
}

# Usage nach jeder Phase
create_checkpoint $PHASE $RUN_ID "metadata/phase${PHASE}_output.json"
```

---

## 8. Logging Pattern

### Standard Log-Format

```bash
log() {
    local level=$1
    local message=$2
    local timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)

    echo "[$timestamp] [$level] $message" | tee -a "runs/$RUN_ID/orchestrator.log"
}

# Usage
log "INFO" "Phase 0 gestartet"
log "WARN" "Retry 1/3 für CDP-Connection"
log "ERROR" "Phase 2 fehlgeschlagen: Invalid JSON"
log "SUCCESS" "Phase 6 abgeschlossen - Recherche erfolgreich"
```

### Log-Levels
- **INFO:** Normale Statusmeldungen
- **WARN:** Recoverable errors, Retries
- **ERROR:** Critical errors, Abbrüche
- **SUCCESS:** Phase/Run erfolgreich abgeschlossen
- **DEBUG:** Nur wenn DEBUG=true (für Entwicklung)

---

## Best Practices

### 1. Idempotency
Alle Operationen sollten idempotent sein:
- Phase-Execution mehrfach ausführbar
- Checkpoint-Creation überschreibbar
- State-Updates safe

### 2. Atomic Operations
Verwende atomic writes:
```bash
# FALSCH
echo "data" > file.json

# RICHTIG
echo "data" > file.json.tmp && mv file.json.tmp file.json
```

### 3. Defensive Programming
```bash
# Prüfe Prerequisiten
[ -z "$RUN_ID" ] && { echo "ERROR: RUN_ID nicht gesetzt"; exit 1; }

# Prüfe File-Existence vor read
[ -f "$file" ] || { echo "ERROR: $file fehlt"; exit 1; }

# Validate JSON vor processing
jq empty "$file" 2>/dev/null || { echo "ERROR: Invalid JSON"; exit 1; }
```

---

## Maintenance

**Dieses Dokument ist Single-Source-of-Truth.**

Bei Änderungen:
1. Update Version-Header
2. Update Last-Updated-Timestamp
3. Teste alle referenzierenden Agents
4. Update Agent-Prompts falls nötig

**Referenzierende Agents:**
- orchestrator-agent.md
- browser-agent.md
- All Phase-Execution-Templates
