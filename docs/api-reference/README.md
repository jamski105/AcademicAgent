# 📖 API Reference

Technische Referenzdokumentation für AcademicAgent Komponenten.

## Überblick

Diese Referenz dokumentiert:
- **Agents** - Spezialisierte Agent-Definitionen
- **Skills** - Skill-Definitionen (Orchestrator)
- **Utilities** - Python-Utility-Module
- **CDP-Wrapper** - Browser-Automatisierungs-API

## Zielgruppe

Diese Dokumentation ist für:
- Entwickler die das System erweitern
- Fortgeschrittene Nutzer die Anpassungen vornehmen
- Contributors die die Architektur verstehen wollen

**Für Endnutzer:** Siehe [User Guide](../user-guide/README.md)
**Für Entwicklung:** Siehe [Developer Guide](../developer-guide/README.md)

---

## Komponenten-Übersicht

### [Agents](agents.md)

Spezialisierte Agents für verschiedene Aufgaben:
- `setup-agent` - Interaktive Konfig-Erstellung
- `browser-agent` - Web-Automatisierung
- `search-agent` - Suchstring-Generierung
- `scoring-agent` - 5D-Bewertung
- `extraction-agent` - Zitat-Extraktion

### [Skills](skills.md)

Haupt-Skills:
- `/academicagent` - Orchestrator-Skill

### [Utilities](utilities.md)

Python-Module:
- `cdp_wrapper.py` - CDP-Client
- `cost_tracker.py` - Kosten-Tracking
- `metrics.py` - Metriken-Collector
- `retry_strategy.py` - Retry-Handler
- `safe_bash.py` - Action-Gate
- `validate_state.py` - State-Validierung

---

## Schnellstart

### Agents aufrufen

```bash
# In Claude Code Chat:
/academicagent        # Haupt-Skill
/setup-agent          # Konfig erstellen
/browser-agent        # Browser-Test
```

### Python-Utilities nutzen

```python
# State validieren
from scripts.validate_state import validate_state
state = validate_state('runs/[timestamp]/metadata/research_state.json')

# Kosten tracken
from scripts.cost_tracker import CostTracker
tracker = CostTracker(run_id="2026-02-18_14-30-00")
tracker.record_llm_call(...)

# CDP-Client nutzen
from scripts.cdp_wrapper import create_cdp_client
cdp = create_cdp_client()
cdp.navigate("https://example.com")
```

---

## Konventionen

### Parameter-Typen

```python
str          # String
int          # Integer
float        # Float
bool         # Boolean
dict         # Dictionary
list         # Liste
Optional[T]  # Kann None sein
Union[A, B]  # Entweder A oder B
```

### Return-Types

```python
→ dict       # Gibt Dictionary zurück
→ None       # Gibt nichts zurück
→ bool       # Gibt Boolean zurück
```

### Exceptions

```python
raises ValueError       # Kann ValueError werfen
raises FileNotFoundError
raises CustomError
```

---

## Navigatio

- **[Agents](agents.md)** - Agent-Definitionen und Prompt-Referenz
- **[Skills](skills.md)** - Skill-Definitionen
- **[Utilities](utilities.md)** - Python-Module Referenz

---

## Weitere Ressourcen

- **[User Guide](../user-guide/README.md)** - Für Endnutzer
- **[Developer Guide](../developer-guide/README.md)** - Für Entwickler
- **[Architecture](../developer-guide/01-architecture.md)** - System-Architektur
- **[GitHub Repository](../../)** - Source Code

---

**[Weiter zu: Agents →](agents.md)**
