from __future__ import annotations

import re

from changeguard.models import (
    AnalysisResult,
    DatasetContext,
    DatasetSchema,
    Decision,
    Finding,
    Severity,
)

_SEVERITY_WEIGHT = {
    Severity.INFO: 0,
    Severity.LOW: 3,
    Severity.MEDIUM: 10,
    Severity.HIGH: 25,
    Severity.CRITICAL: 45,
}

_TYPE_ALIASES = {
    "INT": "INTEGER",
    "INT4": "INTEGER",
    "INT8": "BIGINT",
    "LONG": "BIGINT",
    "CHARACTER VARYING": "VARCHAR",
    "STRING": "VARCHAR",
    "BOOL": "BOOLEAN",
    "DOUBLE PRECISION": "DOUBLE",
    "FLOAT8": "DOUBLE",
    "FLOAT4": "FLOAT",
    "TIMESTAMP WITHOUT TIME ZONE": "TIMESTAMP",
}

_TYPE_FAMILIES = {
    "SMALLINT": "integer",
    "INTEGER": "integer",
    "BIGINT": "integer",
    "DECIMAL": "decimal",
    "NUMERIC": "decimal",
    "REAL": "float",
    "FLOAT": "float",
    "DOUBLE": "float",
    "CHAR": "text",
    "VARCHAR": "text",
    "TEXT": "text",
    "BOOLEAN": "boolean",
    "DATE": "date",
    "TIMESTAMP": "timestamp",
    "TIMESTAMPTZ": "timestamp",
    "JSON": "json",
    "JSONB": "json",
}


def normalize_type(native_type: str) -> tuple[str, int | None]:
    compact = re.sub(r"\s+", " ", native_type.strip().upper())
    compact = re.sub(r"\s*\(\s*", "(", compact)
    compact = re.sub(r"\s*\)\s*", ")", compact)
    match = re.fullmatch(r"([A-Z ]+?)(?:\((\d+)(?:,\s*\d+)?\))?", compact)
    if not match:
        return compact, None
    base = _TYPE_ALIASES.get(match.group(1).strip(), match.group(1).strip())
    size = int(match.group(2)) if match.group(2) else None
    return base, size


def is_compatible_type_change(old_type: str, new_type: str) -> bool:
    old_base, old_size = normalize_type(old_type)
    new_base, new_size = normalize_type(new_type)
    if old_base == new_base:
        if old_size is None or new_size is None:
            return True
        return new_size >= old_size
    if (old_base, new_base) in {
        ("SMALLINT", "INTEGER"),
        ("SMALLINT", "BIGINT"),
        ("INTEGER", "BIGINT"),
        ("REAL", "FLOAT"),
        ("REAL", "DOUBLE"),
        ("FLOAT", "DOUBLE"),
        ("CHAR", "VARCHAR"),
        ("VARCHAR", "TEXT"),
    }:
        return True
    return False


def _field_impacts(field: str, context: DatasetContext) -> tuple[str, ...]:
    exact = []
    for downstream in context.downstreams:
        if any(
            candidate == field or candidate.endswith(f",{field})")
            for candidate in downstream.fields
        ):
            exact.append(downstream.urn)
    if exact:
        return tuple(dict.fromkeys(exact))
    return tuple(downstream.urn for downstream in context.downstreams)


def _severity_for_break(field: str, context: DatasetContext) -> tuple[Severity, tuple[str, ...]]:
    impacts = _field_impacts(field, context)
    has_exact_field_lineage = any(
        candidate == field or candidate.endswith(f",{field})")
        for downstream in context.downstreams
        for candidate in downstream.fields
    )
    if has_exact_field_lineage:
        return Severity.CRITICAL, impacts
    if impacts:
        return Severity.HIGH, impacts
    return Severity.MEDIUM, impacts


def analyze_change(
    current: DatasetSchema,
    proposed: DatasetSchema,
    context: DatasetContext,
    rename_hints: dict[str, str] | None = None,
) -> AnalysisResult:
    if current.dataset_urn != proposed.dataset_urn:
        raise ValueError("Current and proposed schemas must target the same dataset URN")
    if context.dataset_urn and context.dataset_urn != current.dataset_urn:
        raise ValueError("Context dataset URN does not match the schema dataset URN")

    rename_hints = dict(rename_hints or {})
    current_by_name = {column.name: column for column in current.columns}
    proposed_by_name = {column.name: column for column in proposed.columns}
    invalid_hints = {
        old: new
        for old, new in rename_hints.items()
        if old not in current_by_name or new not in proposed_by_name
    }
    if invalid_hints:
        raise ValueError(f"Rename hints reference missing columns: {invalid_hints}")

    findings: list[Finding] = []

    for old_name, new_name in sorted(rename_hints.items()):
        if old_name == new_name:
            continue
        severity, impacts = _severity_for_break(old_name, context)
        findings.append(
            Finding(
                code="COLUMN_RENAME",
                severity=severity,
                field=old_name,
                summary=f"Column {old_name!r} is renamed to {new_name!r}.",
                evidence=(
                    f"DataHub reports {len(impacts)} downstream asset(s) that may still reference "
                    f"{old_name!r}."
                ),
                remediation=(
                    f"Expose {new_name!r} as {old_name!r} through a compatibility view, update "
                    "consumers, then remove the alias in a later version."
                ),
                affected_assets=impacts,
            )
        )

    renamed_old = set(rename_hints)
    renamed_new = set(rename_hints.values())
    for name in sorted(current_by_name.keys() - proposed_by_name.keys() - renamed_old):
        severity, impacts = _severity_for_break(name, context)
        findings.append(
            Finding(
                code="COLUMN_DROPPED",
                severity=severity,
                field=name,
                summary=f"Column {name!r} is removed without a migration mapping.",
                evidence=(
                    f"The catalog contains {len(impacts)} potentially affected downstream asset(s)."
                ),
                remediation=(
                    "Keep the column during a deprecation window or provide an explicit "
                    "rename hint."
                ),
                affected_assets=impacts,
            )
        )

    shared_names = sorted(current_by_name.keys() & proposed_by_name.keys())
    for name in shared_names:
        old = current_by_name[name]
        new = proposed_by_name[name]
        if normalize_type(old.native_type) != normalize_type(new.native_type):
            compatible = is_compatible_type_change(old.native_type, new.native_type)
            severity, impacts = _severity_for_break(name, context)
            if compatible:
                severity = Severity.LOW
            findings.append(
                Finding(
                    code="TYPE_WIDENED" if compatible else "TYPE_CHANGED",
                    severity=severity,
                    field=name,
                    summary=f"Type changes from {old.native_type} to {new.native_type}.",
                    evidence=(
                        "The change is in the compatible widening allow-list."
                        if compatible
                        else (
                            "The change is not a recognized safe widening; "
                            f"{len(impacts)} downstream asset(s) may need updates."
                        )
                    ),
                    remediation=(
                        "Run consumer tests and retain the existing cast during rollout."
                        if compatible
                        else (
                            "Introduce a new typed column or compatibility cast and migrate "
                            "consumers first."
                        )
                    ),
                    affected_assets=impacts if not compatible else (),
                )
            )

        if old.nullable is False and new.nullable is True:
            severity, impacts = _severity_for_break(name, context)
            findings.append(
                Finding(
                    code="NULLABILITY_RELAXED",
                    severity=severity,
                    field=name,
                    summary=f"Column {name!r} can now emit null values.",
                    evidence=(
                        f"Non-null consumers include up to {len(impacts)} cataloged downstream "
                        "asset(s)."
                    ),
                    remediation=(
                        "Backfill a default or update downstream null handling before release."
                    ),
                    affected_assets=impacts,
                )
            )
        elif old.nullable is True and new.nullable is False:
            findings.append(
                Finding(
                    code="NULLABILITY_TIGHTENED",
                    severity=Severity.MEDIUM,
                    field=name,
                    summary=f"Column {name!r} becomes required.",
                    evidence="Existing producers may still send null values.",
                    remediation=(
                        "Validate and backfill existing rows before enforcing the constraint."
                    ),
                )
            )

    for name in sorted(proposed_by_name.keys() - current_by_name.keys() - renamed_new):
        column = proposed_by_name[name]
        if column.nullable is False:
            findings.append(
                Finding(
                    code="REQUIRED_COLUMN_ADDED",
                    severity=Severity.HIGH,
                    field=name,
                    summary=f"Required column {name!r} is added without a cataloged default.",
                    evidence=(
                        "Historical rows and existing producers cannot supply this value "
                        "automatically."
                    ),
                    remediation=(
                        "Add it as nullable, backfill it, then enforce the non-null constraint."
                    ),
                )
            )

    findings.sort(key=lambda item: (-_SEVERITY_WEIGHT[item.severity], item.code, item.field))
    score = sum(_SEVERITY_WEIGHT[finding.severity] for finding in findings)
    if any(finding.severity in {Severity.HIGH, Severity.CRITICAL} for finding in findings):
        score += min(15, len(context.downstreams) * 3)
    score = min(100, score)
    requires_review = any(
        finding.severity in {Severity.MEDIUM, Severity.HIGH, Severity.CRITICAL}
        for finding in findings
    )
    decision = (
        Decision.BLOCK
        if score >= 60
        else Decision.REVIEW
        if score >= 30 or requires_review
        else Decision.PASS
    )

    return AnalysisResult(
        dataset_urn=current.dataset_urn,
        decision=decision,
        risk_score=score,
        findings=tuple(findings),
        owners=context.owners,
        downstream_count=len(context.downstreams),
        evidence_source=context.source,
        rename_hints=rename_hints,
    )
