# browser-agent

Debug/manual entry point for browser automation agent

## Configuration

```json
{
  "context": "fork",
  "agent": "browser-agent",
  "disable-model-invocation": true
}
```

## Parameters

- `$ARGUMENTS`: Task description (e.g., "Navigate to IEEE and search for DevOps papers")

## Instructions

This is a debug/testing entry point for the browser-agent.

You can use this to manually test browser automation tasks without running the full orchestrator.

The browser-agent has access to:
- Read, Grep, Glob (for reading configs and patterns)
- Bash (for running CDP helper scripts)
- WebFetch (for web requests)

But NOT:
- Write, Edit (read-only agent)
- Task (no spawning sub-agents)

### Example Usage

```
/browser-agent Navigate to IEEE Xplore and take a screenshot
```

The agent will execute your request and return structured results (JSON), but will NOT write files directly.
