from __future__ import annotations

import gzip
import tempfile
import unittest
from pathlib import Path

from genopedia.io import (
    InputLimitError,
    InputLimits,
    read_fasta,
    read_fastq,
    read_raw_sequence,
    read_input,
    read_vcf,
    read_sequence_file,
)


class SequenceIoTests(unittest.TestCase):
    def _small_limits(self, **overrides: int) -> InputLimits:
        values = {
            "max_compressed_bytes": 1024,
            "max_decompressed_bytes": 1024,
            "max_records": 2,
            "max_record_bases": 4,
            "max_line_bytes": 128,
            "max_alternatives_per_record": 2,
            "max_info_entries_per_record": 2,
        }
        values.update(overrides)
        return InputLimits(**values)

    def test_fasta_reader_streams_records_and_normalizes_sequence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.fa"
            path.write_text(">alpha first record\nat gc\n>beta\nTTAA\n", encoding="utf-8")

            records = list(read_fasta(path))

        self.assertEqual([record.identifier for record in records], ["alpha", "beta"])
        self.assertEqual(records[0].sequence, "ATGC")
        self.assertEqual(records[0].description, "first record")

    def test_fasta_reader_accepts_carriage_return_line_endings(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "mac.fa"
            path.write_bytes(b">alpha\rATGC\r>beta\rTTAA\r")

            records = list(read_fasta(path))

        self.assertEqual([record.sequence for record in records], ["ATGC", "TTAA"])

    def test_fastq_reader_decodes_phred_quality_scores(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.fastq"
            path.write_text("@read-1\nACGT\n+\nIIII\n", encoding="utf-8")

            records = list(read_fastq(path))

        self.assertEqual(records[0].quality_scores, (40, 40, 40, 40))

    def test_fastq_reader_accepts_wrapped_sequence_and_quality_lines(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "wrapped.fastq"
            path.write_text("@read-1 description\nAC\nGT\n+\nII\nII\n", encoding="utf-8")

            records = list(read_fastq(path))

        self.assertEqual(records[0].sequence, "ACGT")
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

    def test_fasta_and_fastq_enforce_per_record_base_limit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fasta_path = Path(directory) / "large.fa"
            fasta_path.write_text(">large\nACGTA\n", encoding="utf-8")
            fastq_path = Path(directory) / "large.fastq"
            fastq_path.write_text("@large\nACGTA\n+\nIIIII\n", encoding="utf-8")

            with self.assertRaisesRegex(InputLimitError, "base limit"):
                list(read_fasta(fasta_path, limits=self._small_limits()))
            with self.assertRaisesRegex(InputLimitError, "base limit"):
                list(read_fastq(fastq_path, limits=self._small_limits()))

    def test_raw_reader_enforces_per_record_base_limit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "large.txt"
            path.write_text("ACGTA", encoding="utf-8")

            with self.assertRaisesRegex(InputLimitError, "base limit"):
                list(read_raw_sequence(path, limits=self._small_limits()))

    def test_read_input_caps_total_bases_across_individually_valid_records(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "many.fastq"
            path.write_text(
                "@one\nAC\n+\nII\n"
                "@two\nGT\n+\nII\n"
                "@three\nA\n+\nI\n",
                encoding="utf-8",
            )
            limits = self._small_limits(
                max_records=4,
                max_record_bases=2,
                max_total_bases=4,
                max_total_quality_symbols=8,
            )

            with self.assertRaisesRegex(InputLimitError, "total base limit"):
                read_input(path, limits=limits)

    def test_read_input_caps_total_quality_symbols_across_records(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "many.fastq"
            path.write_text(
                "@one\nAC\n+\nII\n"
                "@two\nGT\n+\nII\n"
                "@three\nA\n+\nI\n",
                encoding="utf-8",
            )
            limits = self._small_limits(
                max_records=4,
                max_record_bases=2,
                max_total_bases=8,
                max_total_quality_symbols=4,
            )

            with self.assertRaisesRegex(InputLimitError, "total quality-symbol limit"):
                read_input(path, limits=limits)

    def test_gzip_expansion_is_stopped_at_decompressed_byte_limit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "expanded.fa.gz"
            with gzip.open(path, "wb") as handle:
                handle.write(b">x\n" + b"A" * 200 + b"\n")
            limits = self._small_limits(
                max_decompressed_bytes=32,
                max_record_bases=500,
                max_line_bytes=512,
            )

            with self.assertRaisesRegex(InputLimitError, "decompressed input"):
                list(read_fasta(path, limits=limits))

    def test_gzip_compressed_input_has_its_own_byte_limit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.fa.gz"
            with gzip.open(path, "wb") as handle:
                handle.write(b">x\nA\n")
            limits = self._small_limits(max_compressed_bytes=8)

            with self.assertRaisesRegex(InputLimitError, "compressed input"):
                list(read_fasta(path, limits=limits))

    def test_vcf_caps_allele_bases_alternatives_and_record_count(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            huge_allele = Path(directory) / "huge-allele.vcf"
            huge_allele.write_text(
                "chr1\t1\t.\tA\tAAAAA\t.\tPASS\t.\n", encoding="utf-8"
            )
            too_many_alternatives = Path(directory) / "many-alternatives.vcf"
            too_many_alternatives.write_text(
                "chr1\t1\t.\tA\tC,G,T\t.\tPASS\t.\n", encoding="utf-8"
            )
            too_many_records = Path(directory) / "many-records.vcf"
            too_many_records.write_text(
                "chr1\t1\t.\tA\tC\t.\tPASS\t.\n"
                "chr1\t2\t.\tA\tG\t.\tPASS\t.\n"
                "chr1\t3\t.\tA\tT\t.\tPASS\t.\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(InputLimitError, "allele bases"):
                list(read_vcf(huge_allele, limits=self._small_limits()))
            with self.assertRaisesRegex(InputLimitError, "alternatives per record"):
                list(read_vcf(too_many_alternatives, limits=self._small_limits()))
            with self.assertRaisesRegex(InputLimitError, "record limit"):
                list(read_vcf(too_many_records, limits=self._small_limits()))
