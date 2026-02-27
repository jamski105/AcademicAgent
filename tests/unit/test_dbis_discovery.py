"""
Unit Tests for DBIS Auto-Discovery (v2.3)

Tests the discovery logic, config loading, filtering, and fallback mechanisms.
"""

import pytest
from pathlib import Path
from src.search.dbis_search_orchestrator import (
    load_dbis_config,
    load_dbis_selectors,
    prepare_dbis_search
)


# ============================================
# Fixtures
# ============================================

@pytest.fixture
def config():
    """Load DBIS config"""
    return load_dbis_config()


@pytest.fixture
def selectors():
    """Load DBIS selectors"""
    return load_dbis_selectors()


# ============================================
# Config Loading Tests
# ============================================

def test_load_dbis_config(config):
    """Test: DBIS config loads successfully"""
    assert config is not None
    assert 'disciplines' in config
    assert 'discovery_defaults' in config
    assert 'discovery_blacklist' in config


def test_discovery_defaults_present(config):
    """Test: Discovery defaults are defined"""
    defaults = config.get('discovery_defaults', {})
    assert 'enabled' in defaults
    assert 'max_databases' in defaults
    assert 'cache_ttl_hours' in defaults
    assert 'timeout_seconds' in defaults


def test_discovery_blacklist_present(config):
    """Test: Discovery blacklist is defined"""
    blacklist = config.get('discovery_blacklist', [])
    assert len(blacklist) > 0
    assert 'Katalog' in blacklist
    assert 'Directory' in blacklist
    assert 'Encyclopedia' in blacklist


def test_load_dbis_selectors(selectors):
    """Test: DBIS selectors load successfully"""
    assert selectors is not None
    assert 'database_entry' in selectors
    assert 'database_name' in selectors
    assert 'traffic_light' in selectors


# ============================================
# Discipline Configuration Tests
# ============================================

def test_rechtswissenschaft_has_discovery_enabled(config):
    """Test: Rechtswissenschaft has discovery_enabled: true"""
    disciplines = config.get('disciplines', {})
    jura = disciplines.get('Rechtswissenschaft', {})

    assert jura.get('discovery_enabled', False) == True
    assert jura.get('discovery_max_databases', 0) >= 5
    assert len(jura.get('preferred_databases', [])) >= 3


def test_rechtswissenschaft_has_fallback_databases(config):
    """Test: Rechtswissenschaft has fallback_databases"""
    disciplines = config.get('disciplines', {})
    jura = disciplines.get('Rechtswissenschaft', {})

    fallback = jura.get('fallback_databases', [])
    assert len(fallback) >= 2
    # Should have Beck-Online and Juris at minimum
    fallback_names = [db['name'] if isinstance(db, dict) else db for db in fallback]
    assert 'Beck-Online' in fallback_names
    assert 'Juris' in fallback_names


# ============================================
# prepare_dbis_search() Tests
# ============================================

def test_prepare_dbis_search_discovery_mode():
    """Test: prepare_dbis_search with discovery_enabled discipline"""
    result = prepare_dbis_search(
        user_query="Mietrecht Kündigungsfristen",
        discipline="Rechtswissenschaft",
        max_databases=5
    )

    assert result['mode'] == 'discovery'
    assert result['discipline'] == 'Rechtswissenschaft'
    assert 'discovery' in result
    assert result['discovery']['enabled'] == True
    assert result['discovery']['max_databases'] == 5
    assert len(result['discovery']['preferred_databases']) >= 3
    assert len(result['fallback_databases']) >= 2


def test_prepare_dbis_search_config_mode():
    """Test: prepare_dbis_search with discovery_disabled discipline"""
    result = prepare_dbis_search(
        user_query="Lateinische Metrik",
        discipline="Klassische Philologie",  # Has discovery_enabled: false
        max_databases=3,
        mode="config"  # Force config mode
    )

    assert result['mode'] == 'config'
    assert result['discipline'] == 'Klassische Philologie'
    assert 'databases' in result
    assert 'selectors' in result
    assert len(result['databases']) <= 3


def test_prepare_dbis_search_unknown_discipline():
    """Test: prepare_dbis_search with unknown discipline uses fallback"""
    result = prepare_dbis_search(
        user_query="Test Query",
        discipline="UnknownDiscipline",
        max_databases=3
    )

    assert result['discipline'] == 'Unknown'
    assert result['mode'] == 'config'
    assert 'databases' in result
    assert len(result['databases']) > 0


def test_discovery_selectors_included():
    """Test: Discovery config includes all required selectors"""
    result = prepare_dbis_search(
        user_query="Test",
        discipline="Rechtswissenschaft",
        max_databases=5
    )

    assert 'discovery' in result
    selectors = result['discovery']['selectors']

    assert 'database_entry' in selectors
    assert 'database_name' in selectors
    assert 'traffic_light' in selectors
    assert 'access_link' in selectors
    assert 'green_indicator' in selectors
    assert 'yellow_indicator' in selectors
    assert 'red_indicator' in selectors


def test_discovery_blacklist_included():
    """Test: Discovery config includes blacklist"""
    result = prepare_dbis_search(
        user_query="Test",
        discipline="Rechtswissenschaft",
        max_databases=5
    )

    assert 'discovery' in result
    blacklist = result['discovery']['blacklist']

    assert len(blacklist) > 0
    assert 'Katalog' in blacklist
    assert 'Directory' in blacklist


def test_discovery_cache_key_format():
    """Test: Cache key has correct format"""
    result = prepare_dbis_search(
        user_query="Test",
        discipline="Rechtswissenschaft",
        max_databases=5
    )

    cache_key = result['discovery']['cache_key']
    assert 'dbis_discovery_' in cache_key
    assert 'Rechtswissenschaft' in cache_key
    # Should include today's date
    from datetime import date
    assert date.today().isoformat() in cache_key


def test_preferred_databases_priority():
    """Test: Preferred databases are included in config"""
    result = prepare_dbis_search(
        user_query="Test",
        discipline="Rechtswissenschaft",
        max_databases=5
    )

    preferred = result['discovery']['preferred_databases']
    assert 'Beck-Online' in preferred
    assert 'Juris' in preferred


def test_fallback_databases_structure():
    """Test: Fallback databases have correct structure"""
    result = prepare_dbis_search(
        user_query="Test",
        discipline="Rechtswissenschaft",
        max_databases=5
    )

    fallback = result['fallback_databases']
    assert len(fallback) > 0

    for db in fallback:
        assert isinstance(db, dict)
        assert 'name' in db
        # May have priority, search_selector, etc.


# ============================================
# Mode Selection Tests
# ============================================

def test_mode_auto_uses_config_setting():
    """Test: mode='auto' respects config discovery_enabled setting"""
    result = prepare_dbis_search(
        user_query="Test",
        discipline="Rechtswissenschaft",  # Has discovery_enabled: true
        max_databases=5,
        mode="auto"
    )
    assert result['mode'] == 'discovery'


def test_mode_discovery_forces_discovery():
    """Test: mode='discovery' forces discovery even if disabled in config"""
    result = prepare_dbis_search(
        user_query="Test",
        discipline="Informatik",  # May have discovery_enabled: false
        max_databases=5,
        mode="discovery"  # Force
    )
    assert result['mode'] == 'discovery'
    assert 'discovery' in result


def test_mode_config_forces_config():
    """Test: mode='config' forces config mode even if discovery enabled"""
    result = prepare_dbis_search(
        user_query="Test",
        discipline="Rechtswissenschaft",  # Has discovery_enabled: true
        max_databases=5,
        mode="config"  # Force
    )
    assert result['mode'] == 'config'
    assert 'databases' in result


# ============================================
# Edge Cases & Error Handling
# ============================================

def test_max_databases_limits_selection():
    """Test: max_databases parameter limits database selection"""
    result = prepare_dbis_search(
        user_query="Test",
        discipline="Rechtswissenschaft",
        max_databases=2
    )

    if result['mode'] == 'discovery':
        assert result['discovery']['max_databases'] == 2
    else:
        assert len(result['databases']) <= 2


def test_empty_discipline_uses_fallback():
    """Test: Empty discipline uses fallback"""
    result = prepare_dbis_search(
        user_query="Test",
        discipline="",
        max_databases=3
    )

    assert result['discipline'] == 'Unknown'
    assert 'databases' in result


# ============================================
# Performance Tests
# ============================================

def test_config_loading_is_fast():
    """Test: Config loading completes in reasonable time"""
    import time
    start = time.time()
    config = load_dbis_config()
    elapsed = time.time() - start

    assert elapsed < 0.5  # Should load in < 500ms


def test_prepare_dbis_search_is_fast():
    """Test: prepare_dbis_search completes quickly"""
    import time
    start = time.time()
    result = prepare_dbis_search(
        user_query="Test",
        discipline="Rechtswissenschaft",
        max_databases=5
    )
    elapsed = time.time() - start

    assert elapsed < 0.5  # Should complete in < 500ms


# ============================================
# Integration Test (requires config files)
# ============================================

def test_full_workflow_integration():
    """Integration Test: Full workflow from query to agent config"""
    # This simulates what linear_coordinator does

    # Step 1: User query
    user_query = "Mietrecht Kündigungsfristen"

    # Step 2: Discipline detection (simulated)
    discipline = "Rechtswissenschaft"

    # Step 3: Prepare DBIS search
    config = prepare_dbis_search(
        user_query=user_query,
        discipline=discipline,
        max_databases=5
    )

    # Verify agent-ready config
    assert config['user_query'] == user_query
    assert config['discipline'] == discipline
    assert config['mode'] in ['discovery', 'config']
    assert 'dbis_url' in config or 'databases' in config

    # Discovery mode should have all required fields
    if config['mode'] == 'discovery':
        assert 'discovery' in config
        assert 'fallback_databases' in config
        assert config['discovery']['enabled'] == True

    print(f"✅ Integration test passed! Mode: {config['mode']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
