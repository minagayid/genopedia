from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from genopedia.adapters import FileDropAdapter


class FileDropAdapterTests(unittest.TestCase):
    def test_adapter_discovers_supported_exports_in_stable_order(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "b.fastq").write_text("@b\nAT\n+\nII\n", encoding="utf-8")
            (root / "a.fasta").write_text(">a\nAT\n", encoding="utf-8")
            (root / "notes.txt").write_text("not a sequence", encoding="utf-8")

            discovered = FileDropAdapter(root).discover()

        self.assertEqual([path.name for path in discovered], ["a.fasta", "b.fastq"])

    def test_adapter_reads_an_export_without_mutating_the_source(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.fasta"
            path.write_text(">sample\nATGC\n", encoding="utf-8")

            data = FileDropAdapter(directory).read(path)

        self.assertEqual(data.records[0].sequence, "ATGC")
