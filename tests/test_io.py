from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from genopedia.io import read_fasta, read_fastq, read_vcf, read_sequence_file


class SequenceIoTests(unittest.TestCase):
    def test_fasta_reader_streams_records_and_normalizes_sequence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.fa"
            path.write_text(">alpha first record\nat gc\n>beta\nTTAA\n", encoding="utf-8")

            records = list(read_fasta(path))

        self.assertEqual([record.identifier for record in records], ["alpha", "beta"])
        self.assertEqual(records[0].sequence, "ATGC")
        self.assertEqual(records[0].description, "first record")

    def test_fastq_reader_decodes_phred_quality_scores(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.fastq"
            path.write_text("@read-1\nACGT\n+\nIIII\n", encoding="utf-8")

            records = list(read_fastq(path))

        self.assertEqual(records[0].quality_scores, (40, 40, 40, 40))

    def test_vcf_reader_accepts_missing_quality_and_preserves_alternatives(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.vcf"
            path.write_text(
                "##fileformat=VCFv4.3\n"
                "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\n"
                "chr2\t8\t.\tA\tG,T\t.\tPASS\tDP=12\n",
                encoding="utf-8",
            )

            variants = list(read_vcf(path))

        self.assertEqual(len(variants), 1)
        self.assertEqual(variants[0].position, 8)
        self.assertEqual(variants[0].observed, "G")
        self.assertEqual(variants[0].metadata["alternatives"], ["G", "T"])
        self.assertIsNone(variants[0].quality)

    def test_auto_reader_uses_file_extension(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.fa"
            path.write_text(">alpha\nATGC\n", encoding="utf-8")

            records = list(read_sequence_file(path))

        self.assertEqual(records[0].sequence, "ATGC")

