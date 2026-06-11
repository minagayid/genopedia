"""GenoProject tests."""
from __future__ import annotations

import pytest

from GenoProject.src.genomics import GenomicsDataLoader, SequenceAnalyzer, GenomicsVisualizer


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


def test_detects_simple_variant(analyzer):
    reference = "ATGCCGTAG"
    sample = "ATGTCGTAG"
    variants = analyzer.detect_variants(reference, sample)
    assert len(variants) == 1
    assert variants[0].position == 4
    assert variants[0].reference == "C"
    assert variants[0].observed == "T"


def test_color_map_returns_expected_colors(analyzer):
    colors = analyzer.get_color_map("ATGCUN")
    assert colors[0] == "#FF0000"
    assert colors[1] == "#FFFF00"
    assert colors[2] == "#00FF00"
    assert colors[3] == "#0000FF"
    assert colors[4] == "#8B4513"
    assert colors[5] == "#808080"
