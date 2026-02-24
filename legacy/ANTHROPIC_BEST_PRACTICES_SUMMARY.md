# Anthropic Cookbook - Best Practices für v2.0

**Quelle:** https://github.com/anthropics/anthropic-cookbook
**Analysiert:** 2026-02-23

---

## 🎯 Relevante Patterns für Academic Agent v2.0

### 1. Sub-Agents Pattern (WICHTIG!)

**Anthropic Empfehlung:**
- **Orchestrator (Opus/Sonnet)** koordiniert mehrere **Sub-Agents (Haiku)**
- Orchestrator generiert spezifische Prompts für jeden Sub-Agent
- Sub-Agents arbeiten parallel an Teil-Aufgaben
- Orchestrator sammelt Ergebnisse und synthetisiert finale Antwort

**Beispiel aus Cookbook:**
```python
# Orchestrator (Opus) generiert Prompt für Sub-Agent
def generate_haiku_prompt(question):
    response = client.messages.create(
        model="claude-opus-4-1",
        messages=[{"role": "user", "content": f"Generate prompt for sub-agent: {question}"}]
    )
    return response.content[0].text

# Sub-Agent (Haiku) führt Task aus
def execute_subtask(prompt, data):
    response = client.messages.create(
        model="claude-haiku-4-5",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2048
    )
    return response.content[0].text
```

**✅ FÜR v2.0:**
- Orchestrator = Sonnet (linear coordinator)
- Module = Haiku (schnell, günstig für repetitive Tasks)
- Parallel execution mit `concurrent.futures.ThreadPoolExecutor`

---

### 2. Tool Use Best Practices

**Anthropic Empfehlung:**
- Tools mit klaren `input_schema` definieren
- `description` muss präzise sein (Claude entscheidet basierend darauf)
- Tool-Responses strukturiert zurückgeben
- Agentic Loop: Tool Use → Tool Result → Next Action

**Tool Definition Schema:**
```python
tools = [{
    "name": "search_papers",
    "description": "Search academic papers via API. Use for finding peer-reviewed research.",
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query"},
            "limit": {"type": "integer", "description": "Max results"}
        },
        "required": ["query"]
    }
}]
```

**✅ FÜR v2.0:**
- Jede API (CrossRef, OpenAlex, S2) als Tool definieren
- Orchestrator wählt richtige API basierend auf Task
- Fallback-Chain als Tool-Sequence

---

### 3. Prompt Engineering

**Anthropic Empfehlung:**
- **XML Tags** für strukturierte Inputs/Outputs
- **Thinking Tags** für Chain-of-Thought
- **Step-by-Step Instructions**

**Beispiel:**
```xml
<question>How did Apple's sales change Q1-Q4?</question>

<thinking>
I need to extract sales data from each quarter's report.
I'll use sub-agents to process each PDF in parallel.
</thinking>

<output>
<quarter id="Q1">Sales: $123.9B</quarter>
<quarter id="Q2">Sales: $94.8B</quarter>
...
</output>
```

**✅ FÜR v2.0:**
- XML für strukturierte Daten (candidates, ranked_sources)
- Thinking blocks für komplexe Entscheidungen

---

### 4. Concurrent Execution

**Anthropic Empfehlung:**
- Sub-Agents parallel ausführen mit `ThreadPoolExecutor`
- Nicht sequenziell warten

**Beispiel:**
```python
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor() as executor:
    futures = [executor.submit(process_pdf, pdf) for pdf in pdfs]
    results = [f.result() for f in futures]
```

**✅ FÜR v2.0:**
- Parallel API-Calls (CrossRef + OpenAlex + S2 gleichzeitig)
- Parallel PDF-Downloads

---

### 5. JSON Mode & Structured Outputs

**Anthropic Empfehlung:**
- Pydantic Models für Response-Validierung
- JSON Schema in System Prompt

**✅ FÜR v2.0:**
- Alle Outputs (candidates, quotes) als Pydantic Models
- Auto-Validierung gegen Schema

---

## 🔄 Option C: Linear Coordinator + Module

**Entscheidung:** Linear Coordinator (kein Multi-Agent-Orchestrator!)

### Architektur v2.0 (Option C)

```
┌─────────────────────────────────────────┐
│   Linear Coordinator (Sonnet)          │
│   - Führt Workflow Schritt-für-Schritt │
│   - Ruft Module direkt auf              │
│   - Nutzt Tools für externe APIs        │
└─────────────────────────────────────────┘
         │
         ├──► Module 1: Search (Haiku)
         │    └─ Tool: CrossRef API, OpenAlex API
         │
         ├──► Module 2: Ranking (Haiku)
         │    └─ Lokale Berechnung (5D-Scoring)
         │
         ├──► Module 3: PDF Fetch (Haiku)
         │    └─ Tool: Unpaywall API, Browser
         │
         └──► Module 4: Quote Extraction (Haiku)
              └─ Tool: PyMuPDF
```

**Key Differences vs v1.0:**
- ❌ KEIN Orchestrator-Agent der Sub-Agents spawnt
- ✅ Linear Coordinator = Ein Python-Script mit Sonnet
- ✅ Module = Haiku-Calls für spezifische Tasks
- ✅ Tools = APIs (nicht Agent-Spawning)

---

## 📋 Roadmap-Updates

### Phase 0: Foundation
**ALT:** "Linear Workflow Agent"
**NEU:** "Linear Coordinator + Modul-System"

**Änderungen:**
- Coordinator = `src/coordinator.py` (Sonnet)
- Module = `src/modules/{search,ranking,pdf,extraction}.py` (Haiku)
- Tools = API-Clients als Tool-Definitions

### Phase 1: Search Engine
**ALT:** "API-Clients einzeln"
**NEU:** "Search-Modul mit Tools"

**Änderungen:**
- Search-Modul (Haiku) nutzt Tools:
  - `search_crossref`
  - `search_openalex`
  - `search_semantic_scholar`
- Coordinator entscheidet welche Tools zu nutzen

### Parallelisierung
- `ThreadPoolExecutor` für parallele API-Calls
- Alle 3 APIs gleichzeitig abfragen

---

## 💡 Kern-Erkenntnisse

### Was v2.0 übernehmen sollte:

1. **Sub-Agents Pattern** → Module mit Haiku
2. **Tool Use** → APIs als Tools definieren
3. **XML Tags** → Strukturierte Outputs
4. **Parallel Execution** → ThreadPoolExecutor
5. **JSON Mode** → Pydantic Models

### Was v2.0 NICHT machen sollte:

1. ❌ Multi-Agent mit Task-Tool (zu komplex)
2. ❌ Asynchrone Koordination (fehlerhaft in v1)
3. ❌ Agent spawnt Agent (Orchestrator-Problem)

### v2.0 Architektur = Option C:

- **Linear Coordinator** (Sonnet) führt Workflow aus
- **Module** (Haiku) für spezifische Tasks
- **Tools** (APIs) für externe Daten
- **Parallel** wo möglich (ThreadPoolExecutor)

---

**Status:** Ready to update Roadmap
**Next:** Update V2_ROADMAP.md mit Option C
