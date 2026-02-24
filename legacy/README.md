# Legacy Files - Academic Agent v1.0

**v1.0 Multi-Agent System - Archived for v2.0 Development**

**Moved to legacy:** 2026-02-23
**Academic Agent Version:** v1.0 (v4.1)
**Reason:** v2.0 Linear Coordinator Architecture (Szenario B)

---

## 🚫 Why v1.0 was archived

v1.0 had fundamental architecture issues that could not be fixed incrementally:

| Problem | Impact | v2.0 Solution |
|---------|--------|---------------|
| Multi-Agent Coordination | 40% spawn failures | 1 Linear Coordinator (no spawning) |
| Success Rate | 60% (6.3/10) | 85-92% target |
| Manual Interventions | 4x per run | 0-1x per run |
| Cost | $2.15 per run | $0.27 per run (-87%) |
| PDF Downloads | 17% success | 75-85% target |

**Conclusion:** Complete rewrite (v2.0) was more viable than fixing v1.0.

---

## 📁 Contents

This folder contains all files from the v1.0 system:

### v1.0 Documentation (NEW - 2026-02-23)
- `POST_MORTEM.md` - v1.0 failure analysis
- `PHASE4_SUMMARY.md` - v1.0 Phase 4 results
- `SUMMARY.md` - v1.0 overall summary
- `TECHNICAL_DETAILS_Part1.md`, `Part2.md`, `Part3.md` - v1.0 technical docs
- `TEST_RUN_*.md` - v1.0 test run reports
- `V2_ARCHITECTURE_ANALYSIS.md` - Architecture analysis that led to v2.0
- `V2_ARCHITECTURE_OPTION_C.md` - Option C (Linear Coordinator) analysis
- `ANTHROPIC_BEST_PRACTICES_SUMMARY.md` - Best practices from v1.0

### Original Documentation
- `README.md` (original) - See Academic Agent original docs
- `CHANGELOG.md` - Version history
- `SECURITY.md` - Security guidelines
- `LICENSE` - MIT License
- `PROBLEMS.md` - Known issues
- `PROMPT_QUALITY_ASSESSMENT.md` - Prompt analysis
- `REFACTORING_SUMUP.md` - Refactoring notes
- `CRITICAL_FIXES_2026-02-22.md` - Critical fixes

### Source Code
- `scripts/` - Agent scripts (50 files)
- `shared/` - Shared utilities
- `config/` - Configuration files
- `schemas/` - JSON schemas
- `tests/` - Test files

### Development Environment
- `.venv/` - Python virtual environment
- `node_modules/` - Node.js dependencies
- `.pytest_cache/` - Test cache
- `.github/` - GitHub workflows
- `.claude/` - Claude settings
- `.env.example` - Environment template
- `setup.sh` - Setup script
- `requirements.txt` - Python dependencies
- `package.json` - Node.js dependencies

### Test Run Data
- `01 TEST_RUN/` - Original test run folder (all files)
  - Complete logs, metadata, PDFs
  - See parent directory for curated key files

### Build/Runtime
- `runs/` - Runtime data
- `docs/` - Documentation

---

## ⚠️ Important Notes

**Why were these files moved?**
- To create a clean, focused root directory
- Key test run results are now easily accessible in root
- Legacy files preserved for reference and development

**When to use these files:**
- Development: Use `scripts/`, `shared/`, `config/`
- Setup: Use `setup.sh`, `requirements.txt`, `.env.example`
- Full test run data: Use `01 TEST_RUN/`
- Historical context: Use documentation files

**Current work (v2.0):**
All active development now happens with v2.0 architecture:
- `../V2_ROADMAP.md` - Complete v2.0 roadmap (Szenario B)
- `../MODULE_TYPES_OVERVIEW.md` - Hybrid architecture (3 Haiku + 10 Python modules)
- `../TEST_MODELS_INSTRUCTIONS.md` - Model testing guide
- `../test_claude_models.py` - Model test script

---

## 🔄 Restoration

To restore original structure:
```bash
# Move all legacy files back to root
mv legacy/* .
mv legacy/.* . 2>/dev/null || true
rmdir legacy
```

## ✅ What to keep from v1.0

**DO NOT DELETE v1.0 Code!** These components will be migrated to v2.0:

- ✅ **5D-Scoring Logic** (`scripts/create_quote_library_with_citations.py`) - Proven algorithm
- ✅ **Quote-Extraction Logic** - LLM-based extraction works well
- ✅ **JSON Schemas** (`schemas/`) - Data models still valid
- ✅ **PDF-Parsing** (PyMuPDF) - Keep as-is
- ✅ **Lessons Learned** - What NOT to do in v2.0

---

**v1.0 Archived:** 2026-02-23
**v2.0 Started:** 2026-02-23
**Status:** v2.0 Phase 0 (Foundation) - In Progress
