#!/bin/bash
# Tests for DBIS Proxy Mode
# Validates that domain validation enforces DBIS-first policy

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
SESSION_FILE="/tmp/test_session.json"

echo "🧪 DBIS Proxy Mode Tests"
echo "========================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

PASSED=0
FAILED=0

# Cleanup
rm -f "$SESSION_FILE"

# Test 1: DBIS domain always allowed
echo "[Test 1] DBIS domain always allowed"
RESULT=$(python3 "$ROOT_DIR/scripts/validate_domain.py" "https://dbis.ur.de" --mode proxy 2>/dev/null)
if echo "$RESULT" | jq -e '.allowed == true' > /dev/null; then
  echo -e "${GREEN}✅ PASS${NC}: DBIS domain allowed"
  PASSED=$((PASSED + 1))
else
  echo -e "${RED}❌ FAIL${NC}: DBIS domain blocked"
  FAILED=$((FAILED + 1))
fi
echo ""

# Test 2: Direct database access blocked (no referer)
echo "[Test 2] Direct IEEE access blocked (no DBIS referer)"
RESULT=$(python3 "$ROOT_DIR/scripts/validate_domain.py" "https://ieeexplore.ieee.org" --mode proxy 2>/dev/null)
if echo "$RESULT" | jq -e '.allowed == false' > /dev/null; then
  echo -e "${GREEN}✅ PASS${NC}: Direct database access blocked"
  PASSED=$((PASSED + 1))
else
  echo -e "${RED}❌ FAIL${NC}: Direct database access not blocked"
  FAILED=$((FAILED + 1))
fi
echo ""

# Test 3: Database access allowed WITH DBIS referer
echo "[Test 3] IEEE access allowed WITH DBIS referer"
RESULT=$(python3 "$ROOT_DIR/scripts/validate_domain.py" \
  "https://ieeexplore.ieee.org" \
  --referer "https://dbis.ur.de/dbinfo/fachliste.php" \
  --mode proxy 2>/dev/null)
if echo "$RESULT" | jq -e '.allowed == true' > /dev/null; then
  echo -e "${GREEN}✅ PASS${NC}: Database access via DBIS referer allowed"
  PASSED=$((PASSED + 1))
else
  echo -e "${RED}❌ FAIL${NC}: Database access via DBIS referer blocked"
  FAILED=$((FAILED + 1))
fi
echo ""

# Test 4: Session tracking - start at DBIS
echo "[Test 4] Session tracking - start at DBIS"
RESULT=$(python3 "$ROOT_DIR/scripts/track_navigation.py" \
  "https://dbis.ur.de" \
  "$SESSION_FILE" 2>/dev/null)
if echo "$RESULT" | jq -e '.status == "session_started"' > /dev/null; then
  echo -e "${GREEN}✅ PASS${NC}: Session started from DBIS"
  PASSED=$((PASSED + 1))
else
  echo -e "${RED}❌ FAIL${NC}: Session start failed"
  FAILED=$((FAILED + 1))
fi
echo ""

# Test 5: Session tracking - database allowed after DBIS
echo "[Test 5] Database access WITH active DBIS session"
# First, create session by navigating to DBIS
python3 "$ROOT_DIR/scripts/track_navigation.py" "https://dbis.ur.de" "$SESSION_FILE" > /dev/null 2>&1

# Now try to access database with session
RESULT=$(python3 "$ROOT_DIR/scripts/validate_domain.py" \
  "https://scopus.com" \
  --session-file "$SESSION_FILE" \
  --mode proxy 2>/dev/null)
if echo "$RESULT" | jq -e '.allowed == true' > /dev/null; then
  echo -e "${GREEN}✅ PASS${NC}: Database allowed with active session"
  PASSED=$((PASSED + 1))
else
  echo -e "${RED}❌ FAIL${NC}: Database blocked despite active session"
  FAILED=$((FAILED + 1))
fi
echo ""

# Test 6: Pirate site always blocked
echo "[Test 6] Sci-Hub blocked even with DBIS referer"
RESULT=$(python3 "$ROOT_DIR/scripts/validate_domain.py" \
  "https://sci-hub.se/paper" \
  --referer "https://dbis.ur.de" \
  --mode proxy 2>/dev/null)
if echo "$RESULT" | jq -e '.allowed == false' > /dev/null; then
  echo -e "${GREEN}✅ PASS${NC}: Pirate site blocked"
  PASSED=$((PASSED + 1))
else
  echo -e "${RED}❌ FAIL${NC}: Pirate site not blocked"
  FAILED=$((FAILED + 1))
fi
echo ""

# Test 7: First navigation to non-DBIS blocked
echo "[Test 7] First navigation must be DBIS"
rm -f "$SESSION_FILE"  # Reset session
RESULT=$(python3 "$ROOT_DIR/scripts/track_navigation.py" \
  "https://ieeexplore.ieee.org" \
  "$SESSION_FILE" 2>/dev/null)
if echo "$RESULT" | jq -e '.status == "error"' > /dev/null; then
  echo -e "${GREEN}✅ PASS${NC}: Non-DBIS first navigation blocked"
  PASSED=$((PASSED + 1))
else
  echo -e "${RED}❌ FAIL${NC}: Non-DBIS first navigation not blocked"
  FAILED=$((FAILED + 1))
fi
echo ""

# Test 8: DOI resolver allowed
echo "[Test 8] DOI resolver always allowed"
RESULT=$(python3 "$ROOT_DIR/scripts/validate_domain.py" \
  "https://doi.org/10.1109/example" \
  --mode proxy 2>/dev/null)
if echo "$RESULT" | jq -e '.allowed == true' > /dev/null; then
  echo -e "${GREEN}✅ PASS${NC}: DOI resolver allowed"
  PASSED=$((PASSED + 1))
else
  echo -e "${RED}❌ FAIL${NC}: DOI resolver blocked"
  FAILED=$((FAILED + 1))
fi
echo ""

# Cleanup
rm -f "$SESSION_FILE"

# Summary
TOTAL=$((PASSED + FAILED))

# Calculate pass rate with bc (fallback to awk if not available)
if command -v bc &> /dev/null; then
  PASS_RATE=$(echo "scale=2; $PASSED / $TOTAL * 100" | bc)
else
  PASS_RATE=$(awk "BEGIN {printf \"%.2f\", $PASSED / $TOTAL * 100}")
fi

echo "========================"
echo "Test Results:"
echo "  Total:  $TOTAL"
echo -e "  ${GREEN}Passed: $PASSED${NC}"
echo -e "  ${RED}Failed: $FAILED${NC}"
echo ""
echo "Pass Rate: $PASS_RATE%"

# Vergleich mit awk da bc möglicherweise nicht verfügbar
PASS_RATE_INT=$(echo "$PASS_RATE" | awk -F. '{print $1}')
if [ "$PASS_RATE_INT" -eq 100 ]; then
  echo -e "${GREEN}✅ ALL TESTS PASSED${NC}"
  exit 0
else
  echo -e "${RED}❌ SOME TESTS FAILED${NC}"
  exit 1
fi
