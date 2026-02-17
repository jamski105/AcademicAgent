#!/bin/bash
# CDP Health Check Script
# Monitors Chrome DevTools Protocol connection
# Auto-recovery if Chrome crashes

CDP_PORT=9222
CDP_URL="http://localhost:${CDP_PORT}/json/version"
MAX_RETRIES=3
RETRY_DELAY=5

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Chrome CDP is running
check_cdp() {
    curl -s --connect-timeout 3 "$CDP_URL" > /dev/null 2>&1
    return $?
}

# Get Chrome process info
get_chrome_pid() {
    # macOS
    pgrep -f "remote-debugging-port=${CDP_PORT}" 2>/dev/null | head -1
}

# Check Chrome memory usage
check_chrome_memory() {
    local pid=$(get_chrome_pid)
    if [ -z "$pid" ]; then
        return 1
    fi

    # macOS: Get memory in MB
    local mem_mb=$(ps -o rss= -p "$pid" 2>/dev/null | awk '{print int($1/1024)}')

    if [ -z "$mem_mb" ]; then
        return 1
    fi

    echo "$mem_mb"
    return 0
}

# Restart Chrome with CDP
restart_chrome() {
    echo -e "${YELLOW}🔄 Restarting Chrome...${NC}"

    # Kill existing Chrome
    local pid=$(get_chrome_pid)
    if [ -n "$pid" ]; then
        kill "$pid" 2>/dev/null
        sleep 2
    fi

    # Start Chrome with CDP
    bash "$(dirname "$0")/start_chrome_debug.sh" > /dev/null 2>&1 &

    # Wait for Chrome to start
    local attempts=0
    while [ $attempts -lt 10 ]; do
        sleep 2
        if check_cdp; then
            echo -e "${GREEN}✅ Chrome restarted successfully${NC}"
            return 0
        fi
        attempts=$((attempts + 1))
    done

    echo -e "${RED}❌ Failed to restart Chrome${NC}"
    return 1
}

# Main health check
health_check() {
    local retry_count=0

    while [ $retry_count -lt $MAX_RETRIES ]; do
        # Check CDP connection
        if check_cdp; then
            # Check memory usage
            local mem_mb=$(check_chrome_memory)
            if [ -n "$mem_mb" ]; then
                # Warn if memory > 2GB
                if [ "$mem_mb" -gt 2048 ]; then
                    echo -e "${YELLOW}⚠️  Chrome memory usage: ${mem_mb}MB (high)${NC}"
                fi
            fi

            echo -e "${GREEN}✅ CDP healthy (Port ${CDP_PORT})${NC}"
            return 0
        fi

        # CDP not responding
        echo -e "${RED}❌ CDP not responding (attempt $((retry_count + 1))/${MAX_RETRIES})${NC}"

        # Try to restart
        if restart_chrome; then
            return 0
        fi

        retry_count=$((retry_count + 1))
        if [ $retry_count -lt $MAX_RETRIES ]; then
            echo -e "${YELLOW}Waiting ${RETRY_DELAY}s before retry...${NC}"
            sleep $RETRY_DELAY
        fi
    done

    echo -e "${RED}❌ CDP health check failed after ${MAX_RETRIES} attempts${NC}"
    echo -e "${YELLOW}💡 Manual steps:${NC}"
    echo "   1. Check if Chrome is running: pgrep -f 'remote-debugging-port'"
    echo "   2. Kill Chrome: pkill -f 'remote-debugging-port'"
    echo "   3. Restart: bash scripts/start_chrome_debug.sh"
    echo "   4. Verify: curl http://localhost:9222/json/version"

    return 1
}

# Monitoring mode (for long-running processes)
monitor() {
    local interval=${1:-300} # Default: 5 minutes
    local run_dir=${2:-}

    echo -e "${GREEN}🔍 Starting CDP monitoring (interval: ${interval}s)${NC}"

    if [ -n "$run_dir" ]; then
        echo "   Run directory: $run_dir"
        local log_file="${run_dir}/logs/cdp_health.log"
        mkdir -p "$(dirname "$log_file")"
    fi

    while true; do
        local timestamp=$(date '+%Y-%m-%d %H:%M:%S')

        if check_cdp; then
            local mem_mb=$(check_chrome_memory)
            local status="✅ HEALTHY (${mem_mb}MB)"

            # Memory warning
            if [ -n "$mem_mb" ] && [ "$mem_mb" -gt 2048 ]; then
                status="⚠️  HIGH_MEM (${mem_mb}MB)"
                echo -e "${YELLOW}[${timestamp}] ${status}${NC}"
            fi

            # Log to file
            if [ -n "$run_dir" ]; then
                echo "[${timestamp}] ${status}" >> "$log_file"
            fi
        else
            local status="❌ DOWN - attempting recovery"
            echo -e "${RED}[${timestamp}] ${status}${NC}"

            if [ -n "$run_dir" ]; then
                echo "[${timestamp}] ${status}" >> "$log_file"
            fi

            # Attempt recovery
            if restart_chrome; then
                echo -e "${GREEN}[${timestamp}] ✅ RECOVERED${NC}"
                if [ -n "$run_dir" ]; then
                    echo "[${timestamp}] ✅ RECOVERED" >> "$log_file"
                fi
            else
                echo -e "${RED}[${timestamp}] ❌ RECOVERY FAILED${NC}"
                if [ -n "$run_dir" ]; then
                    echo "[${timestamp}] ❌ RECOVERY FAILED" >> "$log_file"
                fi
                exit 1
            fi
        fi

        sleep "$interval"
    done
}

# Usage info
usage() {
    echo "Usage: cdp_health_check.sh [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  check              One-time health check (default)"
    echo "  monitor [interval] Monitor continuously (interval in seconds, default: 300)"
    echo "  restart            Force Chrome restart"
    echo ""
    echo "Options:"
    echo "  --run-dir <path>   Log to run directory (for monitor mode)"
    echo ""
    echo "Examples:"
    echo "  cdp_health_check.sh check"
    echo "  cdp_health_check.sh monitor 300 --run-dir runs/2026-02-17_14-30-00"
    echo "  cdp_health_check.sh restart"
}

# Main
case "${1:-check}" in
    check)
        health_check
        exit $?
        ;;
    monitor)
        shift
        monitor "$@"
        ;;
    restart)
        restart_chrome
        exit $?
        ;;
    -h|--help)
        usage
        exit 0
        ;;
    *)
        echo "Unknown command: $1"
        usage
        exit 1
        ;;
esac
