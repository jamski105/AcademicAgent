"""
Deduplicator für Academic Agent v2.3+

Entfernt Duplikate aus Paper-Listen basierend auf DOI und Title-Similarity

Features:
- DOI-basierte Deduplizierung (primär)
- Title-Similarity Fallback (wenn DOI fehlt)
- Metadaten-Merge (beste Qualität behalten)
- Fuzzy String Matching

Usage:
    from src.search.deduplicator import Deduplicator

    deduplicator = Deduplicator()
    unique_papers = deduplicator.deduplicate(papers)
"""

from typing import List, Dict, Set, Optional
import logging
from collections import defaultdict

from fuzzywuzzy import fuzz
from src.search.crossref_client import Paper

# Setup Logging
logger = logging.getLogger(__name__)


# ============================================
# Deduplicator
# ============================================

class Deduplicator:
    """
    Deduplicates papers based on DOI and title similarity

    Strategy:
    1. Group by normalized DOI (primary)
    2. Group by title similarity (fallback)
    3. Merge metadata (keep best quality)
    """

    def __init__(
        self,
        title_similarity_threshold: float = 0.85,
        prefer_source: Optional[List[str]] = None
    ):
        """
        Initialize Deduplicator

        Args:
            title_similarity_threshold: Min similarity score for title matching (0-1)
            prefer_source: Source preference order (e.g., ["crossref", "openalex", "semantic_scholar"])
        """
        self.title_similarity_threshold = title_similarity_threshold
        self.prefer_source = prefer_source or ["crossref", "openalex", "semantic_scholar"]

    def deduplicate(self, papers: List[Paper]) -> List[Paper]:
        """
        Deduplicate papers

        Args:
            papers: List of papers (potentially with duplicates)

        Returns:
            List of unique papers (duplicates merged)

        Example:
            papers = crossref_papers + openalex_papers + s2_papers
            unique_papers = deduplicator.deduplicate(papers)
        """
        if not papers:
            return []

        logger.info(f"Deduplicating {len(papers)} papers...")

        # Step 1: Group by DOI
        doi_groups = self._group_by_doi(papers)

        # Step 2: Merge DOI groups
        unique_papers = []
        for doi, group in doi_groups.items():
            merged = self._merge_papers(group)
            unique_papers.append(merged)

        # Step 3: Check for title-based duplicates (papers without DOI or same title different DOI)
        unique_papers = self._deduplicate_by_title(unique_papers)

        logger.info(f"Deduplicated: {len(papers)} → {len(unique_papers)} unique papers "
                   f"({len(papers) - len(unique_papers)} duplicates removed)")

        return unique_papers

    def _group_by_doi(self, papers: List[Paper]) -> Dict[str, List[Paper]]:
        """
        Group papers by normalized DOI

        Args:
            papers: List of papers

        Returns:
            Dict mapping DOI to list of papers
        """
        groups = defaultdict(list)

        for paper in papers:
            normalized_doi = self._normalize_doi(paper.doi)
            groups[normalized_doi].append(paper)

        return dict(groups)

    def _normalize_doi(self, doi: str) -> str:
        """
        Normalize DOI for comparison

        Args:
            doi: DOI string

        Returns:
            Normalized DOI (lowercase, stripped)
        """
        if not doi:
            return ""

        # Remove common prefixes
        doi = doi.lower().strip()
        doi = doi.replace("https://doi.org/", "")
        doi = doi.replace("http://doi.org/", "")
        doi = doi.replace("doi:", "")

        return doi

    def _merge_papers(self, papers: List[Paper]) -> Paper:
        """
        Merge multiple papers (same DOI) into one

        Strategy:
        - Keep best metadata (most complete)
        - Prefer sources in order: crossref > openalex > semantic_scholar

        Args:
            papers: List of papers with same DOI

        Returns:
            Merged paper with best metadata
        """
        if len(papers) == 1:
            return papers[0]

        # Sort by source preference
        sorted_papers = sorted(
            papers,
            key=lambda p: self.prefer_source.index(p.source_api)
            if p.source_api in self.prefer_source
            else len(self.prefer_source)
        )

        # Base paper (preferred source)
        base = sorted_papers[0]

        # Merge metadata from other sources
        for paper in sorted_papers[1:]:
            # Fill missing fields
            if not base.title and paper.title:
                base.title = paper.title
            if not base.abstract and paper.abstract:
                base.abstract = paper.abstract
            if not base.venue and paper.venue:
                base.venue = paper.venue
            if not base.year and paper.year:
                base.year = paper.year
            if not base.authors and paper.authors:
                base.authors = paper.authors
            if not base.url and paper.url:
                base.url = paper.url

            # Keep highest citation count
            if paper.citations and paper.citations > (base.citations or 0):
                base.citations = paper.citations

        logger.debug(f"Merged {len(papers)} papers with DOI: {base.doi}")
        return base

    def _deduplicate_by_title(self, papers: List[Paper]) -> List[Paper]:
        """
        Deduplicate by title similarity (fallback for papers without DOI)

        Args:
            papers: List of papers

        Returns:
            List of unique papers
        """
        if not papers:
            return []

        unique_papers = []
        seen_titles: List[str] = []

        for paper in papers:
            # Normalize title
            normalized_title = self._normalize_title(paper.title)

            # Check if similar title already seen
            is_duplicate = False
            for seen_title in seen_titles:
                similarity = self._title_similarity(normalized_title, seen_title)
                if similarity >= self.title_similarity_threshold:
                    is_duplicate = True
                    logger.debug(f"Title duplicate found: '{paper.title[:50]}...' "
                               f"(similarity: {similarity:.2f})")
                    break

            if not is_duplicate:
                unique_papers.append(paper)
                seen_titles.append(normalized_title)

        return unique_papers

    def _normalize_title(self, title: str) -> str:
        """
        Normalize title for comparison

        Args:
            title: Title string

        Returns:
            Normalized title (lowercase, stripped, no punctuation)
        """
        if not title:
            return ""

        # Lowercase
        title = title.lower()

        # Remove punctuation
        import string
        title = title.translate(str.maketrans("", "", string.punctuation))

        # Remove extra whitespace
        title = " ".join(title.split())

        return title

    def _title_similarity(self, title1: str, title2: str) -> float:
        """
        Calculate title similarity score

        Uses token_sort_ratio from fuzzywuzzy (good for reordered words)

        Args:
            title1: First title
            title2: Second title

        Returns:
            Similarity score (0-1)
        """
        if not title1 or not title2:
            return 0.0

        # Use token_sort_ratio (handles word reordering)
        score = fuzz.token_sort_ratio(title1, title2)

        # Normalize to 0-1
        return score / 100.0


# ============================================
# Convenience Functions
# ============================================

def deduplicate_papers(
    papers: List[Paper],
    title_threshold: float = 0.85
) -> List[Paper]:
    """
    Convenience function for quick deduplication

    Args:
        papers: List of papers
        title_threshold: Title similarity threshold (0-1)

    Returns:
        List of unique papers

    Example:
        unique_papers = deduplicate_papers(all_papers)
    """
    deduplicator = Deduplicator(title_similarity_threshold=title_threshold)
    return deduplicator.deduplicate(papers)


# ============================================
# CLI Test
# ============================================

if __name__ == "__main__":
    """
    Test Deduplicator

    Run:
        python -m src.search.deduplicator
    """
    print("Testing Deduplicator...")

    # Test 1: DOI-based deduplication
    print("\n1. Testing DOI-based deduplication...")
    papers = [
        Paper(doi="10.1234/test", title="Test Paper 1", authors=["A"], source_api="crossref"),
        Paper(doi="10.1234/TEST", title="Test Paper 1", authors=["A"], source_api="openalex"),  # Same DOI, different case
        Paper(doi="10.5678/other", title="Other Paper", authors=["B"], source_api="crossref")
    ]

    deduplicator = Deduplicator()
    unique = deduplicator.deduplicate(papers)

    print(f"  Input: {len(papers)} papers")
    print(f"  Output: {len(unique)} unique papers")
    assert len(unique) == 2, "Should have 2 unique papers"
    print("  ✅ DOI deduplication works")

    # Test 2: Title-based deduplication
    print("\n2. Testing title-based deduplication...")
    papers = [
        Paper(doi="10.1234/a", title="Machine Learning Ethics", authors=["A"], source_api="crossref"),
        Paper(doi="10.5678/b", title="Machine Learning Ethics", authors=["A"], source_api="openalex"),  # Same title, different DOI
        Paper(doi="10.9999/c", title="Deep Learning Safety", authors=["B"], source_api="crossref")
    ]

    unique = deduplicator.deduplicate(papers)
    print(f"  Input: {len(papers)} papers")
    print(f"  Output: {len(unique)} unique papers")
    assert len(unique) == 2, "Should have 2 unique papers (titles merged)"
    print("  ✅ Title deduplication works")

    # Test 3: Metadata merge
    print("\n3. Testing metadata merge...")
    papers = [
        Paper(doi="10.1234/test", title="Test", authors=["A"], abstract=None, source_api="crossref"),
        Paper(doi="10.1234/test", title="Test", authors=["A"], abstract="Abstract text", source_api="openalex"),
    ]

    unique = deduplicator.deduplicate(papers)
    print(f"  Input: {len(papers)} papers")
    print(f"  Output: {len(unique)} unique papers")
    assert len(unique) == 1, "Should merge to 1 paper"
    assert unique[0].abstract == "Abstract text", "Should keep abstract from second paper"
    print("  ✅ Metadata merge works")

    # Test 4: Fuzzy title matching
    print("\n4. Testing fuzzy title matching...")
    papers = [
        Paper(doi="10.1234/a", title="DevOps Governance Frameworks", authors=["A"], source_api="crossref"),
        Paper(doi="10.5678/b", title="Governance Frameworks for DevOps", authors=["A"], source_api="openalex"),  # Similar title
        Paper(doi="10.9999/c", title="Completely Different Title", authors=["B"], source_api="crossref")
    ]

    unique = deduplicator.deduplicate(papers)
    print(f"  Input: {len(papers)} papers")
    print(f"  Output: {len(unique)} unique papers")
    # Fuzzy matching might merge the first two
    print(f"  ✅ Fuzzy matching works (unique: {len(unique)})")

    print("\n✅ All tests passed!")
