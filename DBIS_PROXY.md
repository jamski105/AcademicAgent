# DBIS Proxy Mode - Dokumentation

**Version:** 2.4
**Implementiert:** 2026-02-17

---

## Was ist DBIS Proxy Mode?

**Problem gelöst:** Wie kann der Agent auf 500+ Datenbanken zugreifen ohne jede einzeln in die Whitelist einzutragen?

**Lösung:** Alle Datenbanken MÜSSEN über DBIS (Database Information System) aufgerufen werden. DBIS ist das Uni-Portal das Zugriff auf lizenzierte Datenbanken vermittelt.

---

## Wie funktioniert es?

### Alte Methode (Whitelist):
```
Agent → ieeexplore.ieee.org (direkt)
❌ Problem: Bypassed Uni-Lizenz, nur 33 Datenbanken gelistet
```

### Neue Methode (DBIS Proxy):
```
Agent → dbis.ur.de → klickt auf IEEE → ieeexplore.ieee.org
✅ Vorteil: Alle 500+ Datenbanken automatisch verfügbar
✅ Vorteil: Uni-Authentifizierung durch DBIS
```

---

## Technische Implementierung

### 1. Domain-Whitelist erweitert

[scripts/domain_whitelist.json](file:///Users/j65674/Repos/AcademicAgent/scripts/domain_whitelist.json):

```json
{
  "proxy_mode": "dbis_only",
  "trusted_proxies": [
    "dbis.ur.de",
    "dbis.de",
    "ezproxy.uni-regensburg.de",
    "shibboleth.uni-regensburg.de"
  ],
  "proxy_redirect_policy": {
    "allow_redirects_from_trusted_proxies": true,
    "direct_navigation_blocked": true
  }
}
```

### 2. Domain-Validierung angepasst

[scripts/validate_domain.py](file:///Users/j65674/Repos/AcademicAgent/scripts/validate_domain.py):

**Validierungslogik:**
1. Immer erlaubt: DBIS, EZProxy, Shibboleth
2. Immer blockiert: Sci-Hub, LibGen (Pirate Sites)
3. Datenbanken erlaubt NUR WENN:
   - Referer ist DBIS, ODER
   - Session wurde von DBIS gestartet
4. Direkter Zugriff: BLOCKIERT

**Beispiele:**

```bash
# ❌ Direkt zu IEEE → BLOCKED
python3 scripts/validate_domain.py "https://ieeexplore.ieee.org"
# {
#   "allowed": false,
#   "reason": "Direct database access blocked. Must navigate via DBIS",
#   "suggestion": "Start navigation at https://dbis.ur.de"
# }

# ✅ DBIS als Referer → ALLOWED
python3 scripts/validate_domain.py "https://ieeexplore.ieee.org" \
  --referer "https://dbis.ur.de"
# {
#   "allowed": true,
#   "reason": "Database access via DBIS proxy"
# }

# ✅ Mit aktiver Session → ALLOWED
python3 scripts/validate_domain.py "https://scopus.com" \
  --session-file runs/RUN_ID/session.json
# (Wenn Session von DBIS gestartet wurde)
```

### 3. Session-Tracking

[scripts/track_navigation.py](file:///Users/j65674/Repos/AcademicAgent/scripts/track_navigation.py):

Trackt Navigation um zu prüfen ob Session von DBIS gestartet wurde:

```bash
# Session starten
python3 scripts/track_navigation.py "https://dbis.ur.de" session.json
# → Erstellt session.json mit "started_from_dbis": true

# Weitere Navigation tracken
python3 scripts/track_navigation.py "https://ieeexplore.ieee.org" session.json
# → Fügt zur History hinzu

# Session-Status prüfen
python3 scripts/track_navigation.py --status session.json
```

**session.json Format:**
```json
{
  "session_active": true,
  "started_from_dbis": true,
  "navigation_count": 3,
  "navigation_history": [
    {
      "url": "https://dbis.ur.de",
      "timestamp": "2026-02-17T10:00:00",
      "is_dbis": true
    },
    {
      "url": "https://ieeexplore.ieee.org",
      "timestamp": "2026-02-17T10:01:00",
      "is_dbis": false
    }
  ]
}
```

### 4. Browser-Agent Policy

[.claude/agents/browser-agent.md](file:///Users/j65674/Repos/AcademicAgent/.claude/agents/browser-agent.md#L50-L74):

**NEUE REGEL für Browser-Agent:**

```markdown
**CRITICAL RULES:**
1. ONLY navigate to DBIS first (dbis.ur.de or dbis.de)
2. NEVER navigate directly to databases
3. Let DBIS redirect you to databases
```

---

## Workflow im Agent

### Phase 0: DBIS-Navigation (Start)

```bash
# 1. Agent startet IMMER bei DBIS
python3 scripts/validate_domain.py "https://dbis.ur.de"
# → ALLOWED

# 2. Session-Tracking initialisieren
python3 scripts/track_navigation.py "https://dbis.ur.de" runs/$RUN_ID/session.json
# → session.json erstellt mit "started_from_dbis": true

# 3. User loggt sich in DBIS ein (manuell)
# 4. Agent navigiert zu Datenbank-Liste in DBIS
```

### Phase 2: Datenbank-Suche (via DBIS)

```bash
# 1. Agent klickt in DBIS auf "IEEE Xplore" Link
# 2. DBIS redirectet zu ieeexplore.ieee.org mit Uni-Auth
# 3. Vor Navigation validieren:

python3 scripts/validate_domain.py "https://ieeexplore.ieee.org" \
  --referer "https://dbis.ur.de/dbinfo/detail.php?id=123" \
  --session-file "runs/$RUN_ID/session.json"

# → ALLOWED (wegen DBIS Referer + aktiver Session)

# 4. Session tracken
python3 scripts/track_navigation.py "https://ieeexplore.ieee.org" \
  runs/$RUN_ID/session.json

# 5. Weiter mit Suche
```

---

## Vorteile

### 1. **Alle Datenbanken automatisch verfügbar**
- Keine manuelle Whitelist-Pflege
- 500+ Datenbanken via DBIS → automatisch erlaubt
- Neue Datenbanken: Sofort verfügbar wenn in DBIS

### 2. **Uni-Lizenz Compliance**
- Erzwingt Nutzung der Uni-Authentifizierung
- Verhindert Bypass der Lizenz
- Rechtlich sauber

### 3. **Security**
- Vertrauenswürdiger Einstiegspunkt (DBIS)
- Reduziert Angriffsfläche (nur DBIS direkt erreichbar)
- Pirate Sites immer blockiert

### 4. **Einfacher für User**
- Kein manuelles Whitelist-Management
- Automatische Authentifizierung via DBIS

---

## Tests

[tests/test_dbis_proxy.sh](file:///Users/j65674/Repos/AcademicAgent/tests/test_dbis_proxy.sh):

```bash
# Tests ausführen
bash tests/test_dbis_proxy.sh
```

**Test-Coverage:**
1. ✅ DBIS domain always allowed
2. ✅ Direct IEEE access blocked
3. ✅ IEEE access allowed WITH DBIS referer
4. ✅ Session tracking - start at DBIS
5. ✅ Database access WITH active DBIS session
6. ✅ Pirate site always blocked
7. ✅ First navigation must be DBIS
8. ✅ DOI resolver always allowed

**Pass Rate:** 100% (8/8)

---

## Troubleshooting

### Problem: "Direct database access blocked"

**Ursache:** Agent versucht direkt zu Datenbank zu navigieren

**Lösung:**
```bash
# Starte Navigation bei DBIS
python3 scripts/track_navigation.py --reset runs/$RUN_ID/session.json
# Dann navigiere zu DBIS zuerst
```

### Problem: "Session not started from DBIS"

**Ursache:** Session wurde ohne DBIS-Start initialisiert

**Lösung:**
```bash
# Session zurücksetzen
python3 scripts/track_navigation.py --reset runs/$RUN_ID/session.json
# Neu starten bei DBIS
```

### Problem: Database nicht erreichbar trotz DBIS

**Ursache:** DBIS-Session abgelaufen oder nicht eingeloggt

**Lösung:**
- Manuell in DBIS einloggen (User-Interaktion)
- Session refresh via DBIS

---

## Migration von alter Whitelist

**Backward Compatibility:**

Das System unterstützt beide Modi:

```bash
# Proxy Mode (Standard)
python3 scripts/validate_domain.py "https://example.com" --mode proxy

# Legacy Mode (alte Whitelist)
python3 scripts/validate_domain.py "https://example.com" --mode legacy
```

**Empfehlung:** Nutze Proxy Mode für neue Researches.

---

## Konfiguration

### DBIS-URLs anpassen

Falls du eine andere Uni nutzt:

[scripts/domain_whitelist.json](file:///Users/j65674/Repos/AcademicAgent/scripts/domain_whitelist.json):

```json
{
  "trusted_proxies": [
    "dbis.ur.de",           ← Regensburg
    "dbis.fu-berlin.de",    ← Berlin hinzufügen
    "ezproxy.DEINE-UNI.de"  ← Deine Uni
  ]
}
```

---

## Zusammenfassung

**DBIS Proxy Mode = Game Changer**

- ✅ 500+ Datenbanken ohne manuelle Whitelist
- ✅ Uni-Lizenz Compliance erzwungen
- ✅ Security verbessert
- ✅ Einfacher zu warten

**Setup-Zeit:** 0 Minuten (ist bereits aktiv!)

**Migration:** Automatisch (Proxy Mode ist Default)

---

**Ende der DBIS Proxy Dokumentation**
