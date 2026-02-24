# Academic Agent v2.0 - Modul-Spezifikationen

**Erstellt:** 2026-02-23
**Aktualisiert:** 2026-02-24
**Status:** Grundstruktur implementiert
**Ziel:** Detaillierte Spezifikationen aller Module

---

## 📋 Übersicht

### Implementierungsstatus

✅ **Implementiert:**
- Research Skill (SKILL.md + config_loader.py)
- Konfigurationsdateien (research_modes.yaml, api_config.yaml, academic_context.md)
- Agent-Konfiguration (.claude/settings.json)
- Ordnerstruktur (src/, tests/, config/, docs/)

⏳ **Pending:**
- Agent-Definitionen (4x .md) - Prompts werden später geschrieben
- Python-Module (10 Module) - Werden in Phase 0-7 implementiert

### 4 Agents (LLM-Prompts) - Dateien vorhanden, Prompts folgen

1. **LinearCoordinator** (Sonnet) - `.claude/agents/linear_coordinator.md`
2. **QueryGenerator** (Haiku) - `.claude/agents/query_generator.md`
3. **FiveDScorer** (Haiku) - `.claude/agents/five_d_scorer.md`
4. **QuoteExtractor** (Haiku) - `.claude/agents/quote_extractor.md`

### 10 Python-Module (Deterministisch) - Struktur vorhanden

5. **SearchEngine** - `src/search/` - API-Clients (CrossRef, OpenAlex, S2)
6. **Deduplicator** - `src/search/deduplicator.py` - DOI-basierte Deduplizierung
7. **FiveDScorer** - `src/ranking/` - Citation-Counts, Impact Factor, LLM-Relevanz
8. **PDFFetcher** - `src/pdf/` - PDF-Download Orchestrierung
9. **UnpaywallClient** - `src/pdf/unpaywall_client.py` - Unpaywall API
10. **COREClient** - `src/pdf/core_client.py` - CORE API
11. **DBISBrowserDownloader** - `src/pdf/dbis_browser_downloader.py` - DBIS Browser
12. **QuoteValidator** - `src/extraction/quote_validator.py` - PDF-Text-Validierung
13. **StateManager** - `src/state/` - SQLite + JSON State
14. **ProgressUI** - `src/ui/progress_ui.py` - Rich Progress Bars

---

## 1. LinearCoordinator (Sonnet Agent)

### Verantwortlichkeit
- Workflow-Kontrolle (Phasen 1-6 sequenziell ausführen)
- Modul-Initialisierung und Koordination
- Error-Handling und Fallback-Logik
- User-Feedback via ProgressUI

### Schnittstellen

```python
class LinearCoordinator:
    def run(self, research_query: str) -> ResearchResult:
        """Führt kompletten Recherche-Workflow aus."""

    def resume(self, research_id: str) -> ResearchResult:
        """Setzt abgebrochene Recherche fort (Checkpointing)."""
```

### Code-Beispiel

```python
# .claude/agents/linear_coordinator.md (Agent-Prompt)
def run(self, research_query: str) -> ResearchResult:
    # Phase 1: Setup
    self.ui.show_phase("Phase 1/6: Setup")
    research_id = self.state_manager.create_research_session(research_query)

    # Phase 2: Search via APIs
    self.ui.show_phase("Phase 2/6: Searching APIs")
    papers = self.search_engine.search(query=research_query)
    self.state_manager.save_candidates(papers)

    # Phase 3: Rank Papers
    self.ui.show_phase("Phase 3/6: Ranking Papers")
    ranked_papers = self.scorer.score_and_rank(papers=papers, top_n=15)

    # Phase 4: Fetch PDFs
    self.ui.show_phase("Phase 4/6: Fetching PDFs")
    pdfs = self.pdf_fetcher.fetch_batch(ranked_papers)

    # Phase 5: Extract Quotes
    self.ui.show_phase("Phase 5/6: Extracting Quotes")
    quotes = self.quote_extractor.extract_from_pdfs(pdfs, research_query)

    # Phase 6: Finalize
    return self.state_manager.create_final_output(quotes)
```

### NICHT Verantwortlich für
- ❌ API-Calls (macht SearchEngine)
- ❌ Scoring-Logik (macht FiveDScorer)
- ❌ PDF-Downloads (macht PDFFetcher)
- ❌ Quote-Extraction (macht QuoteExtractor)

---

## 2. SearchEngine (Python-Modul)

### Verantwortlichkeit
- Multi-API-Suche (CrossRef, OpenAlex, Semantic Scholar)
- Deduplizierung via DOI
- Fallback auf Google Scholar (wenn APIs <10 Results)

### Schnittstellen

```python
class SearchEngine:
    def search(
        self,
        query: str,
        sources: list[str] = ["crossref", "openalex", "semantic_scholar"],
        limit: int = 50
    ) -> list[Paper]:
        """Sucht Papers in mehreren APIs, dedupliziert, gibt sortierte Liste."""
```

### Code-Beispiel

```python
# src/search/search_engine.py
class SearchEngine:
    def __init__(self, api_keys: dict):
        self.crossref = CrossRefClient(api_keys["crossref_email"])
        self.openalex = OpenAlexClient(api_keys["openalex_email"])
        self.semantic_scholar = SemanticScholarClient(api_keys["s2_api_key"])

    def search(self, query: str, sources: list[str]) -> list[Paper]:
        results = []

        if "crossref" in sources:
            results.extend(self.crossref.search(query, limit=20))

        if "openalex" in sources:
            results.extend(self.openalex.search(query, limit=20))

        if "semantic_scholar" in sources:
            results.extend(self.semantic_scholar.search(query, limit=20))

        # Deduplizierung via DOI
        unique_papers = self._deduplicate_by_doi(results)

        return unique_papers
```

### Tests

```python
def test_search_returns_papers():
    engine = SearchEngine(api_keys)
    papers = engine.search("DevOps Governance", limit=10)
    assert len(papers) == 10
    assert all(p.doi for p in papers)

def test_deduplication_by_doi():
    engine = SearchEngine(api_keys)
    papers = engine.search("AI Ethics")
    dois = [p.doi for p in papers]
    assert len(dois) == len(set(dois))  # Keine Duplikate
```

---

## 3. FiveDScorer (Hybrid: Python + Haiku)

### Verantwortlichkeit
- 5D-Scoring (Relevanz, Recency, Quality, Authority, Portfolio-Balance)
- **Relevanz-Scoring via Haiku** (Szenario B) - Semantisches Verständnis
- Citation-Count-Integration via OpenAlex (Python)
- Journal Impact Factor via OpenAlex Venue Data (Python)
- Top-N Selektion (Python)

### Schnittstellen

```python
class FiveDScorer:
    def score_and_rank(
        self,
        papers: list[Paper],
        research_query: str,
        top_n: int = 15
    ) -> list[RankedPaper]:
        """Scored Papers nach 5D-Methodik, gibt Top-N zurück."""

    def _compute_relevance_llm(self, paper: Paper, query: str) -> float:
        """LLM-gestützte Relevanz-Berechnung (Szenario B)."""
```

### Code-Beispiel

```python
# src/ranking/five_d_scorer.py
class FiveDScorer:
    def __init__(self):
        self.client = anthropic.Anthropic()  # Für Relevanz-Scoring

    def score_and_rank(self, papers, research_query, top_n=15):
        scored_papers = []

        for paper in papers:
            # Relevanz via Haiku (Szenario B)
            relevance = self._compute_relevance_llm(paper, research_query)

            # Andere Dimensionen via Python
            recency = self._compute_recency(paper.year)
            quality = self._compute_quality(paper.citations, paper.venue)
            authority = self._compute_authority(paper.authors)

            total_score = (relevance * 0.4) + (recency * 0.2) + \
                         (quality * 0.2) + (authority * 0.2)

            scored_papers.append(RankedPaper(paper, total_score))

        # Portfolio-Balance
        balanced = self._apply_portfolio_balance(scored_papers)

        return balanced[:top_n]

    def _compute_relevance_llm(self, paper, query):
        """Haiku-Call für semantische Relevanz."""
        prompt = f"Rate Relevanz von '{paper.title}' für Query '{query}' (0-1)"
        response = self.client.messages.create(
            model="claude-haiku-4",
            messages=[{"role": "user", "content": prompt}]
        )
        return float(response.content[0].text)
```

---

## 4. PDFFetcher (Python-Modul)

### Verantwortlichkeit
- Multi-Strategie PDF-Download (Fallback-Chain)
- **Unpaywall → CORE → DBIS Browser (TIB Institutional Access)**
- Progress-Tracking pro Paper
- Rate-Limiting (10-20s zwischen DBIS-Downloads)
- Retry-Logik mit exponential backoff

### Fallback-Chain

```
1. Unpaywall API    → 40% Erfolg (1-2s)
2. CORE API         → +10% Erfolg (2s)
3. DBIS Browser     → +35-40% Erfolg (15-25s, INSTITUTIONAL!)
```

Bei Fehlschlag aller 3: Paper überspringen (KEIN Manual-Wait!)

### Code-Beispiel

```python
# src/pdf/pdf_fetcher.py
class PDFFetcher:
    def fetch_batch(self, papers, fallback_chain):
        results = []
        for paper in papers:
            result = self.fetch_single(paper, fallback_chain)
            results.append(result)

            if result.source == "dbis_browser":
                self.rate_limiter.wait()  # 10-20s Pause

        return results

    def fetch_single(self, paper, fallback_chain):
        for strategy in fallback_chain:
            try:
                if strategy == "unpaywall":
                    result = self.unpaywall.fetch(paper.doi)
                elif strategy == "core":
                    result = self.core.fetch(paper.doi)
                elif strategy == "dbis_browser":
                    result = self.dbis_browser.download_via_dbis(paper.doi)

                if result.success:
                    return result
            except Exception as e:
                log.warning(f"{strategy} failed: {e}")
                continue

        # Alle Strategien fehlgeschlagen → Paper überspringen
        return PDFResult(success=False, skipped=True)
```

---

Weitere Module siehe [V2_ROADMAP_FULL.md](../V2_ROADMAP_FULL.md) Zeilen 980-1450
