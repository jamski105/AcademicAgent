#!/usr/bin/env python3
"""
Validation Gate - Erzwingt JSON-Schema-Validation für Agent-Outputs

ZWECK:
    Verhindert dass Orchestrator malicious/invalid Agent-Outputs verarbeitet.
    Muss VOR jeder Verwendung von Agent-Outputs aufgerufen werden.

VERWENDUNG:
    python3 scripts/validation_gate.py \
      --agent browser-agent \
      --phase 2 \
      --output-file runs/session/metadata/candidates.json \
      --schema schemas/candidates_schema.json

RETURNS:
    Exit-Code 0: Validation erfolgreich
    Exit-Code 1: Validation fehlgeschlagen (CRITICAL - STOP workflow)

INTEGRATION:
    Orchestrator MUSS nach JEDEM Task()-Call validation_gate.py aufrufen.
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List
import re
import jsonschema
from jsonschema import validate, ValidationError


# Blockierte Muster in Textfeldern (potenzielle Injection)
INJECTION_PATTERNS = [
    (r'ignore\s+(?:all\s+)?(?:(?:previous|prior)\s+)?instructions?', 'Ignore instructions'),
    (r'you\s+are\s+now\s+(a|an)\s+\w+', 'Role takeover'),
    (r'(execute|run)\s+(command|bash|shell|script)', 'Command execution'),
    (r'(curl|wget|ssh|scp)\s+', 'Network command'),
    (r'read\s+(\.env|~/.ssh|secret|credential)', 'Secrets access'),
]


def sanitize_text_field(text: str, field_name: str) -> tuple[str, List[str]]:
    """
    Sanitize a text field and detect injection patterns

    Returns:
        (sanitized_text, warnings)
    """
    warnings = []

    # Check for injection patterns
    for pattern, description in INJECTION_PATTERNS:
        matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
        for match in matches:
            warnings.append(
                f"⚠️  Injection pattern detected in '{field_name}': {description} - '{match.group(0)[:50]}'"
            )

    # Remove HTML tags (should already be done, but defense-in-depth)
    sanitized = re.sub(r'<[^>]+>', '', text)

    # Remove excessive whitespace
    sanitized = re.sub(r'\s+', ' ', sanitized).strip()

    # Truncate extremely long fields
    if len(sanitized) > 10000:
        warnings.append(f"⚠️  Field '{field_name}' truncated from {len(sanitized)} to 10000 chars")
        sanitized = sanitized[:10000] + "..."

    return sanitized, warnings


def validate_json_structure(data: Any, schema: Dict[str, Any]) -> List[str]:
    """
    Validate JSON against schema

    Returns:
        List of validation errors (empty if valid)
    """
    errors = []

    try:
        validate(instance=data, schema=schema)
    except ValidationError as e:
        errors.append(f"Schema-Validierung fehlgeschlagen: {e.message}")
        errors.append(f"  Pfad: {' -> '.join(str(p) for p in e.path)}")
        errors.append(f"  Fehlgeschlagene Einschränkung: {e.validator}")
    except Exception as e:
        errors.append(f"Validierungsfehler: {str(e)}")

    return errors


def sanitize_recursive(data: Any, path: str = "root") -> tuple[Any, List[str]]:
    """
    Recursively sanitize text fields in JSON structure

    Returns:
        (sanitized_data, warnings)
    """
    all_warnings = []

    if isinstance(data, dict):
        sanitized = {}
        for key, value in data.items():
            field_path = f"{path}.{key}"

            # Text fields that need sanitization
            if key in ['title', 'abstract', 'description', 'text', 'content', 'message']:
                if isinstance(value, str):
                    sanitized[key], warnings = sanitize_text_field(value, field_path)
                    all_warnings.extend(warnings)
                else:
                    sanitized[key] = value
            else:
                # Recurse into nested structures
                sanitized[key], warnings = sanitize_recursive(value, field_path)
                all_warnings.extend(warnings)

        return sanitized, all_warnings

    elif isinstance(data, list):
        sanitized = []
        for i, item in enumerate(data):
            item_path = f"{path}[{i}]"
            sanitized_item, warnings = sanitize_recursive(item, item_path)
            sanitized.append(sanitized_item)
            all_warnings.extend(warnings)
        return sanitized, all_warnings

    else:
        # Primitive types (str, int, bool, None)
        return data, []


def validate_agent_output(
    agent_name: str,
    phase: int,
    output_file: Path,
    schema_file: Path,
    run_id: str = None
) -> Dict[str, Any]:
    """
    Validate agent output with schema and sanitization

    Returns:
        {
            'valid': bool,
            'errors': List[str],
            'warnings': List[str],
            'sanitized_data': Any (only if valid)
        }
    """
    errors = []
    warnings = []

    # Schritt 1: Output-Datei laden
    try:
        with open(output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        errors.append(f"Output file not found: {output_file}")
        return {'valid': False, 'errors': errors, 'warnings': warnings}
    except json.JSONDecodeError as e:
        errors.append(f"Ungültiges JSON in Output-Datei: {e}")
        return {'valid': False, 'errors': errors, 'warnings': warnings}

    # Schritt 2: Schema laden
    try:
        with open(schema_file, 'r', encoding='utf-8') as f:
            schema = json.load(f)
    except FileNotFoundError:
        errors.append(f"Schema-Datei nicht gefunden: {schema_file}")
        return {'valid': False, 'errors': errors, 'warnings': warnings}
    except json.JSONDecodeError as e:
        errors.append(f"Ungültiges JSON in Schema-Datei: {e}")
        return {'valid': False, 'errors': errors, 'warnings': warnings}

    # Schritt 3: Struktur validieren
    structure_errors = validate_json_structure(data, schema)
    if structure_errors:
        errors.extend(structure_errors)
        return {'valid': False, 'errors': errors, 'warnings': warnings}

    # Schritt 4: Textfelder bereinigen
    sanitized_data, sanitize_warnings = sanitize_recursive(data)
    warnings.extend(sanitize_warnings)

    # Schritt 5: Prüfe ob Bereinigung etwas geändert hat (potenzielle Injection)
    if sanitize_warnings:
        # Log zu stderr für Orchestrator
        print(f"⚠️  SICHERHEIT: Verdächtige Muster im {agent_name}-Output erkannt", file=sys.stderr)
        for warning in sanitize_warnings[:5]:  # Zeige erste 5
            print(f"   {warning}", file=sys.stderr)

    return {
        'valid': True,
        'errors': [],
        'warnings': warnings,
        'sanitized_data': sanitized_data,
        'injection_patterns_found': len([w for w in warnings if 'Injection pattern' in w])
    }


def main():
    """CLI-Einstiegspunkt"""
    parser = argparse.ArgumentParser(
        description='Validation Gate - Erzwingt JSON-Schema-Validierung für Agent-Outputs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
    # Browser-Agent-Output validieren
    python3 scripts/validation_gate.py \\
      --agent browser-agent \\
      --phase 2 \\
      --output-file runs/session/metadata/candidates.json \\
      --schema schemas/candidates_schema.json

    # Mit run-id für Logging
    python3 scripts/validation_gate.py \\
      --agent scoring-agent \\
      --phase 3 \\
      --output-file runs/session/metadata/ranked_top27.json \\
      --schema schemas/ranked_sources_schema.json \\
      --run-id project_20260219_140000
        """
    )

    parser.add_argument('--agent', required=True, help='Agent-Name (z.B. browser-agent)')
    parser.add_argument('--phase', type=int, required=True, help='Phasennummer')
    parser.add_argument('--output-file', required=True, help='Pfad zur Agent-Output-JSON-Datei')
    parser.add_argument('--schema', required=True, help='Pfad zur JSON-Schema-Datei')
    parser.add_argument('--run-id', help='Research-Run-ID (für Logging)')
    parser.add_argument('--write-sanitized', action='store_true',
                        help='Bereinigten Output zurückschreiben')

    args = parser.parse_args()

    # Validieren
    result = validate_agent_output(
        agent_name=args.agent,
        phase=args.phase,
        output_file=Path(args.output_file),
        schema_file=Path(args.schema),
        run_id=args.run_id
    )

    # Bericht
    if result['valid']:
        print(f"✅ Validierung BESTANDEN", file=sys.stderr)
        print(f"   Agent: {args.agent}", file=sys.stderr)
        print(f"   Phase: {args.phase}", file=sys.stderr)
        print(f"   Output: {args.output_file}", file=sys.stderr)

        if result['warnings']:
            print(f"   Warnungen: {len(result['warnings'])}", file=sys.stderr)
            if result['injection_patterns_found'] > 0:
                print(f"   ⚠️  SICHERHEIT: {result['injection_patterns_found']} Injection-Muster erkannt!", file=sys.stderr)

        # Optional bereinigten Output schreiben
        if args.write_sanitized and result.get('sanitized_data'):
            with open(args.output_file, 'w', encoding='utf-8') as f:
                json.dump(result['sanitized_data'], f, indent=2, ensure_ascii=False)
            print(f"   ✏️  Bereinigter Output zurückgeschrieben", file=sys.stderr)

        # Bereinigten Output zu stdout ausgeben (für Orchestrator)
        print(json.dumps(result['sanitized_data'], indent=2))

        sys.exit(0)
    else:
        print(f"❌ Validierung FEHLGESCHLAGEN", file=sys.stderr)
        print(f"   Agent: {args.agent}", file=sys.stderr)
        print(f"   Phase: {args.phase}", file=sys.stderr)
        print(f"   Output: {args.output_file}", file=sys.stderr)
        print(f"", file=sys.stderr)
        print(f"Fehler:", file=sys.stderr)
        for error in result['errors']:
            print(f"  • {error}", file=sys.stderr)

        if result['warnings']:
            print(f"", file=sys.stderr)
            print(f"Warnungen:", file=sys.stderr)
            for warning in result['warnings'][:10]:  # Zeige erste 10
                print(f"  • {warning}", file=sys.stderr)

        sys.exit(1)


if __name__ == '__main__':
    main()
