from __future__ import annotations

from contextlib import AbstractContextManager
from typing import Any

from changeguard import datahub_gateway
from changeguard.datahub_gateway import DataHubGateway


class FakeDataHubContext(AbstractContextManager[object]):
    def __init__(self, client: object):
        self.client = client

    def __enter__(self) -> object:
        return self.client

    def __exit__(self, *args: object) -> None:
        return None


def test_inspect_dataset_uses_agent_context_kit(monkeypatch: Any) -> None:
    dataset_urn = "urn:li:dataset:(urn:li:dataPlatform:postgres,commerce.orders,PROD)"
    finance_urn = (
        "urn:li:dataset:(urn:li:dataPlatform:postgres,finance.daily_revenue,PROD)"
    )
    calls: list[tuple[str, str | None]] = []

    def get_entities(urns: list[str]) -> list[dict[str, Any]]:
        calls.append(("get_entities", None))
        assert urns == [dataset_urn]
        return [
            {
                "urn": dataset_urn,
                "properties": {"name": "commerce.orders"},
                "ownership": {
                    "owners": [{"owner": {"urn": "urn:li:corpuser:data-platform"}}]
                },
                "tags": {"tags": [{"tag": {"urn": "urn:li:tag:Tier1"}}]},
            }
        ]

    def list_schema_fields(urn: str, limit: int) -> dict[str, Any]:
        calls.append(("list_schema_fields", None))
        assert urn == dataset_urn
        assert limit == 100
        return {
            "fields": [
                {
                    "fieldPath": "order_id",
                    "nativeDataType": "BIGINT",
                    "nullable": False,
                },
                {
                    "fieldPath": "order_total",
                    "nativeDataType": "DECIMAL(12,2)",
                    "nullable": False,
                    "description": "Gross order amount",
                },
            ]
        }

    def get_lineage(
        *,
        urn: str,
        upstream: bool,
        max_hops: int,
        max_results: int,
        column: str | None = None,
    ) -> dict[str, Any]:
        calls.append(("get_lineage", column))
        assert urn == dataset_urn
        assert upstream is False
        assert max_hops == 2
        assert max_results == 200
        if column not in (None, "order_total"):
            return {"downstreams": {"searchResults": []}}
        return {
            "downstreams": {
                "searchResults": [
                    {
                        "entity": {
                            "urn": finance_urn,
                            "properties": {"name": "finance.daily_revenue"},
                        },
                        "degree": 1,
                    }
                ]
            }
        }

    monkeypatch.setattr(
        datahub_gateway,
        "_load_agent_context",
        lambda: (
            FakeDataHubContext,
            get_entities,
            list_schema_fields,
            get_lineage,
            "1.6.0.14",
        ),
    )
    gateway = object.__new__(DataHubGateway)
    gateway.server = "http://127.0.0.1:8080"
    gateway.client = object()

    schema, context = gateway.inspect_dataset(dataset_urn, max_hops=2)

    assert [column.name for column in schema.columns] == ["order_id", "order_total"]
    assert context.dataset_name == "commerce.orders"
    assert context.owners == ("urn:li:corpuser:data-platform",)
    assert context.tags == ("urn:li:tag:Tier1",)
    assert context.source == "datahub-agent-context:1.6.0.14:http://127.0.0.1:8080"
    assert len(context.downstreams) == 1
    assert context.downstreams[0].urn == finance_urn
    assert context.downstreams[0].fields == ("order_total",)
    assert calls == [
        ("get_entities", None),
        ("list_schema_fields", None),
        ("get_lineage", None),
        ("get_lineage", "order_id"),
        ("get_lineage", "order_total"),
    ]


def test_inspect_dataset_rejects_empty_agent_context_schema(monkeypatch: Any) -> None:
    dataset_urn = "urn:li:dataset:(urn:li:dataPlatform:postgres,empty,PROD)"

    monkeypatch.setattr(
        datahub_gateway,
        "_load_agent_context",
        lambda: (
            FakeDataHubContext,
            lambda urns: [{"urn": dataset_urn}],
            lambda urn, limit: {"fields": []},
            lambda **kwargs: {"downstreams": {"searchResults": []}},
            "1.6.0.14",
        ),
    )
    gateway = object.__new__(DataHubGateway)
    gateway.server = "http://127.0.0.1:8080"
    gateway.client = object()

    try:
        gateway.inspect_dataset(dataset_urn)
    except ValueError as exc:
        assert "no schemaMetadata" in str(exc)
    else:
        raise AssertionError("Expected an empty Agent Context Kit schema to be rejected")
