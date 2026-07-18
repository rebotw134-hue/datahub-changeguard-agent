from __future__ import annotations

import json

from changeguard.analyzer import analyze_change
from changeguard.generators import render_compatibility_sql, render_dbt_schema, write_artifacts
from changeguard.models import DatasetContext, DatasetSchema

URN = "urn:li:dataset:(urn:li:dataPlatform:postgres,commerce.orders,PROD)"


def _schema(columns: list[dict[str, object]]) -> DatasetSchema:
    return DatasetSchema.from_dict({"dataset_urn": URN, "columns": columns})


def test_generates_rename_compatibility_view() -> None:
    current = _schema(
        [
            {"name": "order_id", "type": "BIGINT", "nullable": False},
            {"name": "order_total", "type": "DECIMAL(12,2)", "nullable": False},
        ]
    )
    proposed = _schema(
        [
            {"name": "order_id", "type": "BIGINT", "nullable": False},
            {"name": "total_amount", "type": "DECIMAL(12,2)", "nullable": False},
        ]
    )
    context = DatasetContext(URN, "commerce.orders")
    result = analyze_change(current, proposed, context, {"order_total": "total_amount"})

    sql = render_compatibility_sql(current, proposed, result, "commerce.orders_v2")

    assert "total_amount AS order_total" in sql
    assert "FROM commerce.orders_v2" in sql


def test_unmapped_drop_stops_sql_generation() -> None:
    current = _schema([{"name": "legacy", "type": "TEXT"}])
    proposed = _schema([{"name": "replacement", "type": "TEXT"}])
    context = DatasetContext(URN, "commerce.orders")
    result = analyze_change(current, proposed, context)
    sql = render_compatibility_sql(current, proposed, result, "commerce.orders_v2")
    assert "SQL generation stopped" in sql
    assert "CREATE OR REPLACE VIEW" not in sql


def test_dbt_contract_contains_types_and_not_null() -> None:
    proposed = _schema(
        [
            {"name": "order_id", "type": "BIGINT", "nullable": False},
            {"name": "note", "type": "TEXT", "nullable": True},
        ]
    )
    rendered = render_dbt_schema(proposed)
    assert "enforced: true" in rendered
    assert rendered.count("- not_null") == 1


def test_writes_complete_artifact_set(tmp_path) -> None:
    current = _schema([{"name": "order_id", "type": "BIGINT", "nullable": False}])
    proposed = _schema([{"name": "order_id", "type": "VARCHAR(36)", "nullable": False}])
    context = DatasetContext(URN, "commerce.orders")
    result = analyze_change(current, proposed, context)
    paths = write_artifacts(tmp_path, current, proposed, context, result, "commerce.orders_v2")
    assert set(paths) == {"audit", "report", "html", "sql", "dbt", "context"}
    assert all(path.exists() for path in paths.values())
    assert json.loads(paths["audit"].read_text())["decision"] == "REVIEW"
    assert "<!doctype html>" in paths["html"].read_text()
