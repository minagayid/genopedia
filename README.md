# Genopedia

**Sequence tools today. Comparative regeneration research as the next research layer.**

Genopedia's long-term research question is whether linked protein/RNA representations and context-rich expression evidence can help identify conserved regeneration-associated programs across sea stars, salamanders, and lizards. Kidney/nephron repair, beta-cell restoration, neural repair, and limb regeneration motivate that work, but they are separate, unproven translational goals. This repository does not demonstrate a regeneration therapy or a way to transfer animal traits into human DNA.

Start with the [sourced research program](docs/regeneration-research-program.md), [proposed benchmark protocol](docs/regeneration-benchmark.md), and [literature-lead register](docs/regeneration-study-register.json). The register is not an acquired or validated training dataset.

| Layer | Status | Entry point |
|---|---|---|
| Offline DNA/RNA inspection and local reports | Implemented software | Quick start below |
| Protein/transcript identity, provenance, and evidence separation | Implemented data contract | [Protein data format](docs/protein-data-format.md) |
| Optional authenticated API and container deployment | Present, requires API dependencies and configuration | [API deployment](docs/api-deployment.md) |
| Comparative regeneration data curation and leakage-resistant evaluation | Research specification, not an implemented pipeline | [Benchmark](docs/regeneration-benchmark.md) |
| Regeneration-specific ML, causal validation, and human translation | Not demonstrated in this repository | [Research limits and exit gates](docs/regeneration-research-program.md#current-status-and-exit-gates) |

An externally trained NCBI-derived model may become a sequence backbone after its dataset, checkpoint, and evaluation artifacts are verified. No training-job status, model quality, or regeneration result is implied by this README.

## Working toolkit

Genopedia is an offline-first toolkit for inspecting DNA/RNA sequences and producing reproducible local reports. It is designed to run after download on a normal Python installation without TensorFlow, PyTorch, a database, or an internet connection.

The repository also contains a provenance-first protein/genomics data contract. It is a normalized JSONL format with a machine-readable schema, deterministic catalog sorting, sequence SHA-256 deduplication, translation provenance fields, evidence separation, and an optional Jev semantic-ranking adapter. The contract is research-only: it is not for clinical use, synthesis, wet-lab execution, or organism engineering.

The companion [Genopedia Protein Data Format workbook](docs/Genopedia_Protein_Data_Format.xlsx) is the human-facing planning view. It includes the requested protein-first columns plus entity/field dictionaries, relationship guardrails, controlled terms, source registry, deterministic indexing/Jev guidance, examples, and validation rules.

The current release provides:

- Streaming FASTA, FASTQ, VCF, VCF.GZ, and raw-sequence readers.
- Bounded input parsing with configurable compressed/decoded byte, record, line, and per-record allele limits.
- Sequence validation, GC fraction, ambiguous-base counts, Phred summaries, and warnings.
- Overlapping motif search and transparent candidate-region heuristics.
- Sequence comparison with substitutions, insertions, deletions, and replacements.
- A deterministic dependency-free k-mer classifier.
- Self-contained HTML/SVG reports and JSON summaries.
- A versioned, metadata-only reference registry covering authoritative,
  diversity, empirical-read, benchmark, RNA, microbial, human, and
  contamination sources.
- Deterministic sequence-quality anomaly signals and evidence-gated correction
  planning that never rewrites the observed sequence.
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

Inspect the reference registry without downloading data:

```powershell
python -m genopedia reference validate
python -m genopedia reference search --molecule RNA --role rna_family --json
python -m genopedia reference plan --purpose correction --molecule DNA --json
```

Export and validate the protein data contract:

```powershell
python -m genopedia schema export --output schema/genopedia_protein_data.schema.json
python -m genopedia schema validate examples/protein_catalog.jsonl
```

Generate the guarded Jev plan for RefSeq Release 237:

```powershell
python -m genopedia jev plan --semantic-query "relevance to a specified molecular function or protein-of-interest workflow" --output docs/jev-refseq-release-237-plan.json --sql-output docs/jev-refseq-release-237.sql --full-release-scan
```

This writes a reviewable plan and PostgreSQL script; it does not contact Jev or
send records to a third party until PostgreSQL, Jev, the staged release, and
operator approval are present.

See [REFERENCE_ENGINE_PLAN.md](REFERENCE_ENGINE_PLAN.md) for the source
catalog, access/licensing boundary, implemented baseline, and production
upgrade path. The registry is deliberately metadata-only: large, controlled,
or non-redistributable datasets must be acquired under their provider terms.

The convenience launcher also works directly from the repository root:

```powershell
python run_genopedia.py demo
```

## Development

Run the full built-in test suite, including the optional API tests (pytest is not required):

```powershell
python -m pip install -e .[api]
python -m unittest discover -s tests -v
```

The core runtime itself uses only the standard library. For a dependency-free core-only test run, exclude the optional API test module:

```powershell
python -c "import unittest; from pathlib import Path; loader=unittest.TestLoader(); suite=unittest.TestSuite(loader.discover('tests', pattern=p.name) for p in sorted(Path('tests').glob('test_*.py')) if p.name != 'test_api.py'); result=unittest.TextTestRunner(verbosity=2).run(suite); raise SystemExit(not result.wasSuccessful())"
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

## Release and deployment

The core toolkit is a local Python package and CLI and needs no hosted service. This repository also includes an optional authenticated FastAPI service and container setup; see [API deployment](docs/api-deployment.md) for that separate path. CI checks the supported Python versions, builds source and wheel distributions, validates their metadata, installs the wheel into a clean virtual environment, and smoke-tests the installed CLI outside the source checkout.

For PyPI release setup, the release approval gate, and the versioned release checklist, see [docs/release-process.md](docs/release-process.md). Publishing requires a configured PyPI Trusted Publisher and approval in the GitHub `pypi` environment; no long-lived PyPI API token is stored in the repository.

## Coordinate and safety conventions

Sequence comparisons use zero-based positions. VCF positions remain one-based and are marked as such in variant metadata. Variant interpretations are `unknown` unless supplied evidence matches a supported evidence label. Candidate promoters and start codons are heuristics, not gene annotation.

Genopedia is intended for research and engineering workflows. Any clinical interpretation, laboratory action, or genetic intervention requires validated laboratory methods and qualified human review.

## Input resource limits

Readers default to a maximum of 64 MiB compressed input, 128 MiB decoded input, 50,000 records, 5 million sequence/allele bases per record, 1 million total bases per file, 1 million total FASTQ quality symbols, and 8 MiB per line. VCF records are also limited to 1,000 alternate alleles and 1,000 INFO entries. These defaults bound gzip expansion and memory use while retaining support for ordinary local datasets. Trusted workflows with larger files can pass a customized `InputLimits` value to `read_input`, `read_sequence_file`, or a format-specific reader; exceeding a limit raises `InputLimitError`.

```python
from genopedia.io import InputLimits, read_input

limits = InputLimits(max_decompressed_bytes=512 * 1024 * 1024)
data = read_input("large-sample.fasta", limits=limits)
```

## Project layout

```text
genopedia/
├── genopedia/       # dependency-free package and CLI
├── examples/        # runnable example
├── docs/            # research program, benchmark, protein contract, API/release docs
├── schema/           # machine-readable exported data contract
├── tests/           # standard-library tests
├── pyproject.toml   # install metadata and optional extras
└── run_genopedia.py # fresh-checkout launcher
```

## License

MIT. See [LICENSE](LICENSE).

## Agent evaluation roadmap

See [evaluation contracts and evidence gates](docs/evaluation-roadmap.md) and [Agent Eval Lab](https://github.com/minagayid/agent-eval-lab).
