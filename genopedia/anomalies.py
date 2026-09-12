"""Conservative sequence-quality anomaly observations.

These checks identify data-quality or contamination signals. They do not
classify disease, establish clinical significance, or authorize sequence
rewriting.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .core import QualityReport, SequenceAnalyzer, SequenceRecord, normalize_sequence


@dataclass(frozen=True)
class SequenceAnomaly:
    identifier: str
    category: str
    severity: str
    evidence: str
    suggested_action: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "identifier": self.identifier,
            "category": self.category,
            "severity": self.severity,
            "evidence": self.evidence,
            "suggested_action": self.suggested_action,
            "safety": "Quality evidence requires human review; no automatic sequence edit is performed.",
        }


class SequenceAnomalyDetector:
    """Find transparent, deterministic QC signals in one sequence record."""

    def __init__(self, ambiguity_fraction: float = 0.10, max_homopolymer: int = 12) -> None:
        if not 0.0 <= ambiguity_fraction <= 1.0 or max_homopolymer < 2:
            raise ValueError("ambiguity_fraction must be between 0 and 1 and max_homopolymer must be at least 2")
        self.ambiguity_fraction = float(ambiguity_fraction)
        self.max_homopolymer = int(max_homopolymer)
        self.analyzer = SequenceAnalyzer()

    def detect(self, record: SequenceRecord, molecule: str = "DNA") -> list[SequenceAnomaly]:
        normalized = normalize_sequence(record.sequence)
        report: QualityReport = self.analyzer.quality_control(record, molecule=molecule)
        anomalies: list[SequenceAnomaly] = []
        if report.invalid_symbols:
            anomalies.append(
                SequenceAnomaly(
                    record.identifier,
                    "invalid_symbol",
                    "high",
                    f"invalid symbols: {', '.join(report.invalid_symbols)}",
                    "confirm the source format and quarantine the affected record before analysis",
                )
            )
        if normalized and report.ambiguous_count / len(normalized) >= self.ambiguity_fraction:
            anomalies.append(
                SequenceAnomaly(
                    record.identifier,
                    "high_ambiguity",
                    "medium",
                    f"{report.ambiguous_count}/{len(normalized)} bases are ambiguous",
                    "review base-calling quality and retain ambiguity instead of guessing bases",
                )
            )
        if report.mean_quality is not None and report.mean_quality < 20:
            anomalies.append(
                SequenceAnomaly(
                    record.identifier,
                    "low_quality",
                    "medium",
                    f"mean Phred quality is {report.mean_quality:.2f}",
                    "review read-level quality filtering and compare against an appropriate benchmark",
                )
            )
        run_base = ""
        run_length = 0
        for base in normalized:
            if base == run_base:
                run_length += 1
            else:
                run_base, run_length = base, 1
            if run_length == self.max_homopolymer:
                anomalies.append(
                    SequenceAnomaly(
                        record.identifier,
                        "long_homopolymer",
                        "low",
                        f"{base} run is at least {self.max_homopolymer} bases",
                        "compare platform-specific homopolymer error profiles before proposing a correction",
                    )
                )
                break
        return anomalies
