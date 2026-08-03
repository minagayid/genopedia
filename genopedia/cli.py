"""Command-line interface for Genopedia."""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Sequence

from .core import SequenceAnalyzer, SequenceRecord
from .io import read_input
from .reporting import render_html_report, write_html_report


def _synthetic_record(length: int, seed: int) -> SequenceRecord:
    if length < 1:
        raise ValueError("length must be at least 1")
    generator = random.Random(seed)
    sequence = "".join(generator.choice("ATGC") for _ in range(length))
    return SequenceRecord(identifier="synthetic", sequence=sequence, source_format="synthetic")


def _summary(records: list[SequenceRecord], analyzer: SequenceAnalyzer, variants: list) -> dict[str, object]:
    reports = analyzer.summarize_records(records)
    return {
        "records": [report.to_dict() for report in reports],
        "variants": [variant.to_dict() for variant in variants],
    }


def _write_outputs(
    records: list[SequenceRecord],
    variants: list,
    output: Path,
    json_output: Path | None,
) -> None:
    analyzer = SequenceAnalyzer()
    reports = analyzer.summarize_records(records)
    write_html_report(
        output,
        render_html_report(records, variants=variants, quality_reports=reports),
    )
    if json_output is not None:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(
            json.dumps(_summary(records, analyzer, variants), indent=2, sort_keys=True),
            encoding="utf-8",
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="genopedia",
        description="Offline-first DNA/RNA sequence inspection and reporting.",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    demo = commands.add_parser("demo", help="generate a deterministic synthetic report")
    demo.add_argument("--length", type=int, default=120)
    demo.add_argument("--seed", type=int, default=7)
    demo.add_argument("--output", type=Path, default=Path("genopedia-report.html"))
    demo.add_argument("--json-output", type=Path)

    analyze = commands.add_parser("analyze", help="analyze FASTA, FASTQ, VCF, or raw sequence text")
    analyze.add_argument("input", type=Path)
    analyze.add_argument("--format", default="auto", choices=["auto", "fasta", "fastq", "vcf", "text"])
    analyze.add_argument("--output", type=Path, default=Path("genopedia-report.html"))
    analyze.add_argument("--json-output", type=Path)

    compare = commands.add_parser("compare", help="compare a reference sequence with a sample sequence")
    compare.add_argument("reference", type=Path)
    compare.add_argument("sample", type=Path)
    compare.add_argument("--chromosome", default="chr1")
    compare.add_argument("--output", type=Path, default=Path("genopedia-comparison.html"))
    compare.add_argument("--json-output", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "demo":
            records = [_synthetic_record(args.length, args.seed)]
            variants = []
        elif args.command == "analyze":
            data = read_input(args.input, format=args.format)
            records = list(data.records)
            variants = list(data.variants)
        else:
            reference = read_input(args.reference, format="auto")
            sample = read_input(args.sample, format="auto")
            if not reference.records or not sample.records:
                raise ValueError("compare requires sequence files containing at least one record each")
            records = [reference.records[0], sample.records[0]]
            variants = SequenceAnalyzer().detect_variants(
                records[0].sequence,
                records[1].sequence,
                chromosome=args.chromosome,
            )
        _write_outputs(records, variants, args.output, args.json_output)
        print(f"Report written to {args.output}")
        if args.json_output:
            print(f"Summary written to {args.json_output}")
        return 0
    except (OSError, ValueError) as error:
        parser.error(str(error))
        return 2
