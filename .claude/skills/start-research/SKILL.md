# start-research

Interactive config selection and research initialization

## Configuration

```json
{
  "context": "main_thread",
  "disable-model-invocation": true
}
```

## Instructions

You are the entry point for starting a new academic research session.

### Your Task

1. **Interactive Config Selection**
   - Run: `python3 scripts/select_config.py`
   - User selects a config from ./config/
   - Script creates runs/<timestamp>/ directory structure
   - Script returns JSON with: config_path, run_dir, project_name, run_name

2. **Umfang/Preset Selection**
   - Ask user: "Welcher Umfang?"
   - Options:
     - **S (Quick)**: 5-8 sources, 30-45 min, 2-3 databases
     - **M (Standard)**: 18 sources, 3-4h, 6-9 databases (default)
     - **L (Deep)**: 30-50 sources, 5-6h, all available databases
   - Store preset in runs/<timestamp>/metadata.json

3. **Load Config & Validate**
   - Read the selected config from config_path
   - Check required fields: project title, research question, clusters, databases, quality thresholds
   - If missing info: ask user targeted questions

4. **Run Directory Setup**
   - Create subdirectories:
     - runs/<timestamp>/downloads/
     - runs/<timestamp>/metadata/
     - runs/<timestamp>/logs/
     - runs/<timestamp>/outputs/
   - Copy config to: runs/<timestamp>/config.md (snapshot for reproducibility)
   - Create metadata.json: {timestamp, preset, config_filename, project_name}

5. **Chrome CDP Check**
   - Check: `curl -s http://localhost:9222/json/version`
   - If fails: instruct user to run `bash scripts/start_chrome_debug.sh` and wait

6. **User Confirmation**
   - Show summary: config, preset, estimated time, output location
   - Ask: "Soll ich loslegen? (Ja/Nein)"
   - If yes: proceed to step 7

7. **Start Orchestrator**
   - Use Task tool to spawn orchestrator with:
     - subagent_type: "general-purpose"
     - Provide: config_path, run_dir, project_name, preset
     - Instruct orchestrator to use runs/<run_id>/ as working directory
     - Tell orchestrator Chrome CDP is ready on port 9222

### Important

- You run in main thread (NOT forked) because you need Task() and Write permissions
- All research outputs go to runs/<timestamp>/
- Config is single source of truth (no <topic> argument needed)
- You do NOT implement research phases - you only set up and delegate to orchestrator

### Error Handling

- No configs found → guide user to create one from Config_Template.md
- Chrome CDP unreachable → wait for user to start it
- Config invalid → ask user specific questions to fix it
