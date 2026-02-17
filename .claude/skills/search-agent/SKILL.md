# search-agent

Debug/manual entry point for search string generation agent

## Configuration

```json
{
  "context": "fork",
  "agent": "search-agent",
  "disable-model-invocation": true
}
```

## Parameters

- `$ARGUMENTS`: Task description (e.g., "Generate search strings for DevOps governance research")

## Instructions

This is a debug/testing entry point for the search-agent.

You can use this to manually test search string generation without running the full orchestrator.

The search-agent has access to:
- Read, Grep, Glob (for reading configs and database patterns)
- WebSearch (for researching search strategies)

But NOT:
- Write, Edit, Bash (read-only agent)
- Task (no spawning sub-agents)

### Example Usage

```
/search-agent Generate 3 search strings for IEEE Xplore based on config/Config_Demo_DevOps.md
```

The agent will return structured search strings (JSON format), but will NOT write files directly.
