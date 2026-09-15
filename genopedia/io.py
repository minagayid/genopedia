"""Streaming readers for common sequence and variant text formats."""

from __future__ import annotations

import gzip
from contextlib import contextmanager
from dataclasses import dataclass
from io import StringIO
from pathlib import Path
from typing import Iterator

from .core import SequenceRecord, Variant


PathLike = str | Path


class InputLimitError(ValueError):
    """Raised when an input exceeds a documented resource limit."""


@dataclass(frozen=True)
class InputLimits:
    """Resource ceilings applied by every text reader.

    Defaults are intentionally conservative for a local analysis tool: 128 MiB
    of decoded input, 64 MiB of compressed input, 50,000 records, 5 million
    bases per sequence/variant record, and 1 million bases and quality symbols
    across the whole file. Callers processing larger trusted files can pass a
    larger ``InputLimits`` instance explicitly.
    """

    max_compressed_bytes: int = 64 * 1024 * 1024
    max_decompressed_bytes: int = 128 * 1024 * 1024
    max_records: int = 50_000
    max_record_bases: int = 5_000_000
    max_total_bases: int = 1_000_000
    max_total_quality_symbols: int = 1_000_000
    max_line_bytes: int = 8 * 1024 * 1024
    max_alternatives_per_record: int = 1_000
    max_info_entries_per_record: int = 1_000

    def __post_init__(self) -> None:
        for name, value in self.__dict__.items():
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise ValueError(f"{name} must be a positive integer")


DEFAULT_INPUT_LIMITS = InputLimits()
_READ_CHUNK_BYTES = 64 * 1024


class _CompressedByteLimiter:
    """File-like wrapper that prevents gzip from reading past its byte budget."""

    def __init__(self, raw, limit: int) -> None:
        self._raw = raw
        self._limit = limit
        self._read = 0

    def read(self, size: int = -1) -> bytes:
        if size == 0:
            return b""
        remaining_plus_probe = self._limit - self._read + 1
        request = (
            remaining_plus_probe
            if size is None or size < 0
            else min(size, remaining_plus_probe)
        )
        data = self._raw.read(request)
        self._read += len(data)
        if self._read > self._limit:
            raise InputLimitError(
                f"compressed input exceeds {self._limit} byte limit"
            )
        return data

    def readable(self) -> bool:
        return True

    def seekable(self) -> bool:
        return False


class _BoundedTextReader:
    """Decode lines from a byte stream while bounding read-ahead and line size."""

    def __init__(self, source, max_bytes: int) -> None:
        self._source = source
        self._max_bytes = max_bytes
        self._bytes_read = 0
        self._buffer = bytearray()
        self._eof = False
        self.last_line_byte_count = 0

    def _fill(self) -> None:
        if self._eof:
            return
        remaining_plus_probe = self._max_bytes - self._bytes_read + 1
        if remaining_plus_probe <= 0:
            remaining_plus_probe = 1
        data = self._source.read(min(_READ_CHUNK_BYTES, remaining_plus_probe))
        if not data:
            self._eof = True
            return
        self._bytes_read += len(data)
        if self._bytes_read > self._max_bytes:
            raise InputLimitError(
                f"decompressed input exceeds {self._max_bytes} byte limit"
            )
        self._buffer.extend(data)

    def _line_end(self) -> int | None:
        carriage_return = self._buffer.find(b"\r")
        line_feed = self._buffer.find(b"\n")
        if carriage_return < 0:
            return line_feed + 1 if line_feed >= 0 else None
        if line_feed >= 0 and line_feed < carriage_return:
            return line_feed + 1
        if carriage_return + 1 == len(self._buffer) and not self._eof:
            self._fill()
        end = carriage_return + 1
        if end < len(self._buffer) and self._buffer[end] == 10:
            end += 1
        return end

    def readline(self, size: int = -1) -> str:
        if size == 0:
            self.last_line_byte_count = 0
            return ""
        result = bytearray()
        while size < 0 or len(result) < size:
            line_end = self._line_end()
            available = line_end if line_end is not None else len(self._buffer)
            if available:
                take = available if size < 0 else min(available, size - len(result))
                result.extend(self._buffer[:take])
                del self._buffer[:take]
                if (line_end is not None and take == available) or (
                    size >= 0 and len(result) >= size
                ):
                    break
                continue
            if self._eof:
                break
            self._fill()
        self.last_line_byte_count = len(result)
        return result.decode("utf-8", errors="replace")

    def __iter__(self):
        return self

    def __next__(self) -> str:
        line = self.readline()
        if not line:
            raise StopIteration
        return line


@contextmanager
def _open_text(
    path: PathLike, limits: InputLimits = DEFAULT_INPUT_LIMITS
) -> Iterator[_BoundedTextReader]:
    """Open bounded UTF-8 text, counting decoded bytes and compressed gzip bytes."""

    path = Path(path)
    raw = path.open("rb")
    source = raw
    try:
        if path.suffix.lower() == ".gz":
            compressed = _CompressedByteLimiter(raw, limits.max_compressed_bytes)
            source = gzip.GzipFile(fileobj=compressed, mode="rb")
        yield _BoundedTextReader(source, limits.max_decompressed_bytes)
    finally:
        if source is not raw:
            source.close()
        raw.close()


def _read_bounded_line(handle: _BoundedTextReader, limits: InputLimits) -> str:
    line = handle.readline(limits.max_line_bytes + 1)
    if handle.last_line_byte_count > limits.max_line_bytes:
        raise InputLimitError(f"input line exceeds {limits.max_line_bytes} byte limit")
    return line


def _checked_sequence_chunk(
    line: str, current_bases: int, limits: InputLimits, identifier: str
) -> str:
    normalized_bases = sum(
        len(character.upper()) for character in line if not character.isspace()
    )
    if current_bases + normalized_bases > limits.max_record_bases:
        raise InputLimitError(
            f"sequence record {identifier!r} exceeds {limits.max_record_bases} base limit"
        )
    return "".join(character.upper() for character in line if not character.isspace())


def _check_record_count(count: int, limits: InputLimits) -> None:
    if count > limits.max_records:
        raise InputLimitError(f"input exceeds {limits.max_records} record limit")


def _check_total_bases(count: int, limits: InputLimits) -> None:
    if count > limits.max_total_bases:
        raise InputLimitError(
            f"input exceeds {limits.max_total_bases} total base limit"
        )


def _check_total_quality_symbols(count: int, limits: InputLimits) -> None:
    if count > limits.max_total_quality_symbols:
        raise InputLimitError(
            f"input exceeds {limits.max_total_quality_symbols} total quality-symbol limit"
        )


def _record_identifier(header: str, marker: str) -> tuple[str, str]:
    value = header.rstrip("\n\r")
    if not value.startswith(marker):
        raise ValueError(f"expected {marker!r} header")
    content = value[len(marker) :].strip()
    if not content:
        raise ValueError("sequence header has no identifier")
    fields = content.split(None, 1)
    return fields[0], fields[1] if len(fields) == 2 else ""


def read_fasta(
    path: PathLike, *, limits: InputLimits = DEFAULT_INPUT_LIMITS
) -> Iterator[SequenceRecord]:
    """Yield bounded FASTA records without loading the full file into memory."""

    identifier: str | None = None
    description = ""
    sequence_builder = StringIO()
    record_bases = 0
    record_count = 0
    total_bases = 0
    with _open_text(path, limits) as handle:
        line_number = 0
        while True:
            line = _read_bounded_line(handle, limits)
            if not line:
                break
            line_number += 1
            if line.startswith(">"):
                if identifier is not None:
                    yield SequenceRecord(
                        identifier=identifier,
                        sequence=sequence_builder.getvalue(),
                        description=description,
                        source_format="fasta",
                    )
                record_count += 1
                _check_record_count(record_count, limits)
                identifier, description = _record_identifier(line, ">")
                sequence_builder = StringIO()
                record_bases = 0
            elif line.strip():
                if identifier is None:
                    raise ValueError(f"FASTA sequence data before header at line {line_number}")
                chunk = _checked_sequence_chunk(line, record_bases, limits, identifier)
                if chunk:
                    next_total_bases = total_bases + len(chunk)
                    _check_total_bases(next_total_bases, limits)
                    sequence_builder.write(chunk)
                    record_bases += len(chunk)
                    total_bases = next_total_bases
        if identifier is not None:
            yield SequenceRecord(
                identifier=identifier,
                sequence=sequence_builder.getvalue(),
                description=description,
                source_format="fasta",
            )


def read_fastq(
    path: PathLike, *, limits: InputLimits = DEFAULT_INPUT_LIMITS
) -> Iterator[SequenceRecord]:
    """Yield bounded FASTQ records, including wrapped sequence and quality lines."""

    record_count = 0
    total_bases = 0
    total_quality_symbols = 0
    with _open_text(path, limits) as handle:
        while True:
            header = _read_bounded_line(handle, limits)
            if not header:
                return
            record_count += 1
            _check_record_count(record_count, limits)
            identifier, description = _record_identifier(header, "@")
            sequence_builder = StringIO()
            sequence_bases = 0
            while True:
                line = _read_bounded_line(handle, limits)
                if not line:
                    raise ValueError(f"truncated FASTQ record {identifier!r} before its '+' line")
                if line.startswith("+"):
                    break
                if line.strip():
                    chunk = _checked_sequence_chunk(line, sequence_bases, limits, identifier)
                    if chunk:
                        next_total_bases = total_bases + len(chunk)
                        _check_total_bases(next_total_bases, limits)
                        sequence_builder.write(chunk)
                        sequence_bases += len(chunk)
                        total_bases = next_total_bases
            sequence = sequence_builder.getvalue()

            quality_builder = StringIO()
            quality_length = 0
            while quality_length < len(sequence):
                line = _read_bounded_line(handle, limits)
                if not line:
                    raise ValueError(f"truncated FASTQ record {identifier!r} in quality data")
                quality_chunk = line.rstrip("\r\n")
                if quality_length + len(quality_chunk) > len(sequence):
                    raise ValueError(
                        f"FASTQ record {identifier!r} has mismatched sequence and quality lengths"
                    )
                next_total_quality_symbols = total_quality_symbols + len(quality_chunk)
                _check_total_quality_symbols(next_total_quality_symbols, limits)
                quality_builder.write(quality_chunk)
                quality_length += len(quality_chunk)
                total_quality_symbols = next_total_quality_symbols

            quality_text = quality_builder.getvalue()
            if len(sequence) != len(quality_text):
                raise ValueError(
                    f"FASTQ record {identifier!r} has mismatched sequence and quality lengths"
                )
            quality_scores = tuple(max(0, ord(value) - 33) for value in quality_text)
            yield SequenceRecord(
                identifier=identifier,
                sequence=sequence,
                description=description,
                quality_scores=quality_scores,
                source_format="fastq",
            )


def _iter_split(value: str, separator: str) -> Iterator[str]:
    start = 0
    while True:
        end = value.find(separator, start)
        if end < 0:
            yield value[start:]
            return
        yield value[start:end]
        start = end + len(separator)


def _parse_info(value: str, limits: InputLimits) -> dict[str, object]:
    metadata: dict[str, object] = {}
    if value in {"", "."}:
        return metadata
    for entry_count, item in enumerate(_iter_split(value, ";"), start=1):
        if entry_count > limits.max_info_entries_per_record:
            raise InputLimitError(
                f"VCF INFO exceeds {limits.max_info_entries_per_record} entries per record"
            )
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


def read_vcf(
    path: PathLike, *, limits: InputLimits = DEFAULT_INPUT_LIMITS
) -> Iterator[Variant]:
    """Yield bounded normalized first-ALT variants while preserving VCF metadata."""

    record_count = 0
    total_variant_bases = 0
    with _open_text(path, limits) as handle:
        line_number = 0
        while True:
            line = _read_bounded_line(handle, limits)
            if not line:
                break
            line_number += 1
            if not line.strip() or line.startswith("#"):
                continue
            record_count += 1
            _check_record_count(record_count, limits)
            fields = line.rstrip("\r\n").split("\t", 8)
            if len(fields) < 8:
                raise ValueError(f"VCF record at line {line_number} has fewer than 8 columns")
            (
                chromosome,
                position_text,
                identifier,
                reference,
                alternate_text,
                quality_text,
                filter_value,
                info,
            ) = fields[:8]
            try:
                position = int(position_text)
            except ValueError as error:
                raise ValueError(f"invalid VCF position at line {line_number}") from error
            alternatives: list[str] = []
            allele_bases = len(reference) if reference != "." else 0
            _check_total_bases(total_variant_bases + allele_bases, limits)
            for value in _iter_split(alternate_text, ","):
                if not value or value == ".":
                    continue
                if len(alternatives) >= limits.max_alternatives_per_record:
                    raise InputLimitError(
                        "VCF record exceeds "
                        f"{limits.max_alternatives_per_record} alternatives per record"
                    )
                allele_bases += len(value)
                if allele_bases > limits.max_record_bases:
                    raise InputLimitError(
                        f"VCF record exceeds {limits.max_record_bases} allele bases"
                    )
                _check_total_bases(total_variant_bases + allele_bases, limits)
                alternatives.append(value)
            if not alternatives:
                raise ValueError(f"VCF record at line {line_number} has no ALT allele")
            quality = None if quality_text == "." else float(quality_text)
            metadata = _parse_info(info, limits)
            metadata.update(
                {
                    "id": identifier,
                    "filter": filter_value,
                    "alternatives": alternatives,
                    "coordinate_system": "1-based",
                }
            )
            total_variant_bases += allele_bases
            yield Variant(
                chromosome=chromosome,
                position=position,
                reference=reference.upper(),
                observed=alternatives[0].upper(),
                quality=quality,
                variant_type=_variant_type(reference, alternatives[0]),
                metadata=metadata,
            )


def read_raw_sequence(
    path: PathLike,
    identifier: str | None = None,
    *,
    limits: InputLimits = DEFAULT_INPUT_LIMITS,
) -> Iterator[SequenceRecord]:
    sequence_builder = StringIO()
    sequence_bases = 0
    total_bases = 0
    with _open_text(path, limits) as handle:
        while True:
            line = _read_bounded_line(handle, limits)
            if not line:
                break
            chunk = _checked_sequence_chunk(
                line, sequence_bases, limits, identifier or Path(path).stem
            )
            if chunk:
                next_total_bases = total_bases + len(chunk)
                _check_total_bases(next_total_bases, limits)
                sequence_builder.write(chunk)
                sequence_bases += len(chunk)
                total_bases = next_total_bases
    _check_record_count(1, limits)
    sequence = sequence_builder.getvalue()
    yield SequenceRecord(
        identifier=identifier or Path(path).stem,
        sequence=sequence,
        source_format="text",
    )


def read_sequence_file(
    path: PathLike, format: str = "auto", *, limits: InputLimits = DEFAULT_INPUT_LIMITS
) -> Iterator[SequenceRecord]:
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
        yield from read_fasta(path, limits=limits)
    elif selected in {"fastq", "fq"}:
        yield from read_fastq(path, limits=limits)
    elif selected in {"text", "raw"}:
        yield from read_raw_sequence(path, limits=limits)
    else:
        raise ValueError(f"unsupported sequence format: {format}")


@dataclass(frozen=True)
class InputData:
    records: tuple[SequenceRecord, ...] = ()
    variants: tuple[Variant, ...] = ()


def read_input(
    path: PathLike, format: str = "auto", *, limits: InputLimits = DEFAULT_INPUT_LIMITS
) -> InputData:
    path = Path(path)
    selected = format.lower()
    if selected == "auto" and path.suffix.lower() in {".vcf", ".gz"}:
        selected = "vcf" if path.suffix.lower() == ".vcf" else (
            "vcf" if path.name.lower().endswith(".vcf.gz") else "auto"
        )
    if selected == "vcf":
        return InputData(variants=tuple(read_vcf(path, limits=limits)))
    return InputData(records=tuple(read_sequence_file(path, format=selected, limits=limits)))
