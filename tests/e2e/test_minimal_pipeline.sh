#!/bin/bash
# E2E Test: Minimal Research Pipeline
# Tests: setup-agent → browser-agent → extraction-agent

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
TEST_RUN_ID="e2e_test_$(date +%s)"
TEST_RUN_DIR="$ROOT_DIR/runs/$TEST_RUN_ID"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${BLUE}E2E Test: Minimal Research Pipeline${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Test Run ID: $TEST_RUN_ID"
echo "Test Run Dir: $TEST_RUN_DIR"
echo ""

# Setup test environment
mkdir -p "$TEST_RUN_DIR"/{metadata,pdfs,logs,config}

# Test 1: Verify directory structure
echo -e "${BLUE}[Test 1/5]${NC} Verify directory structure"
if [ -d "$TEST_RUN_DIR/metadata" ] && [ -d "$TEST_RUN_DIR/pdfs" ] && [ -d "$TEST_RUN_DIR/logs" ]; then
  echo -e "${GREEN}✅ PASS${NC}: Directory structure created"
else
  echo -e "${RED}❌ FAIL${NC}: Directory structure missing"
  exit 1
fi
echo ""

# Test 2: Create minimal config
echo -e "${BLUE}[Test 2/5]${NC} Create minimal config"
cat > "$TEST_RUN_DIR/config/TestProject_Config.md" <<'EOFCONFIG'
# Test Project Configuration

## RESEARCH QUESTION
Test research question for E2E pipeline validation

## PRIMARY DATABASES
- IEEE Xplore
- SpringerLink

## SEARCH CLUSTERS
**Cluster 1: Core Concept**
- test
- validation
EOFCONFIG

if [ -f "$TEST_RUN_DIR/config/TestProject_Config.md" ]; then
  echo -e "${GREEN}✅ PASS${NC}: Config file created"
else
  echo -e "${RED}❌ FAIL${NC}: Config file creation failed"
  exit 1
fi
echo ""

# Test 3: Validate security utilities
echo -e "${BLUE}[Test 3/5]${NC} Validate security utilities"

# Test action_gate.py
GATE_RESULT=$(python3 "$ROOT_DIR/scripts/action_gate.py" validate \
  --action bash \
  --command "python3 scripts/test.py" \
  --source system 2>/dev/null)

if echo "$GATE_RESULT" | jq -e '.decision == "ALLOW"' > /dev/null 2>&1; then
  echo -e "${GREEN}✅ PASS${NC}: action_gate.py functional"
else
  echo -e "${RED}❌ FAIL${NC}: action_gate.py validation failed"
  exit 1
fi

# Test sanitize_html.py
SANITIZE_TEST="<p>Test</p><!-- injection -->"
SANITIZE_RESULT=$(echo "$SANITIZE_TEST" | python3 "$ROOT_DIR/scripts/sanitize_html.py" 2>/dev/null)

# Robust JSON-based check: verify output has valid JSON with expected structure
if echo "$SANITIZE_RESULT" | jq -e '.text != null and .warnings != null and .injections_detected == 0' > /dev/null 2>&1; then
  echo -e "${GREEN}✅ PASS${NC}: sanitize_html.py functional"
else
  echo -e "${RED}❌ FAIL${NC}: sanitize_html.py validation failed"
  exit 1
fi
echo ""

# Test 4: Verify utility scripts exist
echo -e "${BLUE}[Test 4/5]${NC} Verify utility scripts"
REQUIRED_SCRIPTS=(
  "action_gate.py"
  "sanitize_html.py"
  "safe_bash.py"
  "logger.py"
  "metrics.py"
  "cost_tracker.py"
  "retry_strategy.py"
  "budget_limiter.py"
  "validate_domain.py"
  "cdp_health_check.sh"
)

MISSING=0
for script in "${REQUIRED_SCRIPTS[@]}"; do
  if [ ! -f "$ROOT_DIR/scripts/$script" ]; then
    echo -e "${RED}❌ Missing: scripts/$script${NC}"
    MISSING=$((MISSING + 1))
  fi
done

if [ $MISSING -eq 0 ]; then
  echo -e "${GREEN}✅ PASS${NC}: All utility scripts present (${#REQUIRED_SCRIPTS[@]} scripts)"
else
  echo -e "${RED}❌ FAIL${NC}: $MISSING scripts missing"
  exit 1
fi
echo ""

# Test 5: Verify agent configurations
echo -e "${BLUE}[Test 5/5]${NC} Verify agent configurations"
REQUIRED_AGENTS=(
  "orchestrator-agent.md"
  "setup-agent.md"
  "browser-agent.md"
  "search-agent.md"
  "extraction-agent.md"
  "scoring-agent.md"
)

MISSING_AGENTS=0
for agent in "${REQUIRED_AGENTS[@]}"; do
  if [ ! -f "$ROOT_DIR/.claude/agents/$agent" ]; then
    echo -e "${RED}❌ Missing: .claude/agents/$agent${NC}"
    MISSING_AGENTS=$((MISSING_AGENTS + 1))
  else
    # Check if agent has observability section
    if grep -q "Observability" "$ROOT_DIR/.claude/agents/$agent"; then
      : # Has observability
    else
      echo -e "${YELLOW}⚠️  Warning: $agent missing Observability section${NC}"
    fi
  fi
done

if [ $MISSING_AGENTS -eq 0 ]; then
  echo -e "${GREEN}✅ PASS${NC}: All agent configurations present (${#REQUIRED_AGENTS[@]} agents)"
else
  echo -e "${RED}❌ FAIL${NC}: $MISSING_AGENTS agents missing"
  exit 1
fi
echo ""

# Cleanup
echo -e "${YELLOW}Cleaning up test run directory...${NC}"
rm -rf "$TEST_RUN_DIR"

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}✅ E2E Pipeline Test: PASSED${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Verified:"
echo "  - Directory structure creation"
echo "  - Config file generation"
echo "  - Security utilities (action_gate, sanitizer)"
echo "  - Utility scripts (${#REQUIRED_SCRIPTS[@]} scripts)"
echo "  - Agent configurations (${#REQUIRED_AGENTS[@]} agents)"
echo ""
echo "Note: This is a minimal E2E test."
echo "Full agent invocation tests require Claude Code runtime."
echo ""

exit 0
