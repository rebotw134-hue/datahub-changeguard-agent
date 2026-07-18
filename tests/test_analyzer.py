from __future__ import annotations

import pytest

from changeguard.analyzer import analyze_change, is_compatible_type_change, normalize_type
from changeguard.models import DatasetContext, DatasetSchema, Decision, Severity

URN = "urn:li:dataset:(urn:li:dataPlatform:postgres,commerce.orders,PROD)"


def schema(columns: list[dict[str, object]]) -> DatasetSchema:
    return DatasetSchema.from_dict({"dataset_urn": URN, "columns": columns})


def context(fields: list[str] | None = None) -> DatasetContext:
    return DatasetContext.from_dict(
        {
            "dataset_urn": URN,
            "dataset_name": "commerce.orders",
            "owners": ["urn:li:corpuser:data-team"],
            "downstreams": [
                {
                    "urn": "urn:li:dataset:(urn:li:dataPlatform:postgres,finance.daily,PROD)",
                    "name": "finance.daily",
                    "hops": 1,
                    "fields": fields or [],
                }
            ],
        }
    )


@pytest.mark.parametrize(
    ("old", "new", "expected"),
    [
        ("INT", "BIGINT", True),
        ("VARCHAR(10)", "VARCHAR(20)", True),
        ("VARCHAR(20)", "VARCHAR(10)", False),
        ("BIGINT", "VARCHAR(36)", False),
    ],
)
def test_compatible_type_change(old: str, new: str, expected: bool) -> None:
    assert is_compatible_type_change(old, new) is expected


def test_normalize_type_alias_and_size() -> None:
    assert normalize_type(" character   varying ( 12 ) ") == ("VARCHAR", 12)


def test_breaking_change_with_field_lineage_is_blocked() -> None:
    current = schema(
        [
            {"name": "order_id", "type": "BIGINT", "nullable": False},
            {"name": "order_total", "type": "DECIMAL(12,2)", "nullable": False},
        ]
    )
    proposed = schema(
        [
            {"name": "order_id", "type": "VARCHAR(36)", "nullable": False},
            {"name": "total_amount", "type": "DECIMAL(12,2)", "nullable": False},
        ]
    )

    result = analyze_change(
        current,
        proposed,
        context(["order_id", "order_total"]),
        {"order_total": "total_amount"},
    )

    assert result.decision is Decision.BLOCK
    assert result.risk_score == 93
    assert [finding.code for finding in result.findings] == ["COLUMN_RENAME", "TYPE_CHANGED"]
    assert all(finding.severity is Severity.CRITICAL for finding in result.findings)


def test_nullable_addition_without_downstreams_passes() -> None:
    current = schema([{"name": "order_id", "type": "BIGINT", "nullable": False}])
    proposed = schema(
        [
            {"name": "order_id", "type": "BIGINT", "nullable": False},
            {"name": "note", "type": "TEXT", "nullable": True},
        ]
    )
    result = analyze_change(current, proposed, DatasetContext(URN, "orders"))
    assert result.decision is Decision.PASS
    assert result.findings == ()


def test_invalid_rename_hint_is_rejected() -> None:
    current = schema([{"name": "order_id", "type": "BIGINT"}])
    proposed = schema([{"name": "order_id", "type": "BIGINT"}])
    with pytest.raises(ValueError, match="missing columns"):
        analyze_change(current, proposed, context(), {"missing": "also_missing"})
