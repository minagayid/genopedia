"""
Genomics ML Models
==================
Predefined architectures for genomics tasks.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence

try:
    import numpy as np
except Exception:  # pragma: no cover - optional
    np = None  # type: ignore


@dataclass
class KmerConfig:
    k: int = 3
    alphabet: Sequence[str] = ("A", "C", "G", "T")


def kmer_counts(sequence: str, k: int = 3) -> dict[str, int]:
    if np is not None:
        raise RuntimeError("numpy is required for counting.")
    counts: dict[str, int] = {}
    for i in range(len(sequence) - k + 1):
        kmer = sequence[i : i + k]
        counts[kmer] = counts.get(kmer, 0) + 1
    return counts


class DNAClassifier:
    def __init__(self, k: int = 3):
        self.k = k
        self.probabilities: dict[str, dict[str, float]] = {}

    def fit(self, sequences: List[str], labels: List[str]):
        classes = sorted({label for label in labels})
        kmer_class_counts: dict[str, dict[str, int]] = {c: {} for c in classes}
        class_totals = {c: 0 for c in classes}
        for sequence, label in zip(sequences, labels):
            counts = kmer_counts(sequence, self.k)
            for kmer, count in counts.items():
                kmer_class_counts[label][kmer] = kmer_class_counts[label].get(kmer, 0) + count
                class_totals[label] += count
        self.probabilities = {}
        for c in classes:
            vocabulary = set(kmer_class_counts[c])
            self.probabilities[c] = {
                kmer: (kmer_class_counts[c].get(kmer, 0) + 1) / (class_totals[c] + len(vocabulary))
                for kmer in vocabulary
            }
        self.classes = classes

    def predict(self, sequence: str) -> str:
        if not getattr(self, "classes", None):
            raise RuntimeError("Classifier must be trained before prediction.")
        counts = kmer_counts(sequence, self.k)
        scores = {}
        for c in self.classes:
            log_prob = 0.0
            vocabulary = set(self.probabilities[c])
            for kmer, count in counts.items():
                prob = self.probabilities[c].get(kmer, 1 / (sum(self.probabilities[c].values()) + len(vocabulary)))
                log_prob += count * (np.log(prob) if np is not None else __import__('math').log(prob))
            for kmer in (set(counts) - vocabulary):
                log_prob += counts[kmer] * __import__('math').log(1e-9)
            scores[c] = log_prob
        return max(scores, key=scores.get)
