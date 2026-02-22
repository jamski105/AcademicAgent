#!/usr/bin/env python3
"""
State Validation Script
Validates research_state.json against JSON Schema
Prevents corruption and data loss during resume
"""

import json
import sys
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional

# JSON Schema for research_state.json
STATE_SCHEMA = {
    "type": "object",
    "required": ["run_id", "timestamp", "current_phase", "phases"],
    "properties": {
        "run_id": {"type": "string"},
        "timestamp": {"type": "string"},
        "current_phase": {"type": "integer", "minimum": 0, "maximum": 6},
        "phases": {
            "type": "object",
            "patternProperties": {
                "^[0-6]$": {
                    "type": "object",
                    "required": ["status"],
                    "properties": {
                        "status": {"type": "string", "enum": ["pending", "in_progress", "completed", "failed"]},
                        "started_at": {"type": "string"},
                        "completed_at": {"type": "string"},
                        "error": {"type": "string"},
                        "progress": {"type": "object"}
                    }
                }
            }
        },
        "checksum": {"type": "string"}
    }
}


def calculate_checksum(data: Dict[str, Any]) -> str:
    """Calculate SHA256 checksum of state data (excluding checksum field)."""
    data_copy = data.copy()
    data_copy.pop('checksum', None)
    json_str = json.dumps(data_copy, sort_keys=True)
    return hashlib.sha256(json_str.encode()).hexdigest()


def validate_schema(data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """Validate data against schema."""
    # Check required fields
    for field in STATE_SCHEMA["required"]:
        if field not in data:
            return False, f"Fehlendes Pflichtfeld: {field}"

    # Validate current_phase
    phase = data.get("current_phase")
    if not isinstance(phase, int) or phase < 0 or phase > 6:
        return False, f"Ungültige current_phase: {phase} (muss 0-6 sein)"

    # Validate phases
    phases = data.get("phases", {})
    if not isinstance(phases, dict):
        return False, "Feld 'phases' muss ein Objekt sein"

    for phase_num, phase_data in phases.items():
        if not phase_num.isdigit() or int(phase_num) < 0 or int(phase_num) > 6:
            return False, f"Ungültige Phasennummer: {phase_num}"

        if not isinstance(phase_data, dict):
            return False, f"Phase {phase_num} Daten müssen ein Objekt sein"

        if "status" not in phase_data:
            return False, f"Phase {phase_num} fehlt 'status'-Feld"

        status = phase_data["status"]
        if status not in ["pending", "in_progress", "completed", "failed"]:
            return False, f"Phase {phase_num} hat ungültigen Status: {status}"

    return True, None


def validate_checksum(data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """Validate checksum."""
    if "checksum" not in data:
        return False, "Fehlendes Checksum-Feld"

    stored_checksum = data["checksum"]
    calculated_checksum = calculate_checksum(data)

    if stored_checksum != calculated_checksum:
        return False, f"Checksum stimmt nicht überein! Datei könnte beschädigt sein."

    return True, None


def validate_state_file(state_file: Path) -> tuple[bool, Optional[str], Optional[Dict]]:
    """
    Validate state file.

    Returns:
        (is_valid, error_message, data)
    """
    # Check file exists
    if not state_file.exists():
        return False, f"State-Datei nicht gefunden: {state_file}", None

    # Prüfe ob Datei lesbar ist
    if not state_file.is_file():
        return False, f"Keine Datei: {state_file}", None

    # Parse JSON
    try:
        with open(state_file, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return False, f"Ungültiges JSON: {e}", None
    except Exception as e:
        return False, f"Fehler beim Lesen der Datei: {e}", None

    # Validiere Schema
    is_valid, error = validate_schema(data)
    if not is_valid:
        return False, f"Schema-Validierung fehlgeschlagen: {error}", data

    # Validiere Checksum
    is_valid, error = validate_checksum(data)
    if not is_valid:
        return False, f"Checksum-Validierung fehlgeschlagen: {error}", data

    return True, None, data


def add_checksum(state_file: Path) -> bool:
    """Add or update checksum in state file."""
    try:
        with open(state_file, 'r') as f:
            data = json.load(f)

        # Calculate and add checksum
        data['checksum'] = calculate_checksum(data)

        # Write back
        with open(state_file, 'w') as f:
            json.dump(data, f, indent=2)

        return True
    except Exception as e:
        print(f"❌ Fehler beim Hinzufügen der Checksum: {e}", file=sys.stderr)
        return False


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Verwendung: validate_state.py <state_file> [--add-checksum]", file=sys.stderr)
        sys.exit(1)

    state_file = Path(sys.argv[1])
    add_checksum_flag = "--add-checksum" in sys.argv

    if add_checksum_flag:
        # Add checksum mode
        if add_checksum(state_file):
            print(f"✅ Checksum zu {state_file} hinzugefügt")
            sys.exit(0)
        else:
            sys.exit(1)

    # Validation mode
    is_valid, error, data = validate_state_file(state_file)

    if is_valid:
        print(f"✅ State-Datei ist gültig: {state_file}")
        print(f"   Run-ID: {data['run_id']}")
        print(f"   Aktuelle Phase: {data['current_phase']}")

        # Zeige Phasen-Status
        phases = data.get('phases', {})
        completed = sum(1 for p in phases.values() if p.get('status') == 'completed')
        print(f"   Abgeschlossene Phasen: {completed}/7")

        sys.exit(0)
    else:
        print(f"❌ State-Datei-Validierung fehlgeschlagen: {state_file}", file=sys.stderr)
        print(f"   Fehler: {error}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
