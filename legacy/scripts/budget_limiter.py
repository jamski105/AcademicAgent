#!/usr/bin/env python3
"""
Budget Limiter - Token-Budget-Enforcement für Claude API

Zweck:
    - Verhindert unerwartete hohe API-Kosten
    - Warnt bei 80% Budget-Auslastung
    - Stoppt bei 100% Budget-Auslastung
    - Trackt Budget pro Run und Global

Verwendung:
    python3 scripts/budget_limiter.py check --run-id 2026-02-18_14-30-00
    python3 scripts/budget_limiter.py set-limit --amount 10.00 --run-id 2026-02-18_14-30-00
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any, Optional


class BudgetLimiter:
    """Enforcet Token-Budget-Limits"""

    def __init__(self, run_id: str, run_dir: Path = None):
        self.run_id = run_id
        self.run_dir = run_dir or Path(f"runs/{run_id}")
        self.cost_file = self.run_dir / "metadata" / "llm_costs.jsonl"
        self.budget_file = self.run_dir / "metadata" / "budget.json"

    def set_budget(self, max_cost_usd: float, currency: str = "USD"):
        """
        Setzt Budget-Limit für Run

        Args:
            max_cost_usd: Maximale Kosten in USD
            currency: Währung (default: USD)
        """
        budget_data = {
            "max_cost": max_cost_usd,
            "currency": currency,
            "run_id": self.run_id,
            "alerts": {
                "warning_threshold": 0.8,  # 80%
                "critical_threshold": 1.0   # 100%
            }
        }

        self.budget_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.budget_file, 'w') as f:
            json.dump(budget_data, f, indent=2)

        print(f"✅ Budget gesetzt: ${max_cost_usd} USD für Run {self.run_id}")

    def get_budget(self) -> Optional[Dict[str, Any]]:
        """Lädt Budget-Konfiguration"""
        if not self.budget_file.exists():
            return None

        with open(self.budget_file, 'r') as f:
            return json.load(f)

    def get_current_costs(self) -> float:
        """Berechnet aktuelle Kosten aus llm_costs.jsonl"""
        if not self.cost_file.exists():
            return 0.0

        total_cost = 0.0

        with open(self.cost_file, 'r') as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    total_cost += entry.get("cost_usd", 0.0)
                except:
                    pass

        return total_cost

    def check_budget(self) -> Dict[str, Any]:
        """
        Prüft Budget-Status

        Returns:
            Dict mit:
                - allowed: bool (weitere Aufrufe erlaubt?)
                - current_cost: float
                - max_cost: float
                - usage_percent: float
                - status: str (OK/WARNING/CRITICAL)
                - message: str
        """
        budget = self.get_budget()

        if not budget:
            # Kein Budget gesetzt = alles erlaubt
            return {
                "allowed": True,
                "current_cost": 0.0,
                "max_cost": None,
                "usage_percent": 0.0,
                "status": "NO_BUDGET",
                "message": "Kein Budget gesetzt - alle Aufrufe erlaubt"
            }

        current_cost = self.get_current_costs()
        max_cost = budget["max_cost"]
        usage_percent = (current_cost / max_cost) * 100 if max_cost > 0 else 0

        warning_threshold = budget["alerts"]["warning_threshold"]
        critical_threshold = budget["alerts"]["critical_threshold"]

        # Bestimme Status
        if usage_percent >= (critical_threshold * 100):
            status = "CRITICAL"
            allowed = False
            message = f"🚨 BUDGET ÜBERSCHRITTEN! ${current_cost:.2f} / ${max_cost:.2f} ({usage_percent:.1f}%)"
        elif usage_percent >= (warning_threshold * 100):
            status = "WARNING"
            allowed = True
            message = f"⚠️  BUDGET-WARNUNG! ${current_cost:.2f} / ${max_cost:.2f} ({usage_percent:.1f}%) - Limit bald erreicht"
        else:
            status = "OK"
            allowed = True
            message = f"✅ Budget OK: ${current_cost:.2f} / ${max_cost:.2f} ({usage_percent:.1f}%)"

        return {
            "allowed": allowed,
            "current_cost": current_cost,
            "max_cost": max_cost,
            "usage_percent": usage_percent,
            "status": status,
            "message": message
        }


def main():
    """CLI-Entry-Point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Budget Limiter - Token-Budget-Enforcement",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
    # Budget setzen
    python3 scripts/budget_limiter.py set-limit --run-id 2026-02-18_14-30-00 --amount 10.00

    # Budget prüfen
    python3 scripts/budget_limiter.py check --run-id 2026-02-18_14-30-00

    # JSON-Output
    python3 scripts/budget_limiter.py check --run-id 2026-02-18_14-30-00 --json
        """
    )

    parser.add_argument(
        "command",
        choices=["check", "set-limit", "status"],
        help="Command"
    )

    parser.add_argument(
        "--run-id",
        required=True,
        help="Run-ID (z.B. 2026-02-18_14-30-00)"
    )

    parser.add_argument(
        "--amount",
        type=float,
        help="Budget-Betrag in USD (für set-limit)"
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Output als JSON"
    )

    args = parser.parse_args()

    limiter = BudgetLimiter(run_id=args.run_id)

    if args.command == "set-limit":
        if not args.amount:
            print("❌ --amount erforderlich für set-limit", file=sys.stderr)
            sys.exit(1)

        limiter.set_budget(max_cost_usd=args.amount)
        sys.exit(0)

    elif args.command in ["check", "status"]:
        result = limiter.check_budget()

        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(result["message"])
            if result["status"] == "OK":
                print(f"  Verbleibend: ${result['max_cost'] - result['current_cost']:.2f}")
            elif result["status"] == "WARNING":
                print(f"  🔴 Noch ${result['max_cost'] - result['current_cost']:.2f} bis Limit")
            elif result["status"] == "CRITICAL":
                print(f"  ❌ Überschreitung: ${result['current_cost'] - result['max_cost']:.2f}")

        # Exit-Code basierend auf Status
        if result["status"] == "CRITICAL":
            sys.exit(2)
        elif result["status"] == "WARNING":
            sys.exit(1)
        else:
            sys.exit(0)


if __name__ == "__main__":
    main()
