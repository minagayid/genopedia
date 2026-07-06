"""Genomics analysis pipeline orchestrator.

Ties the loader, analyzer and visualizer into a single, inspectable run:
each stage records what it did and why, so a caller gets both the results
and a human-readable trace. Pure orchestration — no heavy dependencies.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from src.genomics import GenomicsVisualizer, SequenceAnalyzer, Variant


@dataclass
class AnalysisReport:
    """Structured result of a pipeline run over one sample sequence."""

    length: int
    gc_content: float
    motif_hits: dict = field(default_factory=dict)
    functional_regions: list = field(default_factory=list)
    variants: List[Variant] = field(default_factory=list)
    reasoning: List[str] = field(default_factory=list)
    html: Optional[str] = None

    def summary(self) -> dict:
        return {
            "length": self.length,
            "gc_content": round(self.gc_content, 2),
            "motif_hits": self.motif_hits,
            "functional_region_count": len(self.functional_regions),
            "variant_count": len(self.variants),
            "pathogenic_variants": sum(
                1 for v in self.variants if v.pathogenicity in ("likely_pathogenic", "pathogenic", "uncertain")
            ),
        }


class GenomicsPipeline:
    """Run standard analysis over a sample sequence, optionally vs a reference."""

    def __init__(self, motifs: Optional[List[str]] = None):
        self.analyzer = SequenceAnalyzer()
        self.visualizer = GenomicsVisualizer()
        # Common regulatory / structural motifs worth flagging by default.
        self.motifs = motifs or ["TATA", "ATG", "GC", "CAAT"]

    def run(self, sample: str, reference: Optional[str] = None, render_html: bool = False) -> AnalysisReport:
        reasoning: List[str] = [f"Analyzing sample of length {len(sample)}"]

        gc = self.analyzer.calculate_gc_content(sample)
        reasoning.append(f"GC content: {gc:.1f}% ({'GC-rich' if gc >= 60 else 'GC-poor' if gc <= 40 else 'balanced'})")

        motif_hits = {m: self.analyzer.find_motifs(sample, m) for m in self.motifs}
        motif_hits = {m: hits for m, hits in motif_hits.items() if hits}
        reasoning.append(
            f"Scanned {len(self.motifs)} motifs; found hits for: "
            + (", ".join(motif_hits) if motif_hits else "none")
        )

        regions = self.analyzer.identify_functional_regions(sample)
        reasoning.append(f"Identified {len(regions)} candidate functional regions")

        variants: List[Variant] = []
        if reference is not None:
            variants = self.analyzer.detect_variants(reference, sample)
            for v in variants:
                v.pathogenicity = self.analyzer.classify_pathogenicity(v)
            flagged = sum(1 for v in variants if v.pathogenicity == "uncertain")
            reasoning.append(
                f"Compared against reference: {len(variants)} variants "
                f"({flagged} of uncertain significance)"
            )
        else:
            reasoning.append("No reference supplied; skipping variant calling")

        html = self.visualizer.generate_color_html(sample) if render_html else None

        return AnalysisReport(
            length=len(sample),
            gc_content=gc,
            motif_hits=motif_hits,
            functional_regions=regions,
            variants=variants,
            reasoning=reasoning,
            html=html,
        )
