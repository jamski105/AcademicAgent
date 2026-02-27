# Integration Tests - Academic Agent v2.0

## Übersicht

Integration Tests testen **echte API-Calls** und **reale Workflows**. Im Gegensatz zu Unit Tests (gemockt) machen diese Tests echte Requests an externe Services.

## Setup

### 1. Dependencies installieren

```bash
pip install -r requirements-v2.txt
playwright install chromium
```

### 2. API-Keys konfigurieren (Optional)

```bash
# CORE API (optional, verbessert Erfolgsrate)
export CORE_API_KEY="your_core_key"

# TIB Credentials (optional, für DBIS Browser)
export TIB_USERNAME="your_username"
export TIB_PASSWORD="your_password"
```

**Hinweis:** Tests funktionieren auch OHNE API-Keys (Unpaywall ist kostenlos)!

## Tests ausführen

### Alle Integration Tests

```bash
pytest tests/integration/ -v
```

### Nur PDF Workflow Tests

```bash
pytest tests/integration/test_pdf_workflow.py -v
```

### Nur schnelle Tests (ohne Performance Tests)

```bash
pytest tests/integration/test_pdf_workflow.py -v -m "not slow"
```

### Nur Unpaywall Tests

```bash
pytest tests/integration/test_pdf_workflow.py -v -k "unpaywall"
```

### Mit CORE API Tests (braucht API-Key)

```bash
export CORE_API_KEY="your_key"
pytest tests/integration/test_pdf_workflow.py -v -k "core"
```

## Test-Kategorien

### 1. Unpaywall Tests (Keine Keys nötig)

```bash
pytest tests/integration/test_pdf_workflow.py -v -k "unpaywall"
```

**Tests:**
- `test_unpaywall_real_oa_paper` - OA Paper Download
- `test_unpaywall_real_paywalled_paper` - Paywalled Paper (sollte fehlschlagen)

### 2. CORE API Tests (CORE_API_KEY nötig)

```bash
export CORE_API_KEY="your_key"
pytest tests/integration/test_pdf_workflow.py -v -k "core"
```

**Tests:**
- `test_core_real_api` - CORE API Download

### 3. Fallback Chain Tests

```bash
pytest tests/integration/test_pdf_workflow.py -v -k "fallback"
```

**Tests:**
- `test_fallback_chain_unpaywall_only` - Nur Unpaywall
- `test_fallback_chain_with_core` - Unpaywall → CORE

### 4. Batch Processing Tests

```bash
pytest tests/integration/test_pdf_workflow.py -v -k "batch"
```

**Tests:**
- `test_batch_processing_real` - Multiple Papers gleichzeitig
- `test_mixed_success_failure` - Mix aus Success/Failure

### 5. Performance Tests (langsam)

```bash
pytest tests/integration/test_pdf_workflow.py -v -k "performance"
```

**Tests:**
- `test_performance_parallel_downloads` - 5 Papers, Zeit messen

## Erwartete Erfolgsraten

**Mit Unpaywall only:**
- Open Access Papers: ~80-90% Erfolg
- Paywalled Papers: 0% Erfolg (erwartet)

**Mit Unpaywall + CORE:**
- Open Access Papers: ~90-95% Erfolg
- Paywalled Papers: ~10-20% Erfolg

**Mit Unpaywall + CORE + DBIS Browser:**
- Open Access Papers: ~95-100% Erfolg
- Paywalled Papers: ~70-80% Erfolg (wenn TIB Access)

## Troubleshooting

### Tests schlagen fehl: "No module named 'src'"

```bash
# Projekt-Root als PYTHONPATH setzen
export PYTHONPATH=/Users/j65674/Repos/AcademicAgent:$PYTHONPATH
pytest tests/integration/test_pdf_workflow.py -v
```

### Tests schlagen fehl: "playwright not installed"

```bash
playwright install chromium
```

### CORE Tests werden übersprungen

```bash
# API-Key setzen
export CORE_API_KEY="your_key"
```

Kostenloser Key: https://core.ac.uk/services/api

### Rate-Limiting Errors

Unpaywall/CORE haben Rate-Limits:
- Unpaywall: 100k requests/Tag (mehr als genug)
- CORE: 10 req/s mit Key

**Lösung:** Tests mit `--maxfail=1` stoppen bei erstem Fehler:

```bash
pytest tests/integration/ -v --maxfail=1
```

## Test-Daten

Die Tests nutzen **echte DOIs** von bekannten Open Access Journals:

- PLoS ONE Papers (immer OA)
- IEEE Access Papers (meist OA)
- Nature Papers (meist paywalled, für Negativ-Tests)

## CI/CD Integration

Für CI/CD (GitHub Actions, etc.) empfehlen wir:

```yaml
# .github/workflows/integration-tests.yml
- name: Run Integration Tests
  env:
    CORE_API_KEY: ${{ secrets.CORE_API_KEY }}
  run: |
    pytest tests/integration/ -v -m "not slow"
```

**Wichtig:** Nur schnelle Tests in CI (`-m "not slow"`)

## Coverage

Integration Tests prüfen:
- ✅ Echte API-Responses
- ✅ Fallback-Chain Logic
- ✅ Error-Handling (404, Timeouts, etc.)
- ✅ Batch-Processing
- ✅ Caching
- ✅ Performance

**Ergänzen Unit Tests** (gemockt) mit realen Szenarien!
