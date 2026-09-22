-- Genopedia / RefSeq Release 237 Jev execution plan
-- Release date: 2026-09-04; expected proteins: 495,290,394
-- Plan: plan:refseq237-jev-7da34fb470b85e7bba6da13f
--
-- IMPORTANT: This script does not install PostgreSQL or create an API key.
-- It must be reviewed before execution because Jev sends selected row metadata
-- to its provider. It is deliberately capped at 100,000 rows per statement.
-- Increase that cap only after validating counts, cost, and data-sharing scope.

\set ON_ERROR_STOP on
CREATE EXTENSION IF NOT EXISTS jev CASCADE;
SET jev.batch_size = 20;
SET jev.concurrency = 16;
SET jev.max_rows_per_statement = 100000;
SET jev.max_chars_per_statement = 0;
SET jev.notices = 'on';

CREATE SCHEMA IF NOT EXISTS refseq237_jev;

CREATE TABLE IF NOT EXISTS refseq237_jev.run_manifest (
    plan_id text PRIMARY KEY,
    release_number integer NOT NULL,
    release_date date NOT NULL,
    expected_protein_records bigint NOT NULL,
    observed_protein_records bigint,
    semantic_query text NOT NULL,
    jev_version text,
    jev_model text,
    started_at timestamptz,
    completed_at timestamptz,
    status text NOT NULL,
    notes text
);

INSERT INTO refseq237_jev.run_manifest (
    plan_id, release_number, release_date, expected_protein_records,
    semantic_query, jev_version, jev_model, status, notes
)
VALUES (
    'plan:refseq237-jev-7da34fb470b85e7bba6da13f', 237, DATE '2026-09-04', 495290394,
    'relevance to a specified molecular function or protein-of-interest workflow', jev_version(), current_setting('jev.model', true),
    'staged', 'Jev outputs are derived semantic signals; deterministic source joins remain authoritative.'
)
ON CONFLICT (plan_id) DO UPDATE SET
    jev_version = EXCLUDED.jev_version,
    jev_model = EXCLUDED.jev_model,
    status = EXCLUDED.status;

-- Required staging contract. Populate this table from a checksum-verified
-- RefSeq Release 237 parser before running any Jev operation. Do not put raw
-- protein sequences in the semantic view unless a separate review approves it.
CREATE TABLE IF NOT EXISTS refseq237_jev.protein_catalog (
    protein_id text PRIMARY KEY,
    protein_name text,
    product_description text,
    refseq_accession text,
    organism_taxid bigint,
    organism_name text,
    source_division text,
    assembly_id text,
    replicon text,
    gene_id text,
    transcript_id text,
    sequence_sha256 text,
    sequence_length integer,
    release_number integer NOT NULL,
    release_date date NOT NULL,
    source_file text NOT NULL,
    source_row_number bigint,
    source_sha256 text NOT NULL
);

CREATE INDEX IF NOT EXISTS protein_catalog_release_idx
    ON refseq237_jev.protein_catalog (release_number, source_division, organism_taxid, protein_id);
CREATE INDEX IF NOT EXISTS protein_catalog_sequence_idx
    ON refseq237_jev.protein_catalog (sequence_sha256);

-- Fail closed if the staged release is not the reported release.
DO $$
DECLARE observed bigint;
BEGIN
    SELECT count(*) INTO observed
    FROM refseq237_jev.protein_catalog
    WHERE release_number = 237;
    UPDATE refseq237_jev.run_manifest
    SET observed_protein_records = observed
    WHERE plan_id = 'plan:refseq237-jev-7da34fb470b85e7bba6da13f';
    IF observed <> 495290394 THEN
        RAISE EXCEPTION 'RefSeq release 237 count mismatch: observed %, expected 495290394', observed;
    END IF;
END $$;

-- Narrow metadata view: Jev sees only fields needed for semantic judgment.
CREATE OR REPLACE VIEW refseq237_jev.protein_semantic_context AS
SELECT
    protein_id,
    protein_name,
    product_description,
    refseq_accession,
    organism_taxid,
    organism_name,
    source_division,
    assembly_id,
    replicon,
    gene_id,
    transcript_id,
    sequence_length,
    release_number,
    release_date
FROM refseq237_jev.protein_catalog
WHERE release_number = 237;

-- Deterministic source map: this is authoritative for origin/coordinate joins.
CREATE OR REPLACE VIEW refseq237_jev.protein_source_map AS
SELECT protein_id, refseq_accession, organism_taxid, organism_name,
       assembly_id, replicon, gene_id, transcript_id, source_division,
       release_number, release_date
FROM refseq237_jev.protein_catalog
WHERE release_number = 237
ORDER BY source_division, organism_taxid, protein_id;

-- Deterministic row-cap partitions. Every Jev statement below consumes one
-- range, keeping the provider transfer under jev.max_rows_per_statement.
CREATE TABLE IF NOT EXISTS refseq237_jev.jev_batch_ranges (
    plan_id text NOT NULL,
    batch_id bigint NOT NULL,
    lower_protein_id text NOT NULL,
    upper_protein_id text NOT NULL,
    row_count bigint NOT NULL,
    PRIMARY KEY (plan_id, batch_id)
);
DELETE FROM refseq237_jev.jev_batch_ranges WHERE plan_id = 'plan:refseq237-jev-7da34fb470b85e7bba6da13f';
INSERT INTO refseq237_jev.jev_batch_ranges (
    plan_id, batch_id, lower_protein_id, upper_protein_id, row_count
)
WITH numbered AS (
    SELECT protein_id,
           ((row_number() OVER (ORDER BY protein_id) - 1) / 100000)::bigint AS batch_id
    FROM refseq237_jev.protein_semantic_context
), bounds AS (
    SELECT batch_id, min(protein_id) AS lower_protein_id,
           max(protein_id) AS upper_protein_id, count(*) AS row_count
    FROM numbered
    GROUP BY batch_id
)
SELECT 'plan:refseq237-jev-7da34fb470b85e7bba6da13f', batch_id, lower_protein_id, upper_protein_id, row_count
FROM bounds
ORDER BY batch_id;

CREATE TABLE IF NOT EXISTS refseq237_jev.protein_jev_sort (
    plan_id text NOT NULL,
    protein_id text NOT NULL,
    semantic_score double precision,
    raw_eval jsonb,
    query_text text NOT NULL,
    jev_version text,
    jev_model text,
    retrieved_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (plan_id, protein_id)
);
CREATE TABLE IF NOT EXISTS refseq237_jev.protein_jev_rank (
    plan_id text NOT NULL,
    protein_id text NOT NULL,
    relevance_probability double precision,
    raw_eval jsonb,
    query_text text NOT NULL,
    jev_version text,
    jev_model text,
    retrieved_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (plan_id, protein_id)
);
CREATE TABLE IF NOT EXISTS refseq237_jev.protein_jev_classification (
    plan_id text NOT NULL,
    protein_id text NOT NULL,
    class_label text NOT NULL,
    confidence double precision,
    raw_eval jsonb,
    query_text text NOT NULL,
    jev_version text,
    jev_model text,
    retrieved_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (plan_id, protein_id)
);
CREATE TABLE IF NOT EXISTS refseq237_jev.protein_jev_route (
    plan_id text NOT NULL,
    protein_id text NOT NULL,
    route_label text NOT NULL,
    confidence double precision,
    raw_eval jsonb,
    query_text text NOT NULL,
    jev_version text,
    jev_model text,
    retrieved_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (plan_id, protein_id)
);
CREATE TABLE IF NOT EXISTS refseq237_jev.protein_jev_map (
    plan_id text NOT NULL,
    protein_id text NOT NULL,
    map_label text NOT NULL,
    confidence double precision,
    raw_eval jsonb,
    query_text text NOT NULL,
    jev_version text,
    jev_model text,
    retrieved_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (plan_id, protein_id)
);

-- 1) SORT: a semantic score, then a deterministic ID tie-break.
-- The batch loop keeps each statement under jev.max_rows_per_statement.
DO $jev_sort$
DECLARE b record;
BEGIN
    FOR b IN
        SELECT lower_protein_id, upper_protein_id
        FROM refseq237_jev.jev_batch_ranges
        WHERE plan_id = 'plan:refseq237-jev-7da34fb470b85e7bba6da13f'
        ORDER BY batch_id
    LOOP
        INSERT INTO refseq237_jev.protein_jev_sort (
            plan_id, protein_id, semantic_score, raw_eval, query_text,
            jev_version, jev_model
        )
        SELECT 'plan:refseq237-jev-7da34fb470b85e7bba6da13f', p.protein_id,
               jev_score_norm(p, 'relevance to a specified molecular function or protein-of-interest workflow', ARRAY['irrelevant', 'possible', 'strong']),
               jev_eval(p, 'relevance to a specified molecular function or protein-of-interest workflow', 'score', ARRAY['irrelevant', 'possible', 'strong']),
               'relevance to a specified molecular function or protein-of-interest workflow', jev_version(), current_setting('jev.model', true)
        FROM refseq237_jev.protein_semantic_context AS p
        WHERE p.protein_id >= b.lower_protein_id
          AND p.protein_id <= b.upper_protein_id
        ON CONFLICT (plan_id, protein_id) DO UPDATE SET
            semantic_score = EXCLUDED.semantic_score,
            raw_eval = EXCLUDED.raw_eval,
            jev_version = EXCLUDED.jev_version,
            jev_model = EXCLUDED.jev_model,
            retrieved_at = now();
    END LOOP;
END $jev_sort$;

-- 2) RANK: probability ranking, with exact release and ID tie-breaks.
DO $jev_rank$
DECLARE b record;
BEGIN
    FOR b IN
        SELECT lower_protein_id, upper_protein_id
        FROM refseq237_jev.jev_batch_ranges
        WHERE plan_id = 'plan:refseq237-jev-7da34fb470b85e7bba6da13f'
        ORDER BY batch_id
    LOOP
        INSERT INTO refseq237_jev.protein_jev_rank (
            plan_id, protein_id, relevance_probability, raw_eval, query_text,
            jev_version, jev_model
        )
        SELECT 'plan:refseq237-jev-7da34fb470b85e7bba6da13f', p.protein_id,
               jev_prob(p, 'relevance to a specified molecular function or protein-of-interest workflow'),
               jev_eval(p, 'relevance to a specified molecular function or protein-of-interest workflow', 'probability', ARRAY[]::text[]),
               'relevance to a specified molecular function or protein-of-interest workflow', jev_version(), current_setting('jev.model', true)
        FROM refseq237_jev.protein_semantic_context AS p
        WHERE p.protein_id >= b.lower_protein_id
          AND p.protein_id <= b.upper_protein_id
        ON CONFLICT (plan_id, protein_id) DO UPDATE SET
            relevance_probability = EXCLUDED.relevance_probability,
            raw_eval = EXCLUDED.raw_eval,
            jev_version = EXCLUDED.jev_version,
            jev_model = EXCLUDED.jev_model,
            retrieved_at = now();
    END LOOP;
END $jev_rank$;

-- 3) CLASSIFY: controlled broad classes, not unsupported fine-grained biology.
DO $jev_classify$
DECLARE b record;
BEGIN
    FOR b IN
        SELECT lower_protein_id, upper_protein_id
        FROM refseq237_jev.jev_batch_ranges
        WHERE plan_id = 'plan:refseq237-jev-7da34fb470b85e7bba6da13f'
        ORDER BY batch_id
    LOOP
        INSERT INTO refseq237_jev.protein_jev_classification (
            plan_id, protein_id, class_label, confidence, raw_eval, query_text,
            jev_version, jev_model
        )
        SELECT 'plan:refseq237-jev-7da34fb470b85e7bba6da13f', p.protein_id,
               jev_choice(p, 'which broad protein class best fits the supplied RefSeq name, product description, and context?', ARRAY['enzyme_or_metabolism', 'signaling_or_regulation', 'transport_or_membrane', 'structure_or_scaffold', 'host_pathogen_or_defense', 'nucleic_acid_binding_or_expression', 'unknown_or_insufficient_context']),
               jev_confidence(p, 'which broad protein class best fits the supplied RefSeq name, product description, and context?', 'choice', ARRAY['enzyme_or_metabolism', 'signaling_or_regulation', 'transport_or_membrane', 'structure_or_scaffold', 'host_pathogen_or_defense', 'nucleic_acid_binding_or_expression', 'unknown_or_insufficient_context']),
               jev_eval(p, 'which broad protein class best fits the supplied RefSeq name, product description, and context?', 'choice', ARRAY['enzyme_or_metabolism', 'signaling_or_regulation', 'transport_or_membrane', 'structure_or_scaffold', 'host_pathogen_or_defense', 'nucleic_acid_binding_or_expression', 'unknown_or_insufficient_context']),
               'which broad protein class best fits the supplied RefSeq name, product description, and context?',
               jev_version(), current_setting('jev.model', true)
        FROM refseq237_jev.protein_semantic_context AS p
        WHERE p.protein_id >= b.lower_protein_id
          AND p.protein_id <= b.upper_protein_id
        ON CONFLICT (plan_id, protein_id) DO UPDATE SET
            class_label = EXCLUDED.class_label,
            confidence = EXCLUDED.confidence,
            raw_eval = EXCLUDED.raw_eval,
            jev_version = EXCLUDED.jev_version,
            jev_model = EXCLUDED.jev_model,
            retrieved_at = now();
    END LOOP;
END $jev_classify$;

-- 4) ROUTE: assign a review queue; routing is not a biological conclusion.
DO $jev_route$
DECLARE b record;
BEGIN
    FOR b IN
        SELECT lower_protein_id, upper_protein_id
        FROM refseq237_jev.jev_batch_ranges
        WHERE plan_id = 'plan:refseq237-jev-7da34fb470b85e7bba6da13f'
        ORDER BY batch_id
    LOOP
        INSERT INTO refseq237_jev.protein_jev_route (
            plan_id, protein_id, route_label, confidence, raw_eval, query_text,
            jev_version, jev_model
        )
        SELECT 'plan:refseq237-jev-7da34fb470b85e7bba6da13f', p.protein_id,
               jev_choice(p, 'which review queue should receive this protein record based on its supplied metadata and evidence context?', ARRAY['sequence_structure_review', 'function_annotation_review', 'pathway_process_mapping', 'interaction_evidence_review', 'organism_context_review', 'unknown_or_insufficient_context']),
               jev_confidence(p, 'which review queue should receive this protein record based on its supplied metadata and evidence context?', 'choice', ARRAY['sequence_structure_review', 'function_annotation_review', 'pathway_process_mapping', 'interaction_evidence_review', 'organism_context_review', 'unknown_or_insufficient_context']),
               jev_eval(p, 'which review queue should receive this protein record based on its supplied metadata and evidence context?', 'choice', ARRAY['sequence_structure_review', 'function_annotation_review', 'pathway_process_mapping', 'interaction_evidence_review', 'organism_context_review', 'unknown_or_insufficient_context']),
               'which review queue should receive this protein record based on its supplied metadata and evidence context?',
               jev_version(), current_setting('jev.model', true)
        FROM refseq237_jev.protein_semantic_context AS p
        WHERE p.protein_id >= b.lower_protein_id
          AND p.protein_id <= b.upper_protein_id
        ON CONFLICT (plan_id, protein_id) DO UPDATE SET
            route_label = EXCLUDED.route_label,
            confidence = EXCLUDED.confidence,
            raw_eval = EXCLUDED.raw_eval,
            jev_version = EXCLUDED.jev_version,
            jev_model = EXCLUDED.jev_model,
            retrieved_at = now();
    END LOOP;
END $jev_route$;

-- 5) MAP: map to a broad biological map while retaining deterministic source IDs.
DO $jev_map$
DECLARE b record;
BEGIN
    FOR b IN
        SELECT lower_protein_id, upper_protein_id
        FROM refseq237_jev.jev_batch_ranges
        WHERE plan_id = 'plan:refseq237-jev-7da34fb470b85e7bba6da13f'
        ORDER BY batch_id
    LOOP
        INSERT INTO refseq237_jev.protein_jev_map (
            plan_id, protein_id, map_label, confidence, raw_eval, query_text,
            jev_version, jev_model
        )
        SELECT 'plan:refseq237-jev-7da34fb470b85e7bba6da13f', p.protein_id,
               jev_choice(p, 'which high-level biological map best fits this protein without inferring an unsupported organism trait?', ARRAY['enzyme_or_metabolism', 'signaling_or_regulation', 'transport_or_membrane', 'structure_or_scaffold', 'host_pathogen_or_defense', 'nucleic_acid_binding_or_expression', 'unknown_or_insufficient_context']),
               jev_confidence(p, 'which high-level biological map best fits this protein without inferring an unsupported organism trait?', 'choice', ARRAY['enzyme_or_metabolism', 'signaling_or_regulation', 'transport_or_membrane', 'structure_or_scaffold', 'host_pathogen_or_defense', 'nucleic_acid_binding_or_expression', 'unknown_or_insufficient_context']),
               jev_eval(p, 'which high-level biological map best fits this protein without inferring an unsupported organism trait?', 'choice', ARRAY['enzyme_or_metabolism', 'signaling_or_regulation', 'transport_or_membrane', 'structure_or_scaffold', 'host_pathogen_or_defense', 'nucleic_acid_binding_or_expression', 'unknown_or_insufficient_context']),
               'which high-level biological map best fits this protein without inferring an unsupported organism trait?',
               jev_version(), current_setting('jev.model', true)
        FROM refseq237_jev.protein_semantic_context AS p
        WHERE p.protein_id >= b.lower_protein_id
          AND p.protein_id <= b.upper_protein_id
        ON CONFLICT (plan_id, protein_id) DO UPDATE SET
            map_label = EXCLUDED.map_label,
            confidence = EXCLUDED.confidence,
            raw_eval = EXCLUDED.raw_eval,
            jev_version = EXCLUDED.jev_version,
            jev_model = EXCLUDED.jev_model,
            retrieved_at = now();
    END LOOP;
END $jev_map$;


UPDATE refseq237_jev.run_manifest
SET completed_at = now(), status = 'completed'
WHERE plan_id = 'plan:refseq237-jev-7da34fb470b85e7bba6da13f';

-- Auditable retrieval examples with deterministic ordering:
-- SELECT * FROM refseq237_jev.protein_jev_sort
-- WHERE plan_id = 'plan:refseq237-jev-7da34fb470b85e7bba6da13f'
-- ORDER BY semantic_score DESC NULLS LAST, protein_id
-- LIMIT 1000;
-- SELECT route_label, count(*)
-- FROM refseq237_jev.protein_jev_route
-- WHERE plan_id = 'plan:refseq237-jev-7da34fb470b85e7bba6da13f'
-- GROUP BY route_label ORDER BY route_label;
