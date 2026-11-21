# Comparative regeneration research program

Research proposal, last reviewed 2026-11-21. This is a computational research agenda, not a treatment, a validated regeneration model, or a laboratory protocol.

## Question and working hypothesis

Can linked protein/transcript sequence representations, combined with tissue-, cell-type-, and stage-specific expression evidence, help identify conserved regeneration-associated programs across sea stars, salamanders, and lizards?

**Hypothesis, not an established result:** context-aware representations will retrieve independently supported regeneration-associated modules better than sequence similarity or generic wound-response annotations alone. A positive result would support a comparative discovery tool. It would not establish that those modules can regenerate human tissue.

The long-term motivation includes nephron repair/replacement, insulin-producing beta-cell restoration, neural repair, and functional limb regeneration. These are four different biological and translational problems, not four applications of a demonstrated universal regeneration switch.

## Why a protein catalog is necessary but insufficient

RefSeq links genomic DNA, transcripts, and proteins [1]. That makes a useful identity and provenance backbone, but it does not provide the complete tissue-level dynamics of regeneration. A model trained on reference sequences alone has not learned a causal regeneration program merely because it recognizes proteins.

Keep these layers separate:

```text
versioned DNA locus -> transcript isoform -> annotated CDS -> protein isoform
                                      |
             sample / cell type / tissue / time / injury context
                                      |
         expression and regulatory evidence -> candidate module
                                      |
          comparative hypothesis -> independent validation
```

- A protein sequence does not uniquely determine its encoding RNA sequence. Preserve the source transcript, coding coordinates, genetic code, and translation provenance instead of inventing an RNA partner by reverse translation.
- A transcript is not necessarily protein-coding. Record noncoding RNAs separately; do not force every RNA into a protein pair.
- RNA abundance is not a direct measurement of protein abundance, activity, localization, or interactions. An inferred network edge is not a measured interaction.
- An ortholog is a comparative relationship, not proof of interchangeable function or compatible regulation in humans.
- A pathway enrichment or a model ranking is an association, not a demonstration of necessity, sufficiency, safety, or therapeutic efficacy.

The existing [protein data contract](protein-data-format.md) already separates these identities, assertions, predictions, and provenance. Use it rather than introducing a competing flat table.

## Comparative evidence map

| Model and source | What the study supports | Boundary for Genopedia |
|---|---|---|
| Axolotl, *Ambystoma mexicanum*, limb single-cell atlas [2] | Distinct epidermal, mesenchymal, and immune populations across homeostasis and early regeneration | A blastema is a changing multicellular system, not a single protein or generic stem-cell state. Cells from one animal are not independent animal replicates. |
| Green anole, *Anolis carolinensis*, tail single-cell study [3] | Fibroblast/phagocyte programs associated with cartilage formation; experimental evidence in that model | A regenerated lizard tail is not an exact copy of the original and is not a regenerated limb. Do not relabel tail chondrogenesis as human limb restoration. |
| Sea star, *Asterias amurensis*, nerve-cord transcriptome [4] | An actual sea-star entry point with control versus 72-hour post-arm-loss observations | Tissue and time coverage are narrow. The study reports pooled material and two RNA-seq libraries; six animals do not become six independent RNA-seq replicates. Treat differential-expression findings as exploratory until independent replication. |
| Brittle star, *Amphiura filiformis*, genome and arm-regeneration time course [5] | Comparative expression dynamics spanning wound healing, proliferation, and differentiation | Brittle stars are Ophiuroidea, not sea stars/Asteroidea. Keep them as an additional echinoderm comparison, not a substitute mislabeled as starfish. |
| Echinoderm molecular review [6] | Broader evidence and differences among echinoderm taxa and regenerative processes | Literature coverage is uneven. No selected dataset measures the full regeneration ecosystem. Adult and larval regeneration must not be merged without explicit context. |

These are literature leads, not an assertion that raw data, consent/usage terms, checksums, or sample sheets have already been audited or imported. The [study register](regeneration-study-register.json) records this distinction.

## Staged computational program

### 1. Freeze the sequence backbone

Use release-pinned reference records and explicit transcript/CDS/protein links. Preserve accession versions, assembly, source status, sequence digests, software versions, and licensing/access terms. Flag predicted annotations and ambiguous mappings.

An externally trained NCBI-derived model is a **candidate backbone**, not a verified dependency of this checkout. Before use, require its actual dataset manifest, training task, checkpoint URI and digest, tokenizer, configuration, held-out results, and model card. Do not infer its architecture or success from a queued/completed training job. No new regeneration-training results are claimed here.

### 2. Curate a small context-rich pilot

Start with the axolotl limb atlas as a within-species pilot and one independent study for replication if compatible data exist. Add anole and echinoderm studies only after sample metadata and mapping quality pass review.

Capture injury versus uninjured or appropriate wound controls, anatomical position, developmental stage, sampling time, biological animal/donor, pooled samples, assay, batch, and cell-type annotation uncertainty. If a key field is absent, record it as unknown and downgrade the task rather than guessing. For bulk data, cell-composition changes can masquerade as within-cell regulation.

### 3. Establish transparent baselines

Compare sequence similarity/orthogroup retrieval and simple expression-based models before combining sequence embeddings with expression, pathway, and cell-context features. Treat cross-species alignment as a testable modeling choice. Do not combine raw expression values from unrelated technologies as though they were directly comparable.

Use the [benchmark protocol](regeneration-benchmark.md) to freeze targets, splits, baselines, and failure criteria before training. Include generic injury, inflammation, and proliferation controls so that a model cannot succeed merely by detecting damaged tissue.

### 4. Produce evidence cards, not interventions

The intended output is a ranked **module hypothesis** with supporting and contradicting sources, organism/tissue/stage, evidence class, orthology uncertainty, model version, and an abstention reason when support is weak. An expression association and a perturbation result in another species must remain separately labeled.

A useful first success is reproducible retrieval of independently supported modules in held-out research data. A useful negative result is discovering that sequence embeddings add no benefit over the baselines. Publish both.

### 5. Consider translation only through separate expert-led programs

No automatic transition exists from a ranked module to a human intervention. Tissue-specific functional evidence, delivery, dose control, long-term safety, ethics review, and the relevant regulatory pathway would be separate research programs. This repository neither supplies nor executes them.

## Human relevance: four distinct workstreams

| Motivation | Honest research question | Evidence that a sequence-model score cannot supply |
|---|---|---|
| Kidney failure / nephrons | Are context-specific repair or developmental modules informative in an appropriate renal model? | Mature vascularized filtration units and integration into organ architecture. Kidney organoid maturation work illustrates the importance of flow and vasculature, not a demonstrated kidney replacement [7]. |
| Diabetes / beta cells | Which programs associate with functional beta-cell identity in an appropriate pancreatic context? | Regulated insulin release, durable survival, and immune compatibility. Type 1 diabetes includes autoimmune beta-cell destruction; replacing cells alone does not remove that problem [8]. |
| Neural repair | Which programs associate with survival, axon growth, or relevant neural cell states? | Appropriate connections and circuit function. Making more neurons is not equivalent to rebuilding a working circuit [9]. |
| Limb loss | Which temporally and spatially organized multicellular programs are conserved? | Patterned bone/cartilage, muscle, skin, vasculature, innervation, and useful function together. Axolotl limbs and lizard tails provide different evidence [2,3]. |

## Where CRISPR-Cas9 fits, and where it does not

CRISPR-Cas9 is a genome-editing research tool, not a mechanism that automatically transfers a regenerative trait between species. Its possible long-term role here is as one of several expert-selected ways to test a causal hypothesis in an approved research setting, **after** the computational program produces credible evidence.

The repository does not design guide RNAs, choose edit sites, propose donor constructs, provide delivery instructions, or generate a human editing plan. It also does not assume that an animal protein or an RNA sequence should be inserted into human DNA.

Cas9-induced breaks can produce large on-target deletions and complex rearrangements, in addition to concerns about off-target changes [10]. A high prediction score or a short local sequence check cannot rule these out. Translational cell/genome-editing work needs independent scientific and ethical oversight and safety/effectiveness evidence, as emphasized by ISSCR guidance [11].

## Current status and exit gates

- **Implemented already:** local sequence inspection, reporting, reference metadata, protein/transcript provenance contracts, and related software tests. These are software capabilities, not biological validation.
- **Added by this research layer:** a sourced program, literature-lead register, and a preregistration-style benchmark specification.
- **Not implemented or demonstrated:** regeneration-specific data ingestion, a context-aware trained regeneration model, validated cross-species transfer, experimental regeneration, or clinical efficacy.
- **Next gate:** audit one study's sample sheet and downloadable artifacts, freeze an admissible task/split manifest, and establish the simplest baseline. If independent biological replication is unavailable, restrict the claim to exploratory analysis.

## Sources and what they support

Sources were inspected on 2026-11-21. This is a focused starting bibliography, not a systematic review or a claim that these are the newest studies in every area.

1. NCBI, **About RefSeq**, official reference documentation. Linked genomic, transcript, and protein records; varying annotation/curation processes. https://www.ncbi.nlm.nih.gov/refseq/about/
2. Leigh et al. (2018), **Transcriptomic landscape of the blastema niche in regenerating adult axolotl limbs at single-cell resolution**, primary research. https://www.nature.com/articles/s41467-018-07604-0
3. Vonk et al. (2023), **Single-cell analysis of lizard blastema fibroblasts reveals phagocyte-dependent activation of Hedgehog-responsive chondrogenesis**, primary research. https://www.nature.com/articles/s41467-023-40206-z
4. Jo et al. (2025), **De novo assembly of transcriptome during regeneration post-arm amputation in the starfish, Asterias amurensis**, primary data report. Includes BioProject PRJNA1139949 and the study's pooling and coverage limitations. https://pmc.ncbi.nlm.nih.gov/articles/PMC12236018/
5. Parey et al. (2024), **The brittle star genome illuminates the genetic basis of animal appendage regeneration**, primary research. https://www.nature.com/articles/s41559-024-02456-y
6. Medina-Feliciano and Garcia-Arraras (2021), **Regeneration in Echinoderms: Molecular Advancements**, review. https://www.frontiersin.org/journals/cell-and-developmental-biology/articles/10.3389/fcell.2021.768641/full
7. NIDDK (2019), **Streaming fluid across kidney organoids...drives their maturation**, official research summary. https://www.niddk.nih.gov/news/archive/2019/streaming-fluid-across-kidney-organoids-grown-on-chip-drives-maturation
8. NIDDK, **Pancreatic Islet Transplantation**, official clinical background, not evidence for a Genopedia therapy. https://www.niddk.nih.gov/health-information/diabetes/overview/insulin-medicines-treatments/pancreatic-islet-transplantation
9. NINDS (2025 publication), **Spinal Cord Injury**, official research background. https://www.ninds.nih.gov/publications/spinal-cord-injury
10. Kosicki, Tomberg and Bradley (2018), **Repair of double-strand breaks induced by CRISPR-Cas9 leads to large deletions and complex rearrangements**, primary research. https://www.nature.com/articles/nbt.4192
11. ISSCR, **Clinical Translation of Stem Cell-based Interventions**, professional guidance. https://www.isscr.org/guidelines-online/clinical-translation-of-stem-cell-based-interventions
