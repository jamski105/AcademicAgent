# 🌐 Browser-Agent Usage Guide - Konkrete Bash-Befehle

**Für:** Browser-Agent (Phase 0, 2, 4)
**Tool:** scripts/browser_helper.js

---

## 🚀 Quick Reference

### Phase 0: DBIS-Navigation (Datenbanken finden)

**Manuelle Variante (empfohlen für Phase 0):**
```bash
# 1. DBIS manuell öffnen
open "https://dbis.de"

# 2. User navigiert manuell, Agent macht Screenshot
node scripts/browser_helper.js screenshot ~/AcademicAgent/projects/[ProjectName]/logs/dbis_screen.png

# 3. Agent analysiert Screenshot mit Claude Vision
# → Extrahiert Datenbank-URLs

# 4. Speichere Ergebnis
cat > ~/AcademicAgent/projects/[ProjectName]/metadata/databases.json <<EOF
{
  "databases": [
    {"name": "IEEE Xplore", "url": "https://ieeexplore.ieee.org", "access_status": "green"},
    {"name": "SpringerLink", "url": "https://link.springer.com", "access_status": "green"}
  ]
}
EOF
```

**ODER: Automatische Variante (experimentell):**
```bash
# Navigate to DBIS
node scripts/browser_helper.js navigate "https://dbis.de" \
  ~/AcademicAgent/projects/[ProjectName]/metadata/dbis_nav.json
```

---

## 🔍 Phase 2: Datenbank-Durchsuchung

### Schritt 1: Datenbank öffnen

```bash
# Lese Datenbank-URL aus databases.json
DATABASE_URL=$(jq -r '.databases[0].url' ~/AcademicAgent/projects/[ProjectName]/metadata/databases.json)

# Navigiere zur Datenbank
node scripts/browser_helper.js navigate "$DATABASE_URL" \
  ~/AcademicAgent/projects/[ProjectName]/metadata/nav_result.json
```

---

### Schritt 2: Suche ausführen

```bash
# Lese Suchstring aus search_strings.json
SEARCH_STRING=$(jq -r '.search_strings[0].db_specific_string' \
  ~/AcademicAgent/projects/[ProjectName]/metadata/search_strings.json)

DATABASE_NAME=$(jq -r '.search_strings[0].database' \
  ~/AcademicAgent/projects/[ProjectName]/metadata/search_strings.json)

# Führe Suche aus
node scripts/browser_helper.js search \
  scripts/database_patterns.json \
  "$DATABASE_NAME" \
  "$SEARCH_STRING" \
  ~/AcademicAgent/projects/[ProjectName]/metadata/results_temp.json
```

---

### Schritt 3: Ergebnisse akkumulieren

```bash
# Füge Ergebnisse zu candidates.json hinzu
jq -s '.[0].candidates + .[1].results | {candidates: .}' \
  ~/AcademicAgent/projects/[ProjectName]/metadata/candidates.json \
  ~/AcademicAgent/projects/[ProjectName]/metadata/results_temp.json \
  > ~/AcademicAgent/projects/[ProjectName]/metadata/candidates_new.json

mv ~/AcademicAgent/projects/[ProjectName]/metadata/candidates_new.json \
   ~/AcademicAgent/projects/[ProjectName]/metadata/candidates.json
```

---

### Schritt 4: Loop für alle Strings

```bash
# Für jeden Suchstring (0-29):
for i in {0..29}; do
  echo "Processing search string $i..."

  SEARCH_STRING=$(jq -r ".search_strings[$i].db_specific_string" search_strings.json)
  DATABASE_NAME=$(jq -r ".search_strings[$i].database" search_strings.json)

  # Suche ausführen
  node scripts/browser_helper.js search \
    scripts/database_patterns.json \
    "$DATABASE_NAME" \
    "$SEARCH_STRING" \
    results_temp.json

  # Akkumulieren (siehe Schritt 3)
  # ...

  # Rate-Limit-Schutz: Alle 10 Strings 30 Sekunden warten
  if (( ($i + 1) % 10 == 0 )); then
    echo "Rate-limit protection: waiting 30 seconds..."
    sleep 30
  fi
done
```

---

## 📥 Phase 4: PDF-Download

### Variante A: Direct Download via wget (bevorzugt)

```bash
# Lese Top 18 Quellen
for i in {0..17}; do
  DOI=$(jq -r ".ranked_sources[$i].doi" ranked_top27.json)
  ID=$(printf "%03d" $((i+1)))
  AUTHOR=$(jq -r ".ranked_sources[$i].authors[0]" ranked_top27.json | cut -d',' -f1)
  YEAR=$(jq -r ".ranked_sources[$i].year" ranked_top27.json)

  # DOI zu URL
  PDF_URL="https://doi.org/$DOI"

  # Download
  wget -O "pdfs/${ID}_${AUTHOR}_${YEAR}.pdf" "$PDF_URL" 2>/dev/null

  # Verifiziere PDF
  if pdftotext "pdfs/${ID}_${AUTHOR}_${YEAR}.pdf" /tmp/test.txt 2>/dev/null; then
    echo "✅ Downloaded: ${ID}_${AUTHOR}_${YEAR}.pdf"
  else
    echo "❌ Failed: ${ID}_${AUTHOR}_${YEAR}.pdf (trying fallback)"
    # Fallback: Open Access
  fi
done
```

---

### Variante B: Browser-gestützter Download (Fallback)

```bash
# Wenn wget fehlschlägt (Paywall):
# 1. DOI-URL öffnen
node scripts/browser_helper.js navigate "https://doi.org/$DOI" nav.json

# 2. Screenshot machen
node scripts/browser_helper.js screenshot screenshot.png

# 3. Claude analysiert Screenshot → findet PDF-Link
# (Wird vom Agent automatisch gemacht)

# 4. Manuelle Anweisung an User:
echo "⚠️  PDF hinter Paywall. Bitte manuell herunterladen:"
echo "   URL: https://doi.org/$DOI"
echo "   Speichere als: pdfs/${ID}_${AUTHOR}_${YEAR}.pdf"
```

---

## 🛑 Error Handling

### CAPTCHA erkannt

```bash
# Screenshot machen
node scripts/browser_helper.js screenshot captcha.png

# User informieren
echo "⚠️  CAPTCHA erkannt. Bitte manuell lösen:"
echo "   1. Öffne Browser: open 'https://...' "
echo "   2. Löse CAPTCHA"
echo "   3. Drücke ENTER zum Fortfahren"
read

# Retry
# ...
```

---

### UI-Element nicht gefunden

```bash
# Screenshot zur Analyse
node scripts/browser_helper.js screenshot ui_error.png

# Claude analysiert Screenshot
# (Automatisch via Read tool in Claude Code)

# Fallback: Manuelle Instruktion
echo "❌ Suchfeld nicht gefunden. Manuelle Navigation erforderlich."
```

---

## 📊 Debugging

### Test: Einzelner Suchstring

```bash
# Test IEEE Xplore Suche
node scripts/browser_helper.js search \
  scripts/database_patterns.json \
  "IEEE Xplore" \
  "lean governance AND DevOps" \
  test_results.json

# Prüfe Output
cat test_results.json | jq '.results[0]'
```

---

### Test: Navigation

```bash
# Test DBIS-Navigation
node scripts/browser_helper.js navigate "https://dbis.de" test_nav.json
cat test_nav.json
```

---

## ⚡ Performance-Tipps

1. **Parallele Suchen vermeiden** (Rate-Limiting!)
2. **Alle 10 Strings: 30 Sekunden warten**
3. **Bei CAPTCHA: Automatisch 30 Sek Pause**
4. **Screenshots nur bei Fehler** (spart Zeit)
5. **headless=false für Debugging**, headless=true für Production

---

## 🚀 Integration in Browser-Agent Prompt

**Wichtig:** Der Browser-Agent soll diese Befehle verwenden, nicht selbst "Browser öffnen" (was nicht geht).

**Beispiel (Phase 2):**
```markdown
Du bist der Browser-Agent. Führe Phase 2 aus.

WICHTIG: Nutze scripts/browser_helper.js für alle Browser-Operationen!

Schritt 1: Lese search_strings.json
Schritt 2: Für jeden String:
  bash: node scripts/browser_helper.js search ...
Schritt 3: Akkumuliere Ergebnisse in candidates.json
```

---

**Ende der Browser Usage Guide.**
