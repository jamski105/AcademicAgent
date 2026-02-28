"""
Citation Formatter für Academic Agent v2.3+

Formatiert Paper-Zitationen in verschiedenen Stilen:
- APA 7 (American Psychological Association)
- IEEE (Institute of Electrical and Electronics Engineers)
- Harvard
- MLA 9 (Modern Language Association)
- Chicago

Usage:
    from src.export.citation_formatter import format_citation

    citation = format_citation(paper, style="apa7")
"""

from typing import Optional, List
from dataclasses import dataclass


@dataclass
class Paper:
    """Paper metadata for citation"""
    doi: str
    title: str
    authors: List[str]
    year: int
    venue: Optional[str] = None
    volume: Optional[str] = None
    issue: Optional[str] = None
    pages: Optional[str] = None
    url: Optional[str] = None


def format_citation_apa7(paper: Paper) -> str:
    """
    Format citation in APA 7 style

    Format: Smith, J., & Doe, A. (2024). Title. Journal, 41(2), 45-52. https://doi.org/...

    Args:
        paper: Paper object with metadata

    Returns:
        Formatted citation string
    """
    # Authors
    if not paper.authors or len(paper.authors) == 0:
        author_str = "Unknown"
    elif len(paper.authors) == 1:
        author_str = paper.authors[0]
    elif len(paper.authors) == 2:
        author_str = f"{paper.authors[0]}, & {paper.authors[1]}"
    else:
        # 3+ authors: First, Second, ..., & Last
        author_str = ", ".join(paper.authors[:-1]) + f", & {paper.authors[-1]}"

    # Year
    year_str = f"({paper.year})" if paper.year else "(n.d.)"

    # Title (italicized in markdown)
    title_str = f"*{paper.title}*" if paper.title else "Untitled"

    # Venue (journal/conference)
    parts = [f"{author_str} {year_str}. {title_str}."]

    if paper.venue:
        venue_part = f"*{paper.venue}*"
        if paper.volume:
            venue_part += f", *{paper.volume}*"
            if paper.issue:
                venue_part += f"({paper.issue})"
        if paper.pages:
            venue_part += f", {paper.pages}"
        parts.append(venue_part + ".")

    # DOI
    if paper.doi:
        parts.append(f"https://doi.org/{paper.doi}")

    return " ".join(parts)


def format_citation_ieee(paper: Paper) -> str:
    """
    Format citation in IEEE style

    Format: [1] J. Smith and A. Doe, "Title," Journal, vol. 41, no. 2, pp. 45-52, 2024.

    Args:
        paper: Paper object with metadata

    Returns:
        Formatted citation string
    """
    # Authors (initials first)
    if not paper.authors or len(paper.authors) == 0:
        author_str = "Unknown"
    elif len(paper.authors) == 1:
        author_str = _format_ieee_author(paper.authors[0])
    elif len(paper.authors) == 2:
        author_str = f"{_format_ieee_author(paper.authors[0])} and {_format_ieee_author(paper.authors[1])}"
    else:
        # 3+ authors: et al.
        author_str = f"{_format_ieee_author(paper.authors[0])} et al."

    # Title in quotes
    title_str = f'"{paper.title}"' if paper.title else '"Untitled"'

    # Build citation
    parts = [author_str, title_str]

    if paper.venue:
        venue_part = paper.venue
        if paper.volume:
            venue_part += f", vol. {paper.volume}"
        if paper.issue:
            venue_part += f", no. {paper.issue}"
        if paper.pages:
            venue_part += f", pp. {paper.pages}"
        parts.append(venue_part)

    if paper.year:
        parts.append(str(paper.year))

    return ", ".join(parts) + "."


def _format_ieee_author(author: str) -> str:
    """Format author name for IEEE (initials first)"""
    # Simple implementation: J. Smith
    parts = author.split()
    if len(parts) >= 2:
        # Assume "First Last" format
        return f"{parts[0][0]}. {' '.join(parts[1:])}"
    return author


def format_citation_harvard(paper: Paper) -> str:
    """
    Format citation in Harvard style

    Format: Smith, J. and Doe, A. (2024) 'Title', Journal, 41(2), pp. 45-52.

    Args:
        paper: Paper object with metadata

    Returns:
        Formatted citation string
    """
    # Authors
    if not paper.authors or len(paper.authors) == 0:
        author_str = "Unknown"
    elif len(paper.authors) == 1:
        author_str = paper.authors[0]
    elif len(paper.authors) == 2:
        author_str = f"{paper.authors[0]} and {paper.authors[1]}"
    else:
        author_str = f"{paper.authors[0]} et al."

    # Year
    year_str = f"({paper.year})" if paper.year else "(n.d.)"

    # Title in single quotes
    title_str = f"'{paper.title}'" if paper.title else "'Untitled'"

    # Build citation
    parts = [f"{author_str} {year_str}", title_str]

    if paper.venue:
        venue_part = f"*{paper.venue}*"
        if paper.volume and paper.issue:
            venue_part += f", {paper.volume}({paper.issue})"
        elif paper.volume:
            venue_part += f", {paper.volume}"
        if paper.pages:
            venue_part += f", pp. {paper.pages}"
        parts.append(venue_part)

    return ", ".join(parts) + "."


def format_citation_mla(paper: Paper) -> str:
    """
    Format citation in MLA 9 style

    Format: Smith, John, and Alice Doe. "Title." Journal, vol. 41, no. 2, 2024, pp. 45-52.

    Args:
        paper: Paper object with metadata

    Returns:
        Formatted citation string
    """
    # Authors
    if not paper.authors or len(paper.authors) == 0:
        author_str = "Unknown"
    elif len(paper.authors) == 1:
        author_str = paper.authors[0]
    else:
        # First author: Last, First. Others: First Last.
        author_str = f"{paper.authors[0]}, et al."

    # Title in quotes
    title_str = f'"{paper.title}"' if paper.title else '"Untitled"'

    # Build citation
    parts = [f"{author_str}. {title_str}."]

    if paper.venue:
        venue_part = f"*{paper.venue}*"
        if paper.volume:
            venue_part += f", vol. {paper.volume}"
        if paper.issue:
            venue_part += f", no. {paper.issue}"
        parts.append(venue_part)

        if paper.year:
            parts.append(str(paper.year))

        if paper.pages:
            parts.append(f"pp. {paper.pages}")

    return ", ".join(parts) + "."


def format_citation_chicago(paper: Paper) -> str:
    """
    Format citation in Chicago style

    Format: Smith, John, and Alice Doe. "Title." Journal 41, no. 2 (2024): 45-52.

    Args:
        paper: Paper object with metadata

    Returns:
        Formatted citation string
    """
    # Authors
    if not paper.authors or len(paper.authors) == 0:
        author_str = "Unknown"
    elif len(paper.authors) == 1:
        author_str = paper.authors[0]
    elif len(paper.authors) == 2:
        author_str = f"{paper.authors[0]}, and {paper.authors[1]}"
    else:
        author_str = f"{paper.authors[0]}, et al."

    # Title in quotes
    title_str = f'"{paper.title}"' if paper.title else '"Untitled"'

    # Build citation
    parts = [f"{author_str}. {title_str}."]

    if paper.venue:
        venue_part = f"*{paper.venue}*"
        if paper.volume:
            venue_part += f" {paper.volume}"
        if paper.issue:
            venue_part += f", no. {paper.issue}"
        if paper.year:
            venue_part += f" ({paper.year})"
        if paper.pages:
            venue_part += f": {paper.pages}"
        parts.append(venue_part + ".")

    return " ".join(parts)


def format_citation(paper: Paper, style: str = "apa7") -> str:
    """
    Format citation in specified style

    Args:
        paper: Paper object with metadata
        style: Citation style (apa7, ieee, harvard, mla, chicago)

    Returns:
        Formatted citation string

    Raises:
        ValueError: If style is not supported
    """
    style_lower = style.lower()

    if style_lower == "apa7":
        return format_citation_apa7(paper)
    elif style_lower == "ieee":
        return format_citation_ieee(paper)
    elif style_lower == "harvard":
        return format_citation_harvard(paper)
    elif style_lower == "mla":
        return format_citation_mla(paper)
    elif style_lower == "chicago":
        return format_citation_chicago(paper)
    else:
        raise ValueError(f"Unsupported citation style: {style}")


# CLI Interface
def main():
    """CLI for testing citation formatter"""
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Citation Formatter")
    parser.add_argument('--test', action='store_true', help='Run test')
    parser.add_argument('--style', default='apa7', choices=['apa7', 'ieee', 'harvard', 'mla', 'chicago'])

    args = parser.parse_args()

    if args.test:
        # Test paper
        test_paper = Paper(
            doi="10.1109/ICSE.2023.00042",
            title="DevOps Governance Framework",
            authors=["Smith, John", "Doe, Alice", "Johnson, Bob"],
            year=2024,
            venue="IEEE Software",
            volume="41",
            issue="2",
            pages="45-52"
        )

        print("Testing Citation Formatter...\n")

        for style in ['apa7', 'ieee', 'harvard', 'mla', 'chicago']:
            citation = format_citation(test_paper, style)
            print(f"{style.upper()}:")
            print(f"  {citation}\n")

        print("✅ All citation styles tested!")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
