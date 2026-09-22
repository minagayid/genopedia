"""Genopedia: lightweight, offline-first genomics analysis tools."""

from .anomalies import SequenceAnomaly, SequenceAnomalyDetector
from .correction import CorrectionPlanner, CorrectionSuggestion
from .core import (
    FunctionalRegion,
    QualityReport,
    SequenceAnalyzer,
    SequenceRecord,
    Variant,
)
from .references import ReferencePlan, ReferenceRegistry, ReferenceSource
from .io import DEFAULT_INPUT_LIMITS, InputLimitError, InputLimits
from .catalog import build_index_manifest, build_jev_sort_spec, read_jsonl, sort_envelopes, write_jsonl
from .jev_pipeline import (
    REFSEQ_RELEASE_237,
    build_refseq237_jev_plan,
    render_refseq237_jev_sql,
    write_jev_plan,
)
from .schema import (
    ENTITY_SPECS,
    NOT_FOR_CLINICAL_USE,
    NOT_FOR_SYNTHESIS_OR_WET_LAB_USE,
    SCHEMA_VERSION,
    SchemaValidationError,
    make_envelope,
    make_sequence_record,
    schema_document,
    sequence_sha256,
    validate_envelope,
    validate_record,
)

__all__ = [
    "FunctionalRegion",
    "DEFAULT_INPUT_LIMITS",
    "InputLimitError",
    "InputLimits",
    "QualityReport",
    "SequenceAnalyzer",
    "SequenceRecord",
    "SequenceAnomaly",
    "SequenceAnomalyDetector",
    "CorrectionPlanner",
    "CorrectionSuggestion",
    "ReferencePlan",
    "ReferenceRegistry",
    "ReferenceSource",
    "Variant",
    "ENTITY_SPECS",
    "NOT_FOR_CLINICAL_USE",
    "NOT_FOR_SYNTHESIS_OR_WET_LAB_USE",
    "SCHEMA_VERSION",
    "SchemaValidationError",
    "build_index_manifest",
    "build_jev_sort_spec",
    "build_refseq237_jev_plan",
    "make_envelope",
    "make_sequence_record",
    "read_jsonl",
    "REFSEQ_RELEASE_237",
    "render_refseq237_jev_sql",
    "schema_document",
    "sequence_sha256",
    "sort_envelopes",
    "validate_envelope",
    "validate_record",
    "write_jsonl",
    "write_jev_plan",
]

__version__ = "0.3.0"

