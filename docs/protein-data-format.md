# Genopedia protein data format

Genopedia now has a provenance-first, normalized contract for protein and genomics records. The contract is designed for research data integration, release snapshots, deterministic local processing, and later export to columnar or relational systems.

`NOT_FOR_CLINICAL_USE` and `NOT_FOR_SYNTHESIS_OR_WET_LAB_USE` are part of the contract. A sequence, predicted structure, or model score is not evidence that a protein is functional, safe, buildable, or capable of recreating an organism-level trait.

## Design decision

The workbook has a reader-facing `Protein Planner` view, but the implementation does not store all biology in one wide protein row. The canonical format uses one JSONL table per entity type, connected by stable IDs and explicit relations.

| Layer | What it records | Why it is separate |
|---|---|---|
| Identity | Taxa, contexts, assemblies, loci, transcripts, proteins | Prevents source claims from overwriting identity |
| Sequence | Deduplicated DNA, RNA, CDS, and protein bytes by SHA-256 | Prevents repeated payloads while preserving typed usage |
| Translation | Genetic code, strand, orientation, frame, recoding, and derivation | Makes CDS-to-protein conversion reproducible |
| Structure | Experimental or predicted model, coverage, coordinates, confidence, PAE | Prevents predictions from being stored as observations |
| Function | Domains, motifs, pathways, interactions, and phenotype associations | Preserves biological scale and evidence boundaries |
| Evidence | Sources, assays, claims, support, contradiction, and context | Makes assertions auditable |
| Design | Objective, constraints, parents, model/version, seed, uncertainty | Records hypotheses without claiming biological success |
| Indexes | Partition, sort, k-mer, ANN, graph, or Jev manifests | Derived artifacts can be rebuilt from an immutable release |

The two delegated architecture reviews agreed that source-scoped assertions must remain distinct from canonical entities, that releases must be immutable, and that a content hash identifies bytes rather than biological meaning.

## Protein lifecycle represented by the schema

The safe computational lifecycle is:

1. Define the biological question and its scale. A molecular function is different from a cell, tissue, organ, or organism phenotype.
2. Resolve organism, strain, sample, tissue, cell type, developmental stage, and environment in `organism_context`.
3. Resolve assembly, replicon, locus, transcript, transcript segments, and CDS against a versioned release.
4. Record the ribosomal translation context separately from the protein. Include genetic code, orientation, reading frame, start/stop policy, and recoding rules.
5. Link the translation event to input and output sequence records and the provenance activity that produced them.
6. Attach protein names, isoforms, sequence records, structures, domains, motifs, interactions, pathways, and phenotype associations as separate records or evidence-backed assertions.
7. Keep assay observations, curated annotations, comparative evidence, text-mined associations, and model predictions in different evidence classes.
8. For an in-silico design hypothesis, record the desired measurable protein-level objective, parent sequences, constraints, exclusions, model version, input release, seed, output digest, uncertainty, and review state.
9. Rank or search candidates using deterministic indexes first. Add optional semantic ranking only as a derived, auditable view.
10. Publish an immutable release and rebuild derived indexes from its checksum.

This supports trait decomposition without claiming that a single protein recreates night vision, gills, wings, immunity, or behavior. The allowed causal chain is:

```text
protein → expression/context → complex or interaction → pathway/process
        → cell/tissue/organ context → organism phenotype
```

The validator rejects direct protein-to-phenotype causal claims unless intermediate relations are explicitly supplied.

## Machine-readable contract

The source of truth is `genopedia/schema.py`. Export the JSON Schema with:

```powershell
python -m genopedia schema export --output schema/genopedia_protein_data.schema.json
```

Validate a catalog of JSONL record envelopes with:

```powershell
python -m genopedia schema validate examples/protein_catalog.jsonl
```

Each JSONL line has this envelope:

```json
{
  "entity_type": "protein",
  "schema_version": "1.0.0",
  "data": {
    "id": "protein:P01308-1"
  }
}
```

Sequence payloads are referenced by `content_uri` and `sequence_sha256`. A sequence may have multiple `sequence_usage` records, such as a curated protein product, an AlphaFold input, and a design parent. Those roles must not be conflated.

## Workbook layout

The workbook is a working data dictionary and planning interface, not the canonical database.

| Tab | Purpose |
|---|---|
| `Protein Planner` | Requested wide view ordered from protein name/build through chromosome, RNA/CDS, translation, structure, function, dependencies, evidence, and review |
| `Entity Dictionary` | Normalized entity tables and their purpose |
| `Field Dictionary` | Field name, type, requiredness, and definition |
| `Relationships` | Allowed typed links and evidence expectations |
| `Controlled Terms` | Stable vocabularies and prohibited overclaims |
| `Source Registry` | Authoritative source, release, role, and URL |
| `Index and JEV` | Deterministic index rules plus optional semantic ranking contract |
| `Example Records` | One filled example row per major lifecycle stage |
| `Validation Rules` | Fail-closed checks for IDs, digests, translation, provenance, and causal claims |

## Indexing policy

Partition and sort before building specialized indexes. The canonical order is deterministic and includes null ordering, comparator, tie-breaker, input release, and build ID. The implementation currently supports deterministic JSONL ordering and derived index manifests.

K-mer/minimizer search, ANN, CSR/CSC, and Iceberg/Parquet exports are intentionally deferred until a real workload and release scale justify them. Their parameter choices must be recorded in `derived_index_manifest`.

Jev is optional. The current PostgreSQL extension can score or classify rows using a natural-language condition, but its documentation says it streams rows and requires no index. Genopedia therefore treats Jev as a provider/model-dependent semantic ranking layer with a deterministic fallback, not as the primary biological index. See [`docs/jev-integration.sql`](jev-integration.sql).

## Source roles

RefSeq provides linked genomic, transcript, and protein reference sequences.[^1] Ensembl’s lookup endpoint resolves stable gene, transcript, and protein IDs and can expand connected features.[^2] UniProtKB is the protein identity and annotation source of record for many protein records.[^3] RCSB PDB exposes structure data and search APIs, including polymer entities and chains.[^4] Gene Ontology separates molecular function, cellular component, and biological process.[^5] Reactome provides curated pathway knowledge and analysis services.[^6] InterPro supplies protein family, domain, and functional-site annotations.[^7] AlphaFold DB is a structure-model source and its records must retain model and confidence provenance.[^8]

[^1]: https://www.ncbi.nlm.nih.gov/refseq/about/ "NCBI RefSeq overview"
[^2]: https://rest.ensembl.org/documentation/info/lookup "Ensembl REST lookup endpoint"
[^3]: https://www.uniprot.org/help/uniprotkb "UniProtKB help"
[^4]: https://www.rcsb.org/docs/programmatic-access/web-apis-overview "RCSB PDB Web APIs overview"
[^5]: https://geneontology.org/docs/ontology-documentation/ "Gene Ontology documentation"
[^6]: https://reactome.org/ "Reactome pathway database"
[^7]: https://www.ebi.ac.uk/interpro/ "InterPro"
[^8]: https://alphafold.ebi.ac.uk/faq "AlphaFold Protein Structure Database FAQ"
