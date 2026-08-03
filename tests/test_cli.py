from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from genopedia.cli import main


class CliTests(unittest.TestCase):
    def test_example_script_runs_from_repository_root(self) -> None:
        repository_root = Path(__file__).resolve().parents[1]

        result = subprocess.run(
            [sys.executable, "examples/demo_genomics.py"],
            cwd=repository_root,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_demo_command_writes_a_report_and_json_summary(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "report.html"
            summary = Path(directory) / "report.json"

            exit_code = main(
                [
                    "demo",
                    "--length",
                    "24",
                    "--output",
                    str(output),
                    "--json-output",
                    str(summary),
                ]
            )

            self.assertEqual(exit_code, 0)
            self.assertTrue(output.exists())
            self.assertTrue(summary.exists())
            payload = json.loads(summary.read_text(encoding="utf-8"))

        self.assertEqual(payload["records"][0]["length"], 24)

    def test_compare_command_writes_detected_variants(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            reference = root / "reference.txt"
            sample = root / "sample.txt"
            output = root / "comparison.html"
            summary = root / "comparison.json"
            reference.write_text("ACGT", encoding="utf-8")
            sample.write_text("ACGGT", encoding="utf-8")

            exit_code = main(
                [
                    "compare",
                    str(reference),
                    str(sample),
                    "--output",
                    str(output),
                    "--json-output",
                    str(summary),
                ]
            )

            self.assertEqual(exit_code, 0)
            payload = json.loads(summary.read_text(encoding="utf-8"))

        self.assertEqual(payload["variants"][0]["variant_type"], "insertion")
