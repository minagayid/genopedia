from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from genopedia.catalog import build_jev_sort_spec, read_jsonl, write_jsonl
from genopedia.schema import (
    NOT_FOR_CLINICAL_USE,
    SchemaValidationError,
    make_envelope,
    make_sequence_record,
    schema_document,
    sequence_sha256,
    validate_record,
)


class SchemaContractTests(unittest.TestCase):
    def test_sequence_digest_is_normalized_and_stable(self) -> None:
        self.assertEqual(
            sequence_sha256(" ac\n gt ", "DNA"),
            sequence_sha256("ACGT", "DNA"),
        )

    def test_sequence_record_keeps_content_separate_from_usage(self) -> None:
        record = make_sequence_record(
            sequence_id="sequence:sha256:example",
            sequence="ACGT",
            sequence_type="DNA",
            content_uri="cas://sha256/example",
            release_id="release:test-1",
        )
        self.assertEqual(record["length"], 4)
        self.assertNotIn("sequence", record)
        self.assertEqual(validate_record("sequence_record", record), [])

    def test_direct_protein_to_trait_causality_is_blocked(self) -> None:
        issues = validate_record(
            "claim_assertion",
            {
                "id": "claim:direct-1",
                "subject_entity_type": "protein",
                "subject_entity_id": "protein:P01308",
                "predicate": "causes",
                "object_entity_type": "phenotype_trait",
                "object_entity_id": "trait:night-vision",
                "evidence_record_id": "evidence:1",
                "causal_strength": "unknown",
                "assertion_status": "hypothesis",
            },
        )
        self.assertTrue(any(issue.code == "scope_boundary" for issue in issues))

    def test_jsonl_round_trip_is_deterministic(self) -> None:
        records = [
            (
                "dataset_release",
                {
                    "id": "release:test-1",
                    "source_name": "Genopedia",
                    "source_version": "1",
                    "retrieved_at": "2026-09-22",
                    "source_uri": "https://example.test/release",
                    "status": "active",
                },
            ),
            (
                "sequence_record",
                make_sequence_record(
                    sequence_id="sequence:sha256:example",
                    sequence="ACGT",
                    sequence_type="DNA",
                    content_uri="cas://sha256/example",
                    release_id="release:test-1",
                ),
            ),
        ]
        with tempfile.TemporaryDirectory() as directory:
            first_path = Path(directory) / "catalog-one.jsonl"
            second_path = Path(directory) / "catalog-two.jsonl"
            write_jsonl(first_path, reversed(records))
            write_jsonl(second_path, records)
            loaded = read_jsonl(first_path)
            first_lines = first_path.read_text(encoding="utf-8").splitlines()
            second_lines = second_path.read_text(encoding="utf-8").splitlines()

        self.assertEqual([item["entity_type"] for item in loaded], ["dataset_release", "sequence_record"])
        self.assertEqual(first_lines, second_lines)

    def test_jev_is_optional_and_has_deterministic_fallback(self) -> None:
        spec = build_jev_sort_spec(
            input_release_id="release:test-1",
            semantic_query="rank proteins likely to bind the target complex",
            score_levels=["low", "medium", "high"],
        )
        self.assertFalse(spec["authoritative"])
        self.assertEqual(spec["fallback_sort_key"], "data.id")

    def test_schema_document_is_machine_readable(self) -> None:
        document = schema_document()
        self.assertEqual(document["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertIn("protein", document["$defs"])
        self.assertIn("entity_relation", document["$defs"])
        self.assertIn("description", document["$defs"]["variant_assertion"])
        self.assertIn(NOT_FOR_CLINICAL_USE, document["description"])

    def test_variant_and_relation_records_validate(self) -> None:
        variant = {
            "id": "variant:example-1",
            "position": 42,
            "reference": "A",
            "alternate": "G",
            "variant_type": "substitution",
            "evidence_record_id": "evidence:example-1",
            "source_record_id": "source:example-1",
            "release_id": "release:example-1",
        }
        relation = {
            "id": "relation:example-1",
            "subject_entity_type": "protein",
            "subject_entity_id": "protein:example-1",
            "predicate": "participates_in",
            "object_entity_type": "pathway_process",
            "object_entity_id": "pathway:example-1",
            "release_id": "release:example-1",
            "provenance_activity_id": "activity:example-1",
        }
        self.assertEqual(validate_record("variant_assertion", variant), [])
        self.assertEqual(validate_record("entity_relation", relation), [])

    def test_invalid_record_raises_on_envelope_creation(self) -> None:
        with self.assertRaises(SchemaValidationError):
            make_envelope("protein", {"id": "not-namespaced"})


if __name__ == "__main__":
    unittest.main()
