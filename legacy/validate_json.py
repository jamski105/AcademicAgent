#!/usr/bin/env python3
"""
JSON Schema Validator with Text Sanitization

Validates JSON files against schemas and sanitizes text fields to prevent
prompt injection attacks.

Usage:
    python3 validate_json.py --file data.json --schema schema.json [--sanitize-text-fields]
"""

import argparse
import json
import sys
from pathlib import Path

try:
    import jsonschema
except ImportError:
    print("ERROR: jsonschema not installed. Install with: pip install jsonschema", file=sys.stderr)
    sys.exit(1)

# Import sanitization if available
try:
    from sanitize_html import sanitize_html, remove_injection_patterns
    SANITIZE_AVAILABLE = True
except ImportError:
    SANITIZE_AVAILABLE = False
    print("WARNING: sanitize_html not available, text sanitization disabled", file=sys.stderr)


def validate_json_schema(data, schema):
    """Validate JSON data against schema."""
    try:
        jsonschema.validate(instance=data, schema=schema)
        return True, None
    except jsonschema.exceptions.ValidationError as e:
        return False, str(e)


def sanitize_text_fields(data, schema, path=""):
    """
    Recursively sanitize text fields in JSON data.

    Args:
        data: JSON data (dict, list, or primitive)
        schema: JSON schema for this data
        path: Current path in data structure (for logging)

    Returns:
        Sanitized data (modified in-place)
    """
    if not SANITIZE_AVAILABLE:
        return data

    if isinstance(data, dict):
        for key, value in data.items():
            current_path = f"{path}.{key}" if path else key

            # Check if this field is a string type in schema
            if isinstance(value, str):
                # Apply HTML sanitization to prevent injection
                original = value
                sanitized = sanitize_html(value, source="external")

                # Additional prompt injection pattern removal
                sanitized = remove_injection_patterns(sanitized)

                if sanitized != original:
                    print(f"  Sanitized field: {current_path}", file=sys.stderr)
                    data[key] = sanitized

            # Recurse into nested structures
            elif isinstance(value, (dict, list)):
                sanitize_text_fields(value, schema, current_path)

    elif isinstance(data, list):
        for i, item in enumerate(data):
            current_path = f"{path}[{i}]"
            if isinstance(item, (dict, list)):
                sanitize_text_fields(item, schema, current_path)

    return data


def main():
    parser = argparse.ArgumentParser(description="Validate JSON against schema with optional sanitization")
    parser.add_argument("--file", required=True, help="JSON file to validate")
    parser.add_argument("--schema", required=True, help="JSON schema file")
    parser.add_argument("--sanitize-text-fields", action="store_true",
                       help="Sanitize text fields to prevent injection attacks")
    parser.add_argument("--write-sanitized", action="store_true",
                       help="Write sanitized data back to file")

    args = parser.parse_args()

    # Load data
    try:
        with open(args.file, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"ERROR: File not found: {args.file}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in {args.file}: {e}", file=sys.stderr)
        sys.exit(1)

    # Load schema
    try:
        with open(args.schema, 'r') as f:
            schema = json.load(f)
    except FileNotFoundError:
        print(f"ERROR: Schema not found: {args.schema}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in schema: {e}", file=sys.stderr)
        sys.exit(1)

    # Validate schema
    print(f"Validating {args.file} against {args.schema}...", file=sys.stderr)
    valid, error = validate_json_schema(data, schema)

    if not valid:
        print(f"❌ VALIDATION FAILED:", file=sys.stderr)
        print(f"   {error}", file=sys.stderr)
        sys.exit(1)

    print("✅ Schema validation passed", file=sys.stderr)

    # Sanitize if requested
    if args.sanitize_text_fields:
        print("Sanitizing text fields...", file=sys.stderr)
        data = sanitize_text_fields(data, schema)

        # Re-validate after sanitization
        valid, error = validate_json_schema(data, schema)
        if not valid:
            print(f"❌ VALIDATION FAILED after sanitization:", file=sys.stderr)
            print(f"   {error}", file=sys.stderr)
            print("   This may indicate aggressive sanitization broke data structure", file=sys.stderr)
            sys.exit(1)

        print("✅ Sanitization completed", file=sys.stderr)

        # Write sanitized data back if requested
        if args.write_sanitized:
            with open(args.file, 'w') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"✅ Sanitized data written to {args.file}", file=sys.stderr)

    print("✅ Validation successful", file=sys.stderr)
    sys.exit(0)


if __name__ == "__main__":
    main()
