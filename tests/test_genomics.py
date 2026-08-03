from __future__ import annotations

import unittest

from genopedia import SequenceAnalyzer, SequenceRecord, Variant
from genopedia.models import KmerClassifier


class SequenceAnalyzerTests(unittest.TestCase):
    def test_gc_content_is_a_fraction_and_ignores_ambiguous_bases(self) -> None:
        analyzer = SequenceAnalyzer()

        self.assertEqual(analyzer.gc_content("ACTG"), 0.5)
        self.assertEqual(analyzer.gc_content("ACNG"), 2 / 3)
        self.assertEqual(analyzer.gc_content(""), 0.0)

    def test_quality_control_reports_invalid_symbols_without_mutating_input(self) -> None:
        analyzer = SequenceAnalyzer()
        record = SequenceRecord(identifier="sample-1", sequence="ACGT?N")

        report = analyzer.quality_control(record)

        self.assertEqual(record.sequence, "ACGT?N")
        self.assertEqual(report.length, 6)
        self.assertEqual(report.invalid_symbols, ("?",))
        self.assertEqual(report.ambiguous_count, 1)
        self.assertEqual(report.status, "fail")

    def test_motif_search_finds_overlapping_matches(self) -> None:
        positions = SequenceAnalyzer().find_motifs("ATATAT", "ATA")

        self.assertEqual(positions, [0, 2])

    def test_sequence_comparison_reports_an_insertion_at_reference_position(self) -> None:
        variants = SequenceAnalyzer().detect_variants("ACGT", "ACGGT", chromosome="chr7")

        self.assertEqual(len(variants), 1)
        self.assertEqual(variants[0].chromosome, "chr7")
        self.assertEqual(variants[0].position, 3)
        self.assertEqual(variants[0].reference, "")
        self.assertEqual(variants[0].observed, "G")
        self.assertEqual(variants[0].variant_type, "insertion")

    def test_default_variant_interpretation_is_unknown_without_evidence(self) -> None:
        variant = Variant(chromosome="chr1", position=10, reference="A", observed="G")

        self.assertEqual(SequenceAnalyzer().interpret_variant(variant), "unknown")


class KmerClassifierTests(unittest.TestCase):
    def test_classifier_can_fit_and_predict_without_numpy(self) -> None:
        classifier = KmerClassifier(k=2)
        classifier.fit(["AAAAAA", "AAAATA", "CCCCCC", "CCCCAC"], ["A", "A", "C", "C"])

        self.assertEqual(classifier.predict("AAAAAA"), "A")
        self.assertEqual(classifier.predict("CCCCCC"), "C")

    def test_classifier_rejects_prediction_before_training(self) -> None:
        with self.assertRaises(RuntimeError):
            KmerClassifier(k=3).predict("ATGC")
