"""
Genomics ML Models
==================
Predefined architectures for genomics tasks.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Sequence


@dataclass
class KmerConfig:
    k: int = 3
    alphabet: Sequence[str] = ("A", "C", "G", "T")


def kmer_counts(sequence: str, k: int = 3) -> dict[str, int]:
    """Count overlapping k-mers in ``sequence`` (pure Python, no deps)."""
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
        """Return the most likely class label for ``sequence``."""
        return self.predict_proba(sequence)[0][0]

    def predict_proba(self, sequence: str) -> list[tuple[str, float]]:
        """Return (label, log-likelihood) pairs sorted best-first.

        Uses a multinomial naive-Bayes score over k-mer counts with a small
        floor probability for k-mers unseen during training, so unfamiliar
        sequences never produce a math-domain error.
        """
        if not getattr(self, "classes", None):
            raise RuntimeError("Classifier must be trained before prediction.")
        counts = kmer_counts(sequence, self.k)
        unseen_floor = math.log(1e-9)
        scores: dict[str, float] = {}
        for c in self.classes:
            log_prob = 0.0
            class_probs = self.probabilities[c]
            for kmer, count in counts.items():
                prob = class_probs.get(kmer)
                log_prob += count * (math.log(prob) if prob else unseen_floor)
            scores[c] = log_prob
        return sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
