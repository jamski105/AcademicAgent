"""
Unit Tests for Discipline Classifier

Tests the discipline classification logic (keyword-based fallback).

Note: In production, we use the discipline_classifier Agent (Haiku).
These tests verify the fallback Python module works correctly.
"""

import pytest
from pathlib import Path
from src.classification.discipline_classifier import (
    DisciplineClassifier,
    classify_discipline,
    DisciplineResult
)


# ============================================
# Fixtures
# ============================================

@pytest.fixture
def classifier():
    """Create classifier instance with default config"""
    return DisciplineClassifier()


@pytest.fixture
def config_path():
    """Path to test config"""
    return Path(__file__).parent.parent.parent / "config" / "dbis_disciplines.yaml"


# ============================================
# Basic Tests
# ============================================

def test_classifier_initialization(classifier):
    """Test classifier loads config successfully"""
    assert classifier.config is not None
    assert 'disciplines' in classifier.config


def test_classifier_with_custom_config(config_path):
    """Test classifier can load custom config path"""
    classifier = DisciplineClassifier(config_path=config_path)
    assert classifier.config is not None


# ============================================
# Classification Tests
# ============================================

def test_classics_high_confidence(classifier):
    """Test: Classics query should detect Klassische Philologie"""
    result = classifier.classify(
        user_query="Lateinische Metrik in der Augusteischen Dichtung"
    )

    assert result.primary_discipline == "Klassische Philologie"
    assert result.confidence >= 0.70
    assert "L'Année philologique" in result.relevant_databases


def test_computer_science_high_confidence(classifier):
    """Test: CS query should detect Informatik"""
    result = classifier.classify(
        user_query="Machine Learning Optimization Techniques",
        expanded_queries=["ML algorithms", "neural network training"]
    )

    assert result.primary_discipline == "Informatik"
    assert result.confidence >= 0.70
    assert "IEEE Xplore" in result.relevant_databases


def test_medicine_high_confidence(classifier):
    """Test: Medical query should detect Medizin"""
    result = classifier.classify(
        user_query="COVID-19 Treatment Protocols"
    )

    assert result.primary_discipline == "Medizin"
    assert result.confidence >= 0.70
    assert "PubMed" in result.relevant_databases


def test_interdisciplinary_medium_confidence(classifier):
    """Test: Interdisciplinary query should have lower confidence"""
    result = classifier.classify(
        user_query="Social Media Impact on Mental Health"
    )

    # Should detect psychology or sociology
    assert result.primary_discipline in ["Psychologie", "Soziologie"]
    # Should have secondary disciplines
    assert len(result.secondary_disciplines) > 0


def test_ambiguous_low_confidence(classifier):
    """Test: Generic query should have low confidence"""
    result = classifier.classify(
        user_query="Innovation and Change"
    )

    # Confidence should be lower
    assert result.confidence < 0.80
    # Should still return a discipline (fallback)
    assert result.primary_discipline != ""


# ============================================
# Edge Cases
# ============================================

def test_empty_query(classifier):
    """Test: Empty query should return fallback"""
    result = classifier.classify(user_query="")

    # Should fallback to Unknown
    assert result.primary_discipline == "Unknown"
    assert result.confidence < 0.50
    # Should have fallback databases
    assert len(result.relevant_databases) > 0


def test_non_academic_query(classifier):
    """Test: Non-academic query should return Unknown"""
    result = classifier.classify(
        user_query="Best pizza recipe"
    )

    assert result.primary_discipline == "Unknown"
    assert result.confidence < 0.50


def test_german_query(classifier):
    """Test: German query should work"""
    result = classifier.classify(
        user_query="Medizinische Behandlung von Diabetes"
    )

    # Should detect Medizin
    assert result.primary_discipline == "Medizin"


# ============================================
# Config Tests
# ============================================

def test_config_has_required_fields(classifier):
    """Test: Config has required structure"""
    config = classifier.config

    assert 'disciplines' in config
    assert 'mapping_rules' in config
    assert 'dbis' in config

    # Check at least one discipline exists
    disciplines = config['disciplines']
    assert len(disciplines) > 0

    # Check discipline structure
    first_discipline = list(disciplines.values())[0]
    assert 'dbis_category_id' in first_discipline
    assert 'keywords' in first_discipline
    assert 'databases' in first_discipline


def test_database_structure(classifier):
    """Test: Databases have required fields"""
    disciplines = classifier.config['disciplines']

    for discipline_name, discipline_data in disciplines.items():
        databases = discipline_data.get('databases', [])

        for db in databases:
            assert 'name' in db, f"Database missing 'name' in {discipline_name}"
            assert 'priority' in db, f"Database missing 'priority' in {discipline_name}"


# ============================================
# Integration Tests
# ============================================

def test_convenience_function():
    """Test: classify_discipline() convenience function works"""
    result = classify_discipline(
        user_query="DevOps Governance",
        expanded_queries=["continuous delivery governance"]
    )

    assert isinstance(result, dict)
    assert 'primary_discipline' in result
    assert 'confidence' in result
    assert result['primary_discipline'] == "Informatik"


def test_result_serialization(classifier):
    """Test: Result can be serialized to JSON"""
    import json

    result = classifier.classify("Machine Learning")

    # Should be serializable
    json_str = json.dumps(result.__dict__)
    assert len(json_str) > 0

    # Should be deserializable
    data = json.loads(json_str)
    assert data['primary_discipline'] == "Informatik"


# ============================================
# Performance Tests
# ============================================

def test_classification_speed(classifier):
    """Test: Classification should be fast (<1 second)"""
    import time

    start = time.time()
    result = classifier.classify(
        user_query="Machine Learning Optimization",
        expanded_queries=["ML training", "neural networks"]
    )
    duration = time.time() - start

    assert duration < 1.0, f"Classification too slow: {duration}s"


# ============================================
# Test Suite
# ============================================

def test_batch_classification(classifier):
    """Test: Multiple queries in sequence"""
    test_queries = [
        "Lateinische Metrik",
        "Machine Learning",
        "COVID-19 Treatment",
        "DevOps Governance",
        "Römische Rhetorik"
    ]

    for query in test_queries:
        result = classifier.classify(query)
        assert result.primary_discipline != ""
        assert 0.0 <= result.confidence <= 1.0
        assert len(result.relevant_databases) > 0


# ============================================
# Regression Tests
# ============================================

def test_known_good_classifications(classifier):
    """Test: Known good test cases"""
    test_cases = {
        "Lateinische Metrik": "Klassische Philologie",
        "Machine Learning": "Informatik",
        "COVID-19": "Medizin",
        "DevOps": "Informatik",
        "Psychologie": "Psychologie"
    }

    for query, expected in test_cases.items():
        result = classifier.classify(query)
        assert result.primary_discipline == expected, \
            f"Query '{query}' expected {expected}, got {result.primary_discipline}"


# ============================================
# TODO: Integration with Agent
# ============================================

# TODO: Test that Agent output format matches Python module format
# TODO: Test Agent vs Module consistency
# TODO: Test Agent fallback logic

"""
IMPLEMENTATION STATUS: ✅ COMPLETE (Python module)

TODO for full system:
- Test integration with discipline_classifier Agent
- Compare Agent vs Module accuracy
- Benchmark performance
- Validate on real queries

Run tests:
    pytest tests/unit/test_discipline_classifier.py -v
"""
