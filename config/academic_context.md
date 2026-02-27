# Academic Context - User Präferenzen

Diese Datei ist **OPTIONAL** und wird von der Research-Recherche genutzt um User-spezifische Präferenzen zu berücksichtigen.

---

## 🎓 Disziplin & Fachgebiet

**Hauptdisziplin:** Computer Science / Software Engineering

**Spezialisierung:**
- DevOps & Cloud Engineering
- Software Architecture
- IT Governance & Compliance

**Forschungsinteressen:**
- Infrastructure as Code
- Continuous Integration/Deployment
- Cloud Security
- Microservices Architecture

---

## 🔑 Keywords & Terminologie

### Bevorzugte Begriffe:
- "DevOps" (statt "Development Operations")
- "CI/CD" (statt ausgeschrieben)
- "Infrastructure as Code" (statt "IaC" allein)
- "Microservices" (statt "SOA")

### Verwandte Themen:
- Kubernetes, Docker, Container Orchestration
- GitOps, ArgoCD, Flux
- Terraform, Ansible, CloudFormation
- Monitoring: Prometheus, Grafana
- Governance: Compliance, Policy Enforcement

### Ausschluss-Keywords:
- "Agile" (zu allgemein, außer im DevOps-Kontext)
- "Blockchain" (nicht relevant für meine Forschung)

---

## 📚 Bevorzugte Datenbanken & Quellen

### Primäre Quellen (Priorität):
1. **IEEE Xplore** - Software Engineering Papers
2. **ACM Digital Library** - Computing Research
3. **Springer** - Software Engineering Journals
4. **arXiv** - Preprints (cs.SE, cs.DC)

### Sekundäre Quellen:
- Google Scholar (als Fallback)
- Semantic Scholar (für Zitations-Analyse)

### Journal Präferenzen:
- IEEE Transactions on Software Engineering
- ACM Transactions on Software Engineering and Methodology
- Journal of Systems and Software
- Empirical Software Engineering

### Conference Präferenzen:
- ICSE (International Conference on Software Engineering)
- FSE (Foundations of Software Engineering)
- DevOps Conference Series
- IEEE Cloud Computing Conference

---

## 🎯 Qualitätskriterien

### Paper-Auswahl:
- **Minimum Citation Count:** 5+ Citations (für Papers älter als 2 Jahre)
- **Max Paper Age:** 7 Jahre (2018-2025)
  - Ausnahme: Foundational Papers/Highly Cited (10+ Jahre OK wenn >50 Citations)
- **Peer-Review:** Nur peer-reviewed Papers (keine Blog Posts, White Papers)
- **Language:** Englisch (Deutsch optional wenn hochrelevant)

### Venue Quality:
- **Conferences:** CORE Ranking A* oder A
- **Journals:** Impact Factor > 2.0 (oder Top-Tier in Disziplin)
- **Venues:** Etablierte Konferenzen/Journals bevorzugt

### Relevanz-Kriterien:
- **Abstract-Match:** Keywords müssen im Abstract erscheinen
- **Praktische Relevanz:** Bevorzuge Industrie-relevante Papers (nicht nur theoretisch)
- **Empirische Studien:** Bevorzuge empirische Studien mit Fallstudien/Experimenten

---

## 📊 Scoring-Präferenzen

### 5D-Scoring Gewichtung (Optional - überschreibt research_modes.yaml):

**Standard-Gewichtung:** (aus research_modes.yaml)
- Relevanz: 40%
- Recency: 20%
- Quality: 20%
- Authority: 20%

**Meine Präferenz für DevOps-Themen:**
- Relevanz: 45% (wichtiger für mich!)
- Recency: 25% (DevOps entwickelt sich schnell)
- Quality: 20% (Citation Count wichtig)
- Authority: 10% (Venue weniger wichtig als Inhalt)

**Für Foundational Topics (z.B. "Software Architecture"):**
- Relevanz: 40%
- Recency: 10% (ältere Papers OK)
- Quality: 30% (höhere Citation Count wichtig)
- Authority: 20% (etablierte Venues wichtig)

---

## 🚫 Ausschluss-Kriterien

### Nicht relevante Paper-Types:
- Blog Posts, Medium Articles
- Non-Peer-Reviewed White Papers
- Marketing Materials
- Tutorial/How-To ohne Research-Beitrag

### Nicht relevante Topics (Auto-Ausschluss):
- Reine Hardware-Papers (außer Cloud Infrastructure)
- Quantum Computing (nicht mein Fokus)
- Game Development (außer DevOps für Games)
- Mobile App Development (außer CI/CD für Mobile)

---

## 📝 Quote-Extraction Präferenzen

### Quote-Stil:
- **Bevorzugt:** Definitionen, Key Findings, Empirische Resultate
- **Vermeiden:** Einleitungen, Literatur-Reviews, Allgemeine Statements

### Quote-Länge:
- **Ideal:** 15-20 Wörter (kurz & prägnant)
- **Max:** 25 Wörter (aus research_modes.yaml)

### Kontext:
- **Before/After:** 50 Wörter Kontext (aus research_modes.yaml)
- **Mit Seitenzahl:** Immer angeben für Citation

---

## 🔬 Forschungsfokus

### Aktuelle Forschungsfragen:
1. Wie implementieren große Organisationen DevOps Governance?
2. Welche Best Practices gibt es für Infrastructure as Code Testing?
3. Wie wird Compliance in CI/CD Pipelines automatisiert?
4. Welche Metriken messen DevOps Erfolg?

### Methodische Präferenzen:
- **Empirische Studien** > Theoretische Arbeiten
- **Case Studies** aus Industrie bevorzugt
- **Quantitative Daten** (Metriken, Benchmarks) geschätzt
- **Tools & Frameworks** die praktisch anwendbar sind

---

## 💡 Nutzungshinweise

**Wie wird dieser Context genutzt?**

1. **Query Generation (Haiku):**
   - Nutzt Keywords für bessere Boolean Queries
   - Berücksichtigt Terminologie-Präferenzen

2. **Search APIs:**
   - Priorisiert bevorzugte Datenbanken
   - Filtert nach Venue-Präferenzen

3. **Ranking (5D-Scoring):**
   - Nutzt custom Scoring-Gewichtung
   - Filtert nach Qualitätskriterien
   - Wendet Ausschluss-Kriterien an

4. **Quote Extraction:**
   - Bevorzugt spezifische Quote-Typen
   - Nutzt Längen-Präferenzen

**Tipp:** Diese Datei kann pro Projekt angepasst werden!

---

## 📅 Letzte Aktualisierung

**Version:** 1.0
**Datum:** 2026-02-24
**Gültig für:** Academic Agent v2.0
