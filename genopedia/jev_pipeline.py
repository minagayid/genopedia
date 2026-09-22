"""Jev planning and SQL generation for very large RefSeq protein releases.

This module deliberately does not call Jev itself. Jev runs inside PostgreSQL,
uses an external API, and needs a staged RefSeq release plus an operator-supplied
API key. The planner produces an auditable, spend-aware execution contract and
SQL that can be reviewed before any third-party row transfer occurs.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import date
from math import ceil
from pathlib import Path
from typing import Any, Iterable, Mapping


REFSEQ_RELEASE_237: dict[str, Any] = {
    "source_name": "NCBI RefSeq",
    "release_number": 237,
    "release_date": "2026-09-04",
    "data_as_of": "2026-08-31",
    "expected_protein_records": 495_290_394,
    "expected_transcript_records": 86_067_871,
    "expected_organisms": 184_752,
    "source_uri": "https://ftp.ncbi.nlm.nih.gov/refseq/release/",
    "announcement_uri": "https://www.ncbi.nlm.nih.gov/refseq/",
}

DEFAULT_ROUTE_OPTIONS = (
    "sequence_structure_review",
    "function_annotation_review",
    "pathway_process_mapping",
    "interaction_evidence_review",
    "organism_context_review",
    "unknown_or_insufficient_context",
)

DEFAULT_MAP_OPTIONS = (
    "enzyme_or_metabolism",
    "signaling_or_regulation",
    "transport_or_membrane",
    "structure_or_scaffold",
    "host_pathogen_or_defense",
    "nucleic_acid_binding_or_expression",
    "unknown_or_insufficient_context",
)


@dataclass(frozen=True)
class JevOperation:
    name: str
    function: str
    question: str
    options: tuple[str, ...] = ()
    output_table: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "function": self.function,
            "question": self.question,
            "options": list(self.options),
            "output_table": self.output_table,
            "authoritative": False,
            "deterministic_tiebreaker": "protein_id ASC",
        }


JEV_OPERATIONS: tuple[JevOperation, ...] = (
    JevOperation(
        "sort",
        "jev_score_norm",
        "how strongly is this protein relevant to a stated molecular-function query?",
        ("irrelevant", "possible", "strong"),
        "protein_jev_sort",
    ),
    JevOperation(
        "rank",
        "jev_prob",
        "how likely is this protein to be relevant to the stated molecular-function query?",
        (),
        "protein_jev_rank",
    ),
    JevOperation(
        "classify",
        "jev_choice",
        "which broad protein class best fits the supplied RefSeq name, product description, and context?",
        DEFAULT_MAP_OPTIONS,
        "protein_jev_classification",
    ),
    JevOperation(
        "route",
        "jev_choice",
        "which review queue should receive this protein record based on its supplied metadata and evidence context?",
        DEFAULT_ROUTE_OPTIONS,
        "protein_jev_route",
    ),
    JevOperation(
        "map",
        "jev_choice",
        "which high-level biological map best fits this protein without inferring an unsupported organism trait?",
        DEFAULT_MAP_OPTIONS,
        "protein_jev_map",
    ),
)


def _validate_inputs(
    *,
    release_number: int,
    expected_protein_records: int,
    release_date: str,
    batch_size: int,
    max_rows_per_statement: int,
) -> None:
    if release_number != REFSEQ_RELEASE_237["release_number"]:
        raise ValueError("this planner is pinned to RefSeq Release 237")
    if expected_protein_records < 1:
        raise ValueError("expected_protein_records must be positive")
    try:
        date.fromisoformat(release_date)
    except ValueError as error:
        raise ValueError("release_date must be ISO YYYY-MM-DD") from error
    if batch_size < 1 or batch_size > 20:
        raise ValueError("Jev batch_size must be between 1 and 20 for the documented accuracy envelope")
    if max_rows_per_statement < 1:
        raise ValueError("max_rows_per_statement must be positive")


def build_refseq237_jev_plan(
    *,
    semantic_query: str,
    release_number: int = 237,
    expected_protein_records: int = REFSEQ_RELEASE_237["expected_protein_records"],
    release_date: str = REFSEQ_RELEASE_237["release_date"],
    batch_size: int = 20,
    max_rows_per_statement: int = 100_000,
    source_table: str = "refseq237.protein_catalog",
    full_release_scan: bool = False,
) -> dict[str, Any]:
    """Build a reviewed execution plan without contacting Jev."""

    _validate_inputs(
        release_number=release_number,
        expected_protein_records=expected_protein_records,
        release_date=release_date,
        batch_size=batch_size,
        max_rows_per_statement=max_rows_per_statement,
    )
    if not semantic_query.strip():
        raise ValueError("semantic_query must not be empty")
    request_count = ceil(expected_protein_records / batch_size)
    operation_request_count = request_count * len(JEV_OPERATIONS)
    statement_count = ceil(expected_protein_records / max_rows_per_statement)
    plan_core = {
        "source_table": source_table,
        "release_number": release_number,
        "release_date": release_date,
        "semantic_query": semantic_query,
        "batch_size": batch_size,
        "max_rows_per_statement": max_rows_per_statement,
        "operations": [operation.name for operation in JEV_OPERATIONS],
    }
    plan_hash = hashlib.sha256(
        json.dumps(plan_core, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()[:24]
    return {
        "plan_id": f"plan:refseq237-jev-{plan_hash}",
        "status": "planned_not_executed",
        "source": {
            **REFSEQ_RELEASE_237,
            "release_number": release_number,
            "release_date": release_date,
            "expected_protein_records": expected_protein_records,
        },
        "source_table": source_table,
        "semantic_query": semantic_query,
        "full_release_scan_requested": full_release_scan,
        "third_party_transfer": {
            "required": True,
            "approval_required": True,
            "api_key_source": "TYPESAFE_API_KEY or session setting; never stored in this plan",
            "data_minimization": "Jev view excludes raw protein sequence and sends metadata needed by the question",
        },
        "execution": {
            "postgresql_versions": [14, 15, 16, 17],
            "jev_version": "0.2.0 or pinned compatible release",
            "batch_size": batch_size,
            "concurrency": 16,
            "max_rows_per_statement": max_rows_per_statement,
            "estimated_requests_per_operation": request_count,
            "estimated_requests_all_operations": operation_request_count,
            "estimated_statements_per_operation": statement_count,
            "requires_deterministic_prepartition": True,
            "requires_capped_partition_loop": True,
            "partition_keys": ["release_number", "source_division", "organism_taxid", "sequence_sha256_prefix"],
            "deterministic_tiebreaker": "protein_id ASC",
        },
        "operations": [operation.to_dict() for operation in JEV_OPERATIONS],
        "required_preconditions": [
            "Release 237 staged and checksum-verified",
            "observed protein row count equals 495,290,394 before a full-release run",
            "PostgreSQL 14-17 with plpython3u and Jev installed",
            "operator has approved sending the selected metadata to the Jev provider",
            "run uses a non-secret query and an explicit spend/row cap",
        ],
        "safety_and_scope": [
            "Jev output is a derived semantic signal, not a canonical biological assertion",
            "Genomic coordinates and organism mappings remain deterministic source joins",
            "Do not infer a protein-to-organism trait causal claim from a Jev label",
            "Persist raw evaluation, model version, query, release, and retrieval time",
        ],
    }


def render_refseq237_jev_sql(plan: Mapping[str, Any]) -> str:
    """Render executable SQL for an already-reviewed plan."""

    source_table = str(plan["source_table"])
    release_number = int(plan["source"]["release_number"])
    expected = int(plan["source"]["expected_protein_records"])
    release_date = str(plan["source"]["release_date"])
    query = str(plan["semantic_query"]).replace("'", "''")
    plan_id = str(plan["plan_id"]).replace("'", "''")
    max_rows = int(plan["execution"]["max_rows_per_statement"])
    batch_size = int(plan["execution"]["batch_size"])
    class_options = ", ".join("'" + value.replace("'", "''") + "'" for value in DEFAULT_MAP_OPTIONS)
    route_options = ", ".join("'" + value.replace("'", "''") + "'" for value in DEFAULT_ROUTE_OPTIONS)
    sort_loop = rf"""-- 1) SORT: a semantic score, then a deterministic ID tie-break.
-- The batch loop keeps each statement under jev.max_rows_per_statement.
DO $jev_sort$
DECLARE b record;
BEGIN
    FOR b IN
        SELECT lower_protein_id, upper_protein_id
        FROM refseq237_jev.jev_batch_ranges
        WHERE plan_id = '{plan_id}'
        ORDER BY batch_id
    LOOP
        INSERT INTO refseq237_jev.protein_jev_sort (
            plan_id, protein_id, semantic_score, raw_eval, query_text,
            jev_version, jev_model
        )
        SELECT '{plan_id}', p.protein_id,
               jev_score_norm(p, '{query}', ARRAY['irrelevant', 'possible', 'strong']),
               jev_eval(p, '{query}', 'score', ARRAY['irrelevant', 'possible', 'strong']),
               '{query}', jev_version(), current_setting('jev.model', true)
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
"""
    rank_loop = rf"""-- 2) RANK: probability ranking, with exact release and ID tie-breaks.
DO $jev_rank$
DECLARE b record;
BEGIN
    FOR b IN
        SELECT lower_protein_id, upper_protein_id
        FROM refseq237_jev.jev_batch_ranges
        WHERE plan_id = '{plan_id}'
        ORDER BY batch_id
    LOOP
        INSERT INTO refseq237_jev.protein_jev_rank (
            plan_id, protein_id, relevance_probability, raw_eval, query_text,
            jev_version, jev_model
        )
        SELECT '{plan_id}', p.protein_id,
               jev_prob(p, '{query}'),
               jev_eval(p, '{query}', 'probability', ARRAY[]::text[]),
               '{query}', jev_version(), current_setting('jev.model', true)
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
"""
    classify_loop = rf"""-- 3) CLASSIFY: controlled broad classes, not unsupported fine-grained biology.
DO $jev_classify$
DECLARE b record;
BEGIN
    FOR b IN
        SELECT lower_protein_id, upper_protein_id
        FROM refseq237_jev.jev_batch_ranges
        WHERE plan_id = '{plan_id}'
        ORDER BY batch_id
    LOOP
        INSERT INTO refseq237_jev.protein_jev_classification (
            plan_id, protein_id, class_label, confidence, raw_eval, query_text,
            jev_version, jev_model
        )
        SELECT '{plan_id}', p.protein_id,
               jev_choice(p, 'which broad protein class best fits the supplied RefSeq name, product description, and context?', ARRAY[{class_options}]),
               jev_confidence(p, 'which broad protein class best fits the supplied RefSeq name, product description, and context?', 'choice', ARRAY[{class_options}]),
               jev_eval(p, 'which broad protein class best fits the supplied RefSeq name, product description, and context?', 'choice', ARRAY[{class_options}]),
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
"""
    route_loop = rf"""-- 4) ROUTE: assign a review queue; routing is not a biological conclusion.
DO $jev_route$
DECLARE b record;
BEGIN
    FOR b IN
        SELECT lower_protein_id, upper_protein_id
        FROM refseq237_jev.jev_batch_ranges
        WHERE plan_id = '{plan_id}'
        ORDER BY batch_id
    LOOP
        INSERT INTO refseq237_jev.protein_jev_route (
            plan_id, protein_id, route_label, confidence, raw_eval, query_text,
            jev_version, jev_model
        )
        SELECT '{plan_id}', p.protein_id,
               jev_choice(p, 'which review queue should receive this protein record based on its supplied metadata and evidence context?', ARRAY[{route_options}]),
               jev_confidence(p, 'which review queue should receive this protein record based on its supplied metadata and evidence context?', 'choice', ARRAY[{route_options}]),
               jev_eval(p, 'which review queue should receive this protein record based on its supplied metadata and evidence context?', 'choice', ARRAY[{route_options}]),
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
"""
    map_loop = rf"""-- 5) MAP: map to a broad biological map while retaining deterministic source IDs.
DO $jev_map$
DECLARE b record;
BEGIN
    FOR b IN
        SELECT lower_protein_id, upper_protein_id
        FROM refseq237_jev.jev_batch_ranges
        WHERE plan_id = '{plan_id}'
        ORDER BY batch_id
    LOOP
        INSERT INTO refseq237_jev.protein_jev_map (
            plan_id, protein_id, map_label, confidence, raw_eval, query_text,
            jev_version, jev_model
        )
        SELECT '{plan_id}', p.protein_id,
               jev_choice(p, 'which high-level biological map best fits this protein without inferring an unsupported organism trait?', ARRAY[{class_options}]),
               jev_confidence(p, 'which high-level biological map best fits this protein without inferring an unsupported organism trait?', 'choice', ARRAY[{class_options}]),
               jev_eval(p, 'which high-level biological map best fits this protein without inferring an unsupported organism trait?', 'choice', ARRAY[{class_options}]),
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
"""
    return rf"""-- Genopedia / RefSeq Release {release_number} Jev execution plan
-- Release date: {release_date}; expected proteins: {expected:,}
-- Plan: {plan_id}
--
-- IMPORTANT: This script does not install PostgreSQL or create an API key.
-- It must be reviewed before execution because Jev sends selected row metadata
-- to its provider. It is deliberately capped at {max_rows:,} rows per statement.
-- Increase that cap only after validating counts, cost, and data-sharing scope.

\set ON_ERROR_STOP on
CREATE EXTENSION IF NOT EXISTS jev CASCADE;
SET jev.batch_size = {batch_size};
SET jev.concurrency = 16;
SET jev.max_rows_per_statement = {max_rows};
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
    '{plan_id}', {release_number}, DATE '{release_date}', {expected},
    '{query}', jev_version(), current_setting('jev.model', true),
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
    WHERE release_number = {release_number};
    UPDATE refseq237_jev.run_manifest
    SET observed_protein_records = observed
    WHERE plan_id = '{plan_id}';
    IF observed <> {expected} THEN
        RAISE EXCEPTION 'RefSeq release {release_number} count mismatch: observed %, expected {expected}', observed;
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
WHERE release_number = {release_number};

-- Deterministic source map: this is authoritative for origin/coordinate joins.
CREATE OR REPLACE VIEW refseq237_jev.protein_source_map AS
SELECT protein_id, refseq_accession, organism_taxid, organism_name,
       assembly_id, replicon, gene_id, transcript_id, source_division,
       release_number, release_date
FROM refseq237_jev.protein_catalog
WHERE release_number = {release_number}
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
DELETE FROM refseq237_jev.jev_batch_ranges WHERE plan_id = '{plan_id}';
INSERT INTO refseq237_jev.jev_batch_ranges (
    plan_id, batch_id, lower_protein_id, upper_protein_id, row_count
)
WITH numbered AS (
    SELECT protein_id,
           ((row_number() OVER (ORDER BY protein_id) - 1) / {max_rows})::bigint AS batch_id
    FROM refseq237_jev.protein_semantic_context
), bounds AS (
    SELECT batch_id, min(protein_id) AS lower_protein_id,
           max(protein_id) AS upper_protein_id, count(*) AS row_count
    FROM numbered
    GROUP BY batch_id
)
SELECT '{plan_id}', batch_id, lower_protein_id, upper_protein_id, row_count
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

{sort_loop}
{rank_loop}
{classify_loop}
{route_loop}
{map_loop}

UPDATE refseq237_jev.run_manifest
SET completed_at = now(), status = 'completed'
WHERE plan_id = '{plan_id}';

-- Auditable retrieval examples with deterministic ordering:
-- SELECT * FROM refseq237_jev.protein_jev_sort
-- WHERE plan_id = '{plan_id}'
-- ORDER BY semantic_score DESC NULLS LAST, protein_id
-- LIMIT 1000;
-- SELECT route_label, count(*)
-- FROM refseq237_jev.protein_jev_route
-- WHERE plan_id = '{plan_id}'
-- GROUP BY route_label ORDER BY route_label;
"""


def write_jev_plan(
    output: str | Path,
    *,
    semantic_query: str,
    sql_output: str | Path | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Write a JSON plan and optionally its SQL companion."""

    plan = build_refseq237_jev_plan(semantic_query=semantic_query, **kwargs)
    target = Path(output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if sql_output is not None:
        sql_target = Path(sql_output)
        sql_target.parent.mkdir(parents=True, exist_ok=True)
        sql_target.write_text(render_refseq237_jev_sql(plan), encoding="utf-8")
    return plan
