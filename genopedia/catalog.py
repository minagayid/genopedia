"""JSONL catalog I/O and deterministic derived-index manifests."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from .schema import (
    SCHEMA_VERSION,
    SchemaValidationError,
    make_envelope,
    validate_envelope,
)


def _sort_value(value: Any) -> tuple[int, str]:
    if value is None:
        return (1, "")
    if isinstance(value, bool):
        return (0, "1" if value else "0")
    return (0, str(value))


def sort_envelopes(
    envelopes: Iterable[Mapping[str, Any]],
    *,
    fields: tuple[str, ...] = ("entity_type", "id"),
) -> list[dict[str, Any]]:
    """Return a stable sort with nulls last and no mutation of input objects."""

    copied = [dict(item) for item in envelopes]

    def key(envelope: Mapping[str, Any]) -> tuple[tuple[int, str], ...]:
        data = envelope.get("data", {})
        values = []
        for field in fields:
            if field == "entity_type":
                value = envelope.get("entity_type")
            else:
                value = data.get(field) if isinstance(data, Mapping) else None
            values.append(_sort_value(value))
        return tuple(values)

    return sorted(copied, key=key)


def write_jsonl(path: str | Path, records: Iterable[tuple[str, Mapping[str, Any]] | Mapping[str, Any]]) -> Path:
    """Write validated record envelopes as deterministic UTF-8 JSONL."""

    envelopes: list[dict[str, Any]] = []
    for record in records:
        if isinstance(record, Mapping) and "entity_type" in record:
            envelope = dict(record)
            issues = validate_envelope(envelope)
            if issues:
                raise SchemaValidationError(issues)
            envelopes.append(envelope)
        else:
            entity_type, data = record  # type: ignore[misc]
            envelopes.append(make_envelope(entity_type, data))
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="\n") as handle:
        for envelope in sort_envelopes(envelopes):
            handle.write(json.dumps(envelope, sort_keys=True, separators=(",", ":")))
            handle.write("\n")
    return output


def read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            envelope = json.loads(line)
            issues = validate_envelope(envelope)
            if issues:
                detail = "; ".join(f"{item.field}: {item.message}" for item in issues)
                raise SchemaValidationError(
                    [type(item)(item.entity_type, f"line {line_number} {item.field}", item.code, detail) for item in issues]
                )
            records.append(envelope)
    return records


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_index_manifest(
    *,
    input_release_id: str,
    input_path: str | Path,
    index_type: str,
    partition_key: str,
    sort_key: str,
    comparator: str = "unicode-codepoint",
    null_order: str = "last",
    index_parameters: Mapping[str, Any] | None = None,
    build_id: str = "build:genopedia-index-1",
    artifact_uri: str,
) -> dict[str, Any]:
    """Create a reproducible manifest for a derived index artifact."""

    return {
        "id": f"index:{hashlib.sha256((str(input_path) + build_id + index_type).encode()).hexdigest()[:24]}",
        "input_release_id": input_release_id,
        "index_type": index_type,
        "partition_key": partition_key,
        "sort_key": sort_key,
        "comparator": comparator,
        "null_order": null_order,
        "index_parameters": dict(index_parameters or {}),
        "build_id": build_id,
        "artifact_uri": artifact_uri,
        "input_sha256": sha256_file(input_path),
        "deterministic": True,
    }


def build_jev_sort_spec(
    *,
    input_release_id: str,
    semantic_query: str,
    score_levels: list[str],
    fallback_sort_key: str = "data.id",
    model_version: str = "external",
) -> dict[str, Any]:
    """Describe optional Jev semantic ranking without making it authoritative.

    Jev results are a derived, provider/model-dependent ordering.  The
    deterministic fallback remains the canonical sort for reproducibility.
    """

    return {
        "format_version": SCHEMA_VERSION,
        "input_release_id": input_release_id,
        "index_type": "jev_semantic_rank",
        "semantic_query": semantic_query,
        "score_levels": list(score_levels),
        "model_version": model_version,
        "fallback_sort_key": fallback_sort_key,
        "authoritative": False,
        "requires_exact_rerank": True,
        "audit_fields": ["row_id", "query", "model_version", "score", "retrieved_at"],
    }
