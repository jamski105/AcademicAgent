# ⚙️ Konfiguration erstellen

In diesem Kapitel lernst du, wie du eine optimale Recherche-Konfiguration für dein Thema erstellst.

## Was ist eine Recherche-Konfiguration?

Eine Konfiguration definiert **alle Parameter** deiner Literaturrecherche:

- 🎯 **Forschungsfrage** - Was möchtest du untersuchen?
- 🔑 **Keywords** - Welche Begriffe sind relevant?
- 📚 **Disziplinen** - Welche Fachbereiche?
- 📅 **Zeitraum** - Welcher Publikationszeitraum?
- 🌍 **Sprachen** - Welche Sprachen?
- 🎯 **Zielanzahl** - Wie viele Papers brauchst du?

**Gute Konfiguration = Bessere Ergebnisse!**

---

## Drei Wege eine Konfiguration zu erstellen

### 1. Interaktives Setup (Empfohlen für Anfänger)

Starte einfach `/academicagent` im Claude Code Chat. Der Agent führt dich durch alle Schritte:

```
User: /academicagent

Agent: Willkommen! Ich helfe dir bei der Literaturrecherche.
       Lass uns zunächst deine Recherche konfigurieren.

       Was ist deine Forschungsfrage?
```

**Vorteil:** Einfach, geführt, keine Vorkenntnisse nötig
**Nachteil:** Nicht wiederverwendbar für ähnliche Recherchen

### 2. Template kopieren (Empfohlen für Fortgeschrittene)

Kopiere ein Beispiel-Template und passe es an:

```bash
# Beispiel-Template kopieren
cp config/.example/academic_context_cs_example.md config/meine_recherche.md

# In deinem Editor öffnen und anpassen
code config/meine_recherche.md
```

**Vorteil:** Wiederverwendbar, versionierbar, anpassbar
**Nachteil:** Erfordert Verständnis der Konfig-Struktur

### 3. Setup-Agent nutzen (Für mehrere Recherchen)

Erstelle Konfig ohne Recherche zu starten:

```
/setup-agent
```

**Vorteil:** Mehrere Konfigs erstellen, später ausführen
**Nachteil:** Zusätzlicher Schritt vor der Recherche

---

## Konfig-Struktur im Detail

### Vollständiges Template

```markdown
# Recherche-Konfiguration

## Forschungsfrage
[Deine präzise Forschungsfrage]

## Keywords

### Primary Keywords
[Hauptbegriffe, kommagetrennt]

### Secondary Keywords
[Ergänzende Begriffe, kommagetrennt]

### Related Keywords (Optional)
[Verwandte Begriffe, kommagetrennt]

## Disziplinen
[Kommagetrennte Liste relevanter Fachbereiche]

## Suchparameter

### Zeitraum
Von: [Jahr]
Bis: [Jahr]

### Sprachen
[Kommagetrennte Liste]

### Dokumenttypen
[Journal-Artikel, Konferenz-Papers, Books, etc.]

## Qualitätsfilter

### Mindest-Zitationen
[Anzahl oder "keine"]

### Open Access bevorzugt
[Ja/Nein]

### Zielanzahl Papers
[Anzahl - Standard: 18]

## Datenbank-Präferenzen (Optional)

### Ausgeschlossene Datenbanken
[Kommagetrennte Liste von Datenbanken die NICHT durchsucht werden sollen]

### Priorisierte Datenbanken
[Kommagetrennte Liste von Datenbanken mit hoher Priorität]

## Iterative Suchparameter (Optional)

### Databases Per Iteration
[Anzahl - Standard: 5]

### Target Candidates
[Anzahl - Standard: 50]

### Max Iterations
[Anzahl - Standard: 5]
```

---

## Schritt-für-Schritt: Optimale Konfiguration erstellen

### Schritt 1: Forschungsfrage formulieren

**Grundprinzipien:**

✅ **DO:**
- Sei spezifisch und präzise
- Formuliere eine echte Frage (endet mit "?")
- Begrenze den Scope (nicht zu breit)
- Verwende akademische Begriffe

❌ **DON'T:**
- Zu vage: "Was ist KI?"
- Zu breit: "Alles über DevOps"
- Keine Frage: "DevOps Analyse"
- Umgangssprache: "Wie mache ich Apps besser?"

**Beispiele:**

| ❌ Schlecht | ✅ Gut |
|------------|-------|
| "DevOps untersuchen" | "Wie beeinflussen DevOps-Praktiken die Software-Qualität in agilen Teams?" |
| "Machine Learning" | "Welche Algorithmen eignen sich für Sentiment-Analyse in sozialen Medien?" |
| "Blockchain Sicherheit" | "Wie können Smart Contracts vor Reentrancy-Angriffen geschützt werden?" |

**Formel für gute Forschungsfragen:**

```
Wie/Welche/Inwiefern [Hauptkonzept] [Verb] [Kontext/Anwendungsbereich]?
```

Beispiele:
- "Wie **ermöglichen** Lean-Prinzipien **Governance** in DevOps-Teams?"
- "Welche **Faktoren beeinflussen** die Adoption von **Cloud-Native** Architekturen?"
- "Inwiefern **verbessert** Pair Programming **die Code-Qualität** in verteilten Teams?"

### Schritt 2: Keywords strategisch wählen

Keywords sind **der wichtigste Teil** deiner Konfiguration!

#### Primary Keywords

**Was sind Primary Keywords?**
- Die **Hauptkonzepte** deiner Forschungsfrage
- **2-4 Begriffe**, die in jedem relevanten Paper vorkommen sollten
- Meist aus der Forschungsfrage direkt ableitbar

**Beispiel:**

Forschungsfrage: *"Wie ermöglichen Lean-Prinzipien Governance in DevOps-Teams?"*

Primary Keywords:
- Lean Governance
- DevOps
- Agile Teams

**Tipps:**

✅ **Verwende Phrasen** statt Einzelwörter
- Gut: "Lean Governance" (spezifisch)
- Schlecht: "Lean" (zu breit)

✅ **Denke an Synonyme**
- "Machine Learning" = "ML" = "Statistical Learning"
- "Continuous Integration" = "CI" = "Automated Build"

✅ **Beachte Schreibweisen**
- "DevOps" vs "Dev-Ops" vs "Dev Ops"
- "Blockchain" vs "Block-chain" vs "Distributed Ledger"

#### Secondary Keywords

**Was sind Secondary Keywords?**
- **Ergänzende Konzepte**, die häufig zusammen mit Primary Keywords vorkommen
- **3-5 Begriffe**, die den Kontext erweitern
- Nicht zwingend erforderlich, aber erhöhen Relevanz

**Beispiel:**

Secondary Keywords:
- Continuous Delivery
- Process Automation
- IT Governance
- Agile Methodologies
- Team Autonomy

#### Related Keywords (Optional)

**Was sind Related Keywords?**
- **Verwandte Begriffe** aus angrenzenden Bereichen
- Helfen dabei, interdisziplinäre Papers zu finden
- Nützlich für explorative Recherchen

**Beispiel:**

Related Keywords:
- Software Process Improvement
- Quality Assurance
- Value Stream Mapping
- Kanban
- Scrum

#### Keyword-Recherche-Strategie

**1. Start mit der Forschungsfrage**
```
Frage: "Wie ermöglichen Lean-Prinzipien Governance in DevOps-Teams?"
→ Extrahiere Hauptkonzepte:
  - Lean-Prinzipien
  - Governance
  - DevOps-Teams
```

**2. Erweitere mit Synonymen**
```
Lean-Prinzipien:
  → Lean Management, Lean Thinking, Toyota Production System

Governance:
  → IT Governance, Process Governance, Compliance

DevOps-Teams:
  → Agile Teams, Cross-functional Teams, Software Teams
```

**3. Recherchiere in bestehender Literatur**

Suche auf Google Scholar nach 2-3 relevanten Papers und schaue:
- **Welche Begriffe** verwenden die Autoren?
- **Welche Keywords** sind im Paper getaggt?
- **Welche verwandten Themen** werden erwähnt?

**4. Teste deine Keywords**

Vor der eigentlichen Recherche, teste auf Google Scholar:
```
"Lean Governance" AND DevOps
→ Anzahl Ergebnisse: ~450 (gut!)

"Lean Thinking" AND "IT Governance"
→ Anzahl Ergebnisse: ~280 (ok)

"Toyota Production System" AND DevOps
→ Anzahl Ergebnisse: ~15 (zu spezifisch)
```

**Goldilocks-Prinzip:**
- ❌ < 50 Ergebnisse → Zu spezifisch
- ✅ 200-1000 Ergebnisse → Perfekt
- ❌ > 10.000 Ergebnisse → Zu breit

### Schritt 3: Disziplinen auswählen

**Verfügbare Disziplinen:**

| Disziplin | Typische Datenbanken | Wann wählen? |
|-----------|---------------------|--------------|
| **Informatik** | ACM, IEEE, DBLP, arXiv | Software, Algorithmen, IT-Systeme |
| **Wirtschaft & BWL** | WISO, EconBiz, Business Source Elite | Management, Geschäftsmodelle, Strategie |
| **Jura** | juris, beck-online, HeinOnline | Rechtsthemen, Compliance, Datenschutz |
| **Medizin** | PubMed, MEDLINE, Cochrane | Gesundheit, Biologie, Pharmazie |
| **Psychologie** | PsycINFO, PsycArticles | Verhalten, Kognition, Sozialforschung |
| **Interdisziplinär** | Web of Science, Scopus, JSTOR | Übergreifende Themen |

**Tipp:** Wähle **2-3 Disziplinen** für optimale Ergebnisse.

**Beispiele:**

| Forschungsfrage | Disziplinen |
|-----------------|-------------|
| "Wie ermöglichen Lean-Prinzipien Governance in DevOps?" | Informatik, Wirtschaft & BWL |
| "Datenschutz in Cloud-Computing" | Informatik, Jura |
| "Burnout in Software-Teams" | Informatik, Psychologie |
| "Blockchain in der Gesundheitsversorgung" | Informatik, Medizin, Jura |

### Schritt 4: Zeitraum festlegen

**Empfehlungen:**

| Recherche-Typ | Zeitraum | Begründung |
|---------------|----------|------------|
| **Bachelor/Master** | 5-10 Jahre | 2015-2024: Aktuelle Literatur |
| **Doktorarbeit** | 10-15 Jahre | 2010-2024: Umfassender Überblick |
| **Systematisches Review** | Alle verfügbaren | 1990-2024: Vollständige Historie |
| **Trend-Analyse** | 2-3 Jahre | 2022-2024: Neueste Entwicklungen |

**Forschungsfeld-spezifisch:**

- **Schnelllebige Felder** (KI, Cloud, DevOps): 3-5 Jahre
- **Etablierte Felder** (Datenbanken, Netzwerke): 10-15 Jahre
- **Theoretische Grundlagen**: Keine Begrenzung

**Beispiel:**

```markdown
## Suchparameter

### Zeitraum
Von: 2015
Bis: 2024
```

### Schritt 5: Weitere Parameter

#### Sprachen

```markdown
### Sprachen
Englisch, Deutsch
```

**Tipp:** Englisch ist Pflicht (90% der akademischen Literatur). Ergänze deine Muttersprache für lokale Quellen.

#### Dokumenttypen

```markdown
### Dokumenttypen
Journal-Artikel, Konferenz-Papers, Technical Reports
```

**Empfehlungen:**
- ✅ **Immer:** Journal-Artikel, Konferenz-Papers
- ⚠️ **Vorsichtig:** Technical Reports (oft nicht peer-reviewed)
- ❌ **Vermeiden:** Dissertationen (zu lang), Preprints (nicht begutachtet)

#### Qualitätsfilter

```markdown
### Mindest-Zitationen
10

### Open Access bevorzugt
Ja

### Zielanzahl Papers
18
```

**Zielanzahl Guidelines:**

| Arbeitstyp | Empfohlene Anzahl |
|------------|-------------------|
| Seminararbeit | 8-12 Papers |
| Bachelorarbeit | 15-20 Papers |
| Masterarbeit | 20-30 Papers |
| Doktorarbeit | 40-60 Papers |
| Systematisches Review | 50-100 Papers |

**Mindest-Zitationen:**

- **Neue Themen** (< 3 Jahre alt): 0-5 Zitationen
- **Etablierte Themen** (> 5 Jahre): 10-20 Zitationen
- **Klassische Arbeiten**: 50+ Zitationen

---

## Erweiterte Konfiguration

### Datenbanken manuell steuern

#### Datenbanken ausschließen

Wenn du bestimmte Datenbanken NICHT durchsuchen möchtest:

```markdown
## Datenbank-Präferenzen

### Ausgeschlossene Datenbanken
Google Scholar, ResearchGate
```

**Gründe zum Ausschließen:**
- 🐌 **Zu langsam:** Google Scholar (strenge Rate Limits)
- 📉 **Geringe Qualität:** ResearchGate (oft Preprints)
- 💰 **Keine Lizenz:** Wenn deine Uni keinen Zugang hat

#### Datenbanken priorisieren

Wenn du bestimmte Datenbanken bevorzugst:

```markdown
### Priorisierte Datenbanken
ACM Digital Library, IEEE Xplore, SpringerLink
```

**Effekt:** Diese Datenbanken werden in der ersten Iteration durchsucht.

### Iterative Suche anpassen

Für fortgeschrittene Nutzer:

```markdown
## Iterative Suchparameter

### Databases Per Iteration
5  # Standard: 5, Bereich: 3-10

### Target Candidates
50  # Standard: 50, Bereich: 30-100

### Max Iterations
5  # Standard: 5, Bereich: 2-10
```

**Wann anpassen?**

| Parameter | Erhöhen wenn... | Verringern wenn... |
|-----------|-----------------|-------------------|
| **Databases Per Iteration** | Schnellere Recherche gewünscht | Kosten sparen, präzisere Ergebnisse |
| **Target Candidates** | Mehr Auswahl gewünscht | Sehr spezifisches Thema |
| **Max Iterations** | Sehr breites Thema | Budget-Beschränkung |

---

## Beispiel-Konfigurationen

### Beispiel 1: Informatik Bachelor-Arbeit

```markdown
# Recherche-Konfiguration: CI/CD in Microservices

## Forschungsfrage
Welche Best Practices existieren für CI/CD-Pipelines in Microservice-Architekturen?

## Keywords

### Primary Keywords
Continuous Integration, Continuous Delivery, Microservices

### Secondary Keywords
CI/CD Pipelines, Docker, Kubernetes, Automated Testing

### Related Keywords
DevOps, Container Orchestration, Service Mesh

## Disziplinen
Informatik, Software Engineering

## Suchparameter

### Zeitraum
Von: 2018
Bis: 2024

### Sprachen
Englisch

### Dokumenttypen
Journal-Artikel, Konferenz-Papers

## Qualitätsfilter

### Mindest-Zitationen
5

### Open Access bevorzugt
Ja

### Zielanzahl Papers
18
```

### Beispiel 2: BWL Master-Arbeit

```markdown
# Recherche-Konfiguration: Digital Transformation in KMU

## Forschungsfrage
Welche Faktoren beeinflussen den Erfolg der digitalen Transformation in kleinen und mittleren Unternehmen?

## Keywords

### Primary Keywords
Digital Transformation, SME, Digitalization

### Secondary Keywords
Change Management, IT Adoption, Business Model Innovation

### Related Keywords
Industry 4.0, Digital Strategy, Organizational Change

## Disziplinen
Wirtschaft & BWL, Informatik

## Suchparameter

### Zeitraum
Von: 2015
Bis: 2024

### Sprachen
Englisch, Deutsch

### Dokumenttypen
Journal-Artikel, Konferenz-Papers

## Qualitätsfilter

### Mindest-Zitationen
15

### Open Access bevorzugt
Ja

### Zielanzahl Papers
25

## Datenbank-Präferenzen

### Priorisierte Datenbanken
WISO, Business Source Elite, SpringerLink
```

### Beispiel 3: Interdisziplinäre Doktorarbeit

```markdown
# Recherche-Konfiguration: KI-Ethik im Gesundheitswesen

## Forschungsfrage
Welche ethischen Rahmenbedingungen sind notwendig für den Einsatz von KI-Diagnostik in der klinischen Praxis?

## Keywords

### Primary Keywords
Artificial Intelligence Ethics, Medical Diagnosis, Clinical Decision Support

### Secondary Keywords
Machine Learning Healthcare, Medical AI, Ethical Guidelines

### Related Keywords
Algorithm Bias, Patient Privacy, Explainable AI, Medical Law

## Disziplinen
Informatik, Medizin, Jura, Interdisziplinär

## Suchparameter

### Zeitraum
Von: 2010
Bis: 2024

### Sprachen
Englisch, Deutsch

### Dokumenttypen
Journal-Artikel, Konferenz-Papers, Technical Reports

## Qualitätsfilter

### Mindest-Zitationen
20

### Open Access bevorzugt
Nein

### Zielanzahl Papers
50

## Iterative Suchparameter

### Databases Per Iteration
7

### Target Candidates
80

### Max Iterations
6
```

---

## Häufige Fehler vermeiden

### ❌ Fehler 1: Zu breite Keywords

**Schlecht:**
```markdown
Primary Keywords: AI, Data, Systems
```

**Warum schlecht?**
- Millionen von Ergebnissen
- Keine Fokussierung
- Irrelevante Papers

**Besser:**
```markdown
Primary Keywords: Reinforcement Learning, Robotic Control Systems, Sim-to-Real Transfer
```

### ❌ Fehler 2: Nur deutsche Keywords

**Schlecht:**
```markdown
Primary Keywords: Künstliche Intelligenz, Maschinelles Lernen
Sprachen: Deutsch
```

**Warum schlecht?**
- 90% der akademischen Literatur ist auf Englisch
- Sehr begrenzte Ergebnisse

**Besser:**
```markdown
Primary Keywords: Artificial Intelligence, Machine Learning
Secondary Keywords: Künstliche Intelligenz, Maschinelles Lernen
Sprachen: Englisch, Deutsch
```

### ❌ Fehler 3: Zeitraum zu kurz

**Schlecht:**
```markdown
Zeitraum: 2023-2024
```

**Warum schlecht?**
- Zu wenige Papers (Publikation dauert 1-2 Jahre)
- Verlust wichtiger Grundlagenarbeiten

**Besser:**
```markdown
Zeitraum: 2018-2024
```

### ❌ Fehler 4: Zu viele Disziplinen

**Schlecht:**
```markdown
Disziplinen: Informatik, Wirtschaft & BWL, Jura, Medizin, Psychologie, Interdisziplinär
```

**Warum schlecht?**
- Zu viele Datenbanken (langsam & teuer)
- Viele irrelevante Ergebnisse

**Besser:**
```markdown
Disziplinen: Informatik, Wirtschaft & BWL
```

---

## Konfig validieren & testen

Bevor du die Recherche startest, prüfe:

### ✅ Checkliste

- [ ] Forschungsfrage ist präzise und spezifisch
- [ ] 2-4 Primary Keywords definiert
- [ ] Keywords in Google Scholar getestet (200-1000 Ergebnisse)
- [ ] 1-3 Disziplinen ausgewählt
- [ ] Zeitraum passt zum Forschungsfeld
- [ ] Zielanzahl passt zum Arbeitstyp
- [ ] Sprachen inkludieren Englisch

### 🧪 Test-Suche auf Google Scholar

Teste deine Keywords BEVOR du die Recherche startest:

```
1. Öffne Google Scholar: scholar.google.com
2. Suche: "[Primary Keyword 1]" AND "[Primary Keyword 2]"
3. Prüfe:
   - Anzahl Ergebnisse (200-1000 = ideal)
   - Relevanz der Top 10 Papers
   - Sind die Titel relevant für deine Frage?
4. Passe Keywords an falls nötig
```

---

## Nächste Schritte

Jetzt kannst du optimale Konfigurationen erstellen! Als nächstes:

- **[Ergebnisse verstehen](04-understanding-results.md)** - Was bedeuten die Bewertungen?
- **[Best Practices](06-best-practices.md)** - Weitere Tipps für optimale Recherchen
- **[Zurück zum Inhaltsverzeichnis](README.md)**

---

**[← Zurück zu: Workflow](02-basic-workflow.md) | [Weiter zu: Ergebnisse verstehen →](04-understanding-results.md)**
