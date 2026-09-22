"""Provenance-first data contracts for Genopedia protein and genomics records.

The schema deliberately separates canonical entities from source-scoped claims,
predictions, and design hypotheses.  It is a metadata contract, not a wet-lab
protocol or a clinical interpretation system.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any, Mapping


SCHEMA_VERSION = "1.0.0"
SCHEMA_ID = "https://github.com/minagayid/genopedia/schema/genopedia-protein-data-1.0.0.json"
NOT_FOR_CLINICAL_USE = "NOT_FOR_CLINICAL_USE"
NOT_FOR_SYNTHESIS_OR_WET_LAB_USE = "NOT_FOR_SYNTHESIS_OR_WET_LAB_USE"

_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_]*(?::[A-Za-z0-9][A-Za-z0-9._-]*)+$")
_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class FieldSpec:
    name: str
    data_type: str = "string"
    description: str = ""
    required: bool = False
    enum: tuple[str, ...] = ()

    def to_json_schema(self) -> dict[str, Any]:
        type_map = {
            "string": {"type": "string"},
            "integer": {"type": "integer"},
            "number": {"type": "number"},
            "boolean": {"type": "boolean"},
            "array": {"type": "array", "items": {}},
            "object": {"type": "object"},
            "json": {},
        }
        result = dict(type_map[self.data_type])
        if self.description:
            result["description"] = self.description
        if self.enum:
            result["enum"] = list(self.enum)
        return result


@dataclass(frozen=True)
class EntitySpec:
    name: str
    purpose: str
    fields: tuple[FieldSpec, ...]

    @property
    def field_names(self) -> tuple[str, ...]:
        return tuple(field.name for field in self.fields)

    @property
    def required_fields(self) -> tuple[str, ...]:
        return tuple(field.name for field in self.fields if field.required)

    def to_json_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "description": self.purpose,
            "additionalProperties": False,
            "properties": {
                field.name: field.to_json_schema() for field in self.fields
            },
            "required": list(self.required_fields),
        }


def _field(
    name: str,
    data_type: str = "string",
    *,
    required: bool = False,
    description: str = "",
    enum: tuple[str, ...] = (),
) -> FieldSpec:
    return FieldSpec(name, data_type, description, required, enum)


_RECORD_TYPES = ("observed", "reconstructed", "predicted", "designed")
_RELEASE_STATUS = ("active", "deprecated", "superseded", "withdrawn")


ENTITY_SPECS: tuple[EntitySpec, ...] = (
    EntitySpec(
        "dataset_release",
        "Immutable source or project release boundary.",
        (
            _field("id", required=True),
            _field("source_name", required=True),
            _field("source_version", required=True),
            _field("released_at"),
            _field("retrieved_at", required=True),
            _field("source_uri", required=True),
            _field("license"),
            _field("status", required=True, enum=_RELEASE_STATUS),
            _field("supersedes_id"),
        ),
    ),
    EntitySpec(
        "source_record",
        "Source-scoped identifier and retrieval metadata.",
        (
            _field("id", required=True),
            _field("source_name", required=True),
            _field("external_id", required=True),
            _field("external_version"),
            _field("record_uri", required=True),
            _field("record_type", required=True),
            _field("release_id", required=True),
            _field("checksum_sha256"),
        ),
    ),
    EntitySpec(
        "provenance_activity",
        "A reproducible ingestion, transformation, prediction, or indexing step.",
        (
            _field("id", required=True),
            _field("activity_type", required=True),
            _field("software_name", required=True),
            _field("software_version", required=True),
            _field("parameters", "json"),
            _field("input_record_ids", "array"),
            _field("output_record_ids", "array"),
            _field("random_seed", "integer"),
            _field("container_digest"),
            _field("started_at"),
            _field("ended_at"),
        ),
    ),
    EntitySpec(
        "controlled_term",
        "Versioned term from an external vocabulary or ontology.",
        (
            _field("id", required=True),
            _field("vocabulary", required=True),
            _field("accession", required=True),
            _field("label", required=True),
            _field("uri", required=True),
            _field("version"),
            _field("parent_term_id"),
            _field("deprecated", "boolean"),
        ),
    ),
    EntitySpec(
        "taxon",
        "Taxonomic identity used for cross-species comparison.",
        (
            _field("id", required=True),
            _field("scientific_name", required=True),
            _field("rank"),
            _field("ncbi_taxon_id"),
            _field("source_record_id", required=True),
        ),
    ),
    EntitySpec(
        "organism_context",
        "Organism, strain, sample, developmental, tissue, and cell context.",
        (
            _field("id", required=True),
            _field("taxon_id", required=True),
            _field("strain_or_sample"),
            _field("developmental_stage_term_id"),
            _field("tissue_term_id"),
            _field("cell_type_term_id"),
            _field("environment", "json"),
        ),
    ),
    EntitySpec(
        "genome_assembly",
        "Coordinate system and assembly release for genomic features.",
        (
            _field("id", required=True),
            _field("organism_context_id", required=True),
            _field("assembly_accession", required=True),
            _field("assembly_version"),
            _field("coordinate_system", required=True),
            _field("release_id", required=True),
            _field("source_record_id", required=True),
        ),
    ),
    EntitySpec(
        "replicon",
        "Chromosome, plasmid, organelle, or other assembly replicon.",
        (
            _field("id", required=True),
            _field("assembly_id", required=True),
            _field("name", required=True),
            _field("replicon_type", required=True),
            _field("length", "integer", required=True),
            _field("circular", "boolean"),
            _field("sequence_record_id"),
        ),
    ),
    EntitySpec(
        "gene_locus",
        "A gene locus anchored to an explicit assembly and replicon.",
        (
            _field("id", required=True),
            _field("replicon_id", required=True),
            _field("external_id"),
            _field("symbol"),
            _field("start", "integer", required=True),
            _field("end", "integer", required=True),
            _field("strand", required=True),
            _field("feature_type", required=True),
            _field("release_id", required=True),
            _field("source_record_id", required=True),
        ),
    ),
    EntitySpec(
        "transcript",
        "RNA transcript or isoform connected to a gene locus.",
        (
            _field("id", required=True),
            _field("gene_locus_id", required=True),
            _field("external_id"),
            _field("rna_type", required=True),
            _field("sequence_record_id"),
            _field("is_reference", "boolean"),
            _field("release_id", required=True),
            _field("source_record_id", required=True),
        ),
    ),
    EntitySpec(
        "transcript_segment",
        "Exon, UTR, or other reproducible transcript interval.",
        (
            _field("id", required=True),
            _field("transcript_id", required=True),
            _field("ordinal", "integer", required=True),
            _field("segment_type", required=True),
            _field("replicon_id", required=True),
            _field("start", "integer", required=True),
            _field("end", "integer", required=True),
            _field("strand", required=True),
        ),
    ),
    EntitySpec(
        "cds",
        "Coding sequence intervals and completeness metadata.",
        (
            _field("id", required=True),
            _field("transcript_id", required=True),
            _field("start_segment_ordinal", "integer", required=True),
            _field("end_segment_ordinal", "integer", required=True),
            _field("phase", "integer"),
            _field("reading_frame", "integer"),
            _field("complete_5p", "boolean"),
            _field("complete_3p", "boolean"),
            _field("sequence_record_id"),
        ),
    ),
    EntitySpec(
        "translation_context",
        "Ribosomal translation context for a deterministic CDS-to-protein derivation.",
        (
            _field("id", required=True),
            _field("genetic_code_id", required=True),
            _field("strand", required=True),
            _field("orientation", required=True),
            _field("frame", "integer", required=True),
            _field("recoding_rules", "json"),
            _field("start_policy", required=True),
            _field("stop_policy", required=True),
        ),
    ),
    EntitySpec(
        "translation_event",
        "Auditable CDS-to-protein transformation.",
        (
            _field("id", required=True),
            _field("cds_id", required=True),
            _field("translation_context_id", required=True),
            _field("protein_id", required=True),
            _field("input_sequence_id", required=True),
            _field("output_sequence_id", required=True),
            _field("provenance_activity_id", required=True),
            _field("deterministic", "boolean", required=True),
            _field("exact", "boolean", required=True),
        ),
    ),
    EntitySpec(
        "variant_assertion",
        "Release- and context-scoped sequence variant with evidence and effect metadata.",
        (
            _field("id", required=True),
            _field("gene_locus_id"),
            _field("replicon_id"),
            _field("position", "integer", required=True),
            _field("reference", required=True),
            _field("alternate", required=True),
            _field("variant_type", required=True),
            _field("organism_context_id"),
            _field("effect_term_id"),
            _field("evidence_record_id", required=True),
            _field("source_record_id", required=True),
            _field("release_id", required=True),
        ),
    ),
    EntitySpec(
        "protein",
        "Protein product identity without embedding source-specific claims.",
        (
            _field("id", required=True),
            _field("preferred_name", required=True),
            _field("synonyms", "array"),
            _field("gene_locus_id"),
            _field("transcript_id"),
            _field("isoform_label"),
            _field("sequence_record_id", required=True),
            _field("organism_context_id", required=True),
            _field("record_type", required=True, enum=_RECORD_TYPES),
            _field("design_record_id"),
            _field("release_id", required=True),
            _field("source_record_id", required=True),
        ),
    ),
    EntitySpec(
        "sequence_record",
        "Deduplicated sequence bytes plus typed biological usage metadata.",
        (
            _field("id", required=True),
            _field("sequence_type", required=True),
            _field("alphabet", required=True),
            _field("length", "integer", required=True),
            _field("digest_algorithm", required=True),
            _field("sequence_sha256", required=True),
            _field("normalization_version", required=True),
            _field("content_uri", required=True),
            _field("record_type", required=True, enum=_RECORD_TYPES),
            _field("release_id", required=True),
            _field("source_record_id"),
        ),
    ),
    EntitySpec(
        "sequence_usage",
        "Typed link from sequence bytes to the biological object using them.",
        (
            _field("id", required=True),
            _field("sequence_record_id", required=True),
            _field("owner_entity_type", required=True),
            _field("owner_entity_id", required=True),
            _field("usage_type", required=True),
            _field("coordinate_start", "integer"),
            _field("coordinate_end", "integer"),
        ),
    ),
    EntitySpec(
        "structure_model",
        "Experimental or predicted structure with coverage and uncertainty metadata.",
        (
            _field("id", required=True),
            _field("structure_type", required=True),
            _field("structure_accession"),
            _field("sequence_record_id", required=True),
            _field("method", required=True),
            _field("model_name"),
            _field("model_version"),
            _field("coverage_fraction", "number"),
            _field("coordinates_uri", required=True),
            _field("confidence_artifact_uri"),
            _field("pae_artifact_uri"),
            _field("provenance_activity_id", required=True),
            _field("source_record_id"),
        ),
    ),
    EntitySpec(
        "structure_chain",
        "Chain-level mapping between a structure model and a sequence.",
        (
            _field("id", required=True),
            _field("structure_model_id", required=True),
            _field("chain_id", required=True),
            _field("sequence_record_id", required=True),
            _field("residue_start", "integer"),
            _field("residue_end", "integer"),
            _field("mapping_status", required=True),
        ),
    ),
    EntitySpec(
        "domain_motif_annotation",
        "Residue-level domain, motif, or site annotation.",
        (
            _field("id", required=True),
            _field("protein_id", required=True),
            _field("annotation_type", required=True),
            _field("term_id", required=True),
            _field("start", "integer", required=True),
            _field("end", "integer", required=True),
            _field("evidence_record_id", required=True),
            _field("source_record_id", required=True),
            _field("confidence", "number"),
        ),
    ),
    EntitySpec(
        "interaction_assertion",
        "Evidence-backed interaction or complex-participation assertion.",
        (
            _field("id", required=True),
            _field("participant_a_id", required=True),
            _field("participant_b_id", required=True),
            _field("interaction_type", required=True),
            _field("directness", required=True),
            _field("organism_context_id"),
            _field("evidence_record_id", required=True),
            _field("confidence", "number"),
            _field("directionality"),
            _field("negative_assertion", "boolean"),
        ),
    ),
    EntitySpec(
        "pathway_process",
        "Pathway or biological-process term from a versioned source.",
        (
            _field("id", required=True),
            _field("term_id", required=True),
            _field("database", required=True),
            _field("accession", required=True),
            _field("label", required=True),
            _field("source_record_id", required=True),
        ),
    ),
    EntitySpec(
        "phenotype_trait",
        "Phenotype or capability record with explicit biological scale.",
        (
            _field("id", required=True),
            _field("term_id"),
            _field("label", required=True),
            _field("biological_scale", required=True),
            _field("organism_context_id"),
            _field("description"),
            _field("source_record_id", required=True),
        ),
    ),
    EntitySpec(
        "assay_observation",
        "Measured or experimentally observed property with context and controls.",
        (
            _field("id", required=True),
            _field("target_entity_type", required=True),
            _field("target_entity_id", required=True),
            _field("assay_type", required=True),
            _field("measured_property", required=True),
            _field("value_numeric", "number"),
            _field("value_text"),
            _field("unit"),
            _field("replicates", "integer"),
            _field("controls", "json"),
            _field("organism_context_id"),
            _field("evidence_record_id", required=True),
        ),
    ),
    EntitySpec(
        "evidence_record",
        "Evidence and source record for a claim, observation, or annotation.",
        (
            _field("id", required=True),
            _field("evidence_type", required=True),
            _field("source_record_id", required=True),
            _field("publication_id"),
            _field("assay_observation_id"),
            _field("quality_level", required=True),
            _field("supports_claim_id"),
            _field("contradicts_claim_id"),
        ),
    ),
    EntitySpec(
        "model_prediction",
        "Model output kept distinct from observation and curation.",
        (
            _field("id", required=True),
            _field("target_entity_type", required=True),
            _field("target_entity_id", required=True),
            _field("model_name", required=True),
            _field("model_version", required=True),
            _field("task", required=True),
            _field("input_release_id", required=True),
            _field("output", "json", required=True),
            _field("score", "number"),
            _field("uncertainty", "json"),
            _field("calibration_status", required=True),
            _field("provenance_activity_id", required=True),
        ),
    ),
    EntitySpec(
        "design_record",
        "In-silico reconstruction or design hypothesis with explicit limits.",
        (
            _field("id", required=True),
            _field("design_type", required=True, enum=("reconstructed", "predicted", "designed")),
            _field("parent_entity_ids", "array", required=True),
            _field("objective", required=True),
            _field("constraints", "json", required=True),
            _field("exclusions", "json", required=True),
            _field("model_name", required=True),
            _field("model_version", required=True),
            _field("input_release_id", required=True),
            _field("random_seed", "integer"),
            _field("output_sequence_id", required=True),
            _field("review_status", required=True),
            _field("safety_status", required=True),
            _field("provenance_activity_id", required=True),
        ),
    ),
    EntitySpec(
        "claim_assertion",
        "Typed relationship claim that can be supported or contradicted.",
        (
            _field("id", required=True),
            _field("subject_entity_type", required=True),
            _field("subject_entity_id", required=True),
            _field("predicate", required=True),
            _field("object_entity_type", required=True),
            _field("object_entity_id", required=True),
            _field("evidence_record_id", required=True),
            _field("organism_context_id"),
            _field("causal_strength", required=True),
            _field("assertion_status", required=True),
            _field("intermediate_relation_ids", "array"),
        ),
    ),
    EntitySpec(
        "entity_relation",
        "Normalized typed edge between versioned entities, separate from the entities it connects.",
        (
            _field("id", required=True),
            _field("subject_entity_type", required=True),
            _field("subject_entity_id", required=True),
            _field("predicate", required=True),
            _field("object_entity_type", required=True),
            _field("object_entity_id", required=True),
            _field("evidence_record_id"),
            _field("organism_context_id"),
            _field("release_id", required=True),
            _field("provenance_activity_id", required=True),
        ),
    ),
    EntitySpec(
        "safety_uncertainty_review",
        "Research-only review of unknowns, hazards, and scope status.",
        (
            _field("id", required=True),
            _field("target_entity_type", required=True),
            _field("target_entity_id", required=True),
            _field("review_scope", required=True),
            _field("uncertainty_summary", required=True),
            _field("known_unknowns", "array", required=True),
            _field("hazards", "array", required=True),
            _field("status", required=True),
            _field("reviewer"),
            _field("reviewed_at"),
            _field("flags", "array"),
        ),
    ),
    EntitySpec(
        "derived_index_manifest",
        "Deterministic manifest for a derived sort, filter, or search index.",
        (
            _field("id", required=True),
            _field("input_release_id", required=True),
            _field("index_type", required=True),
            _field("partition_key", required=True),
            _field("sort_key", required=True),
            _field("comparator", required=True),
            _field("null_order", required=True),
            _field("index_parameters", "json", required=True),
            _field("build_id", required=True),
            _field("artifact_uri", required=True),
            _field("input_sha256", required=True),
            _field("deterministic", "boolean", required=True),
        ),
    ),
)


ENTITY_SPEC_BY_NAME = {spec.name: spec for spec in ENTITY_SPECS}

CONTROLLED_VOCABULARIES: dict[str, tuple[str, ...]] = {
    "record_type": _RECORD_TYPES,
    "status": _RELEASE_STATUS,
    "biological_scale": ("molecule", "complex", "cell", "tissue", "organ", "organism", "population"),
    "evidence_type": ("experimental", "curated", "computational", "comparative", "text_mined", "negative"),
    "design_safety_status": ("not_assessed", "research_only", "review_required", "not_for_synthesis", "blocked"),
}


@dataclass(frozen=True)
class ValidationIssue:
    entity_type: str
    field: str
    code: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return {
            "entity_type": self.entity_type,
            "field": self.field,
            "code": self.code,
            "message": self.message,
        }


class SchemaValidationError(ValueError):
    """Raised when a record or record envelope fails the Genopedia contract."""

    def __init__(self, issues: list[ValidationIssue]) -> None:
        self.issues = issues
        message = "; ".join(f"{issue.field}: {issue.message}" for issue in issues)
        super().__init__(message or "record failed schema validation")


def entity_spec(entity_type: str) -> EntitySpec:
    try:
        return ENTITY_SPEC_BY_NAME[entity_type]
    except KeyError as error:
        raise KeyError(f"unknown Genopedia entity type: {entity_type}") from error


def is_local_id(value: object) -> bool:
    return isinstance(value, str) and bool(_ID_PATTERN.fullmatch(value))


def normalize_biological_sequence(sequence: str, sequence_type: str) -> str:
    if not isinstance(sequence, str):
        raise TypeError("sequence must be a string")
    normalized = "".join(sequence.split()).upper()
    if sequence_type == "DNA":
        allowed = set("ACGTNRYKMSWBDHV")
    elif sequence_type == "RNA":
        allowed = set("ACGUNRYKMSWBDHV")
    elif sequence_type in {"PROTEIN", "PEPTIDE"}:
        allowed = set("ACDEFGHIKLMNPQRSTVWYBXZJUO*")
    else:
        raise ValueError(f"unsupported sequence_type: {sequence_type}")
    invalid = sorted(set(normalized) - allowed)
    if invalid:
        raise ValueError(f"invalid {sequence_type} symbols: {', '.join(invalid)}")
    return normalized


def sequence_sha256(sequence: str, sequence_type: str) -> str:
    normalized = normalize_biological_sequence(sequence, sequence_type)
    return hashlib.sha256(normalized.encode("ascii")).hexdigest()


def make_sequence_record(
    *,
    sequence_id: str,
    sequence: str,
    sequence_type: str,
    content_uri: str,
    release_id: str,
    record_type: str = "observed",
    source_record_id: str | None = None,
) -> dict[str, Any]:
    normalized = normalize_biological_sequence(sequence, sequence_type)
    record: dict[str, Any] = {
        "id": sequence_id,
        "sequence_type": sequence_type,
        "alphabet": "IUPAC",
        "length": len(normalized),
        "digest_algorithm": "sha256",
        "sequence_sha256": sequence_sha256(normalized, sequence_type),
        "normalization_version": "genopedia-seq-1",
        "content_uri": content_uri,
        "record_type": record_type,
        "release_id": release_id,
    }
    if source_record_id:
        record["source_record_id"] = source_record_id
    return record


def _type_matches(value: object, data_type: str) -> bool:
    if data_type in {"json", "string"}:
        return isinstance(value, (dict, list, str, int, float, bool)) if data_type == "json" else isinstance(value, str)
    if data_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if data_type == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if data_type == "boolean":
        return isinstance(value, bool)
    if data_type == "array":
        return isinstance(value, list)
    if data_type == "object":
        return isinstance(value, Mapping)
    return True


def validate_record(entity_type: str, record: Mapping[str, Any]) -> list[ValidationIssue]:
    spec = entity_spec(entity_type)
    issues: list[ValidationIssue] = []
    if not isinstance(record, Mapping):
        return [ValidationIssue(entity_type, "$", "type", "record must be an object")]
    fields = {field.name: field for field in spec.fields}
    for required in spec.required_fields:
        if required not in record or record[required] in (None, ""):
            issues.append(ValidationIssue(entity_type, required, "required", "required field is missing"))
    for name in record:
        if name not in fields:
            issues.append(ValidationIssue(entity_type, name, "unknown_field", "field is not in the schema"))
            continue
        field = fields[name]
        value = record[name]
        if value is None:
            continue
        if not _type_matches(value, field.data_type):
            issues.append(ValidationIssue(entity_type, name, "type", f"expected {field.data_type}"))
        if field.enum and value not in field.enum:
            issues.append(ValidationIssue(entity_type, name, "enum", f"expected one of {field.enum}"))
        if name == "id" and value is not None and not is_local_id(value):
            issues.append(ValidationIssue(entity_type, name, "identifier", "must be a namespaced local ID"))

    if entity_type == "sequence_record":
        if record.get("digest_algorithm") == "sha256" and not _SHA256_PATTERN.fullmatch(str(record.get("sequence_sha256", ""))):
            issues.append(ValidationIssue(entity_type, "sequence_sha256", "digest", "must be a lowercase SHA-256 digest"))
        if isinstance(record.get("length"), int) and record["length"] < 0:
            issues.append(ValidationIssue(entity_type, "length", "range", "must be non-negative"))
    if entity_type == "replicon" and isinstance(record.get("length"), int) and record["length"] < 0:
        issues.append(ValidationIssue(entity_type, "length", "range", "must be non-negative"))
    if entity_type == "claim_assertion":
        direct_trait_claim = (
            record.get("subject_entity_type") == "protein"
            and record.get("object_entity_type") == "phenotype_trait"
            and record.get("predicate") in {"causes", "necessary_for", "sufficient_for"}
        )
        if direct_trait_claim and not record.get("intermediate_relation_ids"):
            issues.append(
                ValidationIssue(
                    entity_type,
                    "intermediate_relation_ids",
                    "scope_boundary",
                    "direct protein-to-trait causality requires explicit intermediate biology",
                )
            )
    if entity_type == "design_record" and record.get("safety_status") in {"safe", "approved_for_use"}:
        issues.append(
            ValidationIssue(
                entity_type,
                "safety_status",
                "overclaim",
                "the schema records review status; it cannot certify a design as safe",
            )
        )
    if entity_type == "translation_event" and record.get("deterministic") is True:
        for field_name in ("input_sequence_id", "output_sequence_id", "translation_context_id", "provenance_activity_id"):
            if not record.get(field_name):
                issues.append(ValidationIssue(entity_type, field_name, "provenance", "deterministic translation requires this reference"))
    return issues


def validate_envelope(envelope: Mapping[str, Any]) -> list[ValidationIssue]:
    if not isinstance(envelope, Mapping):
        return [ValidationIssue("envelope", "$", "type", "envelope must be an object")]
    entity_type = envelope.get("entity_type")
    if not isinstance(entity_type, str) or entity_type not in ENTITY_SPEC_BY_NAME:
        return [ValidationIssue("envelope", "entity_type", "entity", "unknown entity type")]
    if envelope.get("schema_version") != SCHEMA_VERSION:
        return [ValidationIssue("envelope", "schema_version", "version", f"expected {SCHEMA_VERSION}")]
    if not isinstance(envelope.get("data"), Mapping):
        return [ValidationIssue(entity_type, "data", "type", "data must be an object")]
    return validate_record(entity_type, envelope["data"])


def make_envelope(entity_type: str, record: Mapping[str, Any]) -> dict[str, Any]:
    issues = validate_record(entity_type, record)
    if issues:
        raise SchemaValidationError(issues)
    return {"entity_type": entity_type, "schema_version": SCHEMA_VERSION, "data": dict(record)}


def schema_document() -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": SCHEMA_ID,
        "title": "Genopedia provenance-first protein data format",
        "description": f"Research-only normalized data contract. {NOT_FOR_CLINICAL_USE}; {NOT_FOR_SYNTHESIS_OR_WET_LAB_USE}.",
        "type": "object",
        "properties": {
            "entity_type": {"type": "string", "enum": list(ENTITY_SPEC_BY_NAME)},
            "schema_version": {"type": "string", "const": SCHEMA_VERSION},
            "data": {"type": "object"},
        },
        "required": ["entity_type", "schema_version", "data"],
        "additionalProperties": False,
        "$defs": {spec.name: spec.to_json_schema() for spec in ENTITY_SPECS},
        "x-controlled-vocabularies": {name: list(values) for name, values in CONTROLLED_VOCABULARIES.items()},
    }


def schema_json(indent: int = 2) -> str:
    return json.dumps(schema_document(), indent=indent, sort_keys=True) + "\n"
