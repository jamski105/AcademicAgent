# 🔒 Privacy Policy - AcademicAgent

**Version:** 3.2
**Last Updated:** 2026-02-20
**Effective Date:** 2026-02-20

---

## Zusammenfassung

AcademicAgent is a **local-first, privacy-preserving** research tool. All data remains on your machine. No telemetry, no cloud sync, no tracking.

---

## 1. Datenerfassung

### 1.1 What Data We Collect

**Locally Stored Data:**
- Research configurations (Markdown files in `config/`)
- Downloaded PDFs (`runs/[timestamp]/downloads/`)
- Extracted citations and quotes (`runs/[timestamp]/outputs/`)
- Search metadata and state files (`runs/[timestamp]/metadata/`)
- Execution logs (`runs/[timestamp]/logs/`)

**We DO NOT collect:**
- ❌ Personal identifiable information (PII)
- ❌ Usage telemetry
- ❌ Analytics data
- ❌ Crash reports (unless manually submitted)
- ❌ Login credentials (handled by browser, never accessed by agents)

### 1.2 Where Data Is Stored

All data is stored **locally on your machine**:
- **Location:** `~/[ProjectDirectory]/runs/`
- **Retention:** User-controlled (no automatic deletion)
- **Access:** Only you and the Claude agent (during research sessions)

---

## 2. Datenweitergabe an Dritte

### 2.1 External Services We Interact With

| Service | Data Shared | Purpose | Opt-Out |
|---------|-------------|---------|---------|
| **DBIS Portal** | Navigation behavior, search queries | Database discovery | Cannot opt-out (required for functionality) |
| **Academic Databases** | Search strings, download requests | Paper retrieval | Cannot opt-out (required for functionality) |
| **Claude API (Anthropic)** | Agent prompts, file contents | LLM inference | Cannot opt-out (core functionality) |
| **Chrome Browser** | URLs visited, cookies (session-only) | Browser automation via CDP | Cannot opt-out (required for functionality) |

### 2.2 What We DO NOT Share

- ❌ Your research configurations
- ❌ Downloaded PDFs (stay on your machine)
- ❌ Extracted quotes and citations
- ❌ University credentials (handled in-browser, not by agents)
- ❌ IP address or device identifiers (beyond what your browser naturally sends)

---

## 3. Claude API (Anthropic) Data Handling

### 3.1 What Gets Sent to Claude API

When agents execute, the following data is sent to Anthropic's Claude API:
- Agent system prompts (instructions)
- Research configuration (keywords, research question)
- Web page content (sanitized HTML from academic databases)
- PDF text extracts (for citation extraction)
- File paths and metadata (for file operations)

### 3.2 Anthropic's Data Policy

According to Anthropic's [Commercial Terms](https://www.anthropic.com/legal/commercial-terms):
- ✅ Your data is **not used to train models** (for API usage)
- ✅ Data is **encrypted in transit** (HTTPS/TLS)
- ✅ Anthropic retains prompts for **trust & safety** (30 days, then deleted)
- ✅ You can request data deletion via Anthropic support

**Important:** Review [Anthropic's Privacy Policy](https://www.anthropic.com/legal/privacy) for full details.

---

## 4. Datensicherheit

### 4.1 Encryption

**In Transit:**
- ✅ All API calls to Claude are encrypted (HTTPS/TLS 1.3)
- ✅ Database connections use HTTPS (when available)

**At Rest:**
- ⚠️ **By default, files are stored in plaintext** on your local disk
- ✅ **RECOMMENDED:** Enable disk encryption (FileVault on macOS, LUKS on Linux)

**To enable encryption:**

**macOS:**
```bash
# System Settings → Privacy & Security → FileVault → Turn On
```

**Linux:**
```bash
# Check if LUKS is enabled:
lsblk -o NAME,SIZE,FSTYPE,MOUNTPOINT
# Should show "crypto_LUKS"
```

### 4.2 Access Controls

- ✅ **File system permissions:** Agents can only write to `runs/**` directory
- ✅ **Secret protection:** `.env`, `~/.ssh/`, `secrets/` are blocked
- ✅ **Network restrictions:** Only academic domains whitelisted

### 4.3 Log Redaction (NEW in v3.2)

**Automatic PII/Secret Redaction:**

All logs (`runs/[timestamp]/logs/*.log`) automatically redact sensitive data **before** writing to disk:

| Pattern | Redaction | Example |
| ------- | --------- | ------- |
| API Keys (sk-, AKIA, AIza) | `[REDACTED_API_KEY]` | `sk-abc123...` → `[REDACTED_API_KEY]` |
| Session tokens | `[REDACTED_TOKEN]` | `session_token: xyz...` → `[REDACTED_TOKEN]` |
| Private key blocks | `[REDACTED_PRIVATE_KEY]` | `-----BEGIN PRIVATE KEY-----` → removed |
| Email addresses | Partial mask | `user@example.com` → `us***@example.com` |
| Password fields (JSON) | `[REDACTED]` | `{"password": "..."}` → `{"password": "[REDACTED]"}` |

**Implementation:** `scripts/logger.py::redact_sensitive()`
**Tests:** `tests/unit/test_logger_redaction.py`

**Important Notes:**

- ✅ Redaction is **automatic** (no configuration needed)
- ✅ Redaction is **safe by default** (never crashes logging)
- ⚠️ Redaction is **pattern-based** (not AI-powered; edge cases may leak)
- ⚠️ **Backup/archive logs securely** (redaction happens only at write time)

**Manual Log Review:**

If you suspect logs contain sensitive data (e.g., pre-v3.2 logs):

```bash
# Search for potential secrets in logs
grep -r "sk-\|AKIA\|password" runs/*/logs/

# Delete sensitive logs
rm runs/[timestamp]/logs/phase_*.log
```

**Retention Policy:**

- Logs are kept **indefinitely** by default (user-controlled)
- **Recommended:** Delete logs older than 30 days

```bash
find runs/ -name "*.log" -mtime +30 -delete
```

---

## 5. Datenspeicherung

### 5.1 How Long Data Is Kept

**On Your Machine:**
- **Default:** Forever (until you manually delete)
- **Your Control:** Delete any `runs/[timestamp]` folder at any time

**In Claude API (Anthropic):**
- **Prompts:** 30 days (then deleted)
- **Model outputs:** 30 days (then deleted)

### 5.2 Data Deletion

**Delete a specific research run:**
```bash
rm -rf runs/2026-02-18_14-30-00
```

**Delete all research data:**
```bash
rm -rf runs/*
```

**Delete everything (including configs):**
```bash
rm -rf runs/ config/ logs/
```

---

## 6. Rechtliche Compliance

### 6.1 GDPR (EU General Data Protection Regulation)

**Applicability:** If you are in the EU or process EU citizens' data.

**Compliance Status:**
- ✅ **Article 5 (Data Minimization):** We only collect necessary research data
- ✅ **Article 25 (Privacy by Design):** Local-first architecture, no cloud sync
- ✅ **Article 32 (Security):** Encryption at rest recommended, in-transit enforced
- ⚠️ **Article 17 (Right to Erasure):** You control deletion (local files)
- ⚠️ **Article 15 (Right to Access):** Anthropic handles Claude API data (30 days)

**For Anthropic API data requests:** Contact Anthropic support (privacy@anthropic.com)

### 6.2 ISO 27001

**Applicable Controls:**
- ✅ **A.8.2.3 (Handling of Assets):** Secure storage in `runs/` directory
- ✅ **A.9.4.1 (Information Access Restriction):** Least privilege for agents
- ✅ **A.10.1.1 (Cryptographic Controls):** HTTPS/TLS for API calls
- ⚠️ **A.8.3.1 (Management of Removable Media):** User responsibility for backups

### 6.3 University Compliance

**If using for thesis/dissertation:**
- ✅ **Research data ownership:** You own all downloaded PDFs and citations
- ✅ **Citation integrity:** All citations include source metadata
- ⚠️ **Plagiarism tools:** Ensure your institution accepts AI-assisted research tools

**Recommendation:** Check with your university's research ethics board before use.

---

## 7. Nutzerrechte

### 7.1 Your Rights

You have the right to:
- ✅ **Access:** View all stored data (`runs/`, `config/`, `logs/`)
- ✅ **Rectification:** Edit or correct any research data
- ✅ **Erasure:** Delete any or all research data
- ✅ **Data Portability:** Export data (JSON, BibTeX formats)
- ✅ **Object:** Stop using the tool at any time

### 7.2 Exercising Your Rights

Since data is stored locally, you can exercise these rights directly:

**View all data:**
```bash
ls -R runs/
```

**Export citations:**
```bash
cp runs/[timestamp]/outputs/bibliography.bib ~/Desktop/
```

**Delete everything:**
```bash
rm -rf runs/ config/ logs/
```

---

## 8. Datenschutz für Kinder

AcademicAgent is **not intended for users under 13 years old**. We do not knowingly collect data from children.

If you believe a child has used this tool, delete all research data:
```bash
rm -rf runs/*
```

---

## 9. Änderungen an dieser Richtlinie

**Update Frequency:** This policy is reviewed quarterly.

**Notification:** Updates will be documented in:
- This file (with version number and date)
- GitHub commit messages
- ~~CHANGELOG.md~~ (when created)

**Your Responsibility:** Check this file periodically for changes.

---

## 10. Kontakt & Fragen

**For privacy questions:**
- **GitHub Issues:** [Report privacy concerns](https://github.com/jamski105/AcademicAgent/issues) (public)
- **Email:** your-email@example.com (private)

**For Claude API data questions:**
- **Anthropic Support:** privacy@anthropic.com
- **Anthropic Privacy Policy:** https://www.anthropic.com/legal/privacy

---

## 11. Summary (TL;DR)

✅ **Local-first:** All your data stays on your machine
✅ **No telemetry:** We don't track you
✅ **Claude API:** Prompts sent to Anthropic (deleted after 30 days)
✅ **Encryption:** Use FileVault/LUKS (recommended)
✅ **Your control:** Delete data anytime with `rm -rf runs/*`

**Questions?** Open an issue or email your-email@example.com

---

**Last Review Date:** 2026-02-20
**Next Review Date:** 2026-05-20 (quarterly)
