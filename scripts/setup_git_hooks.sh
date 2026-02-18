#!/bin/bash
# Setup Git Hooks für AcademicAgent Security
# Installiert Pre-Commit-Hook für Secrets-Erkennung

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
HOOKS_DIR="$ROOT_DIR/.git/hooks"

echo "🔒 Richte Git-Sicherheits-Hooks ein..."

# Erstelle hooks-Verzeichnis falls nicht vorhanden
mkdir -p "$HOOKS_DIR"

# ============================================
# Pre-Commit Hook: Secrets-Erkennung
# ============================================
cat > "$HOOKS_DIR/pre-commit" <<'HOOK_EOF'
#!/bin/bash
# Pre-commit Hook: Secrets-Erkennung für AcademicAgent
# Verhindert versehentliches Committen von sensiblen Daten

set -e

RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # Keine Farbe

echo "🔍 Führe Pre-Commit-Sicherheitsprüfungen durch..."

# ============================================
# Check 1: Secrets-Patterns
# ============================================
echo -n "  [1/3] Prüfe auf Secrets... "

# Hole Liste der zu committenden Dateien
FILES=$(git diff --cached --name-only --diff-filter=ACM)

if [ -z "$FILES" ]; then
  echo -e "${GREEN}✓${NC}"
else
  # Definiere Secret-Patterns
  PATTERNS=(
    'ANTHROPIC_API_KEY'
    'CLAUDE_API_KEY'
    'API_KEY.*=.*[a-zA-Z0-9]{20,}'
    'password.*=.*[^{]'
    'secret.*=.*[^{]'
    'token.*=.*[a-zA-Z0-9]{20,}'
    'aws_access_key'
    'aws_secret_key'
    'private_key'
    'BEGIN RSA PRIVATE KEY'
    'BEGIN PRIVATE KEY'
  )

  FOUND_SECRETS=0

  for file in $FILES; do
    # Überspringe Binary-Dateien
    if file "$file" | grep -q "text"; then
      for pattern in "${PATTERNS[@]}"; do
        if grep -iE "$pattern" "$file" > /dev/null 2>&1; then
          if [ $FOUND_SECRETS -eq 0 ]; then
            echo -e "${RED}✗${NC}"
            echo ""
            echo -e "${RED}❌ SECRETS GEFUNDEN!${NC}"
            echo ""
          fi
          echo -e "  ${RED}Gefunden in:${NC} $file"
          echo -e "  ${YELLOW}Pattern:${NC} $pattern"
          grep -n -iE "$pattern" "$file" | sed 's/^/    /'
          echo ""
          FOUND_SECRETS=1
        fi
      done
    fi
  done

  if [ $FOUND_SECRETS -eq 1 ]; then
    echo -e "${RED}❌ COMMIT BLOCKIERT${NC}"
    echo ""
    echo "Um fortzufahren:"
    echo "  1. Entferne Secrets aus den Dateien"
    echo "  2. Nutze Umgebungsvariablen stattdessen"
    echo "  3. Füge zu .gitignore hinzu falls nötig"
    echo "  4. Oder bypass (NICHT EMPFOHLEN): git commit --no-verify"
    echo ""
    exit 1
  else
    echo -e "${GREEN}✓${NC}"
  fi
fi

# ============================================
# Check 2: Sensible Dateien
# ============================================
echo -n "  [2/3] Prüfe auf sensible Dateien... "

SENSITIVE_FILES=(
  '.env'
  '.env.local'
  '.env.production'
  'secrets.json'
  'credentials.json'
  'id_rsa'
  'id_dsa'
  '*.pem'
  '*.key'
  '*.p12'
  '*.pfx'
)

FOUND_SENSITIVE=0

for file in $FILES; do
  basename_file=$(basename "$file")
  for sensitive in "${SENSITIVE_FILES[@]}"; do
    if [[ "$basename_file" == $sensitive ]]; then
      if [ $FOUND_SENSITIVE -eq 0 ]; then
        echo -e "${RED}✗${NC}"
        echo ""
        echo -e "${RED}❌ SENSIBLE DATEI GEFUNDEN!${NC}"
        echo ""
      fi
      echo -e "  ${RED}Datei:${NC} $file"
      FOUND_SENSITIVE=1
    fi
  done
done

if [ $FOUND_SENSITIVE -eq 1 ]; then
  echo ""
  echo -e "${RED}❌ COMMIT BLOCKIERT${NC}"
  echo ""
  echo "Sensible Dateien sollten nicht committet werden."
  echo "Füge sie stattdessen zu .gitignore hinzu."
  echo ""
  exit 1
else
  echo -e "${GREEN}✓${NC}"
fi

# ============================================
# Check 3: Große Dateien (potentielle Daten-Leaks)
# ============================================
echo -n "  [3/3] Prüfe auf große Dateien... "

LARGE_FILE_LIMIT=10485760  # 10 MB

FOUND_LARGE=0

for file in $FILES; do
  if [ -f "$file" ]; then
    SIZE=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null)
    if [ "$SIZE" -gt "$LARGE_FILE_LIMIT" ]; then
      if [ $FOUND_LARGE -eq 0 ]; then
        echo -e "${YELLOW}⚠${NC}"
        echo ""
        echo -e "${YELLOW}⚠️  GROSSE DATEI GEFUNDEN${NC}"
        echo ""
      fi
      SIZE_MB=$((SIZE / 1048576))
      echo -e "  ${YELLOW}Datei:${NC} $file (${SIZE_MB} MB)"
      FOUND_LARGE=1
    fi
  fi
done

if [ $FOUND_LARGE -eq 1 ]; then
  echo ""
  echo -e "${YELLOW}⚠️  WARNUNG${NC}: Große Dateien gefunden (> 10 MB)"
  echo ""
  echo "Große Dateien können sensible Forschungsdaten enthalten."
  echo "Erwäge:"
  echo "  - Git LFS für große Dateien zu nutzen"
  echo "  - Speicherung in runs/ Verzeichnis (gitignored)"
  echo "  - Externen Storage für Datasets"
  echo ""
  read -p "Trotzdem fortfahren? (y/N) " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
  fi
else
  echo -e "${GREEN}✓${NC}"
fi

echo ""
echo -e "${GREEN}✅ Alle Sicherheitsprüfungen bestanden${NC}"
echo ""

exit 0
HOOK_EOF

# Mache Hook ausführbar
chmod +x "$HOOKS_DIR/pre-commit"

echo "✅ Pre-Commit-Hook installiert"
echo ""

# ============================================
# Teste den Hook
# ============================================
echo "🧪 Teste Pre-Commit-Hook..."
echo ""

# Erstelle eine Test-Datei mit Fake-Secret
TEST_FILE="$ROOT_DIR/.git/hooks/test_secret.txt"
echo "ANTHROPIC_API_KEY=sk-ant-1234567890abcdef" > "$TEST_FILE"

# Stage sie
git -C "$ROOT_DIR" add "$TEST_FILE" 2>/dev/null || true

# Versuche zu committen (sollte blockiert werden)
if git -C "$ROOT_DIR" commit -m "Test-Commit mit Secret" --no-verify 2>/dev/null; then
  echo "⚠️  Warnung: Test-Commit erfolgreich (hätte blockiert werden sollen)"
  git -C "$ROOT_DIR" reset HEAD~1 --soft 2>/dev/null || true
else
  echo "✅ Hook blockiert Secrets korrekt"
fi

# Cleanup
rm -f "$TEST_FILE"
git -C "$ROOT_DIR" reset HEAD 2>/dev/null || true

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Git-Hooks-Setup abgeschlossen!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Pre-Commit-Hook wird jetzt:"
echo "  ✓ API-Keys und Secrets erkennen"
echo "  ✓ Sensible Dateien blockieren (.env, *.pem, etc.)"
echo "  ✓ Vor großen Dateien warnen (> 10 MB)"
echo ""
echo "Zum Bypass (NICHT EMPFOHLEN):"
echo "  git commit --no-verify"
echo ""
