#!/usr/bin/env python3
"""
Cost-Tracker für AcademicAgent
Trackt Claude-API-Token-Usage und berechnet Kosten

Verwendung:
    from scripts.cost_tracker import CostTracker, CLAUDE_MODELS

    tracker = CostTracker(run_dir="runs/2026-02-18_14-30-00")

    # Nach Agent-Call
    tracker.record_llm_call(
        agent_name="browser-agent",
        model="claude-opus-4",
        input_tokens=1500,
        output_tokens=800,
        phase=2
    )

    # Summary abrufen
    summary = tracker.get_summary()
    print(f"Gesamt-Kosten: ${summary['total_cost_usd']:.2f}")
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict


# ============================================
# Claude-Modell-Preise (Stand: Februar 2026)
# ============================================

@dataclass
class ModelPricing:
    """Preisinformationen für Claude-Modell"""
    name: str
    input_price_per_mtok: float  # USD per Million Input Tokens
    output_price_per_mtok: float  # USD per Million Output Tokens
    context_window: int  # Max Tokens


# Preise basierend auf Anthropic Pricing (Februar 2026)
# https://www.anthropic.com/pricing
CLAUDE_MODELS = {
    "claude-opus-4-6": ModelPricing(
        name="Claude Opus 4.6",
        input_price_per_mtok=15.00,
        output_price_per_mtok=75.00,
        context_window=200000
    ),
    "claude-opus-4": ModelPricing(
        name="Claude Opus 4",
        input_price_per_mtok=15.00,
        output_price_per_mtok=75.00,
        context_window=200000
    ),
    "claude-sonnet-4-5": ModelPricing(
        name="Claude Sonnet 4.5",
        input_price_per_mtok=3.00,
        output_price_per_mtok=15.00,
        context_window=200000
    ),
    "claude-sonnet-4": ModelPricing(
        name="Claude Sonnet 4",
        input_price_per_mtok=3.00,
        output_price_per_mtok=15.00,
        context_window=200000
    ),
    "claude-haiku-4": ModelPricing(
        name="Claude Haiku 4",
        input_price_per_mtok=0.80,
        output_price_per_mtok=4.00,
        context_window=200000
    )
}


@dataclass
class LLMCall:
    """Einzelner LLM-Call"""
    timestamp: str
    agent_name: str
    model: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cost_usd: float
    phase: Optional[int] = None
    iteration: Optional[int] = None
    run_id: Optional[str] = None


class CostTracker:
    """
    Cost-Tracker für Claude-API-Calls

    Tracked Token-Usage und berechnet Kosten pro Research-Run
    """

    def __init__(self, run_dir: Optional[Path] = None, run_id: Optional[str] = None):
        """
        Initialisiert Cost-Tracker

        Args:
            run_dir: Run-Verzeichnis (z.B. runs/2026-02-18_14-30-00/)
            run_id: Run-ID (falls kein run_dir gegeben)
        """
        self.run_dir = Path(run_dir) if run_dir else None
        self.run_id = run_id or (run_dir.name if run_dir else "unknown")

        # In-Memory-Calls
        self.calls: List[LLMCall] = []

        # Cost-Tracking-Datei
        if self.run_dir:
            self.cost_file = self.run_dir / "metadata" / "llm_costs.jsonl"
            self.cost_file.parent.mkdir(parents=True, exist_ok=True)
        else:
            self.cost_file = Path("llm_costs.jsonl")

    def calculate_cost(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """
        Berechnet Kosten für LLM-Call

        Args:
            model: Modell-Name (z.B. "claude-opus-4")
            input_tokens: Anzahl Input-Tokens
            output_tokens: Anzahl Output-Tokens

        Returns:
            Kosten in USD
        """
        if model not in CLAUDE_MODELS:
            # Fallback: Verwende Opus-Preise (höchste)
            print(f"⚠️  Unbekanntes Modell '{model}', verwende Opus-Preise")
            model = "claude-opus-4"

        pricing = CLAUDE_MODELS[model]

        # Berechne Kosten
        input_cost = (input_tokens / 1_000_000) * pricing.input_price_per_mtok
        output_cost = (output_tokens / 1_000_000) * pricing.output_price_per_mtok
        total_cost = input_cost + output_cost

        return total_cost

    def record_llm_call(
        self,
        agent_name: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        phase: Optional[int] = None,
        iteration: Optional[int] = None
    ):
        """
        Erfasst einen LLM-Call

        Args:
            agent_name: Name des Agents (z.B. "browser-agent", "orchestrator")
            model: Modell-Name (z.B. "claude-opus-4")
            input_tokens: Anzahl Input-Tokens
            output_tokens: Anzahl Output-Tokens
            phase: Optional Phase-Nummer (0-6)
            iteration: Optional Iteration (für Phase 2)
        """
        total_tokens = input_tokens + output_tokens
        cost = self.calculate_cost(model, input_tokens, output_tokens)

        call = LLMCall(
            timestamp=datetime.utcnow().isoformat() + "Z",
            agent_name=agent_name,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            cost_usd=cost,
            phase=phase,
            iteration=iteration,
            run_id=self.run_id
        )

        self.calls.append(call)
        self._persist(call)

        return call

    def _persist(self, call: LLMCall):
        """Schreibt Call in JSONL-Datei"""
        with open(self.cost_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(call)) + "\n")

    def get_summary(self) -> Dict[str, Any]:
        """
        Erstellt Kosten-Zusammenfassung

        Returns:
            Dict mit aggregierten Statistiken
        """
        if not self.calls:
            return {
                "total_cost_usd": 0.0,
                "total_calls": 0,
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "total_tokens": 0,
                "by_agent": {},
                "by_phase": {},
                "by_model": {}
            }

        # Aggregiere Gesamt
        total_cost = sum(c.cost_usd for c in self.calls)
        total_input = sum(c.input_tokens for c in self.calls)
        total_output = sum(c.output_tokens for c in self.calls)
        total_tokens = sum(c.total_tokens for c in self.calls)

        # Aggregiere nach Agent
        by_agent = {}
        for call in self.calls:
            if call.agent_name not in by_agent:
                by_agent[call.agent_name] = {
                    "calls": 0,
                    "cost_usd": 0.0,
                    "input_tokens": 0,
                    "output_tokens": 0
                }
            by_agent[call.agent_name]["calls"] += 1
            by_agent[call.agent_name]["cost_usd"] += call.cost_usd
            by_agent[call.agent_name]["input_tokens"] += call.input_tokens
            by_agent[call.agent_name]["output_tokens"] += call.output_tokens

        # Aggregiere nach Phase
        by_phase = {}
        for call in self.calls:
            if call.phase is not None:
                phase_key = f"phase_{call.phase}"
                if phase_key not in by_phase:
                    by_phase[phase_key] = {
                        "calls": 0,
                        "cost_usd": 0.0,
                        "tokens": 0
                    }
                by_phase[phase_key]["calls"] += 1
                by_phase[phase_key]["cost_usd"] += call.cost_usd
                by_phase[phase_key]["tokens"] += call.total_tokens

        # Aggregiere nach Modell
        by_model = {}
        for call in self.calls:
            if call.model not in by_model:
                by_model[call.model] = {
                    "calls": 0,
                    "cost_usd": 0.0,
                    "tokens": 0
                }
            by_model[call.model]["calls"] += 1
            by_model[call.model]["cost_usd"] += call.cost_usd
            by_model[call.model]["tokens"] += call.total_tokens

        return {
            "total_cost_usd": round(total_cost, 4),
            "total_calls": len(self.calls),
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "total_tokens": total_tokens,
            "by_agent": by_agent,
            "by_phase": by_phase,
            "by_model": by_model,
            "run_id": self.run_id
        }

    def export_summary(self, output_file: Optional[Path] = None):
        """
        Exportiert Kosten-Summary als JSON

        Args:
            output_file: Output-Datei (default: run_dir/metadata/cost_summary.json)
        """
        if output_file is None:
            output_file = self.run_dir / "metadata" / "cost_summary.json" if self.run_dir else Path("cost_summary.json")

        summary = self.get_summary()

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        return output_file

    def print_report(self):
        """Druckt formatierte Kosten-Report"""
        summary = self.get_summary()

        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("💰 LLM KOSTEN-REPORT")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print()

        print(f"🆔 Run-ID: {summary['run_id']}")
        print(f"💵 Gesamt-Kosten: ${summary['total_cost_usd']:.2f} USD")
        print(f"📊 Gesamt-Calls: {summary['total_calls']}")
        print(f"🔢 Gesamt-Tokens: {summary['total_tokens']:,}")
        print(f"   ├─ Input:  {summary['total_input_tokens']:,}")
        print(f"   └─ Output: {summary['total_output_tokens']:,}")
        print()

        if summary['by_agent']:
            print("📦 Kosten nach Agent:")
            for agent, stats in sorted(summary['by_agent'].items(), key=lambda x: x[1]['cost_usd'], reverse=True):
                cost_pct = (stats['cost_usd'] / summary['total_cost_usd']) * 100 if summary['total_cost_usd'] > 0 else 0
                print(f"   {agent:20s} ${stats['cost_usd']:6.2f} ({cost_pct:5.1f}%) | {stats['calls']} Calls")
            print()

        if summary['by_phase']:
            print("🔄 Kosten nach Phase:")
            for phase_key in sorted(summary['by_phase'].keys()):
                stats = summary['by_phase'][phase_key]
                cost_pct = (stats['cost_usd'] / summary['total_cost_usd']) * 100 if summary['total_cost_usd'] > 0 else 0
                print(f"   {phase_key:15s} ${stats['cost_usd']:6.2f} ({cost_pct:5.1f}%) | {stats['tokens']:,} Tokens")
            print()

        if summary['by_model']:
            print("🤖 Kosten nach Modell:")
            for model, stats in sorted(summary['by_model'].items(), key=lambda x: x[1]['cost_usd'], reverse=True):
                cost_pct = (stats['cost_usd'] / summary['total_cost_usd']) * 100 if summary['total_cost_usd'] > 0 else 0
                print(f"   {model:25s} ${stats['cost_usd']:6.2f} ({cost_pct:5.1f}%)")
            print()

        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")


def load_costs_from_file(cost_file: Path) -> CostTracker:
    """
    Lädt Kosten aus JSONL-Datei

    Args:
        cost_file: Pfad zur llm_costs.jsonl

    Returns:
        CostTracker mit geladenen Calls
    """
    run_dir = cost_file.parent.parent  # metadata/llm_costs.jsonl -> run_dir
    tracker = CostTracker(run_dir=run_dir)

    if not cost_file.exists():
        return tracker

    with open(cost_file, "r", encoding="utf-8") as f:
        for line in f:
            call_dict = json.loads(line.strip())
            call = LLMCall(**call_dict)
            tracker.calls.append(call)

    return tracker


# ============================================
# Beispiel-Verwendung
# ============================================

if __name__ == "__main__":
    print("🧪 Teste Cost-Tracker...\n")

    # Erstelle Test-Run-Dir
    test_dir = Path("runs/test_cost_tracking")
    test_dir.mkdir(parents=True, exist_ok=True)

    # Erstelle Tracker
    tracker = CostTracker(run_dir=test_dir)

    print("Test 1: Simuliere Research-Run mit mehreren Agents\n")

    # Phase 0: DBIS-Navigation (Browser-Agent)
    tracker.record_llm_call(
        agent_name="browser-agent",
        model="claude-sonnet-4",
        input_tokens=2500,
        output_tokens=800,
        phase=0
    )

    # Phase 1: Suchstring-Generierung (Search-Agent)
    tracker.record_llm_call(
        agent_name="search-agent",
        model="claude-opus-4",
        input_tokens=1200,
        output_tokens=600,
        phase=1
    )

    # Phase 2: Datenbanksuche - Iteration 1 (Browser-Agent)
    for i in range(5):  # 5 Datenbanken
        tracker.record_llm_call(
            agent_name="browser-agent",
            model="claude-sonnet-4",
            input_tokens=3000,
            output_tokens=1200,
            phase=2,
            iteration=1
        )

    # Phase 2: Iteration 2
    for i in range(5):
        tracker.record_llm_call(
            agent_name="browser-agent",
            model="claude-sonnet-4",
            input_tokens=3000,
            output_tokens=1200,
            phase=2,
            iteration=2
        )

    # Phase 3: Scoring (Scoring-Agent mit Opus für bessere Qualität)
    tracker.record_llm_call(
        agent_name="scoring-agent",
        model="claude-opus-4",
        input_tokens=5000,
        output_tokens=2000,
        phase=3
    )

    # Phase 4: PDF-Download (Browser-Agent)
    for i in range(18):  # 18 PDFs
        tracker.record_llm_call(
            agent_name="browser-agent",
            model="claude-haiku-4",  # Haiku für einfache Downloads
            input_tokens=500,
            output_tokens=200,
            phase=4
        )

    # Phase 5: Zitat-Extraktion (Extraction-Agent)
    for i in range(18):
        tracker.record_llm_call(
            agent_name="extraction-agent",
            model="claude-opus-4",  # Opus für hohe Qualität
            input_tokens=4000,
            output_tokens=1500,
            phase=5
        )

    print(f"✅ {len(tracker.calls)} LLM-Calls simuliert\n")

    # Report anzeigen
    tracker.print_report()

    # Summary exportieren
    summary_file = tracker.export_summary()
    print(f"📊 Summary exportiert: {summary_file}")
    print(f"📊 Cost-Datei: {tracker.cost_file}")

    print("\n✅ Cost-Tracking-Test abgeschlossen!")
