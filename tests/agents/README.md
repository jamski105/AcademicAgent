# Agent Tests

Tests for Claude Code Agents

## Test Strategy

Agent tests are integration tests that verify agent behavior:
- Input/Output contracts
- Error handling
- Timeout behavior
- Integration with coordinator

## Agents to Test

1. **linear_coordinator** - Master orchestrator
2. **query_generator** - Query expansion
3. **llm_relevance_scorer** - Semantic relevance scoring
4. **quote_extractor** - Quote extraction from PDFs
5. **dbis_browser** - Browser automation (Chrome MCP)

## Running Tests

```bash
pytest tests/agents/ -v
```

## Implementation Status

- [ ] test_linear_coordinator.py
- [ ] test_query_generator.py
- [ ] test_llm_relevance_scorer.py
- [ ] test_quote_extractor.py
- [ ] test_dbis_browser.py

## Notes

- Agents are spawned via Task tool
- Tests require Claude Code environment
- May require actual LLM calls (cost consideration)
- Mock strategies TBD
