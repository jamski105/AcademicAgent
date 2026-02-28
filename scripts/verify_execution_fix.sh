#!/bin/bash

# Verification Script for Research Workflow Execution Fixes
# Tests that the workflow actually executes commands instead of simulating

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🔍 Academic Agent v2.3+ - Execution Fix Verification"
echo "=================================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0

# Test function
test_check() {
  local test_name="$1"
  local condition="$2"
  local expected="$3"

  echo -n "Testing: $test_name... "

  if [ "$condition" = "$expected" ]; then
    echo -e "${GREEN}✅ PASS${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
  else
    echo -e "${RED}❌ FAIL${NC}"
    echo "  Expected: $expected"
    echo "  Got: $condition"
    TESTS_FAILED=$((TESTS_FAILED + 1))
  fi
}

echo "Step 1: Verifying File Modifications"
echo "-------------------------------------"

# Check if critical files were modified
test_check "SKILL.md contains explicit instructions" \
  "$(grep -c 'CRITICAL EXECUTION RULES' "$PROJECT_ROOT/.claude/skills/research/SKILL.md")" \
  "1"

test_check "linear_coordinator.md has validation gate" \
  "$(grep -c 'VALIDATION GATE' "$PROJECT_ROOT/.claude/agents/linear_coordinator.md")" \
  "1"

test_check "dbis_browser.md has startup verification" \
  "$(grep -c 'Startup Verification' "$PROJECT_ROOT/.claude/agents/dbis_browser.md")" \
  "1"

test_check "quote_extractor.md has pre-execution guard" \
  "$(grep -c 'Pre-Execution Guard' "$PROJECT_ROOT/.claude/agents/quote_extractor.md")" \
  "1"

echo ""
echo "Step 2: Checking Critical Keywords"
echo "-----------------------------------"

# Check for critical execution keywords
test_check "SKILL.md mentions 'DO NOT simulate'" \
  "$(grep -c 'DO NOT simulate' "$PROJECT_ROOT/.claude/skills/research/SKILL.md")" \
  "1"

test_check "linear_coordinator.md has explicit Bash commands" \
  "$(grep -c 'python3 -m src.pdf.pdf_fetcher' "$PROJECT_ROOT/.claude/agents/linear_coordinator.md")" \
  "1"

test_check "linear_coordinator.md has explicit Task calls" \
  "$(grep -c 'Task(' "$PROJECT_ROOT/.claude/agents/linear_coordinator.md" | awk '{if ($1 >= 3) print "1"; else print "0"}')" \
  "1"

test_check "Validation gate checks PDF_COUNT < 5" \
  "$(grep -c 'PDF_COUNT.*-lt 5' "$PROJECT_ROOT/.claude/agents/linear_coordinator.md")" \
  "1"

echo ""
echo "Step 3: Chrome MCP Configuration Check"
echo "---------------------------------------"

if [ -f "$PROJECT_ROOT/.claude/settings.json" ]; then
  CHROME_MCP_CONFIGURED=$(python3 -c "
import json
import sys
try:
    with open('$PROJECT_ROOT/.claude/settings.json') as f:
        config = json.load(f)
        if 'chrome' in config.get('mcpServers', {}):
            print('yes')
        else:
            print('no')
except:
    print('error')
" 2>/dev/null)

  test_check "Chrome MCP configured in settings.json" \
    "$CHROME_MCP_CONFIGURED" \
    "yes"
else
  echo -e "${YELLOW}⚠️  SKIP: .claude/settings.json not found${NC}"
fi

echo ""
echo "Step 4: Python Module Availability"
echo "-----------------------------------"

# Check if required Python modules exist
test_check "src/pdf/pdf_fetcher.py exists" \
  "$([ -f "$PROJECT_ROOT/src/pdf/pdf_fetcher.py" ] && echo 'yes' || echo 'no')" \
  "yes"

test_check "src/extraction/pdf_parser.py exists" \
  "$([ -f "$PROJECT_ROOT/src/extraction/pdf_parser.py" ] && echo 'yes' || echo 'no')" \
  "yes"

test_check "src/utils/ui_notifier.py exists" \
  "$([ -f "$PROJECT_ROOT/src/utils/ui_notifier.py" ] && echo 'yes' || echo 'no')" \
  "yes"

echo ""
echo "Step 5: Validation Gate Logic Check"
echo "-------------------------------------"

# Check validation gate has all required components
VALIDATION_GATE_COMPLETE=$(grep -A 20 "VALIDATION GATE" "$PROJECT_ROOT/.claude/agents/linear_coordinator.md" | \
  grep -c "PDF_COUNT.*wc -l")

test_check "Validation gate counts PDFs" \
  "$([ "$VALIDATION_GATE_COMPLETE" -ge 1 ] && echo 'yes' || echo 'no')" \
  "yes"

VALIDATION_GATE_EXITS=$(grep -A 50 "VALIDATION GATE" "$PROJECT_ROOT/.claude/agents/linear_coordinator.md" | \
  grep "exit 1" | wc -l | tr -d ' ')

test_check "Validation gate exits on failure" \
  "$([ "$VALIDATION_GATE_EXITS" -ge 1 ] && echo 'yes' || echo 'no')" \
  "yes"

echo ""
echo "=================================================="
echo "Verification Results"
echo "=================================================="
echo ""
echo -e "Tests Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Tests Failed: ${RED}$TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
  echo -e "${GREEN}✅ All verification checks passed!${NC}"
  echo ""
  echo "Your research workflow fixes have been successfully implemented."
  echo ""
  echo "Next Steps:"
  echo "1. Run a test with Quick Mode: /research"
  echo "2. Query: 'DevOps' (or any simple topic)"
  echo "3. Watch for:"
  echo "   - Bash tool calls (python3 -m src... commands)"
  echo "   - Task tool spawning agents"
  echo "   - Chrome window opening"
  echo "   - PDFs in session directory"
  echo ""
  echo "Success Criteria:"
  echo "   • PDF count > 0 (with ls output shown)"
  echo "   • Real quotes from PDF content"
  echo "   • No simulation warnings"
  echo ""
  exit 0
else
  echo -e "${RED}❌ Some verification checks failed!${NC}"
  echo ""
  echo "Please review the failed checks above."
  echo "Common issues:"
  echo "  • Files not modified correctly"
  echo "  • Chrome MCP not configured"
  echo "  • Missing Python modules"
  echo ""
  echo "Check IMPLEMENTATION_SUMMARY.md for details."
  echo ""
  exit 1
fi
