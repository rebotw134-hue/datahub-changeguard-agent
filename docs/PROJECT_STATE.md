# Project State

## Current scope

ChangeGuard reviews one proposed dataset schema against current DataHub metadata. It produces a deterministic risk decision, evidence report, compatibility-view proposal, dbt contract, and optional DataHub writeback.

## Implemented

- Schema diff rules for rename, drop, type, nullability, and required-column changes.
- Downstream impact weighting using DataHub table and field lineage.
- Offline fixture mode and live DataHub mode.
- Official Agent Context Kit reads through `get_entities`, `list_schema_fields`, and `get_lineage`.
- Explicitly confirmed tag and `DATA_SCHEMA` incident writeback with duplicate prevention.
- Machine-readable, Markdown, HTML, SQL, and dbt outputs.
- Agent Skill instructions for MCP-based context collection.

## Verified locally

- Offline example generation and deterministic test suite.
- Live schema, owner, tag, table-lineage, and field-lineage reads from DataHub Core 1.6.
- Live Agent Context Kit 1.6.0.14 provenance recorded in the generated context and audit.
- Explicit tag and `DATA_SCHEMA` incident writeback, read-after-write verification, and duplicate prevention.
- Desktop and mobile HTML report rendering.
- A 1080p, under-two-minute V3 demo with a real Agent Context Kit run, generated report
  walkthrough, local English narration, bilingual captions, and normalized audio.
- The 1:47 V2 demo passed YouTube's copyright check and is available as an unlisted video at
  `https://youtu.be/deXV5ECYfCE`.

## Not in scope for v0.1

- Automatic warehouse changes or SQL deployment.
- Automatic GitHub pull request creation.
- LLM API dependency.
- DataHub Cloud-only contracts or assertions.

## Remaining submission work

1. Push the prepared commits to the empty public GitHub repository and confirm Apache 2.0 is detected.
2. Upload the stronger V3 demo and make the selected final video public, as required by the official rules.
3. Complete the Devpost CAPTCHA, then add the video URL and final screenshots to the project draft.
4. Have the entrant confirm eligibility and the current rules, then submit the completed Devpost entry before the deadline.
