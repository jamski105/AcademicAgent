# extraction-agent

Debug/manual entry point for quote extraction agent

## Configuration

```json
{
  "context": "fork",
  "agent": "extraction-agent",
  "disable-model-invocation": true
}
```

## Parameters

- `$ARGUMENTS`: Task description (e.g., "Extract quotes from PDFs in runs/2026-02-17_14-30-00/downloads/")

## Instructions

This is a debug/testing entry point for the extraction-agent.

You can use this to manually test quote extraction without running the full orchestrator.

The extraction-agent has access to:
- Read, Grep, Glob (for reading PDFs converted to text, configs, keywords)

But NOT:
- Write, Edit, Bash, WebFetch, WebSearch (read-only agent)
- Task (no spawning sub-agents)

### Example Usage

```
/extraction-agent Extract 2-3 quotes from each PDF in runs/2026-02-17_14-30-00/downloads/ based on keywords from config
```

The agent will return structured quotes (JSON format), but will NOT write files directly.

Note: PDFs must be converted to text first (pdftotext is run by orchestrator via Bash in main thread).
