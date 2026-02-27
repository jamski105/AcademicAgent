"""Checkpointer für Resume-Funktionalität - Academic Agent v2.1

v2.1 Changes:
- Checkpoint is stored directly in run directory
- File: runs/{timestamp}/checkpoint.json
- Simplified interface (no more session_id parameter)
"""

import json
import time
from pathlib import Path
from typing import Optional, Dict, Any


class Checkpointer:
    """Saves checkpoints every N minutes for resume functionality"""

    def __init__(self, run_dir: Path, interval_minutes: int = 5):
        """
        Initialize Checkpointer

        Args:
            run_dir: Run directory (e.g. runs/2026-02-27_14-30-00/)
            interval_minutes: Interval between checkpoints (default: 5 minutes)

        Example:
            cp = Checkpointer(run_dir=Path("runs/2026-02-27_14-30-00"))
            cp.save_checkpoint({"phase": 3, "papers_found": 25})
        """
        self.run_dir = run_dir
        self.checkpoint_file = run_dir / "checkpoint.json"
        self.interval_seconds = interval_minutes * 60
        self.last_checkpoint_time = 0

    def should_checkpoint(self) -> bool:
        """Check if it's time to save checkpoint"""
        return (time.time() - self.last_checkpoint_time) >= self.interval_seconds

    def save_checkpoint(self, state: Dict[str, Any]) -> Path:
        """
        Save checkpoint

        Args:
            state: State dict to save

        Returns:
            Path to checkpoint file
        """
        with open(self.checkpoint_file, 'w') as f:
            json.dump({**state, "checkpoint_time": time.time()}, f, indent=2)
        self.last_checkpoint_time = time.time()
        return self.checkpoint_file

    def load_checkpoint(self) -> Optional[Dict[str, Any]]:
        """
        Load checkpoint if exists

        Returns:
            State dict or None if no checkpoint exists
        """
        if not self.checkpoint_file.exists():
            return None
        with open(self.checkpoint_file) as f:
            return json.load(f)

    def delete_checkpoint(self) -> None:
        """Delete checkpoint after successful completion"""
        if self.checkpoint_file.exists():
            self.checkpoint_file.unlink()

    def checkpoint_exists(self) -> bool:
        """Check if checkpoint file exists"""
        return self.checkpoint_file.exists()


if __name__ == "__main__":
    import tempfile
    temp_dir = Path(tempfile.mkdtemp())
    cp = Checkpointer(run_dir=temp_dir, interval_minutes=0)  # 0 for testing
    cp.save_checkpoint({"step": 3, "data": "test"})
    loaded = cp.load_checkpoint()
    assert loaded["step"] == 3
    print("✅ Checkpointer works!")
    import shutil; shutil.rmtree(temp_dir)
