#!/usr/bin/env python3
"""
Live Status Monitor for Academic Agent System
Polls research_state.json and displays live progress in terminal.
"""

import json
import time
import sys
from pathlib import Path
from datetime import datetime
import os

def clear_screen():
    """Clear terminal screen."""
    os.system('clear' if os.name != 'nt' else 'cls')

def format_duration(seconds):
    """Format seconds to human-readable duration."""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        return f"{seconds // 60}m {seconds % 60}s"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"

def get_phase_emoji(phase_num, status):
    """Get emoji for phase based on status."""
    if status == "completed":
        return "✅"
    elif status == "in_progress":
        return "⏳"
    elif status == "failed":
        return "❌"
    else:
        return "⏸️ "

def display_status(run_dir):
    """Display live status from research_state.json."""
    state_file = Path(run_dir) / "metadata" / "research_state.json"

    if not state_file.exists():
        print(f"⚠️  State file not found: {state_file}")
        return False

    try:
        with open(state_file) as f:
            state = json.load(f)
    except json.JSONDecodeError:
        print(f"⚠️  Invalid JSON in state file")
        return False

    clear_screen()

    # Header
    print("╔" + "═" * 62 + "╗")
    print("║  🎓 Academic Agent - Live Status" + " " * 28 + "║")
    print("║  Run: " + state.get("run_id", "Unknown")[:50].ljust(50) + "    ║")
    print("╚" + "═" * 62 + "╝")
    print()

    # Current Phase
    current_phase = state.get("current_phase", 0)
    status = state.get("status", "unknown")

    phase_names = {
        0: "Database Pool",
        1: "Search Strings",
        2: "Database Search",
        3: "Scoring & Ranking",
        4: "PDF Download",
        5: "Quote Extraction",
        6: "Finalization"
    }

    print("Current Phase:", phase_names.get(current_phase, f"Phase {current_phase}"))
    print("Progress:     ", end="")

    # Progress bar
    total_phases = 7
    completed = state.get("last_completed_phase", -1) + 1
    progress = int((completed / total_phases) * 40)
    bar = "█" * progress + "░" * (40 - progress)
    percentage = int((completed / total_phases) * 100)
    print(f"{bar} {percentage}%")
    print()

    # Phase Details
    phase_outputs = state.get("phase_outputs", {})

    for phase in range(7):
        phase_name = phase_names.get(phase, f"Phase {phase}")
        phase_data = phase_outputs.get(str(phase), {})
        phase_status = phase_data.get("status", "pending")
        emoji = get_phase_emoji(phase, phase_status)

        if phase_status == "completed":
            duration = phase_data.get("duration_seconds", 0)
            duration_str = format_duration(duration)

            # Phase-specific metrics
            extra_info = ""
            if phase == 2:  # Database Search
                iteration = phase_data.get("iteration_count", "?")
                dbs = len(phase_data.get("databases_searched", []))
                extra_info = f" - {iteration} iterations, {dbs} DBs"
            elif phase == 3:  # Scoring
                candidates = phase_data.get("candidates_ranked", "?")
                extra_info = f" - {candidates} sources ranked"
            elif phase == 4:  # PDF Download
                pdfs = phase_data.get("pdfs_downloaded", "?")
                extra_info = f" - {pdfs} PDFs"
            elif phase == 5:  # Extraction
                quotes = phase_data.get("quotes_extracted", "?")
                extra_info = f" - {quotes} quotes"

            print(f"{emoji} Phase {phase}: {phase_name} ({duration_str}{extra_info})")
        elif phase_status == "in_progress":
            started = phase_data.get("started_at", "")
            if started:
                # Calculate elapsed time
                try:
                    start_time = datetime.fromisoformat(started.replace('Z', '+00:00'))
                    elapsed = (datetime.now(start_time.tzinfo) - start_time).total_seconds()
                    elapsed_str = format_duration(int(elapsed))
                    print(f"{emoji} Phase {phase}: {phase_name} ({elapsed_str} so far)")
                except:
                    print(f"{emoji} Phase {phase}: {phase_name}")
            else:
                print(f"{emoji} Phase {phase}: {phase_name}")

            # Show iteration progress for Phase 2
            if phase == 2 and "phase_2_state" in state:
                p2_state = state["phase_2_state"]
                iteration = p2_state.get("current_iteration", 0)
                citations = p2_state.get("citations_found", 0)
                target = p2_state.get("target_citations", "?")
                print(f"   ↳ Iteration {iteration} - {citations}/{target} citations")
        else:
            print(f"{emoji} Phase {phase}: {phase_name}")

    print()

    # Budget Tracking (if available)
    budget_tracking = state.get("budget_tracking", {})
    if budget_tracking:
        total_cost = budget_tracking.get("total_cost_usd", 0)
        remaining = budget_tracking.get("remaining_usd", 0)
        percent_used = budget_tracking.get("percent_used", 0)

        print(f"💰 Budget: ${total_cost:.2f} used, ${remaining:.2f} remaining ({percent_used:.1f}%)")
        print()

    # Elapsed Time
    started_at = state.get("started_at", "")
    if started_at:
        try:
            start_time = datetime.fromisoformat(started_at.replace('Z', '+00:00'))
            elapsed = (datetime.now(start_time.tzinfo) - start_time).total_seconds()
            print(f"Elapsed: {format_duration(int(elapsed))}")
        except:
            pass

    # Last Updated
    last_updated = state.get("last_updated", "")
    if last_updated:
        print(f"Last Update: {last_updated}")

    print()
    print("Press Ctrl+C to exit")

    return True

def main():
    """Main monitoring loop."""
    if len(sys.argv) < 2:
        print("Usage: python3 live_monitor.py <run_dir>")
        print("Example: python3 live_monitor.py runs/2026-02-21_06-29-36")
        sys.exit(1)

    run_dir = sys.argv[1]

    if not Path(run_dir).exists():
        print(f"❌ Run directory not found: {run_dir}")
        sys.exit(1)

    print(f"Starting live monitor for: {run_dir}")
    print("Waiting for research_state.json...")
    print()

    # Wait for state file to appear
    state_file = Path(run_dir) / "metadata" / "research_state.json"
    timeout = 30
    waited = 0
    while not state_file.exists() and waited < timeout:
        time.sleep(1)
        waited += 1

    if not state_file.exists():
        print(f"❌ Timeout waiting for state file after {timeout}s")
        sys.exit(1)

    # Monitor loop
    try:
        while True:
            success = display_status(run_dir)
            if not success:
                print("Retrying in 5 seconds...")
            time.sleep(5)
    except KeyboardInterrupt:
        print("\n\n✓ Monitor stopped")
        sys.exit(0)

if __name__ == "__main__":
    main()
