"""Evidence-gated correction planning for Genopedia.

The planner produces reviewable next steps. It intentionally never rewrites
the input sequence and never labels a variant as clinically meaningful.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from .core import Variant


@dataclass(frozen=True)
class CorrectionSuggestion:
    chromosome: str
    position: int
    variant_type: str
    observed: str
    candidate: str | None
    status: str
    evidence: tuple[str, ...]
    next_action: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "chromosome": self.chromosome,
            "position": self.position,
            "variant_type": self.variant_type,
            "observed": self.observed,
            "candidate": self.candidate,
            "status": self.status,
            "evidence": list(self.evidence),
            "next_action": self.next_action,
            "safety": "Review-only planning; no automatic sequence edit or clinical interpretation.",
        }


class CorrectionPlanner:
    """Turn supplied orthogonal evidence into conservative review plans."""

    def __init__(self, minimum_support: int = 2) -> None:
        if minimum_support < 1:
            raise ValueError("minimum_support must be positive")
        self.minimum_support = int(minimum_support)

    def plan(
        self,
        variants: Iterable[Variant],
        *,
        reference_support: Mapping[int, Mapping[str, int]] | None = None,
        read_support: Mapping[int, Mapping[str, int]] | None = None,
    ) -> list[CorrectionSuggestion]:
        reference_support = reference_support or {}
        read_support = read_support or {}
        suggestions: list[CorrectionSuggestion] = []
        for variant in variants:
            ref_counts = dict(reference_support.get(variant.position, {}))
            read_counts = dict(read_support.get(variant.position, {}))
            evidence: list[str] = []
            if ref_counts:
                evidence.append("reference-support supplied")
            if read_counts:
                evidence.append("read-consensus support supplied")
            combined: dict[str, int] = {}
            for allele, count in [*ref_counts.items(), *read_counts.items()]:
                combined[str(allele).upper()] = combined.get(str(allele).upper(), 0) + int(count)
            candidates = [
                (allele, count)
                for allele, count in combined.items()
                if allele != variant.observed.upper()
            ]
            candidates.sort(key=lambda item: (-item[1], item[0]))
            candidate, support = candidates[0] if candidates else (None, 0)
            if candidate is not None and support >= self.minimum_support:
                status = "candidate_for_review"
                evidence.append(f"candidate {candidate} has {support} combined support units")
                next_action = "inspect alignment context, platform error model, and independent evidence before any edit"
            else:
                status = "insufficient_evidence"
                next_action = "collect orthogonal reference/read evidence; retain the observed sequence unchanged"
            suggestions.append(
                CorrectionSuggestion(
                    chromosome=variant.chromosome,
                    position=variant.position,
                    variant_type=variant.variant_type,
                    observed=variant.observed,
                    candidate=candidate,
                    status=status,
                    evidence=tuple(evidence) or ("no orthogonal evidence supplied",),
                    next_action=next_action,
                )
            )
        return suggestions
