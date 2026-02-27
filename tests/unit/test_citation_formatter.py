"""Unit tests for citation_formatter.py"""
import pytest
from src.export.citation_formatter import format_citation, Paper

def test_apa7_citation():
    """Test APA7 citation formatting"""
    paper = Paper(
        doi="10.1109/TEST",
        title="Test Paper",
        authors=["Smith, John", "Doe, Alice"],
        year=2024,
        venue="Test Journal"
    )
    citation = format_citation(paper, "apa7")
    assert "Smith, John, & Doe, Alice (2024)" in citation
    assert "Test Paper" in citation

# TODO: Add tests for all styles
