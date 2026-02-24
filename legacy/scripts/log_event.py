#!/usr/bin/env python3
"""
Log Event Helper - Strukturiertes JSONL-Logging für Academic Agent

Usage:
    python3 scripts/log_event.py <run_id> <agent> <event> [key=value ...]

Example:
    python3 scripts/log_event.py test_run orchestrator phase_start phase=0 agent=browser-agent
"""

import json
import sys
from datetime import datetime
from pathlib import Path


def log_event(run_id: str, agent: str, event: str, **kwargs):
    """
    Schreibt ein strukturiertes Log-Event als JSONL

    Args:
        run_id: Run-ID (z.B. "2026-02-23_14-30-00")
        agent: Agent-Name (z.B. "orchestrator", "browser", "scoring")
        event: Event-Name (z.B. "phase_start", "artifact_check")
        **kwargs: Zusätzliche Event-Felder
    """
    log_file = Path(f"runs/{run_id}/logs/{agent}_agent.jsonl")
    log_file.parent.mkdir(parents=True, exist_ok=True)

    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "event": event,
        "run_id": run_id,
        **kwargs
    }

    with open(log_file, "a") as f:
        f.write(json.dumps(entry) + "\n")


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python3 scripts/log_event.py <run_id> <agent> <event> [key=value ...]")
        print("")
        print("Example:")
        print("  python3 scripts/log_event.py test_run orchestrator phase_start phase=0 agent=browser-agent")
        sys.exit(1)

    run_id, agent, event = sys.argv[1:4]

    # Parse key=value args
    kwargs = {}
    for arg in sys.argv[4:]:
        if "=" in arg:
            key, value = arg.split("=", 1)
            # Try to parse as int/bool/float, otherwise keep as string
            if value.lower() == "true":
                value = True
            elif value.lower() == "false":
                value = False
            elif value.isdigit():
                value = int(value)
            elif value.replace(".", "", 1).isdigit() and value.count(".") == 1:
                value = float(value)
            kwargs[key] = value

    log_event(run_id, agent, event, **kwargs)
