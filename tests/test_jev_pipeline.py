from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from genopedia.jev_pipeline import (
    REFSEQ_RELEASE_237,
    build_refseq237_jev_plan,
    render_refseq237_jev_sql,
    write_jev_plan,
)


class JevPipelineTests(unittest.TestCase):
    def test_release_237_plan_is_explicit_and_spend_aware(self) -> None:
        plan = build_refseq237_jev_plan(semantic_query="relevant to enzyme activity")
        self.assertEqual(plan["source"]["expected_protein_records"], 495_290_394)
        self.assertEqual(plan["source"]["release_date"], "2026-09-04")
        self.assertEqual(len(plan["operations"]), 5)
        self.assertEqual(plan["execution"]["estimated_requests_per_operation"], 24_764_520)
        self.assertEqual(plan["execution"]["estimated_requests_all_operations"], 123_822_600)
        self.assertTrue(plan["third_party_transfer"]["approval_required"])
        self.assertEqual(REFSEQ_RELEASE_237["release_number"], 237)

    def test_small_plan_calculates_batches_and_renders_all_operations(self) -> None:
        plan = build_refseq237_jev_plan(
            semantic_query="relevant to membrane transport",
            expected_protein_records=41,
            batch_size=20,
            max_rows_per_statement=100,
        )
        self.assertEqual(plan["execution"]["estimated_requests_per_operation"], 3)
        sql = render_refseq237_jev_sql(plan)
        for operation in ("SORT", "RANK", "CLASSIFY", "ROUTE", "MAP"):
            self.assertIn(operation, sql)
        self.assertIn("RAISE EXCEPTION", sql)
        self.assertIn("max_rows_per_statement = 100", sql)

    def test_plan_writer_emits_json_and_sql_without_api_contact(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            json_path = Path(directory) / "plan.json"
            sql_path = Path(directory) / "plan.sql"
            plan = write_jev_plan(
                json_path,
                sql_output=sql_path,
                semantic_query="relevant to DNA binding",
                expected_protein_records=2,
                batch_size=2,
                max_rows_per_statement=2,
            )
            saved = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual(saved["plan_id"], plan["plan_id"])
            self.assertTrue(sql_path.read_text(encoding="utf-8").startswith("-- Genopedia / RefSeq"))

    def test_batch_size_above_documented_accuracy_limit_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            build_refseq237_jev_plan(semantic_query="relevant", batch_size=21)


if __name__ == "__main__":
    unittest.main()
