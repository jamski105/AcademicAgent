#!/usr/bin/env python3

"""
Annotated Bibliography Generator - AcademicAgent
Creates Markdown Annotated Bibliography from ranked_candidates.json and quotes.json
"""

import json
import sys
from pathlib import Path
from datetime import datetime

def format_apa7(source):
    """Format source in APA-7 style"""
    authors = source.get('authors', [])
    year = source.get('year', 'n.d.')
    title = source.get('title', 'Untitled')

    if len(authors) == 0:
        author_str = "Unknown"
    elif len(authors) == 1:
        author_str = authors[0]
    elif len(authors) == 2:
        author_str = f"{authors[0]}, & {authors[1]}"
    else:
        author_str = ", ".join(authors[:-1]) + f", & {authors[-1]}"

    return f"{author_str} ({year}). *{title}*."

def main():
    if len(sys.argv) < 5:
        print("Usage: python3 create_bibliography.py <sources.json> <quotes.json> <config.md> <output.md>")
        sys.exit(1)

    sources_file = Path(sys.argv[1])
    quotes_file = Path(sys.argv[2])
    config_file = Path(sys.argv[3])
    output_file = Path(sys.argv[4])

    # Load data
    with open(sources_file, 'r', encoding='utf-8') as f:
        sources_data = json.load(f)

    with open(quotes_file, 'r', encoding='utf-8') as f:
        quotes_data = json.load(f)

    with open(config_file, 'r', encoding='utf-8') as f:
        config_text = f.read()

    # Extract project info from config
    project_title = extract_field(config_text, "Projekt-Titel:")
    research_question = extract_field(config_text, "Forschungsfrage:")

    # Create quote lookup
    quotes_by_source = {}
    for quote in quotes_data.get('quotes', []):
        source_id = quote.get('source_id')
        if source_id not in quotes_by_source:
            quotes_by_source[source_id] = []
        quotes_by_source[source_id].append(quote.get('quote_id'))

    # Generate bibliography
    sources = sources_data.get('ranked_sources', [])[:18]  # Top 18

    with open(output_file, 'w', encoding='utf-8') as f:
        # Header
        f.write(f"# Annotated Bibliography - {project_title}\n\n")
        f.write(f"**Projekt:** {project_title}\n")
        f.write(f"**Forschungsfrage:** {research_question}\n")
        f.write(f"**Datum:** {datetime.now().strftime('%Y-%m-%d')}\n\n")
        f.write("---\n\n")

        # Sources
        for i, source in enumerate(sources, start=1):
            # APA-7 citation
            f.write(f"## {i}. {format_apa7(source)}\n\n")

            # Core statement
            f.write("**Kernaussage:**\n")
            abstract = source.get('abstract', 'N/A')[:300]
            f.write(f"{abstract}...\n\n")

            # Classification
            f.write("**Einordnung:**\n")
            category = source.get('category', 'Primary')
            citations = source.get('citations', 0)
            score = source.get('scores', {}).get('total', 0)
            f.write(f"- Kategorie: {category}\n")
            f.write(f"- Zitationen: {citations}\n")
            f.write(f"- Qualitäts-Score: {score:.1f}/5.0\n")
            f.write(f"- Datenbank: {source.get('database', 'N/A')}\n\n")

            # Usage
            f.write("**Einsatzstelle:**\n")
            f.write("- TBD (wird beim Schreiben festgelegt)\n\n")

            # Quotes
            source_id = source.get('id')
            quote_ids = quotes_by_source.get(source_id, [])
            if quote_ids:
                f.write(f"**Zitate in Quote Library:** {', '.join(quote_ids)}\n\n")
            else:
                f.write("**Zitate in Quote Library:** Keine extrahiert\n\n")

            f.write("---\n\n")

    print(f"✅ Annotated Bibliography created: {output_file}")
    print(f"   Total sources: {len(sources)}")

def extract_field(text, field_name):
    """Extract field value from markdown config"""
    lines = text.split('\n')
    for i, line in enumerate(lines):
        if field_name in line:
            # Next non-empty line
            for j in range(i+1, len(lines)):
                value = lines[j].strip()
                if value and not value.startswith('```'):
                    return value.strip('[]')
    return "N/A"

if __name__ == '__main__':
    main()
