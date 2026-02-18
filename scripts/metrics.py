#!/usr/bin/env python3
"""
Metrics-System für AcademicAgent
Erfasst Performance-Metriken, Kosten und System-Health

Features:
    - Performance-Tracking (Dauer, Durchsatz)
    - Error-Rate-Tracking
    - Database-Performance-Metriken
    - Iteration-Statistiken
    - Export zu JSONL für Analyse
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from contextlib import contextmanager


@dataclass
class Metric:
    """Einzelne Metrik"""
    timestamp: str
    metric_name: str
    value: float
    unit: str
    labels: Dict[str, str]
    run_id: Optional[str] = None


class MetricsCollector:
    """
    Metrics-Collector für AcademicAgent

    Sammelt und persistiert Metriken pro Research-Run
    """

    def __init__(self, run_dir: Optional[Path] = None, run_id: Optional[str] = None):
        """
        Initialisiert Metrics-Collector

        Args:
            run_dir: Run-Verzeichnis (z.B. runs/2026-02-18_14-30-00/)
            run_id: Run-ID (falls kein run_dir gegeben)
        """
        self.run_dir = Path(run_dir) if run_dir else None
        self.run_id = run_id or (run_dir.name if run_dir else "unknown")

        # In-Memory-Metrics
        self.metrics: List[Metric] = []

        # Metrics-Datei
        if self.run_dir:
            self.metrics_file = self.run_dir / "metadata" / "metrics.jsonl"
            self.metrics_file.parent.mkdir(parents=True, exist_ok=True)
        else:
            self.metrics_file = Path("metrics.jsonl")

    def record(
        self,
        metric_name: str,
        value: float,
        unit: str = "count",
        labels: Optional[Dict[str, str]] = None
    ):
        """
        Erfasst eine Metrik

        Args:
            metric_name: Name der Metrik (z.B. "iteration.duration")
            value: Wert (numerisch)
            unit: Einheit (count, seconds, bytes, percent, etc.)
            labels: Optional Labels (z.B. {"database": "IEEE", "phase": "2"})

        Beispiel:
            collector.record("iteration.duration", 35.2, unit="seconds",
                            labels={"iteration": "1", "database_count": "5"})
        """
        metric = Metric(
            timestamp=datetime.utcnow().isoformat() + "Z",
            metric_name=metric_name,
            value=value,
            unit=unit,
            labels=labels or {},
            run_id=self.run_id
        )

        self.metrics.append(metric)
        self._persist(metric)

    def _persist(self, metric: Metric):
        """Schreibt Metrik in JSONL-Datei"""
        with open(self.metrics_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(metric)) + "\n")

    @contextmanager
    def measure_time(self, metric_name: str, labels: Optional[Dict[str, str]] = None):
        """
        Context-Manager für Zeit-Messung

        Verwendung:
            with collector.measure_time("database.search", labels={"database": "IEEE"}):
                # Code der gemessen werden soll
                search_database()
        """
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            self.record(metric_name, duration, unit="seconds", labels=labels)

    def increment(self, metric_name: str, labels: Optional[Dict[str, str]] = None):
        """
        Inkrementiert einen Counter

        Args:
            metric_name: Name des Counters (z.B. "errors.total")
            labels: Optional Labels
        """
        self.record(metric_name, 1.0, unit="count", labels=labels)

    def gauge(self, metric_name: str, value: float, unit: str = "count",
              labels: Optional[Dict[str, str]] = None):
        """
        Setzt einen Gauge-Wert (Momentaufnahme)

        Args:
            metric_name: Name des Gauge (z.B. "memory.usage")
            value: Aktueller Wert
            unit: Einheit
            labels: Optional Labels
        """
        self.record(metric_name, value, unit=unit, labels=labels)

    def get_summary(self) -> Dict[str, Any]:
        """
        Erstellt Zusammenfassung aller Metriken

        Returns:
            Dict mit aggregierten Statistiken
        """
        if not self.metrics:
            return {"error": "Keine Metriken erfasst"}

        # Aggregiere nach Metrik-Namen
        summary = {}

        for metric in self.metrics:
            name = metric.metric_name

            if name not in summary:
                summary[name] = {
                    "count": 0,
                    "sum": 0.0,
                    "min": float('inf'),
                    "max": float('-inf'),
                    "unit": metric.unit,
                    "values": []
                }

            summary[name]["count"] += 1
            summary[name]["sum"] += metric.value
            summary[name]["min"] = min(summary[name]["min"], metric.value)
            summary[name]["max"] = max(summary[name]["max"], metric.value)
            summary[name]["values"].append(metric.value)

        # Berechne Durchschnitte
        for name, stats in summary.items():
            stats["avg"] = stats["sum"] / stats["count"]
            del stats["values"]  # Sparen Speicher

        return summary

    def export_summary(self, output_file: Optional[Path] = None):
        """
        Exportiert Zusammenfassung als JSON

        Args:
            output_file: Output-Datei (default: run_dir/metadata/metrics_summary.json)
        """
        if output_file is None:
            output_file = self.run_dir / "metadata" / "metrics_summary.json" if self.run_dir else Path("metrics_summary.json")

        summary = self.get_summary()

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        return output_file


class IterationMetrics:
    """
    Spezialisierte Metriken für Iterations-Tracking (Phase 2)
    """

    def __init__(self, collector: MetricsCollector):
        self.collector = collector
        self.iteration_starts = {}  # iteration_num -> start_time

    def start_iteration(self, iteration: int, database_count: int):
        """Startet Iteration-Tracking"""
        self.iteration_starts[iteration] = time.time()
        self.collector.gauge(
            "iteration.started",
            iteration,
            labels={"iteration": str(iteration), "database_count": str(database_count)}
        )

    def end_iteration(
        self,
        iteration: int,
        papers_found: int,
        databases_searched: List[str],
        errors: int = 0
    ):
        """Beendet Iteration-Tracking"""
        if iteration not in self.iteration_starts:
            return

        duration = time.time() - self.iteration_starts[iteration]

        # Duration
        self.collector.record(
            "iteration.duration",
            duration,
            unit="seconds",
            labels={"iteration": str(iteration)}
        )

        # Papers gefunden
        self.collector.record(
            "iteration.papers_found",
            papers_found,
            unit="count",
            labels={"iteration": str(iteration)}
        )

        # Durchsatz (Papers/Minute)
        throughput = (papers_found / duration) * 60 if duration > 0 else 0
        self.collector.record(
            "iteration.throughput",
            throughput,
            unit="papers_per_minute",
            labels={"iteration": str(iteration)}
        )

        # Fehler
        if errors > 0:
            self.collector.record(
                "iteration.errors",
                errors,
                unit="count",
                labels={"iteration": str(iteration)}
            )

        # Datenbanken
        for db in databases_searched:
            self.collector.increment(
                "database.searches",
                labels={"database": db, "iteration": str(iteration)}
            )

        del self.iteration_starts[iteration]


class DatabaseMetrics:
    """
    Spezialisierte Metriken für Datenbank-Performance
    """

    def __init__(self, collector: MetricsCollector):
        self.collector = collector

    def record_search(
        self,
        database: str,
        papers_found: int,
        duration: float,
        success: bool = True
    ):
        """Erfasst Datenbank-Suche"""
        labels = {"database": database}

        # Duration
        self.collector.record(
            "database.search.duration",
            duration,
            unit="seconds",
            labels=labels
        )

        # Papers
        if success:
            self.collector.record(
                "database.papers_found",
                papers_found,
                unit="count",
                labels=labels
            )

        # Success/Failure
        self.collector.increment(
            f"database.search.{'success' if success else 'failure'}",
            labels=labels
        )

    def record_download(
        self,
        database: str,
        pdf_count: int,
        total_size_mb: float,
        duration: float
    ):
        """Erfasst PDF-Downloads"""
        labels = {"database": database}

        self.collector.record(
            "database.pdf_downloads",
            pdf_count,
            unit="count",
            labels=labels
        )

        self.collector.record(
            "database.download.size",
            total_size_mb,
            unit="megabytes",
            labels=labels
        )

        self.collector.record(
            "database.download.duration",
            duration,
            unit="seconds",
            labels=labels
        )


class ErrorMetrics:
    """
    Spezialisierte Metriken für Error-Tracking
    """

    def __init__(self, collector: MetricsCollector):
        self.collector = collector

    def record_error(
        self,
        error_type: str,
        phase: Optional[int] = None,
        severity: str = "error",
        context: Optional[Dict[str, str]] = None
    ):
        """
        Erfasst einen Fehler

        Args:
            error_type: Typ (z.B. "captcha", "network", "rate_limit")
            phase: Optional Phase-Nummer
            severity: "warning", "error", "critical"
            context: Optional Kontext-Infos
        """
        labels = {
            "error_type": error_type,
            "severity": severity
        }

        if phase is not None:
            labels["phase"] = str(phase)

        if context:
            labels.update(context)

        self.collector.increment("errors.total", labels=labels)


# ============================================
# Convenience-Funktionen
# ============================================

def create_metrics_collector(run_dir: Path) -> MetricsCollector:
    """Erstellt Metrics-Collector für Run"""
    return MetricsCollector(run_dir=run_dir)


def create_full_metrics_suite(run_dir: Path) -> Dict[str, Any]:
    """
    Erstellt komplette Metrics-Suite für Research-Run

    Returns:
        Dict mit allen Metrics-Collectoren:
        - collector: Haupt-Collector
        - iteration: Iteration-Metriken
        - database: Database-Metriken
        - error: Error-Metriken
    """
    collector = create_metrics_collector(run_dir)

    return {
        "collector": collector,
        "iteration": IterationMetrics(collector),
        "database": DatabaseMetrics(collector),
        "error": ErrorMetrics(collector)
    }


# ============================================
# Beispiel-Verwendung
# ============================================

if __name__ == "__main__":
    print("🧪 Teste Metrics-System...\n")

    # Erstelle Test-Run-Dir
    test_dir = Path("runs/test_metrics")
    test_dir.mkdir(parents=True, exist_ok=True)

    # Erstelle Metrics-Suite
    metrics = create_full_metrics_suite(test_dir)
    collector = metrics["collector"]
    iteration_metrics = metrics["iteration"]
    db_metrics = metrics["database"]
    error_metrics = metrics["error"]

    print("Test 1: Basis-Metriken")
    collector.record("test.metric", 42.5, unit="count")
    collector.increment("test.counter")
    collector.gauge("test.gauge", 75.3, unit="percent")
    print("  ✅ Basis-Metriken erfasst\n")

    print("Test 2: Zeit-Messung")
    with collector.measure_time("test.operation", labels={"type": "example"}):
        time.sleep(0.1)  # Simuliere Arbeit
    print("  ✅ Zeit gemessen\n")

    print("Test 3: Iteration-Metriken")
    iteration_metrics.start_iteration(1, database_count=5)
    time.sleep(0.05)
    iteration_metrics.end_iteration(
        iteration=1,
        papers_found=32,
        databases_searched=["IEEE", "ACM", "Scopus"],
        errors=0
    )
    print("  ✅ Iteration-Metriken erfasst\n")

    print("Test 4: Database-Metriken")
    db_metrics.record_search(
        database="IEEE",
        papers_found=15,
        duration=12.3,
        success=True
    )
    db_metrics.record_download(
        database="IEEE",
        pdf_count=3,
        total_size_mb=5.2,
        duration=8.5
    )
    print("  ✅ Database-Metriken erfasst\n")

    print("Test 5: Error-Metriken")
    error_metrics.record_error(
        error_type="captcha",
        phase=2,
        severity="warning",
        context={"database": "Scopus"}
    )
    print("  ✅ Error-Metriken erfasst\n")

    print("Test 6: Summary-Export")
    summary_file = collector.export_summary()
    print(f"  ✅ Summary exportiert: {summary_file}\n")

    print("Zusammenfassung:")
    summary = collector.get_summary()
    for name, stats in summary.items():
        print(f"  {name}:")
        print(f"    Count: {stats['count']}, Avg: {stats['avg']:.2f} {stats['unit']}")

    print("\n✅ Alle Metrics-Tests erfolgreich!")
    print(f"📊 Metrics-Datei: {collector.metrics_file}")
    print(f"📊 Summary-Datei: {summary_file}")
