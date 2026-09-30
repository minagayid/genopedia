"""Small offline lexical retrieval with source-bound content provenance.

No sequences are generated or edited. Ranking is a transparent token overlap
baseline; it does not establish scientific truth or semantic understanding.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import re


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


@dataclass(frozen=True)
class EvidenceDocument:
    source_id: str
    source_url: str
    source_version: str
    text: str
    license: str

    def __post_init__(self):
        if not all(isinstance(v, str) and v.strip() for v in
                   (self.source_id, self.source_url, self.source_version, self.text, self.license)):
            raise ValueError("All provenance fields are required")
        if len(self.text) > 100_000:
            raise ValueError("Evidence document exceeds local limit")

    @property
    def content_sha256(self) -> str:
        return sha256(self.text.encode("utf-8")).hexdigest()


def retrieve(query: str, documents: list[EvidenceDocument], k: int = 3) -> list[dict]:
    if not query.strip() or len(query) > 4000 or not 1 <= k <= 50 or len(documents) > 10_000:
        raise ValueError("Invalid bounded retrieval request")
    if len({d.source_id for d in documents}) != len(documents):
        raise ValueError("Source IDs must be unique")
    query_tokens = _tokens(query)
    scored = [(len(query_tokens & _tokens(d.text)), d) for d in documents]
    scored.sort(key=lambda pair: (-pair[0], pair[1].source_id))
    return [{"source_id": d.source_id, "source_url": d.source_url,
             "source_version": d.source_version, "license": d.license,
             "content_sha256": d.content_sha256, "score": score, "text": d.text}
            for score, d in scored[:k] if score > 0]


def retrieval_metrics(ranked_ids: list[str], relevant_ids: set[str]) -> dict:
    if not relevant_ids or len(set(ranked_ids)) != len(ranked_ids):
        raise ValueError("Non-empty relevance labels and unique ranked IDs are required")
    hits = set(ranked_ids) & relevant_ids
    return {"precision": len(hits) / len(ranked_ids) if ranked_ids else 0.0,
            "recall": len(hits) / len(relevant_ids),
            "mrr": next((1 / rank for rank, sid in enumerate(ranked_ids, 1)
                         if sid in relevant_ids), 0.0)}
