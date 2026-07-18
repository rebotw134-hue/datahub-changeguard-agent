---
name: datahub-changeguard
description: Review a proposed dataset schema change with DataHub schema, ownership, tags, and downstream lineage before deployment; generate compatibility code and optionally record a confirmed incident.
---

# DataHub ChangeGuard

Use this skill when a user asks whether a schema migration is safe, requests impact analysis, or wants migration code grounded in DataHub metadata.

## Workflow

1. Identify the exact dataset URN and proposed schema file. Do not infer a production URN from a display name.
2. Read DataHub context first through the official Agent Context Kit tools `get_entities`, `list_schema_fields`, and `get_lineage`, with downstream direction and at most two hops. The `changeguard run` command invokes these same tools directly against its authenticated `DataHubClient`.
3. Preserve evidence as structured JSON: schema fields, owners, tags, downstream URNs, hop counts, and field lineage where available.
4. Run ChangeGuard's deterministic analyzer. Supply explicit rename hints; never guess a rename only because two field names look similar.
5. Review `audit.json`, `report.md`, `compatibility_view.sql`, and `dbt_schema.yml`. Treat generated code as a proposal.
6. If the decision is `BLOCK`, explain the affected fields and assets before suggesting writeback.
7. Invoke mutation tools or `changeguard run --writeback --confirm-writeback` only after the user explicitly confirms the catalog change. Verify the tag and incident by reading them back.

## Stop Rules

- Stop if the DataHub entity has no schema metadata.
- Do not claim a downstream field is affected when only table-level lineage exists; label it as potential impact.
- Do not deploy SQL, merge a PR, or alter a warehouse from this skill.
- Do not create duplicate incidents. ChangeGuard fingerprints each audit and reuses an active matching incident.
