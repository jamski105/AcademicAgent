"""
Claude Code Agent Spawner with Fallback
For use within Claude Code Skills/Agents

This module provides the actual Task tool integration for agent spawning.
"""

import sys
import json
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def spawn_agent_with_fallback_json(config_json: str) -> str:
    """
    Spawn agent with fallback - JSON interface for CLI usage.

    Args:
        config_json: JSON string with config:
            {
                "agent_type": "query_generator",
                "prompt": "...",
                "description": "Generate queries",
                "preferred_model": "haiku",
                "fallback_model": "sonnet"
            }

    Returns:
        JSON string with result or error
    """
    try:
        config = json.loads(config_json)

        agent_type = config.get("agent_type")
        prompt = config.get("prompt")
        description = config.get("description", f"Run {agent_type}")
        preferred_model = config.get("preferred_model", "haiku")
        fallback_model = config.get("fallback_model", "sonnet")

        # Log attempt
        logger.info(f"Spawning {agent_type} with {preferred_model.upper()} (fallback: {fallback_model.upper()})")

        # Return instruction for Claude Code to execute
        # Claude Code will see this and execute the appropriate Task tool call

        result = {
            "status": "pending",
            "agent_type": agent_type,
            "preferred_model": preferred_model,
            "fallback_model": fallback_model,
            "instruction": "Claude Code should execute Task tool with these parameters",
            "task_params": {
                "subagent_type": agent_type,
                "description": description,
                "prompt": prompt,
                "model": preferred_model
            },
            "fallback_params": {
                "subagent_type": agent_type,
                "description": description,
                "prompt": prompt,
                "model": fallback_model
            }
        }

        return json.dumps(result, indent=2)

    except Exception as e:
        error_result = {
            "status": "error",
            "error": str(e)
        }
        return json.dumps(error_result, indent=2)


if __name__ == "__main__":
    # CLI interface
    if len(sys.argv) < 2:
        print("Usage: python spawn_with_fallback.py '<config_json>'")
        print("\nExample:")
        print('  python spawn_with_fallback.py \'{"agent_type": "query_generator", "prompt": "...", "description": "Generate queries"}\'')
        sys.exit(1)

    config_json = sys.argv[1]
    result = spawn_agent_with_fallback_json(config_json)
    print(result)
