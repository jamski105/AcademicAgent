# AcademicAgent v2.0 - Test Suite

Test-Suite für AcademicAgent v2.0 mit Unit, Integration und E2E Tests.

---

## 📂 Test-Struktur

```
tests/
├── conftest.py                    # Pytest Configuration & Fixtures
├── pytest.ini                     # Pytest Settings
├── README.md                      # Diese Datei
│
├── unit/                          # Unit Tests (schnell, isoliert)
│   ├── test_retry.py             # Retry-Logik (migriert aus v1.0)
│   ├── test_pdf_security.py      # PDF-Security-Validierung (migriert)
│   ├── test_domain_validator.py  # Domain-Validierung (migriert)
│   ├── test_crossref_client.py   # CrossRef API Client (NEU)
│   ├── test_openalex_client.py   # OpenAlex API Client (NEU)
│   ├── test_semantic_scholar_client.py  # Semantic Scholar (NEU)
│   ├── test_pdf_fetcher.py       # PDF-Download Fallback-Chain (NEU)
│   └── test_five_d_scorer.py     # 5D-Scoring-Algorithmus (NEU)
│
├── integration/                   # Integration Tests (langsam, echte APIs)
│   ├── test_api_clients.py       # API-Client-Integration
│   └── test_pdf_download_chain.py  # PDF-Download-Integration
│
└── e2e/                           # End-to-End Tests (sehr langsam)
    └── test_full_workflow.py      # Kompletter Research-Workflow
```

---

## 🚀 Tests ausführen

### Alle Tests

```bash
pytest
```

### Nur Unit Tests (schnell)

```bash
pytest tests/unit/
# oder
pytest -m unit
```

### Nur Integration Tests

```bash
pytest tests/integration/
# oder
pytest -m integration
```

### Nur E2E Tests

```bash
pytest tests/e2e/
# oder
pytest -m e2e
```

### Tests ohne langsame Tests

```bash
pytest -m "not slow"
```

### Tests ohne Integration/E2E

```bash
pytest -m "not integration and not e2e"
```

### Mit Coverage

```bash
pytest --cov=src --cov-report=html --cov-report=term
```

---

## 📊 Test-Kategorien

### Unit Tests ⚡ (< 1 Sekunde)

**Eigenschaften:**
- Schnell (< 1 Sekunde pro Test)
- Isoliert (keine externen Dependencies)
- Verwenden Mocks für APIs, Browser, etc.

**Migriert aus v1.0:**
- ✅ `test_retry.py` - Retry-Strategie (Exponential Backoff, RetryHandler)
- ✅ `test_pdf_security.py` - PDF-Security-Validierung (Prompt-Injection-Detection)
- ✅ `test_domain_validator.py` - Domain-Validierung (Sci-Hub/LibGen-Blocklist)

**Neu für v2.0:**
- ✅ `test_crossref_client.py` - CrossRef API Client
- ✅ `test_openalex_client.py` - OpenAlex API Client
- ✅ `test_semantic_scholar_client.py` - Semantic Scholar API Client
- ✅ `test_pdf_fetcher.py` - PDF-Fetcher mit Fallback-Chain
- ✅ `test_five_d_scorer.py` - 5D-Scoring-Algorithmus

### Integration Tests 🔗 (1-10 Sekunden)

**Eigenschaften:**
- Langsamer (1-10 Sekunden)
- Macht echte API-Calls (mit Retry)
- Benötigt Internet-Verbindung

**Tests:**
- `test_api_clients.py` - API-Client-Integration
- `test_pdf_download_chain.py` - PDF-Download-Integration

### E2E Tests 🌐 (1-5 Minuten)

**Eigenschaften:**
- Sehr langsam (1-5 Minuten)
- Kompletter Workflow von Anfang bis Ende
- Benötigt alle Credentials (ANTHROPIC_API_KEY, etc.)

**Tests:**
- `test_full_workflow.py` - Kompletter Research-Workflow

---

## 🔧 Test-Fixtures (conftest.py)

### Path Fixtures
- `project_root` - Project root directory
- `src_path` - src/ directory
- `temp_dir` - Temporary directory
- `temp_db` - Temporary SQLite database

### Mock Fixtures
- `mock_crossref_response` - Mock CrossRef API response
- `mock_openalex_response` - Mock OpenAlex API response
- `mock_semantic_scholar_response` - Mock Semantic Scholar response
- `mock_unpaywall_response` - Mock Unpaywall response
- `mock_api_client` - Mock API client
- `mock_browser` - Mock Playwright browser
- `mock_state_manager` - Mock state manager

### Test Data Fixtures
- `sample_paper` - Single paper metadata
- `sample_papers` - List of papers
- `sample_query` - Sample research query
- `sample_pdf_text` - Sample PDF text content
- `test_config` - Test configuration

---

## 📝 Test-Konventionen

### Naming
- Test-Dateien: `test_*.py`
- Test-Klassen: `Test*`
- Test-Funktionen: `test_*`

### Struktur
```python
class TestFeatureName:
    """Tests für Feature-Name"""

    def test_happy_path(self):
        """Test: Happy-Path-Szenario"""
        # Arrange
        # Act
        # Assert

    def test_edge_case(self):
        """Test: Edge-Case-Szenario"""
        # ...
```

### Markers
```python
@pytest.mark.unit          # Unit Test
@pytest.mark.integration   # Integration Test
@pytest.mark.e2e           # E2E Test
@pytest.mark.slow          # Langsamer Test
@pytest.mark.requires_browser  # Benötigt Browser
@pytest.mark.requires_api_key  # Benötigt API-Key
```

---

## 🎯 Test-Coverage-Ziel

**Ziel: 80%+ Coverage**

- Unit Tests: 70-80%
- Integration Tests: 5-10 Tests
- E2E Tests: 3-5 Tests

### Coverage messen

```bash
pytest --cov=src --cov-report=html
open htmlcov/index.html
```

---

## 🐛 Debugging

### Einzelnen Test ausführen

```bash
pytest tests/unit/test_retry.py::TestExponentialBackoff::test_exponential_increases_delay -v
```

### Mit Print-Statements

```bash
pytest -s tests/unit/test_retry.py
```

### Mit Debugger

```bash
pytest --pdb tests/unit/test_retry.py
```

---

## 📦 Dependencies

Installiert via `requirements-v2.txt`:

```txt
pytest>=8.3.0
pytest-asyncio>=0.24.0
pytest-cov>=6.0.0
pytest-mock>=3.14.0
coverage>=7.6.0
faker>=33.3.0
```

---

## 🚨 CI/CD Integration

### GitHub Actions (geplant)

```yaml
# .github/workflows/tests.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements-v2.txt
      - run: pytest -m "not integration and not e2e"
      - run: pytest --cov=src --cov-report=xml
      - uses: codecov/codecov-action@v3
```

---

## 📚 Weitere Informationen

- [TEST_MIGRATION_v2.md](../docs/TEST_MIGRATION_v2.md) - Test-Migrationsstrategie
- [V2_ROADMAP.md](../V2_ROADMAP.md) - Phase 6: Testing
- [pytest Documentation](https://docs.pytest.org/)
