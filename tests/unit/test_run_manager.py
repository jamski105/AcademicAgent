"""Unit tests for run_manager.py"""
import pytest
from pathlib import Path
from src.state.run_manager import RunManager

def test_create_run_directory():
    """Test run directory creation"""
    manager = RunManager(base_dir=Path("runs"))
    run_dir = manager.create_run_directory()
    
    assert run_dir.exists()
    assert (run_dir / "pdfs").exists()
    assert (run_dir / "temp").exists()

def test_get_latest_run():
    """Test getting latest run"""
    manager = RunManager()
    latest = manager.get_latest_run()
    
    if latest:
        assert latest.exists()
        assert latest.is_dir()

# TODO: Add more tests
