#!/usr/bin/env python3

"""
State Manager - AcademicAgent Error Recovery
Speichert und lädt Recherche-State für Resume-Funktionalität
"""

import json
import sys
from pathlib import Path
from datetime import datetime

STATE_FILE = "metadata/research_state.json"

def save_state(project_dir, phase, status, data=None):
    """Speichere aktuellen Recherche-State"""
    project_path = Path(project_dir)
    state_file = project_path / STATE_FILE
    state_file.parent.mkdir(parents=True, exist_ok=True)

    # Load existing state if exists
    if state_file.exists():
        with open(state_file, 'r') as f:
            state = json.load(f)
    else:
        state = {
            "project_name": project_path.name,
            "started_at": datetime.now().isoformat(),
            "phases": {}
        }

    # Update phase state
    state["phases"][f"phase_{phase}"] = {
        "status": status,  # pending, in_progress, completed, failed
        "updated_at": datetime.now().isoformat(),
        "data": data or {}
    }

    state["current_phase"] = phase
    state["last_updated"] = datetime.now().isoformat()

    # Save
    with open(state_file, 'w') as f:
        json.dump(state, f, indent=2)

    print(f"✅ State saved: Phase {phase} - {status}")

def load_state(project_dir):
    """Lade gespeicherten State"""
    project_path = Path(project_dir)
    state_file = project_path / STATE_FILE

    if not state_file.exists():
        return None

    with open(state_file, 'r') as f:
        state = json.load(f)

    return state

def get_last_completed_phase(project_dir):
    """Finde letzte abgeschlossene Phase"""
    state = load_state(project_dir)
    if not state:
        return -1

    last_completed = -1
    for phase_key, phase_data in state.get("phases", {}).items():
        if phase_data["status"] == "completed":
            phase_num = int(phase_key.split("_")[1])
            last_completed = max(last_completed, phase_num)

    return last_completed

def get_resume_point(project_dir):
    """Bestimme wo weiterzumachen ist"""
    last_completed = get_last_completed_phase(project_dir)
    state = load_state(project_dir)

    if not state:
        return {
            "should_resume": False,
            "message": "No previous state found. Starting from Phase 0."
        }

    # Check for failed phases
    for phase_key, phase_data in state.get("phases", {}).items():
        if phase_data["status"] == "failed":
            phase_num = int(phase_key.split("_")[1])
            return {
                "should_resume": True,
                "resume_phase": phase_num,
                "message": f"Phase {phase_num} failed previously. Resume from Phase {phase_num}?"
            }

    # Check for in_progress phases
    for phase_key, phase_data in state.get("phases", {}).items():
        if phase_data["status"] == "in_progress":
            phase_num = int(phase_key.split("_")[1])
            return {
                "should_resume": True,
                "resume_phase": phase_num,
                "message": f"Phase {phase_num} was interrupted. Resume from Phase {phase_num}?"
            }

    # All completed
    if last_completed == 6:
        return {
            "should_resume": False,
            "message": "All phases completed. Research finished!"
        }

    # Resume from next phase
    next_phase = last_completed + 1
    return {
        "should_resume": True,
        "resume_phase": next_phase,
        "message": f"Last completed: Phase {last_completed}. Resume from Phase {next_phase}?"
    }

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Save state:  python3 state_manager.py save <project_dir> <phase> <status> [data]")
        print("  Load state:  python3 state_manager.py load <project_dir>")
        print("  Resume info: python3 state_manager.py resume <project_dir>")
        sys.exit(1)

    action = sys.argv[1]

    if action == "save":
        if len(sys.argv) < 5:
            print("Usage: python3 state_manager.py save <project_dir> <phase> <status>")
            sys.exit(1)

        project_dir = sys.argv[2]
        phase = int(sys.argv[3])
        status = sys.argv[4]
        data = json.loads(sys.argv[5]) if len(sys.argv) > 5 else None

        save_state(project_dir, phase, status, data)

    elif action == "load":
        if len(sys.argv) < 3:
            print("Usage: python3 state_manager.py load <project_dir>")
            sys.exit(1)

        project_dir = sys.argv[2]
        state = load_state(project_dir)

        if state:
            print(json.dumps(state, indent=2))
        else:
            print("No state found.")

    elif action == "resume":
        if len(sys.argv) < 3:
            print("Usage: python3 state_manager.py resume <project_dir>")
            sys.exit(1)

        project_dir = sys.argv[2]
        resume_info = get_resume_point(project_dir)

        print(json.dumps(resume_info, indent=2))

    else:
        print(f"Unknown action: {action}")
        sys.exit(1)

if __name__ == '__main__':
    main()
