"""Optional-model-compatible primitives implemented with the standard library."""

from __future__ import annotations

import json
import math
from collections import Counter
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class KmerConfig:
    k: int = 3


def kmer_counts(sequence: str, k: int = 3) -> dict[str, int]:
    if k < 1:
        raise ValueError("k must be at least 1")
    normalized = "".join(sequence.split()).upper()
    return dict(Counter(normalized[index : index + k] for index in range(len(normalized) - k + 1)))


class KmerClassifier:
    """A deterministic multinomial k-mer classifier with Laplace smoothing."""

    def __init__(self, k: int = 3) -> None:
        if k < 1:
            raise ValueError("k must be at least 1")
        self.k = k
        self.classes: tuple[str, ...] = ()
        self._counts: dict[str, Counter[str]] = {}
        self._totals: dict[str, int] = {}
        self._vocabulary: tuple[str, ...] = ()
        self._sample_counts: Counter[str] = Counter()

    def fit(self, sequences: Iterable[str], labels: Iterable[str]) -> "KmerClassifier":
        sequence_list = list(sequences)
        label_list = list(labels)
        if not sequence_list or not label_list or len(sequence_list) != len(label_list):
            raise ValueError("sequences and labels must be non-empty and have equal lengths")
        self.classes = tuple(sorted(set(label_list)))
        self._counts = {label: Counter() for label in self.classes}
        self._totals = {label: 0 for label in self.classes}
        self._sample_counts = Counter(label_list)
        vocabulary: set[str] = set()
        for sequence, label in zip(sequence_list, label_list):
            counts = kmer_counts(sequence, self.k)
            self._counts[label].update(counts)
            self._totals[label] += sum(counts.values())
            vocabulary.update(counts)
        self._vocabulary = tuple(sorted(vocabulary))
        return self

    def _log_scores(self, sequence: str) -> dict[str, float]:
        if not self.classes:
            raise RuntimeError("classifier must be trained before prediction")
        counts = kmer_counts(sequence, self.k)
        vocabulary_size = max(1, len(self._vocabulary))
        total_samples = sum(self._sample_counts.values())
        scores: dict[str, float] = {}
        for label in self.classes:
            prior = self._sample_counts[label] / total_samples
            denominator = self._totals[label] + vocabulary_size
            score = math.log(prior)
            for kmer, count in counts.items():
                probability = (self._counts[label].get(kmer, 0) + 1) / denominator
                score += count * math.log(probability)
            scores[label] = score
        return scores

    def predict_proba(self, sequence: str) -> dict[str, float]:
        scores = self._log_scores(sequence)
        maximum = max(scores.values())
        exponentials = {label: math.exp(score - maximum) for label, score in scores.items()}
        total = sum(exponentials.values())
        return {label: value / total for label, value in exponentials.items()}

    def predict(self, sequence: str) -> str:
        probabilities = self.predict_proba(sequence)
        return max(probabilities, key=probabilities.get)

    def to_dict(self) -> dict[str, object]:
        return {
            "k": self.k,
            "classes": list(self.classes),
            "counts": {label: dict(counts) for label, counts in self._counts.items()},
            "totals": self._totals,
            "vocabulary": list(self._vocabulary),
            "sample_counts": dict(self._sample_counts),
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True)

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "KmerClassifier":
        classifier = cls(k=int(payload["k"]))
        classifier.classes = tuple(str(value) for value in payload["classes"])
        classifier._counts = {
            str(label): Counter({str(kmer): int(count) for kmer, count in values.items()})
            for label, values in payload["counts"].items()
        }
        classifier._totals = {str(label): int(value) for label, value in payload["totals"].items()}
        classifier._vocabulary = tuple(str(value) for value in payload["vocabulary"])
        classifier._sample_counts = Counter(
            {str(label): int(value) for label, value in payload["sample_counts"].items()}
        )
        return classifier

    @classmethod
    def from_json(cls, value: str) -> "KmerClassifier":
        return cls.from_dict(json.loads(value))


DNAClassifier = KmerClassifier

