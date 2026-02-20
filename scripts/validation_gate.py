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


# Blocked patterns in text fields (potential injection)
INJECTION_PATTERNS = [
    (r'ignore\s+(?:all\s+)?(?:(?:previous|prior)\s+)?instructions?', 'Ignore instructions'),
    (r'you\s+are\s+now\s+(a|an)\s+\w+', 'Role takeover'),
    (r'(execute|run)\s+(command|bash|shell|script)', 'Command execution'),
    (r'(curl|wget|ssh|scp)\s+', 'Network command'),
    (r'read\s+(\.env|~/.ssh|secret|credential)', 'Secret access'),
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
        errors.append(f"Schema validation failed: {e.message}")
        errors.append(f"  Path: {' -> '.join(str(p) for p in e.path)}")
        errors.append(f"  Failed constraint: {e.validator}")
    except Exception as e:
        errors.append(f"Validation error: {str(e)}")

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

    # Step 1: Load output file
    try:
        with open(output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        errors.append(f"Output file not found: {output_file}")
        return {'valid': False, 'errors': errors, 'warnings': warnings}
    except json.JSONDecodeError as e:
        errors.append(f"Invalid JSON in output file: {e}")
        return {'valid': False, 'errors': errors, 'warnings': warnings}

    # Step 2: Load schema
    try:
        with open(schema_file, 'r', encoding='utf-8') as f:
            schema = json.load(f)
    except FileNotFoundError:
        errors.append(f"Schema file not found: {schema_file}")
        return {'valid': False, 'errors': errors, 'warnings': warnings}
    except json.JSONDecodeError as e:
        errors.append(f"Invalid JSON in schema file: {e}")
        return {'valid': False, 'errors': errors, 'warnings': warnings}

    # Step 3: Validate structure
    structure_errors = validate_json_structure(data, schema)
    if structure_errors:
        errors.extend(structure_errors)
        return {'valid': False, 'errors': errors, 'warnings': warnings}

    # Step 4: Sanitize text fields
    sanitized_data, sanitize_warnings = sanitize_recursive(data)
    warnings.extend(sanitize_warnings)

    # Step 5: Check if sanitization changed anything (potential injection)
    if sanitize_warnings:
        # Log to stderr for orchestrator to see
        print(f"⚠️  SECURITY: Suspicious patterns detected in {agent_name} output", file=sys.stderr)
        for warning in sanitize_warnings[:5]:  # Show first 5
            print(f"   {warning}", file=sys.stderr)

    return {
        'valid': True,
        'errors': [],
        'warnings': warnings,
        'sanitized_data': sanitized_data,
        'injection_patterns_found': len([w for w in warnings if 'Injection pattern' in w])
    }


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Validation Gate - Enforce JSON Schema Validation for Agent Outputs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Validate browser-agent output
    python3 scripts/validation_gate.py \\
      --agent browser-agent \\
      --phase 2 \\
      --output-file runs/session/metadata/candidates.json \\
      --schema schemas/candidates_schema.json

    # With run-id for logging
    python3 scripts/validation_gate.py \\
      --agent scoring-agent \\
      --phase 3 \\
      --output-file runs/session/metadata/ranked_top27.json \\
      --schema schemas/ranked_sources_schema.json \\
      --run-id project_20260219_140000
        """
    )

    parser.add_argument('--agent', required=True, help='Agent name (e.g., browser-agent)')
    parser.add_argument('--phase', type=int, required=True, help='Phase number')
    parser.add_argument('--output-file', required=True, help='Path to agent output JSON file')
    parser.add_argument('--schema', required=True, help='Path to JSON schema file')
    parser.add_argument('--run-id', help='Research run ID (for logging)')
    parser.add_argument('--write-sanitized', action='store_true',
                        help='Write sanitized output back to file')

    args = parser.parse_args()

    # Validate
    result = validate_agent_output(
        agent_name=args.agent,
        phase=args.phase,
        output_file=Path(args.output_file),
        schema_file=Path(args.schema),
        run_id=args.run_id
    )

    # Report
    if result['valid']:
        print(f"✅ Validation PASSED", file=sys.stderr)
        print(f"   Agent: {args.agent}", file=sys.stderr)
        print(f"   Phase: {args.phase}", file=sys.stderr)
        print(f"   Output: {args.output_file}", file=sys.stderr)

        if result['warnings']:
            print(f"   Warnings: {len(result['warnings'])}", file=sys.stderr)
            if result['injection_patterns_found'] > 0:
                print(f"   ⚠️  SECURITY: {result['injection_patterns_found']} injection patterns detected!", file=sys.stderr)

        # Optionally write sanitized output
        if args.write_sanitized and result.get('sanitized_data'):
            with open(args.output_file, 'w', encoding='utf-8') as f:
                json.dump(result['sanitized_data'], f, indent=2, ensure_ascii=False)
            print(f"   ✏️  Sanitized output written back", file=sys.stderr)

        # Output sanitized data to stdout (for orchestrator to use)
        print(json.dumps(result['sanitized_data'], indent=2))

        sys.exit(0)
    else:
        print(f"❌ Validation FAILED", file=sys.stderr)
        print(f"   Agent: {args.agent}", file=sys.stderr)
        print(f"   Phase: {args.phase}", file=sys.stderr)
        print(f"   Output: {args.output_file}", file=sys.stderr)
        print(f"", file=sys.stderr)
        print(f"Errors:", file=sys.stderr)
        for error in result['errors']:
            print(f"  • {error}", file=sys.stderr)

        if result['warnings']:
            print(f"", file=sys.stderr)
            print(f"Warnings:", file=sys.stderr)
            for warning in result['warnings'][:10]:  # Show first 10
                print(f"  • {warning}", file=sys.stderr)

        sys.exit(1)


if __name__ == '__main__':
    main()
