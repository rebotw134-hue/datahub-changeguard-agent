# Decisions

## D-001: Separate reasoning from enforcement

The AI assistant or Agent Skill gathers context and explains tradeoffs. A deterministic Python runtime owns schema parsing, scoring, evidence serialization, and code generation. This keeps demos reproducible and avoids requiring a paid model key.

## D-002: Default read-only behavior

Live analysis is read-only. Catalog mutation requires `--writeback --confirm-writeback`, and the MVP writes only a review tag and a `DATA_SCHEMA` incident for `BLOCK` decisions.

## D-003: Incidents instead of description edits

An incident is auditable, stateful, and designed for operational problems. Appending generated text to a dataset description would mix durable documentation with a temporary review result.

## D-004: No inferred renames

Renames require an explicit hint file. Similar field names are not enough evidence to generate compatibility SQL safely.

## D-005: Agent Context Kit for the live read boundary

The live `run` command uses DataHub's official Agent Context Kit tools for entity, schema,
and lineage reads. The deterministic analyzer remains separate so model behavior cannot alter
the enforcement result. SDK and GraphQL mutations remain behind explicit confirmation and
read-after-write verification.
