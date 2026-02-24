#!/bin/bash
# Orchestrator Bash Library
# Version: 1.0.0 (2026-02-23)
# Purpose: Wiederverwendbare Functions für Orchestrator

set -euo pipefail

# ============================================================
# 1. PHASE GUARD - Prüft Prerequisites vor Phase-Start
# ============================================================

phase_guard() {
    local phase=$1
    local run_id=$2
    local run_dir="runs/$run_id"

    echo "🔒 Phase Guard: Prüfe Prerequisites für Phase $phase..."

    # Base checks
    [ -d "$run_dir" ] || { echo "❌ Run-Dir nicht gefunden: $run_dir"; return 1; }
    [ -f "$run_dir/run_config.json" ] || { echo "❌ run_config.json fehlt"; return 1; }

    # Phase-spezifische Checks
    case $phase in
        0)
            # Chrome CDP check
            if ! curl -s http://localhost:9222/json/version &>/dev/null; then
                echo "❌ Chrome CDP nicht erreichbar (Port 9222)"
                return 1
            fi
            ;;
        1)
            [ -f "academic_context.md" ] || { echo "❌ academic_context.md fehlt"; return 1; }
            ;;
        2)
            [ -f "$run_dir/metadata/databases.json" ] || { echo "❌ databases.json fehlt"; return 1; }
            [ -f "$run_dir/metadata/search_strings.json" ] || { echo "❌ search_strings.json fehlt"; return 1; }
            ;;
        3)
            [ -f "$run_dir/metadata/candidates.json" ] || { echo "❌ candidates.json fehlt"; return 1; }
            ;;
        4)
            [ -f "$run_dir/metadata/ranked_sources.json" ] || { echo "❌ ranked_sources.json fehlt"; return 1; }
            ;;
        5)
            [ -d "$run_dir/pdfs" ] && [ "$(ls -A $run_dir/pdfs 2>/dev/null | wc -l)" -gt 0 ] || {
                echo "❌ Keine PDFs gefunden in $run_dir/pdfs"
                return 1
            }
            ;;
        6)
            [ -f "$run_dir/metadata/citations.json" ] || { echo "❌ citations.json fehlt"; return 1; }
            ;;
    esac

    echo "✅ Phase Guard: Prerequisites erfüllt"
    return 0
}

# ============================================================
# 2. RETRY WITH BACKOFF - Exponential Backoff Retry Logic
# ============================================================

retry_with_backoff() {
    local command=$1
    local max_retries=${2:-3}
    local initial_backoff=${3:-5}
    local backoff=$initial_backoff

    for i in $(seq 1 "$max_retries"); do
        if eval "$command"; then
            return 0
        fi

        if [ "$i" -lt "$max_retries" ]; then
            echo "⚠️  Retry $i/$max_retries nach ${backoff}s..."
            sleep "$backoff"
            backoff=$((backoff * 2))
            [ $backoff -gt 60 ] && backoff=60
        fi
    done

    echo "❌ Command failed nach $max_retries Versuchen"
    return 1
}

# ============================================================
# 3. VALIDATE PHASE OUTPUT - JSON Schema + Content Validation
# ============================================================

validate_phase_output() {
    local phase=$1
    local run_id=$2
    local run_dir="runs/$run_id"

    echo "🔍 Validiere Phase $phase Output..."

    # Phase-spezifische Output-Files
    local output_file
    case $phase in
        0) output_file="$run_dir/metadata/databases.json" ;;
        1) output_file="$run_dir/metadata/search_strings.json" ;;
        2) output_file="$run_dir/metadata/candidates.json" ;;
        3) output_file="$run_dir/metadata/ranked_sources.json" ;;
        4) output_file="$run_dir/pdfs" ;;  # Directory
        5) output_file="$run_dir/metadata/citations.json" ;;
        6) output_file="$run_dir/bibliography.md" ;;
        *) echo "❌ Unbekannte Phase: $phase"; return 1 ;;
    esac

    # File/Dir existence
    [ -e "$output_file" ] || { echo "❌ Output fehlt: $output_file"; return 1; }

    # Phase 4 special case (directory)
    if [ $phase -eq 4 ]; then
        local pdf_count=$(ls -1 "$output_file"/*.pdf 2>/dev/null | wc -l)
        [ "$pdf_count" -gt 0 ] || { echo "❌ Keine PDFs gefunden"; return 1; }
        echo "✅ Validation passed: $pdf_count PDFs heruntergeladen"
        return 0
    fi

    # JSON validation
    if [[ "$output_file" == *.json ]]; then
        jq empty "$output_file" 2>/dev/null || {
            echo "❌ Invalides JSON: $output_file"
            return 1
        }

        # Content check
        local count=$(jq 'length' "$output_file" 2>/dev/null || echo "0")
        [ "$count" -gt 0 ] || { echo "❌ Leeres JSON Array"; return 1; }

        echo "✅ Validation passed: $count items in JSON"
    else
        # Markdown/Text validation
        [ -s "$output_file" ] || { echo "❌ Leeres File: $output_file"; return 1; }
        echo "✅ Validation passed: File existiert und nicht leer"
    fi

    return 0
}

# ============================================================
# 4. UPDATE RESEARCH STATE - research_state.json Management
# ============================================================

update_research_state() {
    local action=$1
    local phase=$2
    local run_id=$3
    local state_file="runs/$run_id/research_state.json"

    [ -f "$state_file" ] || { echo "❌ research_state.json nicht gefunden"; return 1; }

    local timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)

    case $action in
        start_phase)
            jq --arg phase "$phase" --arg ts "$timestamp" \
                '.phases[$phase].status = "in_progress" |
                 .phases[$phase].started_at = $ts |
                 .current_phase = ($phase | tonumber)' \
                "$state_file" > "$state_file.tmp" && mv "$state_file.tmp" "$state_file"
            ;;
        complete_phase)
            local output_file=$4
            jq --arg phase "$phase" --arg ts "$timestamp" --arg output "$output_file" \
                '.phases[$phase].status = "completed" |
                 .phases[$phase].completed_at = $ts |
                 .checkpoints += [{"phase": ($phase | tonumber), "timestamp": $ts, "output": $output}]' \
                "$state_file" > "$state_file.tmp" && mv "$state_file.tmp" "$state_file"
            ;;
        fail_phase)
            local error_msg=$4
            jq --arg phase "$phase" --arg ts "$timestamp" --arg error "$error_msg" \
                '.phases[$phase].status = "failed" |
                 .phases[$phase].failed_at = $ts |
                 .phases[$phase].error = $error' \
                "$state_file" > "$state_file.tmp" && mv "$state_file.tmp" "$state_file"
            ;;
        *)
            echo "❌ Unbekannte Action: $action"
            return 1
            ;;
    esac

    echo "✅ State updated: Phase $phase $action"
    return 0
}

# ============================================================
# 5. CREATE CHECKPOINT - Speichert Phase-Checkpoint
# ============================================================

create_checkpoint() {
    local phase=$1
    local run_id=$2
    local output_file=$3
    local checkpoint_dir="runs/$run_id/checkpoints"

    mkdir -p "$checkpoint_dir"

    local full_path="runs/$run_id/$output_file"
    [ -f "$full_path" ] || { echo "⚠️  Output-File nicht gefunden, skip Checkpoint"; return 0; }

    local file_hash=$(sha256sum "$full_path" 2>/dev/null | cut -d' ' -f1 || echo "no-hash")

    cat > "$checkpoint_dir/phase${phase}.json" <<EOF
{
  "phase": $phase,
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "output_file": "$output_file",
  "hash": "$file_hash"
}
EOF

    echo "💾 Checkpoint Phase $phase gespeichert"
    return 0
}

# ============================================================
# 6. LOG - Structured Logging
# ============================================================

log() {
    local level=$1
    local message=$2
    local run_id=${3:-"global"}
    local log_file="runs/$run_id/orchestrator.log"

    mkdir -p "$(dirname "$log_file")"

    local timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    local log_entry="[$timestamp] [$level] $message"

    echo "$log_entry" | tee -a "$log_file"
}

# ============================================================
# 7. CHROME CDP CHECK - Prüft Chrome Verfügbarkeit
# ============================================================

check_chrome_cdp() {
    local max_retries=3
    local backoff=5

    echo "🌐 Prüfe Chrome CDP Verfügbarkeit (Port 9222)..."

    for i in $(seq 1 $max_retries); do
        if curl -s http://localhost:9222/json/version &>/dev/null; then
            echo "✅ Chrome CDP erreichbar"
            return 0
        fi

        if [ $i -lt $max_retries ]; then
            echo "⚠️  Retry $i/$max_retries nach ${backoff}s..."
            sleep $backoff
        fi
    done

    echo "❌ Chrome CDP nicht erreichbar nach $max_retries Versuchen"
    echo "   Starte Chrome mit: chrome --remote-debugging-port=9222"
    return 1
}

# ============================================================
# 8. VALIDATE RUN CONFIG - Prüft run_config.json Struktur
# ============================================================

validate_run_config() {
    local run_id=$1
    local config_file="runs/$run_id/run_config.json"

    [ -f "$config_file" ] || { echo "❌ run_config.json fehlt"; return 1; }

    jq empty "$config_file" 2>/dev/null || {
        echo "❌ run_config.json ist invalides JSON"
        return 1
    }

    # Required fields check
    local required_fields=("run_id" "mode" "session_auto_approve" "target_source_count")
    for field in "${required_fields[@]}"; do
        jq -e ".$field" "$config_file" &>/dev/null || {
            echo "❌ Fehlendes Feld in run_config.json: $field"
            return 1
        }
    done

    echo "✅ run_config.json valide"
    return 0
}

# ============================================================
# EXPORT FUNCTIONS
# ============================================================

export -f phase_guard
export -f retry_with_backoff
export -f validate_phase_output
export -f update_research_state
export -f create_checkpoint
export -f log
export -f check_chrome_cdp
export -f validate_run_config

echo "✅ ORCHESTRATOR_BASH_LIB.sh geladen (Version 1.0.0)"
