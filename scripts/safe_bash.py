#!/usr/bin/env python3
"""
Safe-Bash-Wrapper mit automatischer Action-Gate-Validierung

Zweck:
    - Erzwingt Action-Gate-Validierung VOR Bash-Ausführung
    - Verhindert dass Agents Action-Gate umgehen können
    - Zentralisiert Security-Enforcement

Verwendung:
    # Statt:
    bash scripts/validate_config.py config.md

    # Verwende:
    python3 scripts/safe_bash.py "python3 scripts/validate_config.py config.md"

Agent-Integration:
    In Agent-Prompts: "Verwende `python3 scripts/safe_bash.py <command>` für alle Bash-Operationen"
"""

import sys
import subprocess
import json
import os
from pathlib import Path
from typing import Optional, Dict, Any

# Füge scripts/ zu Path hinzu
sys.path.insert(0, str(Path(__file__).parent))

from action_gate import validate_action


class SafeBashError(Exception):
    """Exception für blockierte Commands"""
    pass


def safe_bash_execute(
    command: str,
    source: str = "system",
    user_intent: Optional[str] = None,
    dry_run: bool = False,
    allow_interactive: bool = False
) -> Dict[str, Any]:
    """
    Führt Bash-Command mit Action-Gate-Validierung aus

    Args:
        command: Bash-Command
        source: Quelle ("system", "user", "external_content")
        user_intent: Optionale User-Intent-Beschreibung
        dry_run: Wenn True, nur validieren ohne auszuführen
        allow_interactive: Erlaube interaktive Commands

    Returns:
        Dict mit Resultat:
        {
            "success": bool,
            "stdout": str,
            "stderr": str,
            "returncode": int,
            "validation": dict
        }

    Raises:
        SafeBashError: Wenn Command blockiert wird
    """

    # Step 1: Validiere mit Action-Gate
    validation_result = validate_action(
        action="bash",
        command=command,
        user_intent=user_intent,
        source=source
    )

    # Step 2: Prüfe ob blockiert
    if validation_result["decision"] == "BLOCK":
        error_msg = (
            f"❌ COMMAND BLOCKIERT\n\n"
            f"Command: {command}\n"
            f"Grund: {validation_result['reason']}\n"
            f"Risiko-Level: {validation_result['risk_level']}\n"
        )

        # Log zu stderr
        print(error_msg, file=sys.stderr)

        # Raise Exception
        raise SafeBashError(error_msg)

    # Step 3: Dry-Run-Modus
    if dry_run:
        return {
            "success": True,
            "stdout": "",
            "stderr": f"[DRY-RUN] Command validiert, würde ausführen: {command}",
            "returncode": 0,
            "validation": validation_result
        }

    # Step 4: Führe Command aus
    try:
        # Bestimme Shell-Modus
        shell = True
        stdin = subprocess.PIPE if not allow_interactive else None

        result = subprocess.run(
            command,
            shell=shell,
            capture_output=True,
            text=True,
            stdin=stdin,
            cwd=os.getcwd()
        )

        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
            "validation": validation_result
        }

    except Exception as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": f"Execution error: {str(e)}",
            "returncode": -1,
            "validation": validation_result
        }


def main():
    """CLI-Entry-Point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Safe-Bash-Wrapper mit Action-Gate-Validierung",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
    # Einfache Ausführung
    python3 scripts/safe_bash.py "python3 scripts/validate_config.py config.md"

    # Mit Source-Angabe
    python3 scripts/safe_bash.py "jq '.title' data.json" --source user

    # Dry-Run (nur Validierung)
    python3 scripts/safe_bash.py "curl https://example.com" --dry-run

    # JSON-Output
    python3 scripts/safe_bash.py "ls -la" --json
        """
    )

    parser.add_argument(
        "command",
        help="Bash-Command zum Ausführen"
    )

    parser.add_argument(
        "--source",
        choices=["system", "user", "external_content"],
        default="system",
        help="Quelle des Commands (default: system)"
    )

    parser.add_argument(
        "--intent",
        help="User-Intent-Beschreibung"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Nur validieren, nicht ausführen"
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Output als JSON"
    )

    parser.add_argument(
        "--allow-interactive",
        action="store_true",
        help="Erlaube interaktive Commands"
    )

    args = parser.parse_args()

    try:
        # Führe Safe-Bash aus
        result = safe_bash_execute(
            command=args.command,
            source=args.source,
            user_intent=args.intent,
            dry_run=args.dry_run,
            allow_interactive=args.allow_interactive
        )

        # Output
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            # Standard-Output
            if result["stdout"]:
                print(result["stdout"], end="")
            if result["stderr"]:
                print(result["stderr"], file=sys.stderr, end="")

        # Exit-Code
        sys.exit(result["returncode"])

    except SafeBashError as e:
        if args.json:
            print(json.dumps({
                "success": False,
                "error": str(e),
                "blocked": True
            }), file=sys.stderr)
        else:
            print(str(e), file=sys.stderr)
        sys.exit(1)

    except Exception as e:
        if args.json:
            print(json.dumps({
                "success": False,
                "error": str(e),
                "blocked": False
            }), file=sys.stderr)
        else:
            print(f"❌ Fehler: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
