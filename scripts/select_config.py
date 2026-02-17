#!/usr/bin/env python3

"""
Config Selector - Interaktive Config-Auswahl für AcademicAgent
"""

import os
import sys
from pathlib import Path
from datetime import datetime

def list_available_configs():
    """Liste alle verfügbaren Configs"""
    # Versuche zuerst Repo-Ordner, dann Home-Ordner
    repo_config_dir = Path(__file__).parent.parent / "config"
    home_config_dir = Path.home() / "AcademicAgent" / "config"

    if repo_config_dir.exists():
        config_dir = repo_config_dir
    elif home_config_dir.exists():
        config_dir = home_config_dir
    else:
        config_dir = repo_config_dir  # Fallback für Fehlermeldung

    if not config_dir.exists():
        print(f"❌ Config-Ordner nicht gefunden: {config_dir}")
        sys.exit(1)

    configs = list(config_dir.glob("Config_*.md"))

    if not configs:
        print(f"❌ Keine Configs gefunden in: {config_dir}")
        print("\nBitte erstelle zuerst eine Config mit:")
        print("  cp ~/AcademicAgent/config/Config_Template.md ~/AcademicAgent/config/Config_MeinProjekt.md")
        sys.exit(1)

    return configs

def display_configs(configs):
    """Zeige verfügbare Configs"""
    print("\n📋 Verfügbare Configs:\n")

    for i, config in enumerate(configs, 1):
        # Extrahiere Projekt-Name aus Dateinamen
        project_name = config.stem.replace("Config_", "")

        # Skip Template
        if project_name == "Template":
            continue

        print(f"  [{i}] {project_name}")

        # Zeige erste Zeilen der Config
        try:
            with open(config, 'r') as f:
                lines = f.readlines()[:5]
                for line in lines:
                    if line.strip().startswith("#") and "Projekt-Titel" in line:
                        # Finde Titel in nächster Zeile
                        idx = lines.index(line)
                        if idx + 1 < len(lines):
                            title = lines[idx + 1].strip()
                            print(f"      → {title}")
                        break
        except:
            pass

    print()

def select_config():
    """Interaktive Config-Auswahl"""
    configs = list_available_configs()

    # Filtere Template raus
    configs = [c for c in configs if "Template" not in c.stem]

    if not configs:
        print("❌ Keine Configs gefunden (außer Template)")
        sys.exit(1)

    display_configs(configs)

    # User-Auswahl
    while True:
        try:
            choice = input("Wähle eine Config (Nummer): ").strip()
            idx = int(choice) - 1

            if 0 <= idx < len(configs):
                selected = configs[idx]
                project_name = selected.stem.replace("Config_", "")
                return selected, project_name
            else:
                print(f"❌ Ungültige Auswahl. Bitte 1-{len(configs)} wählen.")
        except ValueError:
            print("❌ Bitte eine Nummer eingeben.")
        except KeyboardInterrupt:
            print("\n\n❌ Abgebrochen.")
            sys.exit(0)

def create_run_directory(project_name):
    """Erstelle Run-Ordner mit Zeitstempel"""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    run_name = f"{timestamp}"

    # Versuche zuerst Repo-Ordner, dann Home-Ordner
    repo_runs_dir = Path(__file__).parent.parent / "runs"
    home_runs_dir = Path.home() / "AcademicAgent" / "runs"

    if (Path(__file__).parent.parent / "config").exists():
        run_dir = repo_runs_dir / run_name
    else:
        run_dir = home_runs_dir / run_name

    # Erstelle Ordnerstruktur
    (run_dir / "Downloads").mkdir(parents=True, exist_ok=True)
    (run_dir / "metadata").mkdir(parents=True, exist_ok=True)
    (run_dir / "logs").mkdir(parents=True, exist_ok=True)

    return run_dir, run_name

def save_run_info(run_dir, config_path, project_name):
    """Speichere Run-Metadaten"""
    import json

    run_info = {
        "project_name": project_name,
        "config_path": str(config_path),
        "timestamp": datetime.now().isoformat(),
        "status": "initialized"
    }

    with open(run_dir / "metadata" / "run_info.json", 'w') as f:
        json.dump(run_info, f, indent=2)

def main():
    print("\n" + "="*60)
    print("🤖 AcademicAgent - Config Selector")
    print("="*60)

    # Schritt 1: Config auswählen
    config_path, project_name = select_config()

    print(f"\n✅ Config ausgewählt: {project_name}")
    print(f"   Datei: {config_path}")

    # Schritt 2: Run-Ordner erstellen
    run_dir, run_name = create_run_directory(project_name)

    print(f"\n✅ Run-Ordner erstellt:")
    print(f"   {run_dir}")
    print(f"\n   Struktur:")
    print(f"   ├── Quote_Library.csv (wird hier erstellt)")
    print(f"   ├── Downloads/         (PDFs landen hier)")
    print(f"   ├── metadata/          (State & Zwischenergebnisse)")
    print(f"   └── logs/              (Logs)")

    # Schritt 3: Run-Info speichern
    save_run_info(run_dir, config_path, project_name)

    print(f"\n✅ Setup abgeschlossen!")
    print(f"\n" + "="*60)
    print("📋 Nächste Schritte:")
    print("="*60)
    print("\n1. Chrome starten (falls noch nicht laufend):")
    print("   bash scripts/start_chrome_debug.sh")
    print("\n2. Im Claude Code Chat:")
    print(f"   Starte Recherche für Run: {run_name}")
    print(f"   Config: {config_path}")
    print(f"   Arbeitsverzeichnis: {run_dir}")
    print()

    # Output für Agent
    output = {
        "config_path": str(config_path),
        "project_name": project_name,
        "run_dir": str(run_dir),
        "run_name": run_name
    }

    import json
    print("\n" + "="*60)
    print("🤖 Agent-Output (JSON):")
    print("="*60)
    print(json.dumps(output, indent=2))

if __name__ == '__main__':
    main()
