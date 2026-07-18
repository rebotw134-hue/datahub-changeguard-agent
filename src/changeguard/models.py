from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any


class Severity(StrEnum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Decision(StrEnum):
    PASS = "PASS"
    REVIEW = "REVIEW"
    BLOCK = "BLOCK"


@dataclass(frozen=True)
class ColumnSchema:
    name: str
    native_type: str
    nullable: bool | None = None
    description: str | None = None

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> ColumnSchema:
        name = str(value.get("name") or value.get("fieldPath") or "").strip()
        native_type = str(value.get("type") or value.get("nativeDataType") or "").strip()
        if not name or not native_type:
            raise ValueError("Each column requires non-empty 'name' and 'type' values")
        nullable = value.get("nullable")
        if nullable not in (True, False, None):
            raise ValueError(f"Column {name!r} has invalid nullable value: {nullable!r}")
        return cls(
            name=name,
            native_type=native_type,
            nullable=nullable,
            description=value.get("description"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "type": self.native_type,
            "nullable": self.nullable,
            "description": self.description,
        }


@dataclass(frozen=True)
class DatasetSchema:
    dataset_urn: str
    columns: tuple[ColumnSchema, ...]

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> DatasetSchema:
        urn = str(value.get("dataset_urn") or value.get("urn") or "").strip()
        if not urn:
            raise ValueError("Schema requires 'dataset_urn'")
        raw_columns = value.get("columns")
        if not isinstance(raw_columns, list) or not raw_columns:
            raise ValueError("Schema requires a non-empty 'columns' list")
        columns = tuple(ColumnSchema.from_dict(item) for item in raw_columns)
        names = [column.name for column in columns]
        if len(names) != len(set(names)):
            raise ValueError("Schema contains duplicate column names")
        return cls(dataset_urn=urn, columns=columns)

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset_urn": self.dataset_urn,
            "columns": [column.to_dict() for column in self.columns],
        }


@dataclass(frozen=True)
class DownstreamAsset:
    urn: str
    name: str
    hops: int
    fields: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> DownstreamAsset:
        return cls(
            urn=str(value["urn"]),
            name=str(value.get("name") or value["urn"]),
            hops=int(value.get("hops", 1)),
            fields=tuple(str(item) for item in value.get("fields", [])),
        )


@dataclass(frozen=True)
class DatasetContext:
    dataset_urn: str
    dataset_name: str
    owners: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()
    downstreams: tuple[DownstreamAsset, ...] = ()
    source: str = "fixture"

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> DatasetContext:
        return cls(
            dataset_urn=str(value.get("dataset_urn") or value.get("urn") or ""),
            dataset_name=str(value.get("dataset_name") or value.get("name") or "unknown"),
            owners=tuple(str(item) for item in value.get("owners", [])),
            tags=tuple(str(item) for item in value.get("tags", [])),
            downstreams=tuple(
                DownstreamAsset.from_dict(item) for item in value.get("downstreams", [])
            ),
            source=str(value.get("source", "fixture")),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset_urn": self.dataset_urn,
            "dataset_name": self.dataset_name,
            "owners": list(self.owners),
            "tags": list(self.tags),
            "downstreams": [asdict(item) for item in self.downstreams],
            "source": self.source,
        }


@dataclass(frozen=True)
class Finding:
    code: str
    severity: Severity
    field: str
    summary: str
    evidence: str
    remediation: str
    affected_assets: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["severity"] = self.severity.value
        return value


@dataclass(frozen=True)
class AnalysisResult:
    dataset_urn: str
    decision: Decision
    risk_score: int
    findings: tuple[Finding, ...]
    owners: tuple[str, ...]
    downstream_count: int
    evidence_source: str
    rename_hints: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset_urn": self.dataset_urn,
            "decision": self.decision.value,
            "risk_score": self.risk_score,
            "findings": [finding.to_dict() for finding in self.findings],
            "owners": list(self.owners),
            "downstream_count": self.downstream_count,
            "evidence_source": self.evidence_source,
            "rename_hints": dict(self.rename_hints),
        }
