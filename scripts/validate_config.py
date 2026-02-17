#!/usr/bin/env python3

"""
Config Validator - AcademicAgent
Validates Config_*.md files before running the agent
"""

import sys
import re
from pathlib import Path

def validate_config(config_file):
    """Validate config file and return errors/warnings"""
    errors = []
    warnings = []

    with open(config_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Required fields
    required_fields = {
        'Projekt-Titel:': 'Project title',
        'Forschungsfrage:': 'Research question',
        'Cluster 1': 'Cluster 1 (Core concept)',
        'Cluster 2': 'Cluster 2 (Domain/Context)',
        'Cluster 3': 'Cluster 3 (Mechanisms)',
        'Primary Databases': 'Primary Databases',
        'Target Total:': 'Target Total (source count)',
        'Min Year': 'Min Year',
        'Citation Threshold': 'Citation Threshold',
        'Min Score': 'Min Score',
    }

    for field, description in required_fields.items():
        if field not in content:
            errors.append(f"Missing required field: {description} ({field})")

    # Extract values
    projekt_titel = extract_field(content, 'Projekt-Titel:')
    forschungsfrage = extract_field(content, 'Forschungsfrage:')
    min_year = extract_field(content, 'Min Year')
    citation_threshold = extract_field(content, 'Citation Threshold')
    target_total = extract_field(content, 'Target Total:')

    # Validate Project Title
    if not projekt_titel or projekt_titel == 'N/A':
        errors.append("Project title is empty")
    elif len(projekt_titel) < 10:
        warnings.append("Project title is very short (< 10 chars)")

    # Validate Research Question
    if not forschungsfrage or forschungsfrage == 'N/A':
        errors.append("Research question is empty")
    elif '?' not in forschungsfrage:
        warnings.append("Research question doesn't end with '?'")

    # Validate Min Year
    if min_year:
        try:
            year = int(min_year)
            if year < 2000:
                warnings.append(f"Min Year is very old ({year})")
            elif year > 2026:
                errors.append(f"Min Year is in the future ({year})")
        except ValueError:
            errors.append(f"Min Year is not a number: {min_year}")

    # Validate Citation Threshold
    if citation_threshold:
        try:
            threshold = int(citation_threshold)
            if threshold < 0:
                errors.append(f"Citation Threshold is negative: {threshold}")
        except ValueError:
            errors.append(f"Citation Threshold is not a number: {citation_threshold}")

    # Validate Target Total
    if target_total:
        try:
            total = int(target_total.split()[0])
            if total < 5:
                warnings.append(f"Target Total is very low ({total} sources)")
            elif total > 50:
                warnings.append(f"Target Total is very high ({total} sources)")
        except (ValueError, IndexError):
            errors.append(f"Target Total is not a number: {target_total}")

    # Validate Clusters
    cluster_count = content.count('Cluster ')
    if cluster_count < 3:
        errors.append(f"Not enough clusters defined (found {cluster_count}, need 3)")

    # Validate Databases
    db_count = content.count('\n1. ') + content.count('\n2. ') + content.count('\n3. ')
    if db_count < 3:
        warnings.append(f"Only {db_count} databases defined (recommend 3-5)")

    return errors, warnings

def extract_field(content, field_name):
    """Extract field value from markdown config"""
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if field_name in line:
            # Next non-empty line
            for j in range(i+1, min(i+5, len(lines))):
                value = lines[j].strip()
                if value and not value.startswith('```') and not value.startswith('#'):
                    return value.strip('[]`')
    return None

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 validate_config.py <config.md>")
        sys.exit(1)

    config_file = Path(sys.argv[1])

    if not config_file.exists():
        print(f"❌ Error: Config file not found: {config_file}")
        sys.exit(1)

    print(f"🔍 Validating: {config_file.name}")
    print("")

    errors, warnings = validate_config(config_file)

    # Print results
    if errors:
        print("❌ ERRORS:")
        for error in errors:
            print(f"   - {error}")
        print("")

    if warnings:
        print("⚠️  WARNINGS:")
        for warning in warnings:
            print(f"   - {warning}")
        print("")

    if not errors and not warnings:
        print("✅ Config is valid!")
        sys.exit(0)
    elif errors:
        print(f"❌ Validation failed: {len(errors)} error(s), {len(warnings)} warning(s)")
        sys.exit(1)
    else:
        print(f"✅ Config is valid (with {len(warnings)} warning(s))")
        sys.exit(0)

if __name__ == '__main__':
    main()
