# setup-agent

Debug/manual entry point for interactive setup agent

## Configuration

```json
{
  "context": "fork",
  "agent": "setup-agent",
  "disable-model-invocation": true
}
```

## Parameters

- `$ARGUMENTS`: Task description (e.g., "Run interactive setup for Quick Quote mode")

## Instructions

This is a debug/testing entry point for the setup-agent.

You can use this to manually test the interactive setup dialog without starting a full research session.

The setup-agent has access to:
- Read, Grep, Glob (for reading configs and templates)
- Bash (for running setup scripts, Chrome checks)

But NOT:
- Write, Edit (read-only agent)
- Task (no spawning sub-agents)

### Example Usage

```
/setup-agent Guide me through setting up a Quick Quote mode research for microservices papers
```

The agent will conduct an interactive dialog and return setup parameters (JSON), but will NOT write configs or start orchestrator directly.

This is mainly useful for testing the dialog flow and config generation logic.
