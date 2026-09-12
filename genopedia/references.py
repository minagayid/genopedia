"""Versioned, metadata-first reference registry for Genopedia.

The registry deliberately stores source metadata and acquisition constraints,
not biological data. Large, controlled-access, or non-redistributable files
must be acquired by a user who can accept the provider's current terms.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


DEFAULT_MANIFEST = Path(__file__).with_name("reference-manifest.json")
REQUIRED_FIELDS = {
    "id",
    "name",
    "tier",
    "evidence_class",
    "roles",
    "molecules",
    "provider",
    "access",
    "acquisition",
    "data_products",
}


class ReferenceManifestError(ValueError):
    """Raised when a reference manifest is missing required information."""


@dataclass(frozen=True)
class ReferenceSource:
    id: str
    name: str
    tier: str
    evidence_class: str
    roles: tuple[str, ...]
    molecules: tuple[str, ...]
    provider_name: str
    provider_url: str
    access_mode: str
    redistribution: str
    acquisition: str
    data_products: tuple[str, ...]
    index_fields: tuple[str, ...] = ()
    notes: str = ""

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ReferenceSource":
        missing = REQUIRED_FIELDS - payload.keys()
        if missing:
            raise ReferenceManifestError(
                f"reference {payload.get('id', '<unknown>')!r} is missing: "
                + ", ".join(sorted(missing))
            )
        provider = payload["provider"]
        access = payload["access"]
        if not isinstance(provider, dict) or not provider.get("name") or not provider.get("url"):
            raise ReferenceManifestError(f"reference {payload['id']!r} needs provider name and url")
        if not isinstance(access, dict) or not access.get("mode") or not access.get("redistribution"):
            raise ReferenceManifestError(
                f"reference {payload['id']!r} needs access mode and redistribution policy"
            )
        return cls(
            id=str(payload["id"]),
            name=str(payload["name"]),
            tier=str(payload["tier"]),
            evidence_class=str(payload["evidence_class"]),
            roles=tuple(str(value) for value in payload["roles"]),
            molecules=tuple(str(value).upper() for value in payload["molecules"]),
            provider_name=str(provider["name"]),
            provider_url=str(provider["url"]),
            access_mode=str(access["mode"]),
            redistribution=str(access["redistribution"]),
            acquisition=str(payload["acquisition"]),
            data_products=tuple(str(value) for value in payload["data_products"]),
            index_fields=tuple(str(value) for value in payload.get("index_fields", [])),
            notes=str(payload.get("notes", "")),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "tier": self.tier,
            "evidence_class": self.evidence_class,
            "roles": list(self.roles),
            "molecules": list(self.molecules),
            "provider": {"name": self.provider_name, "url": self.provider_url},
            "access": {"mode": self.access_mode, "redistribution": self.redistribution},
            "acquisition": self.acquisition,
            "data_products": list(self.data_products),
            "index_fields": list(self.index_fields),
            "notes": self.notes,
        }


@dataclass(frozen=True)
class ReferencePlan:
    """A deterministic source-selection plan for a future local build."""

    purpose: str
    molecule: str
    source_ids: tuple[str, ...]
    rationale: tuple[str, ...]
    safety: str = "Reference evidence is not a clinical interpretation or a proposed DNA edit."

    def to_dict(self) -> dict[str, Any]:
        return {
            "purpose": self.purpose,
            "molecule": self.molecule,
            "source_ids": list(self.source_ids),
            "rationale": list(self.rationale),
            "safety": self.safety,
        }


class ReferenceRegistry:
    """Load, validate, search, and plan against a pinned source registry."""

    def __init__(self, sources: Iterable[ReferenceSource], manifest_version: str, schema_version: str) -> None:
        self.sources = tuple(sources)
        self.manifest_version = manifest_version
        self.schema_version = schema_version

    @classmethod
    def from_path(cls, path: str | Path = DEFAULT_MANIFEST) -> "ReferenceRegistry":
        manifest_path = Path(path)
        try:
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        except OSError as error:
            raise ReferenceManifestError(f"cannot read reference manifest {manifest_path}") from error
        except json.JSONDecodeError as error:
            raise ReferenceManifestError(f"invalid JSON reference manifest {manifest_path}: {error}") from error
        if not isinstance(payload, dict):
            raise ReferenceManifestError("reference manifest must be a JSON object")
        return cls.from_dict(payload)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ReferenceRegistry":
        if not payload.get("schema_version") or not payload.get("project"):
            raise ReferenceManifestError("manifest needs schema_version and project")
        project = payload["project"]
        if not isinstance(project, dict) or not project.get("manifest_version"):
            raise ReferenceManifestError("manifest project needs manifest_version")
        raw_sources = payload.get("sources")
        if not isinstance(raw_sources, list) or not raw_sources:
            raise ReferenceManifestError("manifest needs a non-empty sources list")
        registry = cls(
            (ReferenceSource.from_dict(item) for item in raw_sources),
            manifest_version=str(project["manifest_version"]),
            schema_version=str(payload["schema_version"]),
        )
        registry.validate()
        return registry

    def validate(self) -> None:
        ids = [source.id for source in self.sources]
        if len(ids) != len(set(ids)):
            raise ReferenceManifestError("reference ids must be unique")
        for source in self.sources:
            if not source.roles or not source.molecules or not source.data_products:
                raise ReferenceManifestError(f"reference {source.id!r} needs roles, molecules, and data_products")
            if not source.provider_url.startswith(("https://", "http://")):
                raise ReferenceManifestError(f"reference {source.id!r} has an invalid provider URL")

    def get(self, source_id: str) -> ReferenceSource:
        for source in self.sources:
            if source.id == source_id:
                return source
        raise KeyError(source_id)

    def search(
        self,
        query: str = "",
        *,
        tier: str | None = None,
        evidence_class: str | None = None,
        role: str | None = None,
        molecule: str | None = None,
        access_mode: str | None = None,
    ) -> list[ReferenceSource]:
        query_terms = tuple(term for term in query.lower().split() if term)
        normalized_molecule = molecule.upper() if molecule else None
        results = []
        for source in self.sources:
            haystack = " ".join(
                [source.id, source.name, source.evidence_class, *source.roles, *source.data_products]
            ).lower()
            if query_terms and not all(term in haystack for term in query_terms):
                continue
            if tier and source.tier.upper() != tier.upper():
                continue
            if evidence_class and source.evidence_class.lower() != evidence_class.lower():
                continue
            if role and role.lower() not in {value.lower() for value in source.roles}:
                continue
            if normalized_molecule and normalized_molecule not in source.molecules:
                continue
            if access_mode and source.access_mode.lower() != access_mode.lower():
                continue
            results.append(source)
        return results

    def plan(self, purpose: str = "reference", molecule: str = "DNA") -> ReferencePlan:
        purpose = purpose.lower().replace(" ", "_")
        molecule = molecule.upper()
        if molecule not in {"DNA", "RNA", "PROTEIN"}:
            raise ValueError("molecule must be DNA, RNA, or PROTEIN")
        purpose_roles = {
            "reference": {"primary_reference", "canonical_transcript", "protein_validation"},
            "anomaly_detection": {
                "primary_reference",
                "sequence_universe",
                "taxonomy",
                "rna_family",
                "rrna",
                "empirical_error",
                "read_evidence",
            },
            "correction": {"primary_reference", "empirical_error", "benchmark", "contamination_screen"},
        }
        roles = purpose_roles.get(purpose)
        if roles is None:
            raise ValueError("purpose must be reference, anomaly_detection, or correction")
        tier_order = {"A": 0, "B": 1, "C": 2}
        candidates = [
            source
            for source in self.sources
            if molecule in source.molecules and (roles & set(source.roles))
        ]
        candidates.sort(key=lambda source: (tier_order.get(source.tier.upper(), 9), source.id))
        selected = tuple(source.id for source in candidates)
        rationale = (
            "Start with pinned provider releases and checksums; resolve access and redistribution terms per source.",
            "Keep authoritative, diversity, empirical-read, benchmark, and contamination evidence distinct.",
            "Use results to generate reviewable evidence, never silent sequence rewriting or clinical interpretation.",
        )
        return ReferencePlan(purpose, molecule, selected, rationale)
