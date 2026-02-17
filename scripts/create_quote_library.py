#!/usr/bin/env python3

"""
Quote Library Generator - AcademicAgent
Creates CSV Quote Library from quotes.json and ranked_top27.json
"""

import json
import csv
import sys
from pathlib import Path

def format_apa7(source):
    """Format source in APA-7 style"""
    authors = source.get('authors', [])
    year = source.get('year', 'n.d.')
    title = source.get('title', 'Untitled')

    # Format authors (up to 20)
    if len(authors) == 0:
        author_str = "Unknown"
    elif len(authors) == 1:
        author_str = authors[0]
    elif len(authors) == 2:
        author_str = f"{authors[0]}, & {authors[1]}"
    else:
        author_str = f"{authors[0]}, et al."

    # APA-7 format
    return f"{author_str} ({year}). {title}."

def main():
    if len(sys.argv) < 4:
        print("Usage: python3 create_quote_library.py <quotes.json> <sources.json> <output.csv>")
        sys.exit(1)

    quotes_file = Path(sys.argv[1])
    sources_file = Path(sys.argv[2])
    output_file = Path(sys.argv[3])

    # Load data
    with open(quotes_file, 'r', encoding='utf-8') as f:
        quotes_data = json.load(f)

    with open(sources_file, 'r', encoding='utf-8') as f:
        sources_data = json.load(f)

    # Create source lookup
    sources = {s['id']: s for s in sources_data.get('ranked_sources', [])}

    # Prepare CSV
    quotes = quotes_data.get('quotes', [])

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)

        # Header
        writer.writerow([
            'ID',
            'APA-7 Zitat',
            'Dokumenttyp',
            'Datenbank',
            'DOI',
            'Zitat',
            'Seite',
            'Kontext',
            'Relevanz',
            'Status',
            'Dateiname'
        ])

        # Rows
        for quote in quotes:
            source_id = quote.get('source_id')
            source = sources.get(source_id, {})

            writer.writerow([
                quote.get('quote_id', ''),
                format_apa7(source),
                source.get('category', 'Primary'),
                source.get('database', 'N/A'),
                source.get('doi', ''),
                quote.get('quote', ''),
                quote.get('page', ''),
                quote.get('context', ''),
                quote.get('relevance', ''),
                'Extracted',
                quote.get('filename', '')
            ])

    print(f"✅ Quote Library created: {output_file}")
    print(f"   Total quotes: {len(quotes)}")

if __name__ == '__main__':
    main()
