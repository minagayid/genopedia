"""Command-line interface for Genopedia."""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Sequence

from .anomalies import SequenceAnomalyDetector
from .core import SequenceAnalyzer, SequenceRecord
from .correction import CorrectionPlanner
from .io import read_input
from .reporting import render_html_report, write_html_report
from .references import DEFAULT_MANIFEST, ReferencePlan, ReferenceRegistry
from .catalog import read_jsonl
from .schema import schema_json


def _synthetic_record(length: int, seed: int) -> SequenceRecord:
    if length < 1:
        raise ValueError("length must be at least 1")
    generator = random.Random(seed)
    sequence = "".join(generator.choice("ATGC") for _ in range(length))
    return SequenceRecord(identifier="synthetic", sequence=sequence, source_format="synthetic")


def _summary(
    records: list[SequenceRecord],
    analyzer: SequenceAnalyzer,
    variants: list,
    reference_plan: ReferencePlan | None = None,
) -> dict[str, object]:
    reports = analyzer.summarize_records(records)
    sequence_anomalies = [item for record in records for item in SequenceAnomalyDetector().detect(record)]
    correction_plan = CorrectionPlanner().plan(variants)
    return {
        "records": [report.to_dict() for report in reports],
        "variants": [variant.to_dict() for variant in variants],
        "sequence_anomalies": [item.to_dict() for item in sequence_anomalies],
        "correction_plan": [item.to_dict() for item in correction_plan],
        "reference_plan": reference_plan.to_dict() if reference_plan else None,
        "safety": "Research use only; evidence requires human review and no automatic sequence edit is performed.",
    }


def _write_outputs(
    records: list[SequenceRecord],
    variants: list,
    output: Path,
    json_output: Path | None,
    reference_plan: ReferencePlan | None = None,
) -> None:
    analyzer = SequenceAnalyzer()
    reports = analyzer.summarize_records(records)
    sequence_anomalies = [item for record in records for item in SequenceAnomalyDetector().detect(record)]
    correction_plan = CorrectionPlanner().plan(variants)
    write_html_report(
        output,
        render_html_report(
            records,
            variants=variants,
            quality_reports=reports,
            sequence_anomalies=sequence_anomalies,
            correction_suggestions=correction_plan,
            reference_plan=reference_plan,
        ),
    )
    if json_output is not None:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(
            json.dumps(_summary(records, analyzer, variants, reference_plan), indent=2, sort_keys=True),
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
    demo.add_argument("--molecule", choices=["DNA", "RNA", "PROTEIN"], default="DNA")
    demo.add_argument("--reference-purpose", choices=["reference", "anomaly_detection", "correction"], default="anomaly_detection")

    analyze = commands.add_parser("analyze", help="analyze FASTA, FASTQ, VCF, or raw sequence text")
    analyze.add_argument("input", type=Path)
    analyze.add_argument("--format", default="auto", choices=["auto", "fasta", "fastq", "vcf", "text"])
    analyze.add_argument("--output", type=Path, default=Path("genopedia-report.html"))
    analyze.add_argument("--json-output", type=Path)
    analyze.add_argument("--molecule", choices=["DNA", "RNA", "PROTEIN"], default="DNA")
    analyze.add_argument("--reference-purpose", choices=["reference", "anomaly_detection", "correction"], default="anomaly_detection")

    compare = commands.add_parser("compare", help="compare a reference sequence with a sample sequence")
    compare.add_argument("reference", type=Path)
    compare.add_argument("sample", type=Path)
    compare.add_argument("--chromosome", default="chr1")
    compare.add_argument("--output", type=Path, default=Path("genopedia-comparison.html"))
    compare.add_argument("--json-output", type=Path)

    reference = commands.add_parser("reference", help="inspect the versioned metadata-only reference registry")
    reference_commands = reference.add_subparsers(dest="reference_command", required=True)
    for command_name, help_text in (("list", "list registry sources"), ("search", "search registry sources")):
        reference_list = reference_commands.add_parser(command_name, help=help_text)
        reference_list.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
        reference_list.add_argument("--query", default="")
        reference_list.add_argument("--tier")
        reference_list.add_argument("--evidence-class")
        reference_list.add_argument("--role")
        reference_list.add_argument("--molecule")
        reference_list.add_argument("--access-mode")
        reference_list.add_argument("--json", action="store_true", dest="as_json")
    validate = reference_commands.add_parser("validate", help="validate a local manifest without downloading data")
    validate.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    validate.add_argument("--json", action="store_true", dest="as_json")
    plan = reference_commands.add_parser("plan", help="build a deterministic source-selection plan")
    plan.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    plan.add_argument("--purpose", choices=["reference", "anomaly_detection", "correction"], default="reference")
    plan.add_argument("--molecule", choices=["DNA", "RNA", "PROTEIN"], default="DNA")
    plan.add_argument("--json", action="store_true", dest="as_json")

    schema = commands.add_parser("schema", help="export or validate the protein data contract")
    schema_commands = schema.add_subparsers(dest="schema_command", required=True)
    schema_export = schema_commands.add_parser("export", help="write the machine-readable schema")
    schema_export.add_argument("--output", type=Path, required=True)
    schema_validate = schema_commands.add_parser("validate", help="validate a JSONL catalog")
    schema_validate.add_argument("input", type=Path)
    return parser


def _reference_rows(registry: ReferenceRegistry, args: argparse.Namespace) -> list[dict[str, object]]:
    return [
        {
            "id": source.id,
            "name": source.name,
            "tier": source.tier,
            "evidence_class": source.evidence_class,
            "roles": list(source.roles),
            "molecules": list(source.molecules),
            "provider_url": source.provider_url,
            "access_mode": source.access_mode,
            "redistribution": source.redistribution,
            "acquisition": source.acquisition,
            "data_products": list(source.data_products),
        }
        for source in registry.search(
            args.query,
            tier=args.tier,
            evidence_class=args.evidence_class,
            role=args.role,
            molecule=args.molecule,
            access_mode=args.access_mode,
        )
    ]


def _run_reference_command(args: argparse.Namespace) -> int:
    registry = ReferenceRegistry.from_path(args.manifest)
    if args.reference_command == "validate":
        payload = {
            "status": "valid",
            "manifest": str(args.manifest),
            "schema_version": registry.schema_version,
            "manifest_version": registry.manifest_version,
            "source_count": len(registry.sources),
        }
    elif args.reference_command in {"list", "search"}:
        rows = _reference_rows(registry, args)
        if args.as_json:
            print(json.dumps(rows, indent=2, sort_keys=True))
        else:
            for row in rows:
                print(f"{row['id']}\t{row['tier']}\t{row['evidence_class']}\t{row['name']}\t{row['access_mode']}")
        return 0
    else:
        payload = registry.plan(purpose=args.purpose, molecule=args.molecule).to_dict()
    print(json.dumps(payload, indent=2, sort_keys=True) if args.as_json or args.reference_command != "validate" else payload["status"])
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "schema":
            if args.schema_command == "export":
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(schema_json(), encoding="utf-8")
                print(f"Schema written to {args.output}")
                return 0
            records = read_jsonl(args.input)
            print(json.dumps({"status": "valid", "records": len(records)}, sort_keys=True))
            return 0
        if args.command == "reference":
            return _run_reference_command(args)
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
        reference_plan = ReferenceRegistry.from_path().plan(
            purpose=getattr(args, "reference_purpose", "correction"),
            molecule=getattr(args, "molecule", "DNA"),
        )
        _write_outputs(records, variants, args.output, args.json_output, reference_plan)
        print(f"Report written to {args.output}")
        if args.json_output:
            print(f"Summary written to {args.json_output}")
        return 0
    except (OSError, ValueError) as error:
        parser.error(str(error))
        return 2
