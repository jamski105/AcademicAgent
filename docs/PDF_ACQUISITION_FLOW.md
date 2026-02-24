# PDF Acquisition Flow - v2.0

**Ziel:** 85-90% PDF-Download-Erfolgsrate (statt 17% in v1.0)

---

## 🎯 Drei-Stufen Fallback-Chain

```
┌─────────────────────────────────────────────────────┐
│ Paper mit DOI                                        │
└──────────────┬──────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────┐
│ Stufe 1: Unpaywall API                              │
│ • Schnell (1-2s)                                    │
│ • Erfolgsrate: ~40%                                 │
│ • Open Access Repository Links                      │
└──────────────┬──────────────────────────────────────┘
               │
               │ ❌ Kein PDF gefunden
               ▼
┌─────────────────────────────────────────────────────┐
│ Stufe 2: CORE API                                   │
│ • Schnell (2-3s)                                    │
│ • Erfolgsrate: +10%                                 │
│ • Aggregiert viele Repositories                     │
└──────────────┬──────────────────────────────────────┘
               │
               │ ❌ Kein PDF gefunden
               ▼
┌─────────────────────────────────────────────────────┐
│ Stufe 3: DBIS Browser (Institutional Access)        │
│ • Langsam (15-25s)                                  │
│ • Erfolgsrate: +35-40%                              │
│ • Headful Browser mit TIB Shibboleth Auth           │
│ • Publisher-Navigation (IEEE, ACM, Springer, etc.)  │
└──────────────┬──────────────────────────────────────┘
               │
               ├─ ✅ PDF erfolgreich
               └─ ❌ Alle Stufen fehlgeschlagen → Skip Paper
```

**Gesamt-Erfolgsrate:** 40% + 10% + 35-40% = **85-90%**

---

## 📝 Implementierung in src/pdf/

### Dateistruktur

```
src/pdf/
├── pdf_fetcher.py              # Orchestriert Fallback-Chain
├── unpaywall_client.py         # Stufe 1
├── core_client.py              # Stufe 2
├── dbis_browser_downloader.py # Stufe 3
├── publisher_navigator.py      # Publisher-spezifische Navigation
└── shibboleth_auth.py          # TIB Authentifizierung
```

---

## ⚙️ Konfiguration

### config/api_config.yaml

```yaml
pdf:
  fallback_chain: ["unpaywall", "core", "dbis_browser"]
  max_parallel_downloads: 3
  dbis_browser_delay_seconds: 15
  skip_after_all_failed: true

timeouts:
  pdf_download: 60
  browser_page_load: 45
  dbis_authentication: 90
```

---

## 🔧 Rate-Limiting

- **Unpaywall/CORE:** Keine Delays (100 req/s möglich)
- **DBIS Browser:** 10-20s Delay zwischen Downloads
  - Human-like Behavior
  - Verhindert Account-Sperrung

---

## 📊 Erfolgs-Metriken

| Stufe | Erfolgsrate | Durchschnitt Zeit | Kumulativ |
|-------|-------------|-------------------|-----------|
| Unpaywall | 40% | 1-2s | 40% |
| CORE | 10% | 2-3s | 50% |
| DBIS Browser | 35-40% | 15-25s | 85-90% |

**v1.0 Vergleich:** 17% Erfolgsrate → **+470% Verbesserung**
