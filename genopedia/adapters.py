"""Vendor-neutral local adapters for exported instrument files."""

from __future__ import annotations

from pathlib import Path

from .io import InputData, read_input


SUPPORTED_SUFFIXES = frozenset(
    {".fa", ".fasta", ".fna", ".fq", ".fastq", ".vcf", ".gz"}
)


class FileDropAdapter:
    """Read sequence exports placed in a local directory.

    The adapter intentionally does not assume a PCR vendor, USB protocol, or
    network service. A vendor-specific adapter can implement the same
    ``discover``/``read`` boundary later without changing analysis code.
    """

    def __init__(self, directory: str | Path, recursive: bool = False) -> None:
        self.directory = Path(directory).resolve()
        self.recursive = recursive

    def discover(self) -> list[Path]:
        if not self.directory.is_dir():
            raise FileNotFoundError(f"file-drop directory does not exist: {self.directory}")
        candidates = self.directory.rglob("*") if self.recursive else self.directory.iterdir()
        supported: list[Path] = []
        for path in candidates:
            if not path.is_file():
                continue
            name = path.name.lower()
            if name.endswith((".fa", ".fasta", ".fna", ".fq", ".fastq", ".vcf", ".fa.gz", ".fasta.gz", ".fq.gz", ".fastq.gz", ".vcf.gz")):
                supported.append(path)
        return sorted(supported, key=lambda path: path.name.lower())

    def read(self, path: str | Path, format: str = "auto") -> InputData:
        source = Path(path).resolve()
        try:
            source.relative_to(self.directory)
        except ValueError as error:
            raise ValueError("file-drop adapter cannot read outside its configured directory") from error
        return read_input(source, format=format)

