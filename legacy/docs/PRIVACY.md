# 🔒 Datenschutzrichtlinie - AcademicAgent

**Zuletzt aktualisiert:** 2026-02-22
**Wirksamkeitsdatum:** 2026-02-22

---

## Zusammenfassung

AcademicAgent ist ein **local-first, datenschutzfreundliches** Recherche-Tool. Alle Daten bleiben auf deinem Rechner. Keine Telemetrie, keine Cloud-Synchronisation, kein Tracking.

---

## 1. Datenerfassung

### 1.1 Welche Daten wir erfassen

**Lokal gespeicherte Daten:**
- Research configurations (Markdown files in `config/`)
- Downloaded PDFs (`runs/[timestamp]/downloads/`)
- Extracted citations and quotes (`runs/[timestamp]/outputs/`)
- Search metadata and state files (`runs/[timestamp]/metadata/`)
- Execution logs (`runs/[timestamp]/logs/`)

**Wir erfassen NICHT:**
- ❌ Personenbezogene Daten (PII)
- ❌ Nutzungstelemetrie
- ❌ Analysedaten
- ❌ Absturzberichte (außer manuell eingereicht)
- ❌ Login-Zugangsdaten (werden vom Browser verwaltet, nie von Agents abgerufen)

### 1.2 Wo Daten gespeichert werden

Alle Daten werden **lokal auf deinem Rechner** gespeichert:
- **Speicherort:** `~/[ProjectDirectory]/runs/`
- **Aufbewahrung:** Benutzergesteuert (keine automatische Löschung)
- **Zugriff:** Nur du und der Claude-Agent (während Recherche-Sitzungen)

---

## 2. Datenweitergabe an Dritte

### 2.1 Externe Dienste, mit denen wir interagieren

| Dienst | Geteilte Daten | Zweck | Opt-Out |
|---------|-------------|---------|---------|
| **DBIS Portal** | Navigationsverhalten, Suchanfragen | Datenbank-Erkennung | Kein Opt-Out möglich (für Funktionalität erforderlich) |
| **Akademische Datenbanken** | Suchstrings, Download-Anfragen | Paper-Abruf | Kein Opt-Out möglich (für Funktionalität erforderlich) |
| **Claude API (Anthropic)** | Agent-Prompts, Dateiinhalte | LLM-Inferenz | Kein Opt-Out möglich (Kernfunktionalität) |
| **Chrome Browser** | Besuchte URLs, Cookies (nur Session) | Browser-Automatisierung via CDP | Kein Opt-Out möglich (für Funktionalität erforderlich) |

### 2.2 Was wir NICHT teilen

- ❌ Deine Recherche-Konfigurationen
- ❌ Heruntergeladene PDFs (bleiben auf deinem Rechner)
- ❌ Extrahierte Zitate und Quellenangaben
- ❌ Universitäts-Zugangsdaten (werden im Browser verwaltet, nicht von Agents)
- ❌ IP-Adresse oder Geräte-Identifier (außer dem, was dein Browser natürlicherweise sendet)

---

## 3. Claude API (Anthropic) Datenhandhabung

### 3.1 Was an die Claude API gesendet wird

Wenn Agents ausgeführt werden, werden folgende Daten an Anthropics Claude API gesendet:
- Agent-System-Prompts (Anweisungen)
- Recherche-Konfiguration (Keywords, Forschungsfrage)
- Webseiteninhalte (bereinigtes HTML aus akademischen Datenbanken)
- PDF-Textauszüge (für Zitat-Extraktion)
- Dateipfade und Metadaten (für Dateioperationen)

### 3.2 Anthropics Datenrichtlinie

Gemäß Anthropics [Commercial Terms](https://www.anthropic.com/legal/commercial-terms):
- ✅ Deine Daten werden **nicht zum Trainieren von Modellen verwendet** (bei API-Nutzung)
- ✅ Daten sind **während der Übertragung verschlüsselt** (HTTPS/TLS)
- ✅ Anthropic speichert Prompts für **Trust & Safety** (30 Tage, dann gelöscht)
- ✅ Du kannst Datenlöschung über Anthropic-Support anfordern

**Wichtig:** Überprüfe [Anthropics Datenschutzrichtlinie](https://www.anthropic.com/legal/privacy) für vollständige Details.

---

## 4. Datensicherheit

### 4.1 Verschlüsselung

**Während der Übertragung:**
- ✅ Alle API-Aufrufe an Claude sind verschlüsselt (HTTPS/TLS 1.3)
- ✅ Datenbankverbindungen nutzen HTTPS (wenn verfügbar)

**Im Ruhezustand:**
- ⚠️ **Standardmäßig werden Dateien in Klartext gespeichert** auf deiner lokalen Festplatte
- ✅ **EMPFOHLEN:** Aktiviere Festplattenverschlüsselung (FileVault auf macOS, LUKS auf Linux)

**Verschlüsselung aktivieren:**

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

### 4.2 Zugriffskontrollen

- ✅ **Dateisystem-Berechtigungen:** Agents können nur in `runs/**`-Verzeichnis schreiben
- ✅ **Secrets-Schutz:** `.env`, `~/.ssh/`, `secrets/` sind blockiert
- ✅ **Netzwerk-Beschränkungen:** Nur akademische Domains sind gelistet

### 4.3 Log-Redaktion

**Automatische PII/Secret-Redaktion:**

Alle Logs (`runs/[timestamp]/logs/*.log`) schwärzen automatisch sensible Daten **bevor** sie auf Festplatte geschrieben werden:

| Muster | Redaktion | Beispiel |
| ------- | --------- | -------- |
| API Keys (sk-, AKIA, AIza) | `[REDACTED_API_KEY]` | `sk-abc123...` → `[REDACTED_API_KEY]` |
| Session-Tokens | `[REDACTED_TOKEN]` | `session_token: xyz...` → `[REDACTED_TOKEN]` |
| Private-Key-Blöcke | `[REDACTED_PRIVATE_KEY]` | `-----BEGIN PRIVATE KEY-----` → entfernt |
| E-Mail-Adressen | Teilweise maskiert | `user@example.com` → `us***@example.com` |
| Passwort-Felder (JSON) | `[REDACTED]` | `{"password": "..."}` → `{"password": "[REDACTED]"}` |

**Implementierung:** `scripts/logger.py::redact_sensitive()`
**Tests:** `tests/unit/test_logger_redaction.py`

**Wichtige Hinweise:**

- ✅ Redaktion ist **automatisch** (keine Konfiguration nötig)
- ✅ Redaktion ist **standardmäßig sicher** (stürzt Logging nie ab)
- ⚠️ Redaktion ist **musterbasiert** (nicht KI-gestützt; Grenzfälle können durchrutschen)
- ⚠️ **Logs sicher sichern/archivieren** (Redaktion erfolgt nur beim Schreiben)

**Manuelle Log-Überprüfung:**

Falls du vermutest, dass Logs sensible Daten enthalten:

```bash
# Search for potential secrets in logs
grep -r "sk-\|AKIA\|password" runs/*/logs/

# Delete sensitive logs
rm runs/[timestamp]/logs/phase_*.log
```

**Aufbewahrungsrichtlinie:**

- Logs werden standardmäßig **unbegrenzt** aufbewahrt (benutzergesteuert)
- **Empfohlen:** Lösche Logs älter als 30 Tage

```bash
find runs/ -name "*.log" -mtime +30 -delete
```

---

## 5. Datenspeicherung

### 5.1 Wie lange Daten aufbewahrt werden

**Auf deinem Rechner:**
- **Standard:** Für immer (bis du sie manuell löschst)
- **Deine Kontrolle:** Lösche jeden `runs/[timestamp]`-Ordner jederzeit

**In der Claude API (Anthropic):**
- **Prompts:** 30 Tage (dann gelöscht)
- **Modell-Ausgaben:** 30 Tage (dann gelöscht)

### 5.2 Datenlöschung

**Lösche eine bestimmte Recherche:**
```bash
rm -rf runs/2026-02-18_14-30-00
```

**Lösche alle Recherche-Daten:**
```bash
rm -rf runs/*
```

**Lösche alles (inkl. Konfigurationen):**
```bash
rm -rf runs/ config/ logs/
```

---

## 6. Rechtliche Compliance

### 6.1 GDPR (EU-Datenschutz-Grundverordnung)

**Anwendbarkeit:** Wenn du in der EU bist oder Daten von EU-Bürgern verarbeitest.

**Compliance-Status:**
- ✅ **Artikel 5 (Datenminimierung):** Wir erfassen nur notwendige Recherche-Daten
- ✅ **Artikel 25 (Privacy by Design):** Local-first-Architektur, keine Cloud-Synchronisation
- ✅ **Artikel 32 (Sicherheit):** Verschlüsselung im Ruhezustand empfohlen, bei Übertragung erzwungen
- ⚠️ **Artikel 17 (Recht auf Löschung):** Du kontrollierst die Löschung (lokale Dateien)
- ⚠️ **Artikel 15 (Auskunftsrecht):** Anthropic verwaltet Claude-API-Daten (30 Tage)

**Für Anthropic-API-Datenanfragen:** Kontaktiere Anthropic-Support (privacy@anthropic.com)

### 6.2 ISO 27001

**Anwendbare Controls:**
- ✅ **A.8.2.3 (Umgang mit Assets):** Sichere Speicherung im `runs/`-Verzeichnis
- ✅ **A.9.4.1 (Informationszugriffsbeschränkung):** Minimale Berechtigungen für Agents
- ✅ **A.10.1.1 (Kryptografische Controls):** HTTPS/TLS für API-Aufrufe
- ⚠️ **A.8.3.1 (Verwaltung von Wechselmedien):** Benutzerverantwortung für Backups

### 6.3 Universitäts-Compliance

**Bei Verwendung für Abschlussarbeit/Dissertation:**
- ✅ **Forschungsdaten-Eigentum:** Du besitzt alle heruntergeladenen PDFs und Quellenangaben
- ✅ **Zitat-Integrität:** Alle Zitate enthalten Quellen-Metadaten
- ⚠️ **Plagiatsprüfungs-Tools:** Stelle sicher, dass deine Institution KI-gestützte Recherche-Tools akzeptiert

**Empfehlung:** Kläre vor Nutzung mit der Forschungsethik-Kommission deiner Universität ab.

---

## 7. Nutzerrechte

### 7.1 Deine Rechte

Du hast das Recht auf:
- ✅ **Zugang:** Alle gespeicherten Daten einsehen (`runs/`, `config/`, `logs/`)
- ✅ **Berichtigung:** Alle Recherche-Daten bearbeiten oder korrigieren
- ✅ **Löschung:** Alle oder einzelne Recherche-Daten löschen
- ✅ **Datenübertragbarkeit:** Daten exportieren (JSON, BibTeX-Formate)
- ✅ **Widerspruch:** Tool jederzeit nicht mehr verwenden

### 7.2 Ausübung deiner Rechte

Da Daten lokal gespeichert werden, kannst du diese Rechte direkt ausüben:

**Alle Daten einsehen:**
```bash
ls -R runs/
```

**Zitate exportieren:**
```bash
cp runs/[timestamp]/outputs/bibliography.bib ~/Desktop/
```

**Alles löschen:**
```bash
rm -rf runs/ config/ logs/
```

## 9. Änderungen an dieser Richtlinie

**Aktualisierungsfrequenz:** Diese Richtlinie wird vierteljährlich überprüft.

**Benachrichtigung:** Aktualisierungen werden dokumentiert in:
- Dieser Datei (mit Versionsnummer und Datum)
- GitHub-Commit-Nachrichten
- ~~CHANGELOG.md~~ (wenn erstellt)

**Deine Verantwortung:** Überprüfe diese Datei regelmäßig auf Änderungen.

---

## 11. Zusammenfassung (TL;DR)

✅ **Local-first:** Alle deine Daten bleiben auf deinem Rechner
✅ **Keine Telemetrie:** Wir tracken dich nicht
✅ **Claude API:** Prompts an Anthropic gesendet (nach 30 Tagen gelöscht)
✅ **Verschlüsselung:** Nutze FileVault/LUKS (empfohlen)
✅ **Deine Kontrolle:** Lösche Daten jederzeit mit `rm -rf runs/*`


---

**Letztes Prüfdatum:** 2026-02-22
**Nächstes Prüfdatum:** 2026-05-22 (vierteljährlich)
