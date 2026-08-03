# Genopedia

Genopedia is an offline-first toolkit for inspecting DNA/RNA sequences and producing reproducible local reports. It is designed to run after download on a normal Python installation without TensorFlow, PyTorch, a database, or an internet connection.

The current release provides:

- Streaming FASTA, FASTQ, VCF, VCF.GZ, and raw-sequence readers.
- Sequence validation, GC fraction, ambiguous-base counts, Phred summaries, and warnings.
- Overlapping motif search and transparent candidate-region heuristics.
- Sequence comparison with substitutions, insertions, deletions, and replacements.
- A deterministic dependency-free k-mer classifier.
- Self-contained HTML/SVG reports and JSON summaries.
- A research-only interpretation boundary: no diagnosis, treatment advice, or proposed DNA edits.

PCR and sequencing instruments are vendor-specific. Genopedia accepts exported files by default and exposes a clean boundary for future vendor adapters; it does not pretend that generic software can control every PCR device without its model and communication protocol.

## Quick start from a fresh download

Requirements: Python 3.10 or newer. The core runtime uses only the Python standard library.

```powershell
python -m genopedia demo --length 120 --output report.html --json-output report.json
```

Open `report.html` locally. No server or deployment is required.

Analyze a file:

```powershell
python -m genopedia analyze sample.fasta --output sample-report.html --json-output sample.json
python -m genopedia analyze sample.fastq --output reads-report.html
python -m genopedia analyze variants.vcf.gz --output variants-report.html
```

The convenience launcher also works directly from the repository root:

```powershell
python run_genopedia.py demo
```

## Development

Run the built-in test suite without installing pytest:

```powershell
python -m unittest discover -s tests -v
```

Install the package in editable mode if you want the `genopedia` command:

```powershell
python -m pip install -e .
genopedia demo
```

Optional integrations are intentionally isolated from the core:

```powershell
python -m pip install -e .[bio]  # Biopython helpers
python -m pip install -e .[ml]   # NumPy/scikit-learn extensions
python -m pip install -e .[dev]  # pytest, formatting, and lint tools
```

## Coordinate and safety conventions

Sequence comparisons use zero-based positions. VCF positions remain one-based and are marked as such in variant metadata. Variant interpretations are `unknown` unless supplied evidence matches a supported evidence label. Candidate promoters and start codons are heuristics, not gene annotation.

Genopedia is intended for research and engineering workflows. Any clinical interpretation, laboratory action, or genetic intervention requires validated laboratory methods and qualified human review.

## Project layout

```text
genopedia/
├── genopedia/       # dependency-free package and CLI
├── examples/        # runnable example
├── tests/           # standard-library tests
├── pyproject.toml   # install metadata and optional extras
└── run_genopedia.py # fresh-checkout launcher
```

## License

MIT. See [LICENSE](LICENSE).
