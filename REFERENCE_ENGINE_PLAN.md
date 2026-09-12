# Genopedia reference engine plan

This repository now includes a metadata-only reference registry in
`genopedia/reference-manifest.json`. It records source identity, evidence
class, supported molecule, provider URL, acquisition strategy, access mode,
redistribution constraints, and index fields. It intentionally does not copy
large biological databases into Git or download controlled-access data.

## Implemented baseline

- Registry loading and structural validation with the standard library.
- Search and filtering by query, tier, evidence class, role, molecule, and access mode.
- Deterministic reference plans for general reference, anomaly detection, and correction review.
- Conservative sequence anomaly signals for invalid symbols, ambiguity, low Phred quality, and long homopolymers.
- Evidence-gated correction planning that never rewrites an input sequence.
- CLI entry points: `reference list`, `reference search`, `reference validate`, and `reference plan`.

Examples:

```text
python -m genopedia reference validate
python -m genopedia reference search --molecule RNA --role rna_family --json
python -m genopedia reference plan --purpose correction --molecule DNA --json
```

## Upgrade path to a production-capable engine

1. Add provider adapters that harvest metadata first and require an explicit
   dataset/accession selection before downloading.
2. Add a lockfile containing exact releases, URLs, file sizes, SHA-256 hashes,
   license/DUA references, and retrieval timestamps.
3. Normalize selected FASTA/FASTQ/VCF data while preserving originals and
   provenance; validate sequence alphabets and checksums at every boundary.
4. Build sharded FAI/k-mer/minimizer/Bloom/taxonomy indexes. Keep large index
   artifacts outside Git and address them from a local data root.
5. Add benchmark fixtures with known truth for substitutions, insertions,
   deletions, homopolymers, platform error profiles, contamination, and RNA.
6. Report precision, recall, false-correction rate, and abstention rate by
   platform and context. A correction candidate must be reviewable and
   reproducible before it can be promoted.

## Acceptance gates

- No source is acquired without a pinned release/accession and checksum.
- Controlled or non-redistributable sources remain metadata-only until the
  user supplies lawful access and accepts the provider terms.
- Reports preserve observed data and expose evidence, uncertainty, and next
  actions; they do not make clinical claims or silently edit sequences.
- Registry, anomaly, correction, and report behavior is covered by tests.
