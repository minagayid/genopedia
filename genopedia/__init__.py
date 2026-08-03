"""Genopedia: lightweight, offline-first genomics analysis tools."""

from .core import (
    FunctionalRegion,
    QualityReport,
    SequenceAnalyzer,
    SequenceRecord,
    Variant,
)

__all__ = [
    "FunctionalRegion",
    "QualityReport",
    "SequenceAnalyzer",
    "SequenceRecord",
    "Variant",
]

__version__ = "0.2.0"

