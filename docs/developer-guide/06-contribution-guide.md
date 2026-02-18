# 🤝 Contribution Guide

Willkommen! Dieser Guide hilft dir, zu AcademicAgent beizutragen.

## Erste Schritte

### 1. Fork & Clone

```bash
# Fork auf GitHub (via Web UI)

# Clone deinen Fork
git clone https://github.com/YOUR_USERNAME/AcademicAgent.git
cd AcademicAgent

# Add upstream remote
git remote add upstream https://github.com/ORIGINAL_OWNER/AcademicAgent.git
```

### 2. Development-Setup

```bash
# Install dependencies
bash setup.sh

# Install test dependencies
pip install -r tests/requirements-test.txt

# Install pre-commit hooks
bash scripts/setup_git_hooks.sh

# Verify setup
pytest tests/unit/ -v
```

### 3. Branch erstellen

```bash
# Sync with upstream
git fetch upstream
git checkout main
git merge upstream/main

# Create feature branch
git checkout -b feature/my-feature
# oder
git checkout -b fix/issue-123
```

---

## Arten von Contributions

### 🐛 Bug Fixes

**Wann:** Du hast einen Bug gefunden und möchtest ihn fixen.

**Prozess:**

1. **Check existing issues:** Gibt es schon ein Issue?
2. **Create issue** (falls nicht vorhanden):
   ```markdown
   **Bug Description:**
   [Was ist das Problem?]

   **Steps to Reproduce:**
   1. [Schritt 1]
   2. [Schritt 2]
   ...

   **Expected Behavior:**
   [Was sollte passieren?]

   **Actual Behavior:**
   [Was passiert tatsächlich?]

   **Environment:**
   - OS: [macOS 14.1]
   - Python: [3.10.5]
   - AcademicAgent: [commit hash]
   ```

3. **Fix implementieren:**
   ```bash
   git checkout -b fix/issue-123
   # ... make changes ...
   pytest tests/unit/ -v
   git commit -m "fix: resolve issue #123"
   ```

4. **Add test:**
   ```python
   # tests/unit/test_bugfix.py
   def test_issue_123_fixed():
       """Test that issue #123 is resolved."""
       result = function_that_was_broken(...)
       assert result == expected_value
   ```

5. **Create PR** (siehe unten)

### ✨ New Features

**Wann:** Du möchtest neue Funktionalität hinzufügen.

**Prozess:**

1. **Diskutiere Feature:**
   - Erstelle ein **Discussion** (nicht Issue)
   - Beschreibe Use Case und Benefit
   - Warte auf Feedback von Maintainers

2. **Design:**
   - Überlege Architektur
   - Welche Komponenten betroffen?
   - Breaking Changes?

3. **Implementierung:**
   ```bash
   git checkout -b feature/awesome-feature
   # ... implement ...
   pytest tests/unit/ tests/integration/ -v
   ```

4. **Documentation:**
   - Update relevante Docs
   - Add docstrings
   - Add examples

5. **Create PR**

### 📚 Documentation

**Wann:** Du möchtest Dokumentation verbessern.

**Prozess:**

1. **Identify gap:**
   - Was fehlt?
   - Was ist unklar?
   - Was ist veraltet?

2. **Make changes:**
   ```bash
   git checkout -b docs/improve-setup-guide
   # Edit docs/...
   ```

3. **Preview:**
   - Markdown lokal rendern
   - Check Links
   - Check Formatting

4. **Create PR**

### 🗄️ New Database

**Wann:** Du möchtest Support für neue Datenbank hinzufügen.

**Siehe:** [Datenbanken hinzufügen](03-adding-databases.md)

**Checkliste:**
- [ ] Eintrag in `database_disciplines.yaml`
- [ ] Selektoren getestet
- [ ] Suchstring-Syntax dokumentiert
- [ ] Integration-Test geschrieben
- [ ] Dokumentation aktualisiert

---

## Code-Konventionen

### Python

**Style Guide:** [PEP 8](https://pep8.org/)

```python
# ✅ Good

def calculate_5d_score(candidate, config):
    """
    Calculate 5D score for a candidate paper.

    Args:
        candidate (dict): Paper metadata
        config (dict): Research configuration

    Returns:
        dict: {'score': float, 'breakdown': dict}
    """
    # Implementation...
    return {'score': total_score, 'breakdown': breakdown}

# ❌ Bad

def calc_score(c,cfg): # No docstring, unclear names
    s=0 # Unclear variable
    # ...
    return s
```

**Naming:**
- Functions: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Private: `_leading_underscore`

**Imports:**
```python
# Standard library first
import os
import sys
import json

# Third-party second
import requests
import pytest

# Local last
from scripts.cdp_wrapper import CDPClient
from scripts.scoring import calculate_5d_score
```

### Markdown

```markdown
# Headers haben Leerzeile davor und danach

## Zweite Ebene

Text mit **bold** und *italic*.

- Listen mit Leerzeile davor
- Item 2

Code blocks mit Language:

```python
def example():
    return True
```

Links: [Text](URL)
```

### Git Commits

**Format:** [Conventional Commits](https://www.conventionalcommits.org/)

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat:` - Neues Feature
- `fix:` - Bug Fix
- `docs:` - Dokumentation
- `test:` - Tests hinzufügen/ändern
- `refactor:` - Code-Refactoring
- `perf:` - Performance-Verbesserung
- `chore:` - Build/Tooling-Änderungen

**Examples:**
```bash
# Good commits:
git commit -m "feat(scoring): add journal impact factor to quality score"
git commit -m "fix(browser-agent): handle timeout in IEEE Xplore search"
git commit -m "docs(user-guide): add troubleshooting section for VPN issues"
git commit -m "test(action-gate): add tests for privilege escalation blocking"

# Bad commits:
git commit -m "fixed stuff"
git commit -m "update"
git commit -m "wip"
```

---

## Pull Request Process

### 1. Vorbereitung

```bash
# Ensure up-to-date
git fetch upstream
git rebase upstream/main

# Run tests
pytest tests/unit/ tests/integration/ -v

# Check for secrets
bash scripts/setup_git_hooks.sh --check-only

# Run linting (if configured)
pylint scripts/*.py
```

### 2. PR erstellen

**Title:** Folgt Commit-Convention

```
feat(scoring): add H-Index to journal quality scoring
fix(browser-agent): handle CAPTCHA detection properly
docs(developer-guide): add section on testing strategies
```

**Description-Template:**

```markdown
## Description

[Clear description of what this PR does]

## Motivation

[Why is this change needed? What problem does it solve?]

## Changes

- [Change 1]
- [Change 2]
- [Change 3]

## Testing

- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing performed

**Test Results:**
```
[Paste test output]
```

## Checklist

- [ ] Code follows project conventions
- [ ] Tests pass locally
- [ ] Documentation updated
- [ ] No secrets in code
- [ ] Commits follow Conventional Commits

## Related Issues

Closes #123
Related to #456

## Screenshots (if applicable)

[Add screenshots for UI changes]
```

### 3. Review-Prozess

**Reviewer werden:**
- Code-Qualität prüfen
- Tests ausreichend?
- Dokumentation vorhanden?
- Sicherheitsaspekte beachtet?

**Feedback einarbeiten:**
```bash
# Make changes based on review
# ...

# Amend or create new commit
git add .
git commit -m "refactor: address review comments"

# Push to update PR
git push origin feature/my-feature
```

### 4. Merge

Nach Approval:
- Maintainer mergt PR
- Branch wird automatisch gelöscht
- Du wirst als Contributor gelistet!

---

## Testing-Richtlinien

### Unit Tests erforderlich für:

- ✅ Alle neuen Funktionen
- ✅ Alle Bug Fixes
- ✅ Alle Refactorings

**Coverage-Ziel:** Min. 80% für neuen Code

```python
# Für jede neue Funktion:
def new_function(param):
    """Function doing something."""
    # implementation...

# Schreibe mindestens:
def test_new_function_happy_path():
    """Test successful case."""
    result = new_function(valid_input)
    assert result == expected_output

def test_new_function_error_case():
    """Test error handling."""
    with pytest.raises(ExpectedError):
        new_function(invalid_input)
```

### Integration Tests für:

- ✅ Neue Datenbanken
- ✅ Agent-Interaktionen
- ✅ CDP-Operationen
- ✅ State-Management

---

## Review-Guidelines

### Als Reviewer

**Was zu prüfen:**

1. **Funktionalität:**
   - Löst der Code das Problem?
   - Edge Cases behandelt?

2. **Code-Qualität:**
   - Lesbar und wartbar?
   - Folgt Konventionen?
   - Keine Duplikation?

3. **Tests:**
   - Ausreichende Coverage?
   - Tests sinnvoll?
   - Tests laufen durch?

4. **Sicherheit:**
   - Input-Validierung?
   - Keine Secrets?
   - Action-Gate verwendet?

5. **Dokumentation:**
   - Docstrings vorhanden?
   - Docs aktualisiert?
   - Beispiele hilfreich?

**Feedback geben:**

✅ **Konstruktiv:**
```
Suggestion: Consider using a dictionary here instead of multiple
if-statements. This would be more maintainable and easier to extend.

Example:
```python
handlers = {
    'type_a': handle_a,
    'type_b': handle_b,
}
result = handlers.get(type, default_handler)()
```
```

❌ **Nicht konstruktiv:**
```
This code is bad. Rewrite it.
```

### Als Author

**Wie auf Feedback reagieren:**

✅ **Gut:**
```
Thanks for the suggestion! I've refactored to use a dictionary.
See commit abc123.
```

```
Good point about the edge case. I've added a test and fixed the
issue. See test_edge_case() in commit def456.
```

❌ **Nicht gut:**
```
It works fine, I don't see the problem.
```

---

## Community-Standards

### Code of Conduct

Wir erwarten:

- 🤝 **Respektvoller Umgang** mit allen Contributors
- 💬 **Konstruktives Feedback** ohne persönliche Angriffe
- 🌍 **Inklusivität** unabhängig von Background
- 🎓 **Geduld** mit Anfängern
- 🔍 **Fokus auf technische Qualität** statt persönliche Präferenzen

### Communication

**GitHub Issues:**
- Für Bugs, Feature Requests
- Nutze Templates
- Suche erst nach Duplikaten

**GitHub Discussions:**
- Für Fragen, Ideas, Feedback
- Offene Diskussionen
- Hilfe für andere

**Pull Requests:**
- Klar beschrieben
- Fokussiert (eine Sache pro PR)
- Gute Commit-Messages

---

## Getting Help

### Ich habe eine Frage

1. **Suche erst:**
   - README.md
   - Docs
   - Existing Issues/Discussions

2. **Frage dann:**
   - GitHub Discussions für allgemeine Fragen
   - Issues nur für konkrete Bugs

### Ich bin stuck mit meiner Contribution

1. **WIP-PR erstellen:**
   - Titel mit `[WIP]` prefix
   - Beschreibe wo du steckst
   - Frage nach Hilfe

2. **Ping Maintainers:**
   - In PR-Kommentar: `@maintainer-username`
   - Beschreibe spezifisches Problem

---

## Recognition

### Contributors werden gelistet

- ✅ Im README
- ✅ In Release Notes
- ✅ Als GitHub Contributor

### Bedeutende Contributions

- 🌟 Mention in Release Notes
- 🎉 Twitter/Blog Shoutout
- 🏆 "Top Contributor" Badge

---

## Checkliste: PR-Ready

Vor dem PR-Submit:

- [ ] Code folgt Konventionen
- [ ] Tests geschrieben und passing
- [ ] Documentation aktualisiert
- [ ] Keine Secrets im Code
- [ ] Commits folgen Conventional Commits
- [ ] Branch ist up-to-date mit main
- [ ] PR-Description vollständig
- [ ] Linting passed (falls configured)
- [ ] Self-review durchgeführt

---

## Resources

### Dokumentation

- [User Guide](../user-guide/README.md)
- [Developer Guide](README.md)
- [API Reference](../api-reference/README.md)
- [Architecture](01-architecture.md)
- [Security](05-security.md)

### External

- [PEP 8 Style Guide](https://pep8.org/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [GitHub Flow](https://guides.github.com/introduction/flow/)

---

**Danke für deine Contribution! 🎉**

Jeder Beitrag, ob groß oder klein, hilft AcademicAgent besser zu werden.

**[← Zurück zum Developer Guide](README.md)**
