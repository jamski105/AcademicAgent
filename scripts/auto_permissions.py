#!/usr/bin/env python3
"""
Auto-Permission System for Academic Agent
Grants automatic permissions for agent-specific safe paths.
"""

import os
import re
from pathlib import Path
from typing import Tuple, Optional

# Agent-specific auto-allowed paths
AUTO_ALLOWED_PATHS = {
    "setup-agent": {
        "write": [
            r"^runs/[^/]+/run_config\.json$",
            r"^runs/[^/]+/config/.*\.json$",
            r"^runs/[^/]+/metadata/search_strategy\.txt$",
            r"^runs/[^/]+/logs/setup_.*\.log$",
        ],
        "read": [
            r"^config/academic_context\.md$",
            r"^config/database_disciplines\.yaml$",
            r"^\.claude/agents/.*\.md$",
        ]
    },
    "orchestrator-agent": {
        "write": [
            r"^runs/[^/]+/metadata/research_state\.json$",
            r"^runs/[^/]+/errors/.*\.json$",
            r"^runs/[^/]+/logs/orchestrator_.*\.jsonl$",
            r"^runs/[^/]+/metadata/.*\.json$",
        ],
        "read": [
            r"^runs/[^/]+/.*\.json$",
            r"^config/.*$",
            r"^schemas/.*\.json$",
        ]
    },
    "browser-agent": {
        "write": [
            r"^runs/[^/]+/logs/browser_.*\.(log|jsonl|png)$",
            r"^runs/[^/]+/screenshots/.*\.png$",
            r"^runs/[^/]+/metadata/databases\.json$",
            r"^runs/[^/]+/metadata/candidates\.json$",
            r"^runs/[^/]+/metadata/session\.json$",
            r"^runs/[^/]+/downloads/.*\.pdf$",
            r"^runs/[^/]+/downloads/downloads\.json$",
        ],
        "read": [
            r"^runs/[^/]+/metadata/(databases|search_strings|ranked_candidates)\.json$",
            r"^runs/[^/]+/run_config\.json$",
            r"^scripts/database_patterns\.json$",
        ]
    },
    "extraction-agent": {
        "write": [
            r"^runs/[^/]+/outputs/quotes\.json$",
            r"^runs/[^/]+/txt/.*\.txt$",
            r"^runs/[^/]+/logs/extraction_.*\.jsonl$",
            r"^runs/[^/]+/errors/extraction_error_.*\.json$",
        ],
        "read": [
            r"^runs/[^/]+/downloads/.*\.pdf$",
            r"^runs/[^/]+/txt/.*\.txt$",
            r"^runs/[^/]+/run_config\.json$",
        ]
    },
    "scoring-agent": {
        "write": [
            r"^runs/[^/]+/metadata/ranked_.*\.json$",
            r"^runs/[^/]+/logs/scoring_.*\.jsonl$",
        ],
        "read": [
            r"^runs/[^/]+/metadata/candidates\.json$",
            r"^runs/[^/]+/run_config\.json$",
        ]
    },
    "search-agent": {
        "write": [
            r"^runs/[^/]+/metadata/search_strings\.json$",
            r"^runs/[^/]+/logs/search_.*\.jsonl$",
        ],
        "read": [
            r"^runs/[^/]+/metadata/databases\.json$",
            r"^runs/[^/]+/run_config\.json$",
        ]
    }
}

# Global safe paths (all agents)
GLOBAL_SAFE_PATHS = {
    "write": [
        r"^/tmp/.*$",
        r"^runs/[^/]+/logs/.*$",
    ],
    "read": [
        r"^config/.*$",
        r"^docs/.*$",
        r"^schemas/.*$",
        r"^\.claude/shared/.*$",
    ]
}

# Blocked paths (never allow)
BLOCKED_PATHS = [
    r"^~?/\.ssh/.*",
    r"^~?/\.aws/.*",
    r"^\.env$",
    r"^.*credentials.*\.json$",
    r"^\.git/.*",
]


def normalize_path(path: str) -> str:
    """Normalize path for matching."""
    # Expand home directory
    path = os.path.expanduser(path)
    # Remove leading ./
    if path.startswith("./"):
        path = path[2:]
    return path


def is_blocked(path: str) -> bool:
    """Check if path is in blocked list."""
    normalized = normalize_path(path)
    for pattern in BLOCKED_PATHS:
        if re.match(pattern, normalized):
            return True
    return False


def check_permission(
    agent_name: str,
    operation: str,  # "read" or "write"
    path: str
) -> Tuple[bool, Optional[str]]:
    """
    Check if agent has auto-permission for operation on path.

    Args:
        agent_name: Name of agent (e.g., "setup-agent")
        operation: "read" or "write"
        path: File path to check

    Returns:
        (allowed: bool, reason: Optional[str])
    """
    # Normalize path
    normalized = normalize_path(path)

    # Check blocked first (highest priority)
    if is_blocked(normalized):
        return False, f"Path is blocked (security): {path}"

    # Check agent-specific paths
    agent_paths = AUTO_ALLOWED_PATHS.get(agent_name, {}).get(operation, [])
    for pattern in agent_paths:
        if re.match(pattern, normalized):
            return True, f"Auto-allowed for {agent_name} ({operation})"

    # Check global safe paths
    global_paths = GLOBAL_SAFE_PATHS.get(operation, [])
    for pattern in global_paths:
        if re.match(pattern, normalized):
            return True, f"Global safe path ({operation})"

    # Not auto-allowed
    return False, f"No auto-permission rule matches"


def get_agent_from_context() -> Optional[str]:
    """
    Try to detect current agent from environment or context.

    Returns:
        Agent name or None
    """
    # Check environment variable (set by orchestrator)
    agent = os.environ.get("CURRENT_AGENT")
    if agent:
        return agent

    # Check parent process name (fallback)
    # This is less reliable but can work
    try:
        import psutil
        parent = psutil.Process().parent()
        if parent:
            cmdline = " ".join(parent.cmdline())
            for agent_name in AUTO_ALLOWED_PATHS.keys():
                if agent_name in cmdline:
                    return agent_name
    except:
        pass

    return None


def check_current_agent_permission(operation: str, path: str) -> Tuple[bool, Optional[str]]:
    """
    Check permission for current agent context.

    Args:
        operation: "read" or "write"
        path: File path

    Returns:
        (allowed: bool, reason: Optional[str])
    """
    agent = get_agent_from_context()
    if not agent:
        return False, "Could not detect current agent context"

    return check_permission(agent, operation, path)


def main():
    """CLI for testing permissions."""
    import sys

    if len(sys.argv) < 4:
        print("Usage: python3 auto_permissions.py <agent> <operation> <path>")
        print("Example: python3 auto_permissions.py setup-agent write runs/test/run_config.json")
        sys.exit(1)

    agent = sys.argv[1]
    operation = sys.argv[2]
    path = sys.argv[3]

    allowed, reason = check_permission(agent, operation, path)

    if allowed:
        print(f"✅ ALLOWED: {reason}")
        sys.exit(0)
    else:
        print(f"❌ DENIED: {reason}")
        sys.exit(1)


if __name__ == "__main__":
    main()
