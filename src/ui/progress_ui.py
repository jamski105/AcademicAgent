"""
Progress UI für Academic Agent v2.0

Real-time Progress Bars mit rich library:
- Phase Progress (6 Phasen)
- Task Progress (Papers, PDFs, Quotes)
- Live Metrics
"""

from typing import Optional, Dict, Any
from rich.progress import (
    Progress,
    SpinnerColumn,
    BarColumn,
    TextColumn,
    TimeElapsedColumn,
    TaskProgressColumn,
    TaskID
)
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.live import Live
from rich import box


class ResearchProgress:
    """Progress tracker for research workflow"""

    # Phase names
    PHASES = [
        "Setup",
        "Search",
        "Rank",
        "Fetch PDFs",
        "Extract Quotes",
        "Finalize"
    ]

    def __init__(self):
        """Initialize Progress UI"""
        self.console = Console()
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(bar_width=40),
            TaskProgressColumn(),
            TextColumn("•"),
            TimeElapsedColumn(),
            console=self.console
        )

        # Track tasks
        self.phase_task: Optional[TaskID] = None
        self.current_task: Optional[TaskID] = None

        # Metrics
        self.metrics: Dict[str, Any] = {
            "papers_found": 0,
            "papers_ranked": 0,
            "pdfs_downloaded": 0,
            "quotes_extracted": 0,
            "current_phase": 0,
            "total_phases": 6
        }

    def start(self):
        """Start progress tracking"""
        self.progress.start()

        # Create main phase task
        self.phase_task = self.progress.add_task(
            "[cyan]Research Workflow",
            total=len(self.PHASES)
        )

    def stop(self):
        """Stop progress tracking"""
        self.progress.stop()

    def start_phase(self, phase_number: int, description: Optional[str] = None):
        """
        Start a new phase

        Args:
            phase_number: Phase number (1-6)
            description: Optional custom description
        """
        phase_name = self.PHASES[phase_number - 1]
        self.metrics["current_phase"] = phase_number

        desc = description or f"Phase {phase_number}/6: {phase_name}"

        # Update main progress
        if self.phase_task is not None:
            self.progress.update(self.phase_task, completed=phase_number - 1)

        # Create task for this phase
        self.current_task = self.progress.add_task(
            f"[green]{desc}",
            total=100
        )

    def update_phase_progress(self, percent: float, status: Optional[str] = None):
        """
        Update current phase progress

        Args:
            percent: Progress percentage (0-100)
            status: Optional status message
        """
        if self.current_task is not None:
            desc = f"[green]Phase {self.metrics['current_phase']}/6"
            if status:
                desc += f" - {status}"

            self.progress.update(
                self.current_task,
                completed=percent,
                description=desc
            )

    def complete_phase(self):
        """Mark current phase as complete"""
        if self.current_task is not None:
            self.progress.update(self.current_task, completed=100)
            self.progress.remove_task(self.current_task)
            self.current_task = None

        # Update main progress
        if self.phase_task is not None:
            current = self.metrics["current_phase"]
            self.progress.update(self.phase_task, completed=current)

    def update_metric(self, metric: str, value: int):
        """
        Update a metric

        Args:
            metric: Metric name
            value: New value
        """
        if metric in self.metrics:
            self.metrics[metric] = value

    def print_summary(self):
        """Print final summary"""
        table = Table(title="Research Summary", box=box.ROUNDED)

        table.add_column("Metric", style="cyan", no_wrap=True)
        table.add_column("Value", style="green")

        table.add_row("Papers Found", str(self.metrics["papers_found"]))
        table.add_row("Papers Ranked", str(self.metrics["papers_ranked"]))
        table.add_row("PDFs Downloaded", str(self.metrics["pdfs_downloaded"]))
        table.add_row("Quotes Extracted", str(self.metrics["quotes_extracted"]))

        self.console.print("\n")
        self.console.print(table)

    def print_error(self, error_message: str, phase: Optional[str] = None):
        """
        Print error message

        Args:
            error_message: Error message
            phase: Optional phase name
        """
        title = f"Error in {phase}" if phase else "Error"

        panel = Panel(
            f"[red]{error_message}[/red]",
            title=title,
            border_style="red"
        )

        self.console.print("\n")
        self.console.print(panel)

    def print_success(self, message: str):
        """
        Print success message

        Args:
            message: Success message
        """
        panel = Panel(
            f"[green]{message}[/green]",
            title="Success",
            border_style="green"
        )

        self.console.print("\n")
        self.console.print(panel)

    def __enter__(self):
        """Context manager entry"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop()


# ============================================
# Simple Progress Bar (for single tasks)
# ============================================

class SimpleProgress:
    """Simple progress bar for single tasks"""

    def __init__(self, description: str, total: int):
        """
        Initialize simple progress

        Args:
            description: Task description
            total: Total items
        """
        self.description = description
        self.total = total
        self.progress = Progress(
            TextColumn("[bold blue]{task.description}"),
            BarColumn(bar_width=50),
            TaskProgressColumn(),
            TimeElapsedColumn()
        )
        self.task_id: Optional[TaskID] = None

    def start(self):
        """Start progress"""
        self.progress.start()
        self.task_id = self.progress.add_task(self.description, total=self.total)

    def update(self, advance: int = 1):
        """Update progress"""
        if self.task_id is not None:
            self.progress.update(self.task_id, advance=advance)

    def stop(self):
        """Stop progress"""
        self.progress.stop()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


# ============================================
# Test Code
# ============================================

if __name__ == "__main__":
    """Test Progress UI"""
    import time

    print("Testing Progress UI...")

    # Test ResearchProgress
    with ResearchProgress() as progress:
        # Phase 1: Setup
        progress.start_phase(1, "Setting up environment")
        time.sleep(0.5)
        progress.update_phase_progress(50, "Loading config")
        time.sleep(0.5)
        progress.update_phase_progress(100, "Setup complete")
        progress.complete_phase()

        # Phase 2: Search
        progress.start_phase(2, "Searching APIs")
        time.sleep(0.5)
        progress.update_metric("papers_found", 15)
        progress.update_phase_progress(33, "CrossRef done")
        time.sleep(0.5)
        progress.update_phase_progress(66, "OpenAlex done")
        time.sleep(0.5)
        progress.update_phase_progress(100, "Search complete")
        progress.complete_phase()

        # Phase 3: Rank
        progress.start_phase(3, "Ranking papers")
        time.sleep(0.5)
        progress.update_metric("papers_ranked", 15)
        progress.update_phase_progress(100, "Ranking complete")
        progress.complete_phase()

        # Print summary
        progress.print_summary()
        progress.print_success("Research workflow completed!")

    print("\n✅ Progress UI test completed!")
