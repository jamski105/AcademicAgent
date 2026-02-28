"""
CSV Exporter für Academic Agent v2.3+

Exportiert Quotes als CSV mit formatierten Zitationen und Source-Annotation.

CSV Spalten:
- Zitat
- Seitenzahl
- Werk
- Formatiertes_Zitat
- DOI
- Jahr
- Autoren
- Quelle (v2.2 - API/DBIS source)

Usage:
    from src.export.csv_exporter import export_quotes_csv

    export_quotes_csv(quotes, papers, style="apa7", output_path=Path("quotes.csv"))
"""

import csv
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

from src.export.citation_formatter import format_citation, Paper


def export_quotes_csv(
    quotes: List[Dict[str, Any]],
    papers: List[Dict[str, Any]],
    citation_style: str,
    output_path: Path
) -> None:
    """
    Export quotes to CSV with formatted citations

    Args:
        quotes: List of quote dicts with keys: text, page, paper_doi, etc.
        papers: List of paper dicts with metadata
        citation_style: Citation style (apa7, ieee, harvard, mla, chicago)
        output_path: Output CSV file path

    Example:
        quotes = [{"text": "Quote...", "page": 5, "paper_doi": "10.1109/..."}]
        papers = [{"doi": "10.1109/...", "title": "...", "authors": [...]}]
        export_quotes_csv(quotes, papers, "apa7", Path("quotes.csv"))
    """
    # Create paper lookup by DOI
    paper_lookup = {p.get("doi", ""): p for p in papers}

    # Prepare rows
    rows = []
    for quote in quotes:
        # Get paper metadata
        doi = quote.get("paper_doi") or quote.get("doi", "")
        paper_data = paper_lookup.get(doi, {})

        if not paper_data:
            # Skip quotes without matching paper
            continue

        # Create Paper object for citation
        paper = Paper(
            doi=paper_data.get("doi", ""),
            title=paper_data.get("title", ""),
            authors=paper_data.get("authors", []),
            year=paper_data.get("year", 0),
            venue=paper_data.get("venue"),
            volume=paper_data.get("volume"),
            issue=paper_data.get("issue"),
            pages=paper_data.get("pages"),
            url=paper_data.get("url")
        )

        # Format citation
        formatted_citation = format_citation(paper, citation_style)

        # Create row
        row = {
            "Zitat": quote.get("text") or quote.get("quote", ""),
            "Seitenzahl": quote.get("page") or quote.get("page_number", ""),
            "Werk": paper_data.get("title", ""),
            "Formatiertes_Zitat": formatted_citation,
            "DOI": paper_data.get("doi", ""),
            "Jahr": paper_data.get("year", ""),
            "Autoren": "; ".join(paper_data.get("authors", [])),
            "Quelle": paper_data.get("source", "unknown")  # v2.2: source annotation
        }
        rows.append(row)

    # Write CSV
    if rows:
        fieldnames = ["Zitat", "Seitenzahl", "Werk", "Formatiertes_Zitat", "DOI", "Jahr", "Autoren", "Quelle"]

        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        print(f"✅ Exported {len(rows)} quotes to {output_path}")
    else:
        print(f"⚠️  No quotes to export")


# CLI Interface
def main():
    """CLI for CSV Exporter"""
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="CSV Exporter for Quotes")
    parser.add_argument('--quotes', help='Input JSON file with quotes')
    parser.add_argument('--papers', help='Input JSON file with papers')
    parser.add_argument('--style', default='apa7',
                        choices=['apa7', 'ieee', 'harvard', 'mla', 'chicago'],
                        help='Citation style (default: apa7)')
    parser.add_argument('--output', help='Output CSV file path')
    parser.add_argument('--test', action='store_true', help='Run test with sample data')

    args = parser.parse_args()

    if args.test:
        # Test data
        test_quotes = [
            {
                "text": "DevOps governance requires continuous compliance monitoring.",
                "page": 5,
                "paper_doi": "10.1109/ICSE.2023.00042"
            },
            {
                "text": "Policy automation reduces manual checks by 80%.",
                "page": 7,
                "paper_doi": "10.1109/ICSE.2023.00042"
            }
        ]

        test_papers = [
            {
                "doi": "10.1109/ICSE.2023.00042",
                "title": "DevOps Governance Framework",
                "authors": ["Smith, John", "Doe, Alice"],
                "year": 2024,
                "venue": "IEEE Software",
                "volume": "41",
                "issue": "2",
                "pages": "45-52"
            }
        ]

        output_path = Path("test_quotes.csv")
        export_quotes_csv(test_quotes, test_papers, "apa7", output_path)

        # Show result
        print(f"\n📄 CSV Preview:")
        with open(output_path, 'r', encoding='utf-8') as f:
            print(f.read())

        # Cleanup
        output_path.unlink()
        print("\n✅ CSV Exporter test passed!")
        sys.exit(0)

    # Validate required args (if not test mode)
    if not args.quotes or not args.papers or not args.output:
        parser.error("--quotes, --papers, and --output are required (unless --test)")

    try:
        # Load quotes
        with open(args.quotes, 'r', encoding='utf-8') as f:
            data = json.load(f)
            quotes = data.get('quotes', data) if isinstance(data, dict) else data

        # Load papers
        with open(args.papers, 'r', encoding='utf-8') as f:
            data = json.load(f)
            papers = data.get('papers', data) if isinstance(data, dict) else data

        # Export
        output_path = Path(args.output)
        export_quotes_csv(quotes, papers, args.style, output_path)

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
