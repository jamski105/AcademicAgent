#!/usr/bin/env python3

"""
Dynamic Config Generator - AcademicAgent
Generates optimized config based on research mode and user dialog
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

# Research Mode Configurations
RESEARCH_MODES = {
    "quick_quote": {
        "name": "Quick Quote Mode",
        "target_total": 8,
        "target_quotes": "8-12",
        "databases_count": 3,
        "min_year_offset": 5,  # Last 5 years
        "citation_threshold": 20,
        "peer_reviewed": True,
        "phases": [0, 1, 2, 3, 4, 5, 6],
        "extraction_focus": "targeted",  # Only most relevant quotes
        "search_strings_limit": 15,
    },
    "deep_research": {
        "name": "Deep Research Mode",
        "target_total": 18,
        "target_quotes": "40-50",
        "databases_count": 8,
        "min_year_offset": 10,
        "citation_threshold": 50,
        "peer_reviewed": True,
        "phases": [0, 1, 2, 3, 4, 5, 6],
        "extraction_focus": "comprehensive",
        "search_strings_limit": 30,
    },
    "chapter_support": {
        "name": "Chapter Support Mode",
        "target_total": 12,
        "target_quotes": "20-30",
        "databases_count": 5,
        "min_year_offset": 7,
        "citation_threshold": 30,
        "peer_reviewed": True,
        "phases": [0, 1, 2, 3, 4, 5, 6],
        "extraction_focus": "chapter_relevant",
        "search_strings_limit": 20,
    },
    "citation_expansion": {
        "name": "Citation Expansion Mode",
        "target_total": 12,
        "target_quotes": "25-35",
        "databases_count": 2,  # Scopus, Web of Science
        "min_year_offset": 10,
        "citation_threshold": 10,
        "peer_reviewed": True,
        "phases": [1, 2, 3, 4, 5, 6],  # Skip Phase 0 (DBIS)
        "extraction_focus": "comprehensive",
        "search_strings_limit": 10,
        "special": "snowballing",
    },
    "trend_analysis": {
        "name": "Trend Analysis Mode",
        "target_total": 10,
        "target_quotes": "15-25",
        "databases_count": 4,
        "min_year_offset": 2,  # Last 2 years only
        "citation_threshold": 0,  # Include new papers
        "peer_reviewed": False,  # Include preprints
        "phases": [0, 1, 2, 3, 4, 5, 6],
        "extraction_focus": "recent_trends",
        "search_strings_limit": 15,
        "special": "sort_by_date",
    },
    "controversy_mapping": {
        "name": "Controversy Mapping Mode",
        "target_total": 16,
        "target_quotes": "30-40",
        "databases_count": 6,
        "min_year_offset": 8,
        "citation_threshold": 30,
        "peer_reviewed": True,
        "phases": [0, 1, 2, 3, 4, 5, 6],
        "extraction_focus": "balanced_perspectives",
        "search_strings_limit": 25,
        "special": "pro_contra_balance",
    },
    "survey_overview": {
        "name": "Survey/Overview Mode",
        "target_total": 40,
        "target_quotes": "60-80",
        "databases_count": 9,
        "min_year_offset": 12,
        "citation_threshold": 50,
        "peer_reviewed": True,
        "phases": [0, 1, 2, 3, 4, 5, 6],
        "extraction_focus": "systematic_review",
        "search_strings_limit": 40,
        "special": "prisma_flow",
    },
}

# Discipline-specific database mappings
DISCIPLINE_DATABASES = {
    "informatik": [
        "IEEE Xplore",
        "ACM Digital Library",
        "SpringerLink",
        "Scopus",
        "ScienceDirect",
        "arXiv",
        "Web of Science",
    ],
    "jura": [
        "Beck-Online",
        "Juris",
        "HeinOnline",
        "SpringerLink",
        "JSTOR",
    ],
    "medizin": [
        "PubMed",
        "Cochrane Library",
        "Scopus",
        "SpringerLink",
        "ScienceDirect",
        "Web of Science",
    ],
    "bwl": [
        "EBSCO Business Source",
        "JSTOR",
        "SpringerLink",
        "Scopus",
        "ScienceDirect",
        "Web of Science",
    ],
    "ingenieurwesen": [
        "IEEE Xplore",
        "SpringerLink",
        "Scopus",
        "ScienceDirect",
        "Web of Science",
    ],
    "sozialwissenschaften": [
        "JSTOR",
        "EBSCO",
        "Scopus",
        "SpringerLink",
        "Web of Science",
    ],
    "geisteswissenschaften": [
        "JSTOR",
        "SpringerLink",
        "MLA International Bibliography",
        "Web of Science",
    ],
}


def generate_config(
    mode,
    question,
    keywords,
    discipline,
    databases=None,
    min_year=None,
    min_citations=None,
    peer_reviewed=None,
    output_path=None,
    context=None,
):
    """Generate config file based on parameters"""

    if mode not in RESEARCH_MODES:
        print(f"Fehler: Unbekannter Modus '{mode}'")
        print(f"Verfügbare Modi: {', '.join(RESEARCH_MODES.keys())}")
        sys.exit(1)

    mode_config = RESEARCH_MODES[mode]

    # Get discipline databases
    discipline_key = discipline.lower().replace(" ", "").replace("/", "")
    if discipline_key not in DISCIPLINE_DATABASES:
        # Try partial match
        for key in DISCIPLINE_DATABASES:
            if key in discipline_key or discipline_key in key:
                discipline_key = key
                break
        else:
            discipline_key = "informatik"  # Default

    discipline_dbs = DISCIPLINE_DATABASES[discipline_key]

    # Select databases
    if databases is None:
        # Use first N databases from discipline list
        databases = discipline_dbs[: mode_config["databases_count"]]
    else:
        databases = databases.split(",")

    # Calculate min_year
    if min_year is None:
        current_year = datetime.now().year
        min_year = current_year - mode_config["min_year_offset"]

    # Set defaults
    if min_citations is None:
        min_citations = mode_config["citation_threshold"]

    if peer_reviewed is None:
        peer_reviewed = mode_config["peer_reviewed"]

    # Parse keywords
    if isinstance(keywords, str):
        keywords = json.loads(keywords)

    # Generate project name
    project_name = (
        question.replace(" ", "_")
        .replace("?", "")
        .replace("'", "")[:50]
    )

    # Generate config content
    config_content = f"""# 📋 Config - {project_name}

**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Mode:** {mode_config["name"]}
**Estimated Duration:** {get_estimated_duration(mode)}

---

## 1. PROJECT INFO

**Projekt-Titel:**
```
{project_name}
```

**Disziplin:**
```
{discipline}
```

**Forschungsfrage:**
```
{question}
```

**Kontext:**
```
{context or "Interactive Setup - User-guided research"}
```

**Recherche-Modus:**
```
{mode_config["name"]}

{get_mode_description(mode)}
```

---

## 2. SEARCH CLUSTERS

"""

    # Add keyword clusters
    for i, (cluster_name, cluster_terms) in enumerate(keywords.items(), 1):
        config_content += f"""### Cluster {i}: {cluster_name}

**EN:**
```
{chr(10).join(f"- {term}" for term in cluster_terms)}
```

---

"""

    config_content += f"""## 3. DATABASES

**Primary Databases ({len(databases)}):**
```
{chr(10).join(f"- {db}" for db in databases)}
```

**Rationale:** Selected for {discipline} research, optimized for {mode_config["name"]}

---

## 4. TARGETS

**Target Total:**
```
{mode_config["target_total"]} Quellen
```

**Target Quotes:**
```
{mode_config["target_quotes"]} Zitate
```

**Extraction Strategy:**
```
{mode_config["extraction_focus"]}
```

---

## 5. QUALITY THRESHOLDS

**Min Year:**
```
{min_year}
```

**Citation Threshold:**
```
{min_citations} Citations (minimum)
```

**Peer-Reviewed Only:**
```
{peer_reviewed}
```

**Document Types:**
```
- Journal Articles: ✅
- Conference Papers: ✅
- Book Chapters: {"✅" if mode != "trend_analysis" else "❌"}
- Preprints: {"✅" if mode == "trend_analysis" else "❌"}
```

---

## 6. SPECIAL CONFIGURATIONS

**Active Phases:**
```
{", ".join(f"Phase {p}" for p in mode_config["phases"])}
```

**Search Strings Limit:**
```
{mode_config["search_strings_limit"]} strings (per database)
```

**Special Features:**
```
{get_special_features(mode)}
```

---

## 7. OUTPUT SPECIFICATIONS

**Generated Files:**
```
1. Quote Library (CSV): {mode_config["target_quotes"]} Zitate
2. Annotated Bibliography (Markdown): {mode_config["target_total"]} Quellen
3. PDFs: {mode_config["target_total"]} Files
4. Self-Assessment: Rating + Metrics
{get_mode_specific_outputs(mode)}
```

**Working Directory:**
```
~/AcademicAgent/runs/{run_id}/
```

---

## 8. METADATA

**Generated By:** Interactive Setup Agent
**Mode:** {mode}
**Timestamp:** {datetime.now().isoformat()}

---

**Ready for Orchestrator handoff!** 🚀
"""

    # Write to file
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"config/Config_Interactive_{timestamp}.md"

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(config_content)

    print(f"✅ Config generiert: {output_file}")
    print(f"📋 Modus: {mode_config['name']}")
    print(f"🎯 Ziel: {mode_config['target_total']} Quellen")
    print(f"⏱️ Geschätzt: {get_estimated_duration(mode)}")

    return output_file


def get_estimated_duration(mode):
    """Get estimated duration for mode"""
    durations = {
        "quick_quote": "30-45 Min",
        "deep_research": "3.5-4.5 h",
        "chapter_support": "1.5-2 h",
        "citation_expansion": "1-1.5 h",
        "trend_analysis": "1-1.5 h",
        "controversy_mapping": "2-2.5 h",
        "survey_overview": "5-6 h",
    }
    return durations.get(mode, "Unknown")


def get_mode_description(mode):
    """Get description for mode"""
    descriptions = {
        "quick_quote": "Fast targeted search for specific quotes. Optimized for speed.",
        "deep_research": "Comprehensive literature review. Full pipeline with all databases.",
        "chapter_support": "Targeted search for specific chapter/section. Balanced depth.",
        "citation_expansion": "Snowballing from existing papers. Uses citation networks.",
        "trend_analysis": "Focus on newest publications. Includes preprints and recent papers.",
        "controversy_mapping": "Find balanced pro/contra perspectives on a topic.",
        "survey_overview": "Systematic literature review. PRISMA-style comprehensive search.",
    }
    return descriptions.get(mode, "")


def get_special_features(mode):
    """Get special features for mode"""
    features = {
        "quick_quote": "- Reduced database count\n- Focused extraction\n- Fast turnaround",
        "deep_research": "- All databases\n- Comprehensive extraction\n- Full quality scoring",
        "chapter_support": "- Chapter-specific keywords\n- Relevance scoring for section\n- Categorized by topic",
        "citation_expansion": "- Forward/backward citation search\n- Snowballing strategy\n- Citation network analysis",
        "trend_analysis": "- Sort by publication date\n- Include preprints\n- Focus on last 2 years",
        "controversy_mapping": "- Pro/Contra keyword sets\n- Balanced source selection\n- Perspective categorization",
        "survey_overview": "- PRISMA flow diagram\n- Inclusion/exclusion tracking\n- Quality assessment table",
    }
    return features.get(mode, "None")


def get_mode_specific_outputs(mode):
    """Get mode-specific output files"""
    outputs = {
        "citation_expansion": "\n5. Citation Network Graph (JSON)",
        "survey_overview": "\n5. PRISMA Flow Diagram (PNG)\n6. Quality Assessment Table (CSV)",
        "controversy_mapping": "\n5. Perspective Matrix (CSV)",
    }
    return outputs.get(mode, "")


def main():
    parser = argparse.ArgumentParser(
        description="Generate research config dynamically"
    )

    parser.add_argument(
        "--mode",
        required=True,
        choices=list(RESEARCH_MODES.keys()),
        help="Research mode",
    )

    parser.add_argument(
        "--question", required=True, help="Research question"
    )

    parser.add_argument(
        "--keywords",
        required=True,
        help='Keywords as JSON string (e.g., \'{"Cluster 1": ["term1", "term2"]}\')',
    )

    parser.add_argument(
        "--discipline", required=True, help="Academic discipline"
    )

    parser.add_argument(
        "--databases", help="Comma-separated database list (optional)"
    )

    parser.add_argument(
        "--min-year", type=int, help="Minimum publication year"
    )

    parser.add_argument(
        "--min-citations", type=int, help="Minimum citation count"
    )

    parser.add_argument(
        "--peer-reviewed",
        type=lambda x: x.lower() == "true",
        help="Peer-reviewed only (true/false)",
    )

    parser.add_argument("--output", help="Output file path")

    parser.add_argument("--context", help="Research context (optional)")

    args = parser.parse_args()

    generate_config(
        mode=args.mode,
        question=args.question,
        keywords=args.keywords,
        discipline=args.discipline,
        databases=args.databases,
        min_year=args.min_year,
        min_citations=args.min_citations,
        peer_reviewed=args.peer_reviewed,
        output_path=args.output,
        context=args.context,
    )


if __name__ == "__main__":
    main()
