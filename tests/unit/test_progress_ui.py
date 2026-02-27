"""
Unit Tests for Progress UI - Academic Agent v2.0

Tests for:
- ResearchProgress class
- SimpleProgress class
- Progress tracking and metrics
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from rich.progress import TaskID

from src.ui.progress_ui import ResearchProgress, SimpleProgress


# ============================================
# Fixtures
# ============================================

@pytest.fixture
def research_progress():
    """Create ResearchProgress instance"""
    return ResearchProgress()


@pytest.fixture
def simple_progress():
    """Create SimpleProgress instance"""
    return SimpleProgress(description="Test Task", total=100)


# ============================================
# ResearchProgress Tests
# ============================================

class TestResearchProgressInit:
    """Test ResearchProgress initialization"""

    def test_init_creates_console(self, research_progress):
        """Test that console is created"""
        assert research_progress.console is not None

    def test_init_creates_progress(self, research_progress):
        """Test that progress object is created"""
        assert research_progress.progress is not None

    def test_init_sets_default_metrics(self, research_progress):
        """Test that default metrics are initialized"""
        assert research_progress.metrics["papers_found"] == 0
        assert research_progress.metrics["papers_ranked"] == 0
        assert research_progress.metrics["pdfs_downloaded"] == 0
        assert research_progress.metrics["quotes_extracted"] == 0
        assert research_progress.metrics["current_phase"] == 0
        assert research_progress.metrics["total_phases"] == 6

    def test_init_phase_names(self, research_progress):
        """Test that phase names are correct"""
        assert len(research_progress.PHASES) == 6
        assert research_progress.PHASES[0] == "Setup"
        assert research_progress.PHASES[5] == "Finalize"


class TestResearchProgressStart:
    """Test starting progress tracking"""

    def test_start_creates_phase_task(self, research_progress):
        """Test that start() creates main phase task"""
        research_progress.start()
        assert research_progress.phase_task is not None
        research_progress.stop()

    def test_start_initializes_progress(self, research_progress):
        """Test that progress is started"""
        with patch.object(research_progress.progress, 'start') as mock_start:
            research_progress.start()
            mock_start.assert_called_once()
            research_progress.stop()


class TestResearchProgressPhases:
    """Test phase tracking"""

    def test_start_phase_creates_task(self, research_progress):
        """Test that start_phase creates task"""
        research_progress.start()
        research_progress.start_phase(1, "Test Phase")
        assert research_progress.current_task is not None
        research_progress.stop()

    def test_start_phase_updates_metrics(self, research_progress):
        """Test that start_phase updates current_phase metric"""
        research_progress.start()
        research_progress.start_phase(3)
        assert research_progress.metrics["current_phase"] == 3
        research_progress.stop()

    def test_start_phase_uses_default_description(self, research_progress):
        """Test that start_phase uses default phase name"""
        research_progress.start()
        research_progress.start_phase(2)  # Should be "Search"
        # Verify by checking the task was created
        assert research_progress.current_task is not None
        research_progress.stop()

    def test_update_phase_progress(self, research_progress):
        """Test updating phase progress"""
        research_progress.start()
        research_progress.start_phase(1)

        # Should not raise error
        research_progress.update_phase_progress(50, "Half done")
        research_progress.update_phase_progress(100, "Complete")

        research_progress.stop()

    def test_complete_phase(self, research_progress):
        """Test completing a phase"""
        research_progress.start()
        research_progress.start_phase(1)
        research_progress.complete_phase()

        # Task should be cleared
        assert research_progress.current_task is None
        research_progress.stop()

    def test_multiple_phases_sequential(self, research_progress):
        """Test running multiple phases sequentially"""
        research_progress.start()

        for i in range(1, 4):
            research_progress.start_phase(i)
            research_progress.update_phase_progress(50)
            research_progress.update_phase_progress(100)
            research_progress.complete_phase()
            assert research_progress.metrics["current_phase"] == i

        research_progress.stop()


class TestResearchProgressMetrics:
    """Test metrics tracking"""

    def test_update_metric_updates_value(self, research_progress):
        """Test that update_metric changes metric value"""
        research_progress.update_metric("papers_found", 42)
        assert research_progress.metrics["papers_found"] == 42

    def test_update_metric_multiple_times(self, research_progress):
        """Test updating metric multiple times"""
        research_progress.update_metric("papers_ranked", 10)
        assert research_progress.metrics["papers_ranked"] == 10

        research_progress.update_metric("papers_ranked", 20)
        assert research_progress.metrics["papers_ranked"] == 20

    def test_update_metric_ignores_unknown_metric(self, research_progress):
        """Test that unknown metrics are ignored"""
        research_progress.update_metric("unknown_metric", 123)
        assert "unknown_metric" not in research_progress.metrics

    def test_update_all_metrics(self, research_progress):
        """Test updating all available metrics"""
        research_progress.update_metric("papers_found", 100)
        research_progress.update_metric("papers_ranked", 50)
        research_progress.update_metric("pdfs_downloaded", 45)
        research_progress.update_metric("quotes_extracted", 135)

        assert research_progress.metrics["papers_found"] == 100
        assert research_progress.metrics["papers_ranked"] == 50
        assert research_progress.metrics["pdfs_downloaded"] == 45
        assert research_progress.metrics["quotes_extracted"] == 135


class TestResearchProgressOutput:
    """Test output methods"""

    def test_print_summary(self, research_progress):
        """Test printing summary"""
        research_progress.update_metric("papers_found", 15)
        research_progress.update_metric("papers_ranked", 15)
        research_progress.update_metric("pdfs_downloaded", 12)
        research_progress.update_metric("quotes_extracted", 36)

        # Should not raise error
        research_progress.print_summary()

    def test_print_error(self, research_progress):
        """Test printing error message"""
        # Should not raise error
        research_progress.print_error("Test error", phase="Phase 2")

    def test_print_error_without_phase(self, research_progress):
        """Test printing error without phase"""
        # Should not raise error
        research_progress.print_error("Test error")

    def test_print_success(self, research_progress):
        """Test printing success message"""
        # Should not raise error
        research_progress.print_success("Test success!")


class TestResearchProgressContextManager:
    """Test context manager interface"""

    def test_context_manager_starts_and_stops(self):
        """Test that context manager calls start/stop"""
        with ResearchProgress() as progress:
            assert progress.phase_task is not None
        # After exit, progress should be stopped

    def test_context_manager_with_phases(self):
        """Test using context manager with phases"""
        with ResearchProgress() as progress:
            progress.start_phase(1)
            progress.update_phase_progress(50)
            progress.complete_phase()
        # Should complete without error


# ============================================
# SimpleProgress Tests
# ============================================

class TestSimpleProgressInit:
    """Test SimpleProgress initialization"""

    def test_init_sets_description(self, simple_progress):
        """Test that description is set"""
        assert simple_progress.description == "Test Task"

    def test_init_sets_total(self, simple_progress):
        """Test that total is set"""
        assert simple_progress.total == 100

    def test_init_creates_progress(self, simple_progress):
        """Test that progress object is created"""
        assert simple_progress.progress is not None

    def test_init_task_id_none(self, simple_progress):
        """Test that task_id starts as None"""
        assert simple_progress.task_id is None


class TestSimpleProgressOperations:
    """Test SimpleProgress operations"""

    def test_start_creates_task(self, simple_progress):
        """Test that start() creates task"""
        simple_progress.start()
        assert simple_progress.task_id is not None
        simple_progress.stop()

    def test_update_advances_progress(self, simple_progress):
        """Test that update() advances progress"""
        simple_progress.start()
        # Should not raise error
        simple_progress.update(10)
        simple_progress.update(5)
        simple_progress.stop()

    def test_update_with_default_advance(self, simple_progress):
        """Test update with default advance=1"""
        simple_progress.start()
        simple_progress.update()  # Defaults to 1
        simple_progress.stop()

    def test_stop_before_start(self, simple_progress):
        """Test that stop before start doesn't crash"""
        # Should not raise error
        simple_progress.stop()


class TestSimpleProgressContextManager:
    """Test SimpleProgress context manager"""

    def test_context_manager_auto_start_stop(self):
        """Test that context manager auto starts/stops"""
        with SimpleProgress("Test", 100) as progress:
            assert progress.task_id is not None
        # After exit, should be stopped

    def test_context_manager_with_updates(self):
        """Test using context manager with updates"""
        with SimpleProgress("Processing", 50) as progress:
            for _ in range(10):
                progress.update(5)
        # Should complete without error

    def test_context_manager_full_workflow(self):
        """Test full workflow with context manager"""
        with SimpleProgress("Full Test", 100) as progress:
            for i in range(10):
                progress.update(10)


# ============================================
# Integration Tests
# ============================================

class TestProgressIntegration:
    """Test integration between components"""

    def test_research_progress_full_workflow(self):
        """Test complete research workflow simulation"""
        with ResearchProgress() as progress:
            # Phase 1
            progress.start_phase(1, "Setup")
            progress.update_phase_progress(50)
            progress.update_phase_progress(100)
            progress.complete_phase()

            # Phase 2
            progress.start_phase(2, "Search")
            progress.update_metric("papers_found", 20)
            progress.update_phase_progress(100)
            progress.complete_phase()

            # Phase 3
            progress.start_phase(3, "Rank")
            progress.update_metric("papers_ranked", 15)
            progress.update_phase_progress(100)
            progress.complete_phase()

            # Verify metrics
            assert progress.metrics["papers_found"] == 20
            assert progress.metrics["papers_ranked"] == 15
            assert progress.metrics["current_phase"] == 3

    def test_all_six_phases(self):
        """Test all six phases"""
        with ResearchProgress() as progress:
            for phase_num in range(1, 7):
                progress.start_phase(phase_num)
                progress.update_phase_progress(50)
                progress.update_phase_progress(100)
                progress.complete_phase()

            assert progress.metrics["current_phase"] == 6


# ============================================
# Edge Cases
# ============================================

class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_update_phase_progress_without_start(self, research_progress):
        """Test updating progress without starting phase"""
        research_progress.start()
        # Should not crash even without active phase
        research_progress.update_phase_progress(50)
        research_progress.stop()

    def test_complete_phase_without_current_task(self, research_progress):
        """Test completing phase without current task"""
        research_progress.start()
        # Should not crash
        research_progress.complete_phase()
        research_progress.stop()

    def test_simple_progress_update_before_start(self):
        """Test updating SimpleProgress before start"""
        progress = SimpleProgress("Test", 100)
        # Should not crash
        progress.update(10)

    def test_zero_total_simple_progress(self):
        """Test SimpleProgress with zero total"""
        with SimpleProgress("Zero", 0) as progress:
            progress.update(1)  # Should handle gracefully
