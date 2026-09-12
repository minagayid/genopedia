from __future__ import annotations

import json
import unittest

from genopedia.anomalies import SequenceAnomalyDetector
from genopedia.core import SequenceRecord, Variant
from genopedia.correction import CorrectionPlanner
from genopedia.references import ReferenceRegistry


class ReferenceRegistryTests(unittest.TestCase):
    def test_bundled_manifest_is_valid_and_filterable(self) -> None:
        registry = ReferenceRegistry.from_path()

        self.assertGreaterEqual(len(registry.sources), 15)
        self.assertIn("rfam", {source.id for source in registry.search(molecule="RNA", role="rna_family")})
        self.assertEqual(registry.plan("correction", "DNA").purpose, "correction")

    def test_reference_plan_serializes_without_non_json_values(self) -> None:
        payload = ReferenceRegistry.from_path().plan("anomaly_detection", "RNA").to_dict()

        json.dumps(payload)
        self.assertIn("sequencing-read-archives", payload["source_ids"])


class SequenceEvidenceTests(unittest.TestCase):
    def test_quality_signals_and_correction_plan_are_conservative(self) -> None:
        record = SequenceRecord(identifier="read-1", sequence="ATGNNNNNNNNNNCCCCCCCCCC", quality_scores=(10,) * 22)
        anomalies = SequenceAnomalyDetector(ambiguity_fraction=0.1, max_homopolymer=8).detect(record)
        variant = Variant(chromosome="chr1", position=4, reference="A", observed="G")
        plan = CorrectionPlanner().plan(
            [variant], reference_support={4: {"A": 1}}, read_support={4: {"A": 2}}
        )

        self.assertIn("high_ambiguity", {item.category for item in anomalies})
        self.assertIn("low_quality", {item.category for item in anomalies})
        self.assertEqual(plan[0].status, "candidate_for_review")
        self.assertEqual(plan[0].candidate, "A")
        self.assertIn("no automatic sequence edit", plan[0].to_dict()["safety"])
