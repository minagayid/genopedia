"""Streaming readers for common sequence and variant text formats."""

from __future__ import annotations

import gzip
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, TextIO

from .core import SequenceRecord, Variant, normalize_sequence


PathLike = str | Path


def _open_text(path: PathLike) -> TextIO:
    path = Path(path)
    if path.suffix.lower() == ".gz":
        return gzip.open(path, "rt", encoding="utf-8", errors="replace")
    return path.open("r", encoding="utf-8", errors="replace")


def _record_identifier(header: str, marker: str) -> tuple[str, str]:
    value = header.rstrip("\n\r")
    if not value.startswith(marker):
        raise ValueError(f"expected {marker!r} header")
    content = value[len(marker) :].strip()
    if not content:
        raise ValueError("sequence header has no identifier")
    fields = content.split(None, 1)
    return fields[0], fields[1] if len(fields) == 2 else ""


def read_fasta(path: PathLike) -> Iterator[SequenceRecord]:
    """Yield FASTA records without loading the full file into memory."""

    identifier: str | None = None
    description = ""
    chunks: list[str] = []
    with _open_text(path) as handle:
        for line_number, line in enumerate(handle, start=1):
            if line.startswith(">"):
                if identifier is not None:
                    yield SequenceRecord(
                        identifier=identifier,
                        sequence=normalize_sequence("".join(chunks)),
                        description=description,
                        source_format="fasta",
                    )
                identifier, description = _record_identifier(line, ">")
                chunks = []
            elif line.strip():
                if identifier is None:
                    raise ValueError(f"FASTA sequence data before header at line {line_number}")
                chunks.append(line.strip())
        if identifier is not None:
            yield SequenceRecord(
                identifier=identifier,
                sequence=normalize_sequence("".join(chunks)),
                description=description,
                source_format="fasta",
            )


def read_fastq(path: PathLike) -> Iterator[SequenceRecord]:
    """Yield FASTQ records and decode Sanger/Phred+33 qualities."""

    with _open_text(path) as handle:
        while True:
            header = handle.readline()
            if not header:
                return
            sequence_line = handle.readline()
            plus_line = handle.readline()
            quality_line = handle.readline()
            if not sequence_line or not plus_line or not quality_line:
                raise ValueError("truncated FASTQ record")
            identifier, description = _record_identifier(header, "@")
            if not plus_line.startswith("+"):
                raise ValueError(f"FASTQ record {identifier!r} is missing its '+' line")
            sequence = normalize_sequence(sequence_line)
            quality_text = quality_line.rstrip("\r\n")
            if len(sequence) != len(quality_text):
                raise ValueError(f"FASTQ record {identifier!r} has mismatched sequence and quality lengths")
            quality_scores = tuple(max(0, ord(value) - 33) for value in quality_text)
            yield SequenceRecord(
                identifier=identifier,
                sequence=sequence,
                description=description,
                quality_scores=quality_scores,
                source_format="fastq",
            )


def _parse_info(value: str) -> dict[str, object]:
    metadata: dict[str, object] = {}
    if value in {"", "."}:
        return metadata
    for item in value.split(";"):
        if "=" not in item:
            metadata[item] = True
            continue
        key, item_value = item.split("=", 1)
        metadata[key] = item_value
    return metadata


def _variant_type(reference: str, observed: str) -> str:
    if len(reference) == len(observed) == 1:
        return "substitution"
    if len(reference) < len(observed):
        return "insertion"
    if len(reference) > len(observed):
        return "deletion"
    return "replacement"


def read_vcf(path: PathLike) -> Iterator[Variant]:
    """Yield normalized first-ALT variants while preserving VCF metadata."""

    with _open_text(path) as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip() or line.startswith("#"):
                continue
            fields = line.rstrip("\r\n").split("\t")
            if len(fields) < 8:
                raise ValueError(f"VCF record at line {line_number} has fewer than 8 columns")
            chromosome, position_text, identifier, reference, alternate_text, quality_text, filter_value, info = fields[:8]
            try:
                position = int(position_text)
            except ValueError as error:
                raise ValueError(f"invalid VCF position at line {line_number}") from error
            alternatives = [value for value in alternate_text.split(",") if value and value != "."]
            if not alternatives:
                raise ValueError(f"VCF record at line {line_number} has no ALT allele")
            quality = None if quality_text == "." else float(quality_text)
            metadata = _parse_info(info)
            metadata.update(
                {
                    "id": identifier,
                    "filter": filter_value,
                    "alternatives": alternatives,
                    "coordinate_system": "1-based",
                }
            )
            yield Variant(
                chromosome=chromosome,
                position=position,
                reference=reference.upper(),
                observed=alternatives[0].upper(),
                quality=quality,
                variant_type=_variant_type(reference, alternatives[0]),
                metadata=metadata,
            )


def read_raw_sequence(path: PathLike, identifier: str | None = None) -> Iterator[SequenceRecord]:
    with _open_text(path) as handle:
        sequence = normalize_sequence(handle.read())
    yield SequenceRecord(
        identifier=identifier or Path(path).stem,
        sequence=sequence,
        source_format="text",
    )


def read_sequence_file(path: PathLike, format: str = "auto") -> Iterator[SequenceRecord]:
    path = Path(path)
    selected = format.lower()
    if selected == "auto":
        suffixes = [suffix.lower() for suffix in path.suffixes]
        if ".fastq" in suffixes or ".fq" in suffixes:
            selected = "fastq"
        elif ".fasta" in suffixes or ".fa" in suffixes or ".fna" in suffixes:
            selected = "fasta"
        else:
            selected = "text"
    if selected in {"fasta", "fa", "fna"}:
        yield from read_fasta(path)
    elif selected in {"fastq", "fq"}:
        yield from read_fastq(path)
    elif selected in {"text", "raw"}:
        yield from read_raw_sequence(path)
    else:
        raise ValueError(f"unsupported sequence format: {format}")


@dataclass(frozen=True)
class InputData:
    records: tuple[SequenceRecord, ...] = ()
    variants: tuple[Variant, ...] = ()


def read_input(path: PathLike, format: str = "auto") -> InputData:
    path = Path(path)
    selected = format.lower()
    if selected == "auto" and path.suffix.lower() in {".vcf", ".gz"}:
        selected = "vcf" if path.suffix.lower() == ".vcf" else (
            "vcf" if path.name.lower().endswith(".vcf.gz") else "auto"
        )
    if selected == "vcf":
        return InputData(variants=tuple(read_vcf(path)))
    return InputData(records=tuple(read_sequence_file(path, format=selected)))

