from __future__ import annotations

import hashlib
import json
import warnings
from collections import defaultdict
from dataclasses import dataclass
from functools import lru_cache
from importlib.metadata import version
from typing import Any

from changeguard.models import (
    AnalysisResult,
    ColumnSchema,
    DatasetContext,
    DatasetSchema,
    DownstreamAsset,
)

REVIEW_TAG_ID = "changeguard-review-required"
FIELD_LINEAGE_SCAN_LIMIT = 100


@lru_cache(maxsize=1)
def _load_sdk() -> tuple[type[Any], type[Any], type[Any]]:
    from datahub.errors import ExperimentalWarning

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ExperimentalWarning)
        from datahub.sdk import DataHubClient, Dataset, Tag

    return DataHubClient, Dataset, Tag


@lru_cache(maxsize=1)
def _load_agent_context() -> tuple[type[Any], Any, Any, Any, str]:
    from datahub.errors import ExperimentalWarning

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ExperimentalWarning)
        from datahub_agent_context.context import DataHubContext
        from datahub_agent_context.mcp_tools.entities import get_entities, list_schema_fields
        from datahub_agent_context.mcp_tools.lineage import get_lineage

    return (
        DataHubContext,
        get_entities,
        list_schema_fields,
        get_lineage,
        version("datahub-agent-context"),
    )


@dataclass(frozen=True)
class WritebackResult:
    tag_urn: str
    incident_urn: str
    created_incident: bool
    fingerprint: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "tag_urn": self.tag_urn,
            "incident_urn": self.incident_urn,
            "created_incident": self.created_incident,
            "fingerprint": self.fingerprint,
        }


class DataHubGateway:
    def __init__(self, server: str, token: str | None = None, timeout_sec: float = 20.0):
        from datahub.ingestion.graph.client import DatahubClientConfig, DataHubGraph

        DataHubClient, _, _ = _load_sdk()
        config = DatahubClientConfig(
            server=server.rstrip("/"),
            token=token or None,
            timeout_sec=timeout_sec,
            retry_max_times=2,
        )
        self.server = server.rstrip("/")
        self.graph = DataHubGraph(config)
        self.client = DataHubClient(graph=self.graph)

    def inspect_dataset(
        self, dataset_urn: str, max_hops: int = 2
    ) -> tuple[DatasetSchema, DatasetContext]:
        from datahub.metadata.urns import DatasetUrn

        DataHubContext, get_entities, list_schema_fields, get_lineage, kit_version = (
            _load_agent_context()
        )
        with DataHubContext(self.client):
            entities = get_entities([dataset_urn])
            schema = list_schema_fields(dataset_urn, limit=FIELD_LINEAGE_SCAN_LIMIT)
            table_lineage = get_lineage(
                urn=dataset_urn,
                upstream=False,
                max_hops=max_hops,
                max_results=200,
            )

            fields = schema.get("fields") or []
            if not fields:
                raise ValueError(f"DataHub dataset has no schemaMetadata aspect: {dataset_urn}")
            if not entities or entities[0].get("error"):
                detail = entities[0].get("error") if entities else "empty response"
                raise ValueError(f"Agent Context Kit could not read {dataset_urn}: {detail}")
            entity = entities[0]

            current = DatasetSchema(
                dataset_urn=dataset_urn,
                columns=tuple(
                    ColumnSchema(
                        name=str(field["fieldPath"]),
                        native_type=str(field.get("nativeDataType") or "UNKNOWN"),
                        nullable=bool(field.get("nullable", True)),
                        description=field.get("description"),
                    )
                    for field in fields
                ),
            )

            lineage_by_urn: dict[str, tuple[str, int]] = {}
            source_fields_by_downstream: dict[str, set[str]] = defaultdict(set)

            def collect_lineage(payload: dict[str, Any], source_field: str | None = None) -> None:
                results = (payload.get("downstreams") or {}).get("searchResults") or []
                for item in results:
                    downstream = item.get("entity") or {}
                    urn = downstream.get("urn")
                    if not urn:
                        continue
                    properties = downstream.get("properties") or {}
                    name = properties.get("name") or downstream.get("name")
                    if not name:
                        name = DatasetUrn.from_string(urn).name
                    try:
                        hops = int(item.get("degree") or 1)
                    except (TypeError, ValueError):
                        hops = 1
                    previous = lineage_by_urn.get(urn)
                    if previous is None or hops < previous[1]:
                        lineage_by_urn[urn] = (str(name), hops)
                    if source_field:
                        source_fields_by_downstream[urn].add(source_field)

            collect_lineage(table_lineage)
            for column in current.columns[:FIELD_LINEAGE_SCAN_LIMIT]:
                field_lineage = get_lineage(
                    urn=dataset_urn,
                    column=column.name,
                    upstream=False,
                    max_hops=max_hops,
                    max_results=200,
                )
                collect_lineage(field_lineage, source_field=column.name)

        downstreams = tuple(
            DownstreamAsset(
                urn=urn,
                name=name,
                hops=hops,
                fields=tuple(sorted(source_fields_by_downstream[urn])),
            )
            for urn, (name, hops) in sorted(
                lineage_by_urn.items(), key=lambda value: (value[1][1], value[0])
            )
        )
        properties = entity.get("properties") or {}
        owners = tuple(
            owner["owner"]["urn"]
            for owner in (entity.get("ownership") or {}).get("owners") or []
            if (owner.get("owner") or {}).get("urn")
        )
        tags = tuple(
            tag["tag"]["urn"]
            for tag in (entity.get("tags") or {}).get("tags") or []
            if (tag.get("tag") or {}).get("urn")
        )
        context = DatasetContext(
            dataset_urn=dataset_urn,
            dataset_name=(
                str(properties["name"])
                if properties.get("name")
                else DatasetUrn.from_string(dataset_urn).name
            ),
            owners=owners,
            tags=tags,
            downstreams=downstreams,
            source=f"datahub-agent-context:{kit_version}:{self.server}",
        )
        return current, context

    def seed_demo(self) -> dict[str, str]:
        from datahub.metadata.urns import DatasetUrn

        _, Dataset, _ = _load_sdk()
        source = Dataset(
            platform="postgres",
            name="commerce.orders",
            description="Canonical order facts used by finance and growth models.",
            owners=["data-platform@changeguard.demo"],
            schema=[
                ("order_id", "BIGINT", "Stable order identifier"),
                ("customer_id", "BIGINT", "Customer identifier"),
                ("order_total", "DECIMAL(12,2)", "Gross order amount"),
                ("currency", "VARCHAR(3)", "ISO currency code"),
                ("created_at", "TIMESTAMP", "Order creation timestamp"),
            ],
        )
        finance = Dataset(
            platform="postgres",
            name="finance.daily_revenue",
            description="Daily revenue aggregate used for finance close.",
            owners=["finance-analytics@changeguard.demo"],
            schema=[
                ("revenue_date", "DATE"),
                ("gross_revenue", "DECIMAL(18,2)"),
                ("order_count", "BIGINT"),
            ],
        )
        finance.set_upstreams(
            {
                source.urn: {
                    "gross_revenue": ["order_total"],
                    "order_count": ["order_id"],
                }
            }
        )
        growth = Dataset(
            platform="postgres",
            name="growth.customer_ltv",
            description="Customer lifetime value feature table.",
            owners=["growth-data@changeguard.demo"],
            schema=[
                ("customer_id", "BIGINT"),
                ("lifetime_value", "DECIMAL(18,2)"),
                ("last_order_at", "TIMESTAMP"),
            ],
        )
        growth.set_upstreams(
            {
                source.urn: {
                    "customer_id": ["customer_id"],
                    "lifetime_value": ["order_total"],
                    "last_order_at": ["created_at"],
                }
            }
        )

        for dataset in (source, finance, growth):
            self.client.entities.upsert(dataset)

        return {
            "source": str(source.urn),
            "finance": str(finance.urn),
            "growth": str(growth.urn),
            "platform": str(DatasetUrn.from_string(str(source.urn)).platform),
        }

    def _active_incidents(self, dataset_urn: str) -> list[dict[str, Any]]:
        query = f"""
        query {{
          dataset(urn: {json.dumps(dataset_urn)}) {{
            incidents(state: ACTIVE, start: 0, count: 100) {{
              incidents {{ urn title description }}
            }}
          }}
        }}
        """
        response = self.graph.execute_graphql(query=query)
        return ((response.get("dataset") or {}).get("incidents") or {}).get("incidents") or []

    def writeback(self, result: AnalysisResult, confirm: bool = False) -> WritebackResult:
        if not confirm:
            raise PermissionError("DataHub writeback requires explicit confirmation")
        if result.decision.value != "BLOCK":
            raise ValueError("Writeback is limited to BLOCK decisions in the MVP")

        from datahub.metadata.urns import DatasetUrn, TagUrn

        _, _, Tag = _load_sdk()
        canonical = json.dumps(result.to_dict(), sort_keys=True, separators=(",", ":"))
        fingerprint = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:12]
        title = f"ChangeGuard blocked schema change [{fingerprint}]"

        tag = Tag(
            name=REVIEW_TAG_ID,
            display_name="ChangeGuard: Review Required",
            description="Applied when ChangeGuard finds a high-impact schema proposal.",
            color="#B42318",
        )
        if not self.graph.exists(str(TagUrn(REVIEW_TAG_ID))):
            self.client.entities.upsert(tag)
        dataset = self.client.entities.get(DatasetUrn.from_string(result.dataset_urn))
        dataset.add_tag(TagUrn(REVIEW_TAG_ID))
        self.client.entities.update(dataset)

        for incident in self._active_incidents(result.dataset_urn):
            if incident.get("title") == title:
                return WritebackResult(
                    tag_urn=str(TagUrn(REVIEW_TAG_ID)),
                    incident_urn=str(incident["urn"]),
                    created_incident=False,
                    fingerprint=fingerprint,
                )

        top_findings = "; ".join(
            f"{finding.code}:{finding.field}" for finding in result.findings[:5]
        )
        description = (
            f"Automated pre-deployment review blocked this proposal at risk "
            f"{result.risk_score}/100. Findings: {top_findings}. "
            f"Evidence source: {result.evidence_source}. Review generated artifacts before rollout."
        )
        mutation = f"""
        mutation {{
          raiseIncident(input: {{
            resourceUrn: {json.dumps(result.dataset_urn)}
            type: DATA_SCHEMA
            title: {json.dumps(title)}
            description: {json.dumps(description)}
          }})
        }}
        """
        response = self.graph.execute_graphql(query=mutation)
        incident_urn = response.get("raiseIncident")
        if not incident_urn:
            raise RuntimeError(f"DataHub did not return an incident URN: {response}")
        return WritebackResult(
            tag_urn=str(TagUrn(REVIEW_TAG_ID)),
            incident_urn=str(incident_urn),
            created_incident=True,
            fingerprint=fingerprint,
        )

    def verify_writeback(self, dataset_urn: str) -> dict[str, Any]:
        from datahub.metadata.schema_classes import GlobalTagsClass

        tags = self.graph.get_aspect(dataset_urn, GlobalTagsClass)
        tag_urns = [item.tag for item in tags.tags] if tags else []
        incidents = self._active_incidents(dataset_urn)
        return {
            "dataset_urn": dataset_urn,
            "review_tag_present": f"urn:li:tag:{REVIEW_TAG_ID}" in tag_urns,
            "tags": tag_urns,
            "active_changeguard_incidents": [
                incident
                for incident in incidents
                if str(incident.get("title", "")).startswith("ChangeGuard blocked schema change")
            ],
        }
