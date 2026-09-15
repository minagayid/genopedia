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
]

__version__ = "0.2.0"

