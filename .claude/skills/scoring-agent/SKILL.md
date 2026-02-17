# scoring-agent

Debug/manual entry point for 5D scoring and ranking agent

## Configuration

```json
{
  "context": "fork",
  "agent": "scoring-agent",
  "disable-model-invocation": true
}
```

## Parameters

- `$ARGUMENTS`: Task description (e.g., "Score these 10 candidates based on config quality thresholds")

## Instructions

This is a debug/testing entry point for the scoring-agent.

You can use this to manually test scoring and ranking without running the full orchestrator.

The scoring-agent has access to:
- Read, Grep, Glob (for reading configs and candidates)

But NOT:
- Write, Edit, Bash, WebFetch, WebSearch (read-only agent)
- Task (no spawning sub-agents)

### Example Usage

```
/scoring-agent Apply 5D scoring to candidates in runs/2026-02-17_14-30-00/metadata/candidates.json
```

The agent will return ranked results (JSON format), but will NOT write files directly.
