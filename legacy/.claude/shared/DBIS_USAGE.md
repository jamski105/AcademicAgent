# DBIS Usage Guide (für Agents)

**Zweck:** Zentrale Dokumentation für DBIS-Integration in allen Agents

---

## 1. Was ist DBIS?

**DBIS (Database Information System)** ist ein zentraler Katalog wissenschaftlicher Datenbanken.

**Warum DBIS nutzen?**
- ✅ Zentraler Zugang zu 500+ Datenbanken
- ✅ Uni-Lizenz-Authentifizierung automatisch
- ✅ Keine individuelle Login-Verwaltung
- ✅ Legaler Zugang zu kostenpflichtigen Ressourcen

---

## 2. DBIS URLs

### Standard-URLs

```
Homepage:     https://dbis.ur.de
TIB-Zugang:   https://dbis.ur.de/UBTIB
Suche:        https://dbis.ur.de/UBTIB/suche
```

### Such-URLs (für WebFetch/Browser)

```
# Keyword-Suche
https://dbis.ur.de/UBTIB/suche?q={keywords}

# Fachgebiets-Suche
https://dbis.ur.de/UBTIB/fachgebiet/{disziplin}

# Beispiele
https://dbis.ur.de/UBTIB/suche?q=machine+learning
https://dbis.ur.de/UBTIB/fachgebiet/Informatik
```

---

## 3. DBIS-Proxy-Regel (KRITISCH für alle Agents)

**MANDATORY RULE:** Alle Datenbankzugriffe MÜSSEN über DBIS erfolgen!

### Warum Proxy-Modus?

1. **Uni-Lizenz-Compliance** - Direkter Zugriff umgeht Lizenzierung
2. **Automatische Authentifizierung** - DBIS übernimmt Login
3. **Legaler Zugang** - Verhindert unerlaubte Zugriffe
4. **Keine Whitelists** - Ein Einstiegspunkt für 500+ DBs

### DBIS-Proxy Workflow

```
RICHTIG:
User → DBIS → IEEE Xplore → Paper
       ✅ Uni-Lizenz aktiv

FALSCH:
User → IEEE Xplore direkt → Paywall
       ❌ Keine Lizenz
```

---

## 4. Domain-Validierung (für browser-agent)

### Erlaubte Domains

```bash
# 1. Start IMMER bei DBIS
if [ "$FIRST_NAVIGATION" = true ]; then
  if [[ "$URL" != *"dbis.ur.de"* ]] && [[ "$URL" != *"dbis.de"* ]]; then
    ERROR: "Navigation muss bei DBIS starten"
    exit 1
  fi
fi

# 2. Nach DBIS-Start: Alle Weiterleitungen erlaubt
# DBIS leitet zu lizenzierten Datenbanken weiter → OK

# 3. DOI-Resolver immer erlaubt
if [[ "$URL" == *"doi.org"* ]]; then
  ALLOWED
fi
```

### Blockierte Domains

```bash
# ❌ NIEMALS erlaubt
- sci-hub.* (Piratenseite)
- libgen.* (Piratenseite)
- z-lib.org (Piratenseite)

# ❌ Direkte Datenbank-Navigation (ohne DBIS)
# Nur wenn NICHT von DBIS weitergeleitet
```

### Session-Tracking

```python
# Tracke DBIS-Session in session.json
{
  "started_at_dbis": true,
  "dbis_session_id": "abc123",
  "allowed_redirects": [
    "ieeexplore.ieee.org",  # Von DBIS weitergeleitet
    "link.springer.com"      # Von DBIS weitergeleitet
  ]
}

# Validierung vor jeder Navigation
if url.domain not in session.allowed_redirects:
  if not came_from_dbis(url):
    BLOCK
```

---

## 5. DBIS Zugangsampel-System

DBIS zeigt Zugriffsstatus pro Datenbank:

| Symbol | Bedeutung | Aktion |
|--------|-----------|--------|
| 🟢 **Grün** | Vollzugriff (Uni-Lizenz) | ✅ Nutzen |
| 🟡 **Gelb** | Teilzugriff (manche Journals frei) | ⚠️ Prüfen ob Artikel verfügbar |
| 🔴 **Rot** | Kein Zugriff | ❌ Überspringen |
| 🟦 **Frei** | Open Access | ✅ Nutzen |

**Agent-Verhalten:**
```python
if access_status == "green" or access_status == "free":
    USE_DATABASE
elif access_status == "yellow":
    TRY_AND_CHECK_PAYWALLS
elif access_status == "red":
    SKIP_DATABASE
```

---

## 6. DBIS Discovery Workflow (für setup-agent)

### Schritt 1: Query-Konstruktion

```python
# Aus user research question extrahieren
keywords = extract_keywords(research_question)
discipline = extract_discipline(academic_context)

# DBIS-Query bauen
query = f"{' '.join(keywords)} {discipline}"
url = f"https://dbis.ur.de/UBTIB/suche?q={urllib.parse.quote(query)}"
```

### Schritt 2: DBIS-Suche ausführen

```python
# Via WebFetch
result = WebFetch(url, prompt="""
Extrahiere von dieser DBIS-Suchergebnisseite:
1. Datenbank-Namen
2. Beschreibungen
3. Zugangsinfo (grün/gelb/rot/frei)
4. DBIS-IDs (aus Links)

Return JSON array.
""")
```

### Schritt 3: Relevanz-Scoring

```python
for db in dbis_results:
    score = 50  # Basis für DBIS-Entdeckungen

    # Keyword-Match in Beschreibung
    if any(kw in db.description.lower() for kw in keywords):
        score += 30

    # Disziplin-Match
    if discipline.lower() in db.description.lower():
        score += 20

    # Zugang
    if db.access == "green" or db.access == "free":
        score += 15

    # Quality-Indikatoren
    if "peer-reviewed" in db.description:
        score += 10

    db.score = min(score, 100)
```

### Schritt 4: Merge mit YAML-Datenbanken

```python
# YAML-DBs haben Basis-Score 70-95
yaml_dbs = load_yaml_databases()

# DBIS-DBs haben berechnet 50-100
dbis_dbs = discover_from_dbis()

# Merge
all_dbs = yaml_dbs + [db for db in dbis_dbs if db.name not in yaml_names]

# Falls DBIS DB bereits in YAML: Boost YAML score
for db in yaml_dbs:
    if db.name in dbis_names:
        db.score += 10  # DBIS bestätigt Relevanz

# Sortiere nach Score
all_dbs.sort(key=lambda x: x.score, reverse=True)
```

---

## 6.5 DBIS Automatische Navigation (für browser-agent Phase 0)

**Zweck:** Agent navigiert automatisch via DBIS-Proxy zu allen benötigten Datenbanken.

### Workflow

**1. Navigiere zu DBIS Startseite**
```bash
navigate "https://dbis.ur.de/UBTIB"
```

**2. Warte auf Login (falls nötig)**
```bash
if detect_login_required():
    inform_user("⚠️ Bitte logge dich in DBIS ein")
    wait_for_user_confirmation()
```

**3. Für jede Datenbank:**

**a) Suche in DBIS**
```python
import urllib.parse
query = urllib.parse.quote(database_name)
url = f"https://dbis.ur.de/UBTIB/suche?q={query}"
result = WebFetch(url, "Extrahiere erste Datenbank-Ressourcen-ID")
resource_id = result['resource_id']  # z.B. "123456"
```

**b) Navigiere zu Detail-Seite**
```bash
navigate f"https://dbis.ur.de/UBTIB/resources/{resource_id}"
```

**c) Klicke "Zur Datenbank" Button**
```python
# CSS-Selektoren für Button (in Priorität)
selectors = [
    'a.db-link',
    'a[href*="dbis.ur.de/dblp"]',
    'button:contains("Zur Datenbank")'
]
click(selector)
```

**d) DBIS leitet weiter**
```
→ https://ieeexplore.ieee.org
→ Uni-Lizenz ist aktiv!
```

**e) Track Session**
```json
{
  "allowed_redirects": ["ieeexplore.ieee.org"],
  "came_from_dbis": true,
  "dbis_resource_id": "123456"
}
```

### CSS-Selektoren für DBIS

**Suchergebnisseite:**
- Ressourcen-ID: `a[href*="/UBTIB/resources/"]`
- Datenbank-Name: `h3.db-title a`
- Zugangsampel: `span.access-indicator`

**Detail-Seite:**
- "Zur Datenbank" Button: `a.db-link`, `a[href*="dbis.ur.de/dblp"]`
- Datenbank-URL: `a[href]:contains("Zur Datenbank")`

### Output-Format

**databases.json:**
```json
{
  "databases": [
    {
      "name": "IEEE Xplore",
      "url": "https://ieeexplore.ieee.org",
      "access_status": "green",
      "dbis_resource_id": "123456",
      "came_from_dbis": true,
      "dbis_validated": true
    }
  ]
}
```

---

## 7. DBIS HTML-Struktur (für Parsing)

### Suchergebnisseite

```html
<div class="result-list">
  <div class="result-item">
    <h3 class="db-title">
      <a href="/UBTIB/resources/123456">Datenbank Name</a>
    </h3>
    <p class="db-description">
      Beschreibung mit Fachgebiet und Inhalt...
    </p>
    <span class="access-indicator green">Vollzugriff</span>
  </div>
</div>
```

### Detailseite

```html
<div class="db-detail">
  <h1 class="db-name">IEEE Xplore</h1>
  <div class="db-description-full">...</div>
  <div class="db-subjects">
    <span>Informatik</span>
    <span>Elektrotechnik</span>
  </div>
  <a href="https://ieeexplore.ieee.org" class="db-link">Zur Datenbank</a>
</div>
```

---

## 8. Error Handling

### DBIS nicht erreichbar

```python
try:
    dbis_results = fetch_dbis(query)
except TimeoutError:
    # Fallback: Nur YAML-Datenbanken nutzen
    logger.warning("DBIS unavailable, using YAML databases only")
    return yaml_databases_only()
```

### Session abgelaufen

```python
if "login" in page_content or "anmelden" in page_content:
    logger.error("DBIS session expired")
    inform_user("🚨 DBIS-Session abgelaufen. Bitte neu anmelden.")
    # Pause und warte auf User-Login
```

### CAPTCHA

```python
if detect_captcha(screenshot):
    logger.warning("CAPTCHA detected on DBIS")
    inform_user("🚨 CAPTCHA erkannt. Bitte manuell lösen.")
    # Warte 30 Sekunden, dann retry
```

---

## 9. Rate Limiting

**DBIS-Richtlinien:**
- Max 1 Request pro Sekunde
- Max 100 Requests pro Stunde
- Bei Überschreitung: 429 Too Many Requests

**Agent-Implementation:**

```python
import time

last_dbis_request = 0

def dbis_request_with_rate_limit(url):
    global last_dbis_request

    # Warte mindestens 1 Sekunde seit letztem Request
    elapsed = time.time() - last_dbis_request
    if elapsed < 1.0:
        time.sleep(1.0 - elapsed)

    result = make_request(url)
    last_dbis_request = time.time()

    return result
```

---

## 10. Security-Hinweise

### HTML-Sanitization (MANDATORY)

```bash
# VOR jedem Read von DBIS-HTML
python3 scripts/sanitize_html.py \
  runs/$RUN_ID/dbis_page.html \
  runs/$RUN_ID/dbis_page_sanitized.html

# Nur sanitized version lesen
Read: runs/$RUN_ID/dbis_page_sanitized.html
```

### Domain-Validation (MANDATORY)

```bash
# VOR jeder Navigation
python3 scripts/validate_domain.py "$URL" \
  --referer "$PREVIOUS_URL" \
  --session-file runs/$RUN_ID/session.json

if [ $? -ne 0 ]; then
  echo "❌ Domain blocked: $URL"
  exit 1
fi
```

### Keine Credentials speichern

```python
# ❌ NIEMALS
save_credentials(username, password)

# ✅ RICHTIG
# Lass User sich in Browser einloggen
# Browser-Session bleibt aktiv
# Keine Credentials im Code
```

---

## 11. Testing

### Test DBIS-Zugriff

```bash
# Prüfe ob DBIS erreichbar
curl -I https://dbis.ur.de/UBTIB
# Erwarte: 200 OK

# Teste Suche
curl "https://dbis.ur.de/UBTIB/suche?q=test"
# Erwarte: HTML mit Suchergebnissen
```

### Test Domain-Validation

```bash
# Sollte ERLAUBT sein
python3 scripts/validate_domain.py "https://dbis.ur.de"
# Exit: 0

# Sollte BLOCKIERT sein
python3 scripts/validate_domain.py "https://sci-hub.ru"
# Exit: 1
```

---

## 12. Logging (MANDATORY)

Alle DBIS-Interaktionen müssen geloggt werden:

```python
# DBIS-Suche
logger.info("DBIS search started",
    query=query,
    url=dbis_url)

# DBIS-Ergebnisse
logger.metric("dbis_databases_found", count, unit="count")

# DBIS-Navigationsfehler
logger.error("DBIS navigation failed",
    url=url,
    error=str(e))

# Domain blockiert
logger.warning("Domain blocked by DBIS policy",
    url=url,
    reason="Direct database access not allowed")
```

---

## Zusammenfassung: Die 3 wichtigsten DBIS-Regeln

1. **🔒 DBIS-Proxy-Modus ist MANDATORY**
   - Erste Navigation IMMER zu dbis.ur.de
   - Weiterleitungen von DBIS sind erlaubt
   - Direkte Datenbank-Zugriffe sind blockiert

2. **🎯 DBIS für Discovery nutzen**
   - setup-agent sucht zusätzliche relevante DBs
   - Scoring basierend auf Relevanz
   - Merge mit YAML-Datenbanken

3. **🛡️ Security & Validation**
   - HTML-Sanitization vor jedem Read
   - Domain-Validation vor jeder Navigation
   - Keine Credentials speichern
   - Alle Aktionen loggen

---

**Ende der DBIS Usage Guide**
