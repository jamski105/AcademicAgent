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


# Blockierte Befehlsmuster
BLOCKED_PATTERNS = [
    (r'(curl|wget|fetch)\s+.*https?://', 'Netzwerkanfrage an externe URL', 'HIGH'),
    (r'(ssh|scp|rsync)\s+', 'Versuch einer Remote-Verbindung', 'HIGH'),
    (r'(cat|grep|head|tail)\s+.*\.env', 'Zugriff auf Secrets-Datei (.env)', 'CRITICAL'),
    (r'(cat|grep|head|tail)\s+.*/\.ssh/', 'Zugriff auf Secrets-Datei (SSH-Keys)', 'CRITICAL'),
    (r'(cat|grep|head|tail)\s+.*/secrets?/', 'Zugriff auf Secrets-Verzeichnis', 'CRITICAL'),
    (r'rm\s+-rf?\s+/', 'Destruktive Dateisystemoperation', 'CRITICAL'),
    (r'dd\s+if=.*of=', 'Raw-Disk-Operation', 'CRITICAL'),
    (r'mkfs\s+', 'Dateisystem-Erstellung (destruktiv)', 'CRITICAL'),
    (r'sudo\s+', 'Versuch der Rechteausweitung', 'CRITICAL'),
    (r'chmod\s+\+x.*evil|malware|backdoor', 'Verdächtige Executable-Erstellung', 'HIGH'),
]

# Erlaubte Befehlsmuster (Whitelist)
ALLOWED_PATTERNS = [
    (r'python3\s+scripts/', 'Python-Script im scripts/-Verzeichnis'),
    (r'node\s+scripts/', 'Node-Script im scripts/-Verzeichnis'),
    (r'bash\s+scripts/', 'Bash-Script im scripts/-Verzeichnis'),
    (r'sh\s+scripts/', 'Shell-Script im scripts/-Verzeichnis'),
    (r'jq\s+', 'JSON-Verarbeitung'),
    (r'grep\s+', 'Textsuche'),
    (r'cat\s+(?!.*\.env|.*/\.ssh/|.*/secrets?/)', 'Datei-Lesen (nicht-sensibel)'),
    (r'pdftotext\s+', 'PDF-Textextraktion'),
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
            return True, f"Domain {domain} ist in Whitelist"
    return False, f"Domain nicht in Whitelist: {url}"


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

    # Regel 1: BLOCK wenn source external_content ist
    if source == 'external_content':
        return {
            'decision': 'BLOCK',
            'reason': 'Aktion stammt aus externem Inhalt (Web/PDF). Nur Benutzer- oder System-Anweisungen können Aktionen auslösen.',
            'risk_level': 'HIGH'
        }

    # Regel 2: Validiere Bash-Befehle
    if action == 'bash' and command:
        # Prüfe blockierte Muster zuerst
        is_blocked, reason, risk_level = check_blocked_patterns(command)
        if is_blocked:
            return {
                'decision': 'BLOCK',
                'reason': f"Blockiertes Muster erkannt: {reason}",
                'risk_level': risk_level
            }

        # Prüfe erlaubte Muster
        is_allowed, reason = check_allowed_patterns(command)
        if is_allowed:
            return {
                'decision': 'ALLOW',
                'reason': f"Befehl in Whitelist: {reason}",
                'risk_level': 'LOW'
            }

        # Wenn nicht explizit erlaubt, sei vorsichtig
        return {
            'decision': 'BLOCK',
            'reason': 'Befehl nicht in Whitelist. Verwende Scripts im scripts/-Verzeichnis.',
            'risk_level': 'MEDIUM'
        }

    # Regel 3: Validiere WebFetch-URLs
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

    # Regel 4: Schreiboperationen - nur im runs/-Verzeichnis erlaubt
    if action == 'write':
        if command and 'runs/' in command:
            return {
                'decision': 'ALLOW',
                'reason': 'Schreiboperation im runs/-Verzeichnis',
                'risk_level': 'LOW'
            }
        else:
            return {
                'decision': 'BLOCK',
                'reason': 'Schreiboperationen nur im runs/-Verzeichnis erlaubt',
                'risk_level': 'MEDIUM'
            }

    # Standard: Erlauben mit niedrigem Risiko
    return {
        'decision': 'ALLOW',
        'reason': 'Aktion durch Standard-Regeln validiert',
        'risk_level': 'LOW'
    }


def main():
    """Haupteinstiegspunkt"""
    parser = argparse.ArgumentParser(description='Action Gate - Sicherheits-Validator')
    parser.add_argument('command_type', choices=['validate'], help='Befehlstyp')
    parser.add_argument('--action', required=True, help='Aktionstyp (bash, webfetch, write)')
    parser.add_argument('--command', help='Auszuführender Befehl')
    parser.add_argument('--url', help='Abzurufende URL')
    parser.add_argument('--user-intent', help='Ursprüngliche Benutzeraufgabe')
    parser.add_argument('--source', default='system', choices=['system', 'user', 'external_content'],
                        help='Quelle der Aktion')

    args = parser.parse_args()

    # Validieren
    result = validate_action(
        action=args.action,
        command=args.command,
        url=args.url,
        user_intent=args.user_intent,
        source=args.source
    )

    # JSON ausgeben
    print(json.dumps(result, indent=2))

    # Exit-Code: 0 für ALLOW, 1 für BLOCK
    sys.exit(0 if result['decision'] == 'ALLOW' else 1)


if __name__ == '__main__':
    main()
