"""Core genomics data structures and deterministic analysis."""

from __future__ import annotations

from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Any, Iterable


DNA_ALPHABET = frozenset("ACGTNRYKMSWBDHV")
RNA_ALPHABET = frozenset("ACGUNRYKMSWBDHV")
UNAMBIGUOUS_BASES = frozenset("ACGTU")
INTERPRETATIONS = frozenset(
    {"benign", "likely_benign", "uncertain", "likely_pathogenic", "pathogenic", "unknown"}
)


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value


def normalize_sequence(sequence: str) -> str:
    """Remove formatting whitespace and normalize bases to uppercase."""

    if not isinstance(sequence, str):
        raise TypeError("sequence must be a string")
    return "".join(sequence.split()).upper()


@dataclass(frozen=True)
class SequenceRecord:
    """A sequence and its optional sequencing metadata."""

    identifier: str
    sequence: str
    description: str = ""
    quality_scores: tuple[int, ...] = ()
    source_format: str = "text"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "identifier": self.identifier,
            "sequence": self.sequence,
            "description": self.description,
            "length": len(self.sequence),
            "quality_scores": list(self.quality_scores),
            "source_format": self.source_format,
            "metadata": _json_safe(self.metadata),
        }


@dataclass(frozen=True)
class Variant:
    """An observed sequence difference.

    Positions produced by sequence comparison are zero-based. Positions read
    from VCF retain VCF's one-based coordinate system in metadata.
    """

    chromosome: str
    position: int
    reference: str
    observed: str
    quality: float | None = None
    variant_type: str = "substitution"
    interpretation: str = "unknown"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "chromosome": self.chromosome,
            "position": self.position,
            "reference": self.reference,
            "observed": self.observed,
            "quality": self.quality,
            "variant_type": self.variant_type,
            "interpretation": self.interpretation,
            "metadata": _json_safe(self.metadata),
        }


@dataclass(frozen=True)
class FunctionalRegion:
    """A candidate region identified by a transparent heuristic."""

    name: str
    start: int
    end: int
    region_type: str
    evidence: str = "heuristic"

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "start": self.start,
            "end": self.end,
            "region_type": self.region_type,
            "evidence": self.evidence,
        }


@dataclass(frozen=True)
class QualityReport:
    """Quality-control result for one sequence record."""

    identifier: str
    length: int
    gc_fraction: float
    ambiguous_count: int
    invalid_symbols: tuple[str, ...]
    mean_quality: float | None
    status: str
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "identifier": self.identifier,
            "length": self.length,
            "gc_fraction": self.gc_fraction,
            "ambiguous_count": self.ambiguous_count,
            "invalid_symbols": list(self.invalid_symbols),
            "mean_quality": self.mean_quality,
            "status": self.status,
            "warnings": list(self.warnings),
        }


class SequenceAnalyzer:
    """Small, dependency-free analysis primitives for DNA and RNA."""

    def gc_content(self, sequence: str) -> float:
        normalized = normalize_sequence(sequence)
        informative = [base for base in normalized if base in UNAMBIGUOUS_BASES]
        if not informative:
            return 0.0
        return sum(base in {"G", "C"} for base in informative) / len(informative)

    def quality_control(self, record: SequenceRecord, molecule: str = "DNA") -> QualityReport:
        normalized = normalize_sequence(record.sequence)
        alphabet = DNA_ALPHABET if molecule.upper() == "DNA" else RNA_ALPHABET
        invalid = tuple(sorted({base for base in normalized if base not in alphabet}))
        ambiguous = sum(base not in UNAMBIGUOUS_BASES for base in normalized if base in alphabet)
        warnings: list[str] = []

        if not normalized:
            warnings.append("sequence is empty")
        if invalid:
            warnings.append("sequence contains invalid symbols")
        if ambiguous:
            warnings.append("sequence contains ambiguous bases")
        if record.quality_scores and len(record.quality_scores) != len(normalized):
            warnings.append("quality score count does not match sequence length")
        mean_quality = (
            sum(record.quality_scores) / len(record.quality_scores)
            if record.quality_scores
            else None
        )
        if mean_quality is not None and mean_quality < 20:
            warnings.append("mean Phred quality is below 20")

        status = "fail" if not normalized or invalid or (
            record.quality_scores and len(record.quality_scores) != len(normalized)
        ) else ("warn" if warnings else "pass")
        return QualityReport(
            identifier=record.identifier,
            length=len(normalized),
            gc_fraction=self.gc_content(normalized),
            ambiguous_count=ambiguous,
            invalid_symbols=invalid,
            mean_quality=mean_quality,
            status=status,
            warnings=tuple(warnings),
        )

    def find_motifs(self, sequence: str, motif: str) -> list[int]:
        sequence = normalize_sequence(sequence)
        motif = normalize_sequence(motif)
        if not motif:
            raise ValueError("motif must not be empty")
        return [
            index
            for index in range(len(sequence) - len(motif) + 1)
            if sequence[index : index + len(motif)] == motif
        ]

    def identify_functional_regions(self, sequence: str) -> list[FunctionalRegion]:
        """Return candidate regions; this is not a clinical annotation."""

        normalized = normalize_sequence(sequence)
        regions: list[FunctionalRegion] = []
        for position in self.find_motifs(normalized, "TATA"):
            regions.append(
                FunctionalRegion(
                    name=f"candidate-promoter-{position}",
                    start=max(0, position - 25),
                    end=min(len(normalized), position + 25),
                    region_type="promoter",
                )
            )
        for position in self.find_motifs(normalized, "ATG"):
            regions.append(
                FunctionalRegion(
                    name=f"candidate-start-codon-{position}",
                    start=position,
                    end=position + 3,
                    region_type="start_codon",
                )
            )
        return regions

    def detect_variants(
        self, reference: str, sample: str, chromosome: str = "chr1"
    ) -> list[Variant]:
        """Compare two strings and report substitutions and indels.

        The standard-library sequence matcher keeps the core usable on a
        clean Python installation. It is intended for short/medium sequence
        comparisons; dedicated aligners remain optional for large genomes.
        """

        reference = normalize_sequence(reference)
        sample = normalize_sequence(sample)
        matcher = SequenceMatcher(None, reference, sample, autojunk=False)
        variants: list[Variant] = []
        for tag, ref_start, ref_end, sample_start, sample_end in matcher.get_opcodes():
            if tag == "equal":
                continue
            ref_segment = reference[ref_start:ref_end]
            sample_segment = sample[sample_start:sample_end]
            if tag == "replace" and len(ref_segment) == len(sample_segment):
                for offset, (ref_base, sample_base) in enumerate(
                    zip(ref_segment, sample_segment)
                ):
                    if ref_base != sample_base:
                        variants.append(
                            Variant(
                                chromosome=chromosome,
                                position=ref_start + offset,
                                reference=ref_base,
                                observed=sample_base,
                                variant_type="substitution",
                            )
                        )
            else:
                if not ref_segment:
                    variant_type = "insertion"
                elif not sample_segment:
                    variant_type = "deletion"
                else:
                    variant_type = "replacement"
                variants.append(
                    Variant(
                        chromosome=chromosome,
                        position=ref_start,
                        reference=ref_segment,
                        observed=sample_segment,
                        variant_type=variant_type,
                    )
                )
        return variants

    def interpret_variant(self, variant: Variant, evidence: dict[str, Any] | None = None) -> str:
        """Apply supplied evidence, otherwise remain explicitly unknown."""

        evidence = evidence or variant.metadata
        value = str(evidence.get("interpretation", evidence.get("clinical_significance", "unknown")))
        return value if value in INTERPRETATIONS else "unknown"

    def summarize_records(
        self, records: Iterable[SequenceRecord], molecule: str = "DNA"
    ) -> list[QualityReport]:
        return [self.quality_control(record, molecule=molecule) for record in records]

