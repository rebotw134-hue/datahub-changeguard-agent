# Judge Guide

## The 20-second version

DataHub ChangeGuard is a pre-deployment safety gate for schema changes. It uses DataHub's
official Agent Context Kit to discover the current schema, owners, tags, downstream tables,
and field lineage. A deterministic engine then blocks unsafe proposals, generates bounded
remediation code, and can record a confirmed tag and `DATA_SCHEMA` incident back in DataHub.

## Why it is not a built-in DataHub feature

DataHub stores the context and exposes impact signals. ChangeGuard evaluates a proposed
schema that has not reached production yet, combines explicit rename intent with field-level
lineage, produces a reproducible release decision, generates compatibility SQL and a dbt
contract, and records the review result back into the graph. It composes DataHub capabilities
into a guarded deployment workflow instead of recreating the catalog.

## Fast evidence path

1. `output/agent-context-example/datahub_context.json` proves the official Agent Context Kit version, source dataset, owners, tags, and field-level downstream impact.
2. `output/agent-context-example/audit.json` contains the deterministic `BLOCK 100/100` decision and evidence for every finding.
3. `output/agent-context-example/report.html` is the human review package.
4. `output/agent-context-example/compatibility_view.sql` and `dbt_schema.yml` are concrete remediation artifacts.
5. `docs/EVIDENCE.md` records live commands, writeback verification, media checks, and hashes.

## Judging criteria map

| Criterion | Evidence |
| --- | --- |
| Use of DataHub | Agent Context Kit entity/schema/lineage reads; DataHub owner and tag context; confirmed tag and incident writeback |
| Technical execution | Deterministic analyzer, explicit mutation gates, field-lineage confidence, idempotent incident handling, automated tests and CI |
| Originality | Reviews a not-yet-deployed schema and turns graph context into a release gate plus mergeable remediation code |
| Real-world usefulness | Prevents breaking schema migrations before finance, growth, or ML consumers fail |
| Submission quality | English README, under-two-minute demo with a real live run, checked-in sample outputs, one-command offline reproduction |
| Open-source bonus | Reproducible Agent Context Kit documentation defect and proposed upstream correction in `docs/DATAHUB_FEEDBACK.md` |

## Safety boundary

ChangeGuard never deploys SQL or changes a warehouse. Live reads are the default. DataHub
mutation requires both `--writeback` and `--confirm-writeback`, applies only to a `BLOCK`
decision, and is verified by reading the tag and incident back.
