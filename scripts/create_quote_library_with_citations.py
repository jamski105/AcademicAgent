#!/usr/bin/env python3
"""
Enhanced Quote Library Generator with Configurable Citation Style
Adds full formatted citations to Quote_Library.csv based on run_config.json
"""

import csv
import json
import sys
from pathlib import Path

def format_apa7_reference(source):
    """Generate APA 7 reference."""
    authors = source.get("authors", [])
    if not authors:
        author_str = "Unknown"
    elif len(authors) == 1:
        author_str = authors[0]
    elif len(authors) == 2:
        author_str = f"{authors[0]}, & {authors[1]}"
    else:
        author_str = ", ".join(authors[:-1]) + f", & {authors[-1]}"

    year = source.get("year", "n.d.")
    title = source.get("title", "Untitled")
    journal = source.get("journal", "")
    volume = source.get("volume", "")
    issue = source.get("issue", "")
    pages = source.get("pages", "")
    publisher = source.get("publisher", "")
    doi = source.get("doi", "")

    parts = [f"{author_str} ({year}). {title}."]

    if journal:
        journal_part = f"{journal}"
        if volume:
            journal_part += f", {volume}"
            if issue:
                journal_part += f"({issue})"
        if pages:
            journal_part += f", {pages}"
        parts.append(journal_part + ".")
    elif publisher:
        parts.append(f"{publisher}.")

    if doi:
        parts.append(f"https://doi.org/{doi}")

    return " ".join(parts)

def format_mla_reference(source):
    """Generate MLA 9 reference."""
    authors = source.get("authors", [])
    if not authors:
        author_str = "Unknown"
    else:
        # First author: Last, First. Others: First Last.
        author_str = authors[0]
        if len(authors) > 1:
            author_str += ", et al."

    title = source.get("title", "Untitled")
    journal = source.get("journal", "")
    volume = source.get("volume", "")
    issue = source.get("issue", "")
    year = source.get("year", "n.d.")
    pages = source.get("pages", "")
    doi = source.get("doi", "")

    parts = [f'{author_str}. "{title}."']

    if journal:
        parts.append(f"{journal},")
        if volume:
            parts.append(f"vol. {volume},")
        if issue:
            parts.append(f"no. {issue},")
        parts.append(f"{year},")
        if pages:
            parts.append(f"pp. {pages}.")
    else:
        parts.append(f"{year}.")

    if doi:
        parts.append(f"doi:{doi}.")

    return " ".join(parts)

def format_chicago_reference(source):
    """Generate Chicago 17 reference."""
    authors = source.get("authors", [])
    if not authors:
        author_str = "Unknown"
    elif len(authors) == 1:
        author_str = authors[0]
    elif len(authors) == 2:
        author_str = f"{authors[0]} and {authors[1]}"
    else:
        author_str = f"{authors[0]} et al."

    year = source.get("year", "n.d.")
    title = source.get("title", "Untitled")
    journal = source.get("journal", "")
    volume = source.get("volume", "")
    issue = source.get("issue", "")
    pages = source.get("pages", "")
    doi = source.get("doi", "")

    parts = [f'{author_str}. {year}. "{title}."']

    if journal:
        journal_part = f"{journal} {volume}"
        if issue:
            journal_part += f", no. {issue}"
        if pages:
            journal_part += f": {pages}"
        parts.append(journal_part + ".")

    if doi:
        parts.append(f"https://doi.org/{doi}.")

    return " ".join(parts)

def format_ieee_reference(source):
    """Generate IEEE reference."""
    authors = source.get("authors", [])
    if not authors:
        author_str = "Unknown"
    else:
        # IEEE uses initials: J. Smith
        author_str = ", ".join(authors)

    title = source.get("title", "Untitled")
    journal = source.get("journal", "")
    volume = source.get("volume", "")
    issue = source.get("issue", "")
    year = source.get("year", "n.d.")
    pages = source.get("pages", "")
    doi = source.get("doi", "")

    parts = [f'{author_str}, "{title},"']

    if journal:
        journal_part = f"{journal}"
        if volume:
            journal_part += f", vol. {volume}"
        if issue:
            journal_part += f", no. {issue}"
        if pages:
            journal_part += f", pp. {pages}"
        journal_part += f", {year}."
        parts.append(journal_part)

    if doi:
        parts.append(f"doi: {doi}.")

    return " ".join(parts)

def format_harvard_reference(source):
    """Generate Harvard reference."""
    authors = source.get("authors", [])
    if not authors:
        author_str = "Unknown"
    elif len(authors) == 1:
        author_str = authors[0]
    else:
        author_str = f"{authors[0]} et al."

    year = source.get("year", "n.d.")
    title = source.get("title", "Untitled")
    journal = source.get("journal", "")
    volume = source.get("volume", "")
    issue = source.get("issue", "")
    pages = source.get("pages", "")
    doi = source.get("doi", "")

    parts = [f"{author_str}, {year}. {title}."]

    if journal:
        journal_part = f"{journal}, {volume}"
        if issue:
            journal_part += f"({issue})"
        if pages:
            journal_part += f", pp.{pages}"
        parts.append(journal_part + ".")

    if doi:
        parts.append(f"DOI: {doi}.")

    return " ".join(parts)

def format_citation(source, citation_style):
    """
    Format citation based on specified style.

    Args:
        source: Dict with source metadata
        citation_style: str like "APA 7", "MLA", "Chicago", "IEEE", "Harvard"

    Returns:
        str: Formatted citation
    """
    style_lower = citation_style.lower().replace(" ", "")

    if "apa" in style_lower:
        return format_apa7_reference(source)
    elif "mla" in style_lower:
        return format_mla_reference(source)
    elif "chicago" in style_lower:
        return format_chicago_reference(source)
    elif "ieee" in style_lower:
        return format_ieee_reference(source)
    elif "harvard" in style_lower:
        return format_harvard_reference(source)
    else:
        # Default to APA 7
        return format_apa7_reference(source)

def create_quote_library(quotes_file, sources_file, config_file, output_csv):
    """
    Create Quote Library CSV with formatted citations.

    Args:
        quotes_file: Path to quotes.json
        sources_file: Path to ranked_candidates.json
        config_file: Path to run_config.json
        output_csv: Path to output Quote_Library.csv
    """
    # Load quotes
    with open(quotes_file) as f:
        quotes_data = json.load(f)
    quotes = quotes_data.get("quotes", [])

    # Load sources
    with open(sources_file) as f:
        sources_data = json.load(f)
    sources = sources_data.get("ranked_sources", sources_data.get("sources", []))

    # Load config to get citation style
    with open(config_file) as f:
        config = json.load(f)
    citation_style = config.get("output_preferences", {}).get("citation_style", "APA 7")

    print(f"Verwende Zitationsstil: {citation_style}")

    # Create lookup dict
    source_lookup = {s.get("id", s.get("source_id")): s for s in sources}

    # Write CSV
    fieldnames = [
        "Quote_ID",
        "Source_ID",
        "Authors",
        "Year",
        "Title",
        "Page",
        "Quote",
        "Context",
        "Relevance",
        "Keywords_Matched",
        "Full_Citation"  # Generic name
    ]

    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for quote in quotes:
            source_id = quote.get("source_id")
            source = source_lookup.get(source_id, {})

            # Generate citation in specified style
            full_citation = format_citation(source, citation_style) if source else "Quelle nicht gefunden"

            row = {
                "Quote_ID": quote.get("quote_id", ""),
                "Source_ID": source_id,
                "Authors": "; ".join(quote.get("authors", [])),
                "Year": quote.get("year", ""),
                "Title": quote.get("source_title", ""),
                "Page": quote.get("page", ""),
                "Quote": quote.get("quote", ""),
                "Context": quote.get("context", ""),
                "Relevance": quote.get("relevance", ""),
                "Keywords_Matched": "; ".join(quote.get("keywords_matched", [])),
                "Full_Citation": full_citation
            }

            writer.writerow(row)

    print(f"✅ Quote Library erstellt: {output_csv}")
    print(f"   {len(quotes)} Zitate mit {citation_style}-Zitationen")

def main():
    if len(sys.argv) < 5:
        print("Verwendung: python3 create_quote_library_with_citations.py <quotes.json> <sources.json> <config.json> <output.csv>")
        print("Beispiel: python3 create_quote_library_with_citations.py \\")
        print("    runs/2026-02-21_06-29-36/metadata/quotes.json \\")
        print("    runs/2026-02-21_06-29-36/metadata/ranked_candidates.json \\")
        print("    runs/2026-02-21_06-29-36/run_config.json \\")
        print("    runs/2026-02-21_06-29-36/Quote_Library.csv")
        sys.exit(1)

    quotes_file = sys.argv[1]
    sources_file = sys.argv[2]
    config_file = sys.argv[3]
    output_csv = sys.argv[4]

    # Validate inputs
    for file_path, name in [(quotes_file, "Quotes"), (sources_file, "Sources"), (config_file, "Config")]:
        if not Path(file_path).exists():
            print(f"❌ {name}-Datei nicht gefunden: {file_path}")
            sys.exit(1)

    create_quote_library(quotes_file, sources_file, config_file, output_csv)

if __name__ == "__main__":
    main()
