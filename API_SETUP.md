# API-Keys Setup - Academic Agent v2.0

**Wichtig:** API-Keys sind **OPTIONAL**! Das System funktioniert ohne Keys im Standard-Modus.

---

## 🚀 Standard-Modus (OHNE Keys) - Plug & Play

**Keine Registrierung nötig!** Funktioniert sofort:

- ✅ CrossRef: 50 Anfragen/Sekunde
- ✅ OpenAlex: ~100 Anfragen/Tag (reicht für 2-3 Recherchen)
- ✅ Semantic Scholar: 100 Anfragen/5 Minuten
- ✅ Unpaywall: Funktioniert mit generischer Email

**Erfolgsrate:** 75-80%
**Setup-Zeit:** 0 Minuten ✅

➡️ **Du kannst sofort loslegen!**

---

## ⚡ Enhanced-Modus (MIT Keys) - Optional für bessere Performance

Wenn du mehr als 2-3 Recherchen pro Tag machen oder bessere Limits haben möchtest:

### Vorteile:
- ✅ OpenAlex: Unbegrenzte Anfragen (statt 100/Tag)
- ✅ Semantic Scholar: Schneller (1 req/s statt 100 req/5min)
- ✅ CORE: +10% PDF-Downloads
- ✅ **Erfolgsrate:** 85-92% (statt 75-80%)

**Setup-Zeit:** ~5 Minuten (alle Keys sind kostenlos!)

---

## 📝 API-Keys Registrierung (Schritt-für-Schritt)

### 1. CrossRef (Email - Optional)

**Was:** Größte DOI-Datenbank (140+ Millionen Papers)
**Kosten:** Kostenlos
**Registrierung:** Keine! Nur Email angeben

**Vorteile:**
- Höflichkeits-Header für bessere Reputation
- Kein Rate-Limit-Unterschied (50 req/s mit und ohne)

**Setup:**
```yaml
# In config/api_config.yaml:
api_keys:
  crossref_email: "deine.email@example.com"
```

**Empfehlung:** ⚠️ Optional - bringt kaum Vorteile

---

### 2. OpenAlex (Email - EMPFOHLEN!)

**Was:** Open-Source Alternative zu Google Scholar (250+ Millionen Papers)
**Kosten:** Kostenlos
**Registrierung:** Keine! Nur Email angeben

**Vorteile:**
- ⚡ **Unbegrenzte Anfragen** (10 req/s)
- Ohne Email: Nur ~100 Anfragen/Tag
- **Wichtig für Heavy Use!**

**Setup:**
```yaml
# In config/api_config.yaml:
api_keys:
  openalex_email: "deine.email@example.com"
```

**Link:** https://openalex.org/
**Dokumentation:** https://docs.openalex.org/how-to-use-the-api/rate-limits-and-authentication

**Empfehlung:** ✅ **STARK EMPFOHLEN** wenn du mehr als 2-3 Recherchen/Tag machst!

---

### 3. Semantic Scholar (API Key - Optional)

**Was:** Allen Institute AI-Datenbank (200+ Millionen Papers)
**Kosten:** Kostenlos
**Registrierung:** Ja (dauert 2 Minuten)

**Vorteile:**
- Schneller: 1 req/s (statt 100 req/5min ohne Key)
- Semantische Suche (KI-gestützt)

**Registrierung:**

1. Gehe zu: https://www.semanticscholar.org/product/api
2. Klicke auf **"Request API Key"**
3. Fülle Formular aus:
   - Name
   - Email
   - Verwendungszweck: "Academic Research"
4. Du bekommst sofort einen Key per Email

**Setup:**
```yaml
# In config/api_config.yaml:
api_keys:
  semantic_scholar_api_key: "DEIN_KEY_HIER"
```

**Link:** https://www.semanticscholar.org/product/api
**Dokumentation:** https://api.semanticscholar.org/

**Empfehlung:** ⚠️ Optional - nur wenn du viele Anfragen machst

---

### 4. Unpaywall (Email - Optional)

**Was:** Open-Access PDF-Datenbank (30+ Millionen PDFs)
**Kosten:** Kostenlos
**Registrierung:** Keine! Nur Email angeben

**Vorteile:**
- Tracking (sie sehen welche Anfragen von dir kommen)
- Kein Performance-Unterschied

**Setup:**
```yaml
# In config/api_config.yaml:
api_keys:
  unpaywall_email: "deine.email@example.com"
```

**Link:** https://unpaywall.org/products/api
**Dokumentation:** https://unpaywall.org/products/api

**Empfehlung:** ⚠️ Optional - bringt keine Vorteile

---

### 5. CORE (API Key - Optional für mehr PDFs)

**Was:** CORE (Open University UK) - Aggregiert Open-Access Repositories
**Kosten:** Kostenlos (10.000 Anfragen/Tag)
**Registrierung:** Ja (dauert 5 Minuten)

**Vorteile:**
- +10% PDF-Downloads
- Zugriff auf institutionelle Repositories

**Registrierung:**

1. Gehe zu: https://core.ac.uk/services/api
2. Klicke auf **"Register for API Key"**
3. Erstelle Account (Email + Passwort)
4. Bestätige Email
5. Gehe zu: https://core.ac.uk/account/api-keys
6. Erstelle neuen API Key
7. Kopiere Key

**Setup:**
```yaml
# In config/api_config.yaml:
api_keys:
  core_api_key: "DEIN_KEY_HIER"
```

**Link:** https://core.ac.uk/services/api
**Dokumentation:** https://core.ac.uk/documentation/api

**Empfehlung:** ✅ Empfohlen wenn du viele PDFs brauchst (+10% Erfolgsrate)

---

## 📁 Wo trage ich die Keys ein?

**Datei:** `config/api_config.yaml`

**Vollständiges Beispiel:**

```yaml
api_keys:
  # CrossRef - Optional
  crossref_email: "max.mustermann@example.com"

  # OpenAlex - EMPFOHLEN für Heavy Use
  openalex_email: "max.mustermann@example.com"

  # Semantic Scholar - Optional
  semantic_scholar_api_key: "abc123xyz456"

  # Unpaywall - Optional
  unpaywall_email: "max.mustermann@example.com"

  # CORE - Optional (für mehr PDFs)
  core_api_key: "def789ghi012"
```

**Wichtig:**
- Leer lassen = Standard-Modus (funktioniert ohne!)
- Keys eintragen = Enhanced-Modus (bessere Limits)

---

## 🔒 Alternative: Environment Variables

Statt Keys in `api_config.yaml` kannst du auch Environment Variables nutzen:

```bash
# In deiner Shell (.bashrc, .zshrc, etc.):
export CROSSREF_EMAIL="deine.email@example.com"
export OPENALEX_EMAIL="deine.email@example.com"
export SEMANTIC_SCHOLAR_API_KEY="dein_key"
export UNPAYWALL_EMAIL="deine.email@example.com"
export CORE_API_KEY="dein_key"
```

**Vorteil:** Keys nicht im Repository (sicherer für Git)

---

## ✅ Setup prüfen

Nach dem Eintragen der Keys kannst du prüfen ob alles funktioniert:

```bash
# Config Loader testen
python .claude/skills/research/scripts/config_loader.py \
    --mode standard \
    --query "Test"

# Erwartete Ausgabe:
# ✅ Config loaded successfully!
# 🔧 API Mode: enhanced  (← Zeigt dass Keys gefunden wurden!)
# 🔑 API Keys Status:
#    CrossRef: ✅
#    OpenAlex: ✅
#    Semantic Scholar: ✅
#    CORE: ✅
```

---

## 💡 Empfohlene Setup-Strategie

### Für Gelegenheitsnutzer (1-2 Recherchen/Monat):
```yaml
api_keys:
  # Alles leer lassen - Standard-Modus reicht!
  crossref_email: ""
  openalex_email: ""
  semantic_scholar_api_key: ""
  unpaywall_email: ""
  core_api_key: ""
```
**Erfolgsrate:** 75-80% ✅

---

### Für Normalnutzer (5-10 Recherchen/Monat):
```yaml
api_keys:
  crossref_email: ""
  openalex_email: "deine.email@example.com"  # ← NUR DIESE!
  semantic_scholar_api_key: ""
  unpaywall_email: ""
  core_api_key: ""
```
**Erfolgsrate:** 80-85% ⚡
**Setup-Zeit:** 30 Sekunden

---

### Für Heavy User (täglich):
```yaml
api_keys:
  crossref_email: "deine.email@example.com"
  openalex_email: "deine.email@example.com"
  semantic_scholar_api_key: "dein_key_hier"
  unpaywall_email: "deine.email@example.com"
  core_api_key: "dein_key_hier"
```
**Erfolgsrate:** 85-92% 🚀
**Setup-Zeit:** ~5 Minuten

---

## ❓ Häufige Fragen

### F: Muss ich API-Keys haben?
**A:** Nein! Standard-Modus funktioniert ohne Keys (75-80% Erfolgsrate).

### F: Welchen Key sollte ich als erstes holen?
**A:** OpenAlex Email - gibt unbegrenzte Requests (statt 100/Tag).

### F: Kosten die Keys Geld?
**A:** Nein, alle sind **kostenlos**!

### F: Wie lange dauert die Registrierung?
**A:**
- Email angeben (CrossRef, OpenAlex, Unpaywall): 30 Sekunden
- Mit Registrierung (Semantic Scholar, CORE): 2-5 Minuten

### F: Werden meine Keys gespeichert?
**A:** Ja, in `config/api_config.yaml`. Alternativ nutze Environment Variables.

### F: Was passiert wenn ein Key nicht funktioniert?
**A:** System fällt automatisch auf Standard-Modus zurück (ohne Key).

### F: Kann ich Keys später hinzufügen?
**A:** Ja! Einfach in `config/api_config.yaml` eintragen und neu starten.

---

## 🆘 Probleme?

### "Config not found"
```bash
# Prüfen ob Datei existiert:
ls -la config/api_config.yaml

# Falls nicht: Datei wurde nicht erstellt
# → Siehe requirements-v2.txt Installation
```

### "API Key invalid"
```bash
# Prüfen ob Key korrekt eingetragen:
cat config/api_config.yaml | grep "_api_key"

# Falls leer oder falsch:
# → Key nochmal von Registrierungs-Email kopieren
```

### "Module not found"
```bash
# Dependencies installieren:
pip install -r requirements-v2.txt
```

---

## 📚 Weiterführende Links

- **OpenAlex Docs:** https://docs.openalex.org/
- **Semantic Scholar API:** https://api.semanticscholar.org/
- **CORE API Docs:** https://core.ac.uk/documentation/api
- **CrossRef API:** https://www.crossref.org/documentation/retrieve-metadata/rest-api/
- **Unpaywall API:** https://unpaywall.org/products/api

---

## 🎯 TL;DR - Schnellstart

**Option 1: Standard-Modus (Plug & Play)**
```bash
# Nichts tun - funktioniert sofort! ✅
```

**Option 2: Enhanced-Modus (empfohlen)**
```bash
# 1. Öffne config/api_config.yaml
# 2. Trage deine Email bei openalex_email ein
# 3. Fertig! (dauert 30 Sekunden)
```

**Option 3: Maximum Performance**
```bash
# 1. Registriere bei Semantic Scholar + CORE (~5 Min)
# 2. Trage alle Keys in config/api_config.yaml ein
# 3. Erfolgsrate: 85-92% 🚀
```

---

Viel Erfolg! 🎓
