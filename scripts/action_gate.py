#!/usr/bin/env python3
"""
Action Gate - Sicherheits-Validator für Tool-Aufrufe
Validiert dass Tool-Aufrufe sicher sind vor Ausführung

Verwendung:
  python3 scripts/action_gate.py validate \
    --action "bash" \
    --command "curl https://evil.com" \
    --user-intent "Research for thesis" \
    --source "external_content"

Gibt JSON mit Entscheidung (ALLOW/BLOCK) und Begründung zurück
"""

import sys
import json
import re
import argparse
from typing import Dict, Any


# Blocked command patterns
BLOCKED_PATTERNS = [
    (r'(curl|wget|fetch)\s+.*https?://', 'Network request to external URL', 'HIGH'),
    (r'(ssh|scp|rsync)\s+', 'Remote connection attempt', 'HIGH'),
    (r'(cat|grep|head|tail)\s+.*\.env', 'Secret file access (.env)', 'CRITICAL'),
    (r'(cat|grep|head|tail)\s+.*/\.ssh/', 'Secret file access (SSH keys)', 'CRITICAL'),
    (r'(cat|grep|head|tail)\s+.*/secrets?/', 'Secret directory access', 'CRITICAL'),
    (r'rm\s+-rf?\s+/', 'Destructive filesystem operation', 'CRITICAL'),
    (r'dd\s+if=.*of=', 'Raw disk operation', 'CRITICAL'),
    (r'mkfs\s+', 'Filesystem creation (destructive)', 'CRITICAL'),
    (r'sudo\s+', 'Privilege escalation attempt', 'CRITICAL'),
    (r'chmod\s+\+x.*evil|malware|backdoor', 'Suspicious executable creation', 'HIGH'),
]

# Allowed command patterns (whitelisted)
ALLOWED_PATTERNS = [
    (r'python3\s+scripts/', 'Python script in scripts/ directory'),
    (r'node\s+scripts/', 'Node script in scripts/ directory'),
    (r'bash\s+scripts/', 'Bash script in scripts/ directory'),
    (r'sh\s+scripts/', 'Shell script in scripts/ directory'),
    (r'jq\s+', 'JSON processing'),
    (r'grep\s+', 'Text search'),
    (r'cat\s+(?!.*\.env|.*/\.ssh/|.*/secrets?/)', 'File reading (non-sensitive)'),
]

# Allowed domains for WebFetch
ALLOWED_DOMAINS = [
    'ieeexplore.ieee.org',
    'dl.acm.org',
    'link.springer.com',
    'scopus.com',
    'pubmed.ncbi.nlm.nih.gov',
    'beck-online.beck.de',
    'arxiv.org',
    'researchgate.net',
    'doaj.org',
    'dbis.ur.de',
    'dbis.de',
]


def check_blocked_patterns(command: str) -> tuple[bool, str, str]:
    """
    Check if command matches blocked patterns
    Returns: (is_blocked, reason, risk_level)
    """
    for pattern, reason, risk_level in BLOCKED_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return True, reason, risk_level
    return False, '', 'LOW'


def check_allowed_patterns(command: str) -> tuple[bool, str]:
    """
    Check if command matches allowed patterns
    Returns: (is_allowed, reason)
    """
    for pattern, reason in ALLOWED_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return True, reason
    return False, ''


def check_domain_allowed(url: str) -> tuple[bool, str]:
    """
    Check if URL domain is in whitelist
    Returns: (is_allowed, reason)
    """
    for domain in ALLOWED_DOMAINS:
        if domain in url:
            return True, f"Domain {domain} is whitelisted"
    return False, f"Domain not in whitelist: {url}"


def validate_action(
    action: str,
    command: str = None,
    url: str = None,
    user_intent: str = None,
    source: str = 'system'
) -> Dict[str, Any]:
    """
    Validate if an action should be allowed

    Args:
        action: Type of action (bash, webfetch, write, etc.)
        command: Command to execute (for bash)
        url: URL to fetch (for webfetch)
        user_intent: Original user task/intent
        source: Where action originated (system, user, external_content)

    Returns:
        {
            'decision': 'ALLOW' | 'BLOCK',
            'reason': 'Explanation',
            'risk_level': 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
        }
    """

    # Rule 1: BLOCK if source is external_content
    if source == 'external_content':
        return {
            'decision': 'BLOCK',
            'reason': 'Action originated from external content (web/PDF). Only user or system instructions can trigger actions.',
            'risk_level': 'HIGH'
        }

    # Rule 2: Validate bash commands
    if action == 'bash' and command:
        # Check blocked patterns first
        is_blocked, reason, risk_level = check_blocked_patterns(command)
        if is_blocked:
            return {
                'decision': 'BLOCK',
                'reason': f"Blocked pattern detected: {reason}",
                'risk_level': risk_level
            }

        # Check allowed patterns
        is_allowed, reason = check_allowed_patterns(command)
        if is_allowed:
            return {
                'decision': 'ALLOW',
                'reason': f"Whitelisted command: {reason}",
                'risk_level': 'LOW'
            }

        # If not explicitly allowed, be cautious
        return {
            'decision': 'BLOCK',
            'reason': 'Command not in whitelist. Use scripts in scripts/ directory.',
            'risk_level': 'MEDIUM'
        }

    # Rule 3: Validate WebFetch URLs
    if action == 'webfetch' and url:
        is_allowed, reason = check_domain_allowed(url)
        if is_allowed:
            return {
                'decision': 'ALLOW',
                'reason': reason,
                'risk_level': 'LOW'
            }
        else:
            return {
                'decision': 'BLOCK',
                'reason': reason,
                'risk_level': 'HIGH'
            }

    # Rule 4: Write operations - only allow in runs/ directory
    if action == 'write':
        if command and 'runs/' in command:
            return {
                'decision': 'ALLOW',
                'reason': 'Write operation in runs/ directory',
                'risk_level': 'LOW'
            }
        else:
            return {
                'decision': 'BLOCK',
                'reason': 'Write operations only allowed in runs/ directory',
                'risk_level': 'MEDIUM'
            }

    # Default: allow with low risk
    return {
        'decision': 'ALLOW',
        'reason': 'Action validated by default rules',
        'risk_level': 'LOW'
    }


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Action Gate - Security Validator')
    parser.add_argument('command_type', choices=['validate'], help='Command type')
    parser.add_argument('--action', required=True, help='Action type (bash, webfetch, write)')
    parser.add_argument('--command', help='Command to execute')
    parser.add_argument('--url', help='URL to fetch')
    parser.add_argument('--user-intent', help='Original user task')
    parser.add_argument('--source', default='system', choices=['system', 'user', 'external_content'],
                        help='Source of action')

    args = parser.parse_args()

    # Validate
    result = validate_action(
        action=args.action,
        command=args.command,
        url=args.url,
        user_intent=args.user_intent,
        source=args.source
    )

    # Output JSON
    print(json.dumps(result, indent=2))

    # Exit code: 0 for ALLOW, 1 for BLOCK
    sys.exit(0 if result['decision'] == 'ALLOW' else 1)


if __name__ == '__main__':
    main()
