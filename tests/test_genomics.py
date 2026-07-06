"""Genopedia genomics pipeline tests."""
from __future__ import annotations

import pytest

from src.genomics import GenomicsDataLoader, GenomicsVisualizer, SequenceAnalyzer
from src.models import DNAClassifier, kmer_counts
from src.pipeline import GenomicsPipeline


@pytest.fixture
def loader():
    return GenomicsDataLoader()


@pytest.fixture
def analyzer():
    return SequenceAnalyzer()


@pytest.fixture
def visualizer():
    return GenomicsVisualizer()


def test_synthetic_dna_generation(loader):
    sequence = loader.generate_synthetic_dna(120)
    assert len(sequence) == 120
    assert set(sequence).issubset({"A", "T", "G", "C"})


def test_synthetic_rna_uses_uracil(loader):
    sequence = loader.generate_synthetic_rna(80)
    assert len(sequence) == 80
    assert set(sequence).issubset({"A", "U", "G", "C"})


def test_detects_simple_variant(analyzer):
    # reference ATGC..., sample ATGT... differ at 0-based index 3
    variants = analyzer.detect_variants("ATGCCGTAG", "ATGTCGTAG")
    assert len(variants) == 1
    assert variants[0].position == 3
    assert variants[0].reference == "C"
    assert variants[0].observed == "T"


def test_color_map_returns_expected_colors(analyzer):
    colors = analyzer.get_color_map("ATGCUN")
    assert colors == ["#FF0000", "#FFFF00", "#00FF00", "#0000FF", "#8B4513", "#808080"]


def test_gc_content_pure_python():
    analyzer = SequenceAnalyzer()
    assert analyzer.calculate_gc_content("GGCC") == 100.0
    assert analyzer.calculate_gc_content("ATAT") == 0.0
    assert analyzer.calculate_gc_content("ATGC") == 50.0
    assert analyzer.calculate_gc_content("") == 0.0


def test_kmer_counts_runs_without_error():
    counts = kmer_counts("ATGATG", k=3)
    assert counts["ATG"] == 2
    assert counts["TGA"] == 1


def test_dna_classifier_learns_and_predicts():
    clf = DNAClassifier(k=2)
    clf.fit(
        ["ATATATATAT", "ATATATATAT", "GCGCGCGCGC", "GCGCGCGCGC"],
        ["at_rich", "at_rich", "gc_rich", "gc_rich"],
    )
    assert clf.predict("ATATATAT") == "at_rich"
    assert clf.predict("GCGCGCGC") == "gc_rich"


def test_classifier_predict_before_fit_raises():
    with pytest.raises(RuntimeError):
        DNAClassifier().predict("ATGC")


class TestPipeline:
    def test_run_produces_report_and_reasoning(self):
        pipeline = GenomicsPipeline()
        report = pipeline.run("TATAATGCCGTAGATG", render_html=True)
        assert report.length == 16
        assert 0 <= report.gc_content <= 100
        assert "ATG" in report.motif_hits
        assert report.reasoning
        assert report.html and report.html.startswith("<div")

    def test_run_with_reference_calls_variants(self):
        pipeline = GenomicsPipeline()
        report = pipeline.run(sample="ATGTCGTAG", reference="ATGCCGTAG")
        assert len(report.variants) == 1
        assert report.variants[0].pathogenicity != "unknown"
        assert report.summary()["variant_count"] == 1

    def test_run_without_reference_skips_variants(self):
        report = GenomicsPipeline().run("ATGCATGC")
        assert report.variants == []
