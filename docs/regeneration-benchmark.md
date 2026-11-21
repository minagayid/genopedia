# Regeneration benchmark protocol

Status: proposed, not an implemented training pipeline. Version 0.1, 2026-11-21.

Read the [research program](regeneration-research-program.md) first. This protocol defines what a future result would need to demonstrate. It does not report accuracy, trained weights, causal targets, or treatment recommendations.

## First admissible question

Within a single well-described species and anatomical context, can a model distinguish a regeneration-associated state or retrieve independently supported modules after controlling for animal, batch, generic injury, cell composition, and sequence-family leakage?

Choose **one** task below for the first pilot. Do not call a result on one task success on the others.

| Task | Unit of prediction | Baseline | Proposed metrics | Allowed claim |
|---|---|---|---|---|
| Stage/state prediction | Held-out biological sample, or donor-aggregated cell-type sample | Majority class and simple regularized expression model | Macro-F1, per-class recall, confusion matrix, donor-level uncertainty | Discrimination in the evaluated sampling setting |
| Module retrieval | Source-scoped candidate module | Sequence/orthogroup retrieval, expression-only ranking, curated-pathway lookup | Precision@k and recall@k on an independently curated reference set; report unjudged items separately | Recovery of research associations, not true causal discovery |
| Cross-species transfer | Held-out species/study with defensible context mapping | Orthology/pathway baseline | Same task metric, coverage, abstention rate, subgroup performance | Transfer only to the evaluated context |

A literature list is incomplete ground truth. Unannotated genes are not established negatives. Where negative labels are unavailable, describe a positive-unlabeled retrieval task rather than claiming specificity or AUROC against biological negatives.

## Freeze a study manifest before modeling

The literature register is a discovery aid. A usable acquisition manifest must additionally contain:

- source study and raw/processed accession versions;
- exact retrieved asset URLs, retrieval timestamps, license/access terms, and SHA-256 digests;
- assay, genome/transcriptome assembly and annotation release;
- individual animal/donor ID, pooled-sample membership, sample/library ID, batch, and technical replicates;
- organism, developmental stage, tissue, anatomical location, injury/control definition, time and units, and cell-type annotation method;
- missing or ambiguous fields and the decision they block;
- preprocessing tools/versions and parameters, exclusions, mapping loss, and QC decisions;
- sequence/CDS/protein identity links to the existing data contract;
- split assignments, grouping keys, and a manifest checksum.

Never invent accession versions, checksums, donor identities, replicate counts, or missing metadata. Stop the affected task when the record cannot support its intended claim.

### Special case: the sea-star lead

The *Asterias amurensis* report describes pooled nerve-cord material and two sequencing libraries, control versus 72 hours after arm loss. Its organism counts do not establish multiple independent RNA-seq libraries per condition. Until raw metadata establishes otherwise, use this lead for exploratory annotation or retrieval only, not a conventional replicated differential-expression benchmark or a train/validation/test classifier. See [the source report](https://pmc.ncbi.nlm.nih.gov/articles/PMC12236018/).

## Leakage controls

1. Split animals/donors and their related libraries before normalization, feature selection, or fitting. All cells and technical replicates from one biological unit stay together. Pooled material is an inseparable unit; overlapping pool members cannot cross splits.
2. Keep related timepoints from the same individual grouped. A temporal test must also prevent donor leakage and respect the actual sampling design.
3. Fit learned preprocessing and tune hyperparameters on training/validation data only. Freeze all choices before final test evaluation. Document whether any integration or embedding model saw test inputs, even without labels.
4. For sequence tasks, deduplicate exact bytes and audit homologous-family/orthogroup overlap. Use similarity-clustered splits when claiming generalization beyond known families. Report cluster method, thresholds, and the performance/coverage tradeoff.
5. Use a separate leave-one-study-out evaluation for batch generalization. Species and study can be confounded: leaving out a species is not clean evidence of species transfer if its assay also changes.
6. Audit pretraining overlap for any NCBI-derived checkpoint. If its corpus cannot be reconstructed, mark contamination risk unknown and avoid a clean unseen-sequence claim.
7. Keep labels used for evaluation independent of model inputs. A pathway annotation supplied as a feature cannot simultaneously be treated as a newly discovered test label.
8. Prevent reference-label leakage through names, descriptions, identifiers, or literature text. Evaluate an ablation with those fields removed.

Sequence similarity, study, tissue, and injury labels can all be shortcuts. Report the shortcut audits alongside performance, not only in an appendix.

## Biological controls and ablations

- Compare against appropriate uninjured and generic injury/wound-healing controls where available. If no such control exists, do not claim regeneration specificity.
- Separate bulk compositional changes from within-cell-type changes. Treat cells as nested within biological samples, not as thousands of independent animals.
- Compare expression only, sequence only, context only, and combined representations. Preserve the same split and evaluation budget.
- Compare one-to-one ortholog restriction against broader orthogroup mapping; quantify excluded genes, ambiguous matches, and many-to-many relationships.
- Preserve supported developmental and anatomical differences. Do not equate time after injury across species solely by clock time or force unrelated cell types into a shared label.
- Run grouped label-permutation controls where the study design permits. Record the permutation unit and do not break donor/batch constraints.

## Model and result record

Every run should publish an immutable research record containing:

| Item | Required content |
|---|---|
| Inputs | Study, preprocessing, split, and label-manifest digests |
| Model | Architecture/task, checkpoint and tokenizer versions/digests, initialization, trainable components |
| Training | Seed, hyperparameters, environment/dependency lock, source commit, compute usage |
| Outputs | All task metrics, per-study/species/cell-context slices, coverage and abstentions |
| Uncertainty | Donor-level resampling or justified alternative; number of independent units |
| Evidence | Supporting and contradictory observations, and whether labels were independently curated |
| Limitations | Missing contexts, family/batch shortcuts, pretraining contamination uncertainty, failed replications |

Do not manufacture confidence intervals when independent biological units are too few. Report that limitation and the raw unit-level results instead. Do not select a single favorable seed without disclosing the others.

## Proposed go/no-go gates

- **G0, acquisition:** provenance, terms, assets, metadata, and biological replication are sufficient for the chosen task. Otherwise restrict to exploratory work.
- **G1, baseline:** a reproducible simple baseline runs from the frozen manifest. Publish it even if no complex model is trained.
- **G2, modeling:** a combined representation improves a preregistered primary metric over the strongest baseline under identical splits; uncertainty and failure analysis support the interpretation. Choose the practical effect threshold before seeing test results.
- **G3, replication:** performance and evidence direction survive an independent study/context where the task remains valid. Otherwise report a study-specific finding.
- **G4, interpretation:** a domain reviewer checks evidence cards, contradictions, biological context, and abstentions. No score is promoted automatically to a causal statement.

Passing G4 still establishes neither experimental regeneration nor clinical safety/effectiveness. Those are outside this benchmark.

## Deliverables for the first pilot

1. Audited study/sample and asset manifests, with no sensitive participant data committed.
2. Reproducible preprocessing and baseline command, environment lock, and split audit.
3. Held-out result table with honest unit counts and uncertainty.
4. A small set of source-linked evidence cards, including negative or inconclusive findings.
5. A model/data card stating what the model was trained to do and what it must not be used for.

These are planned deliverables. They should only be marked complete when their artifacts and results actually exist.
