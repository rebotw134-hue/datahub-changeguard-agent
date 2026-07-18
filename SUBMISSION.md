# DataHub ChangeGuard - Devpost submission copy

## Primary category

Agents That Do Real Work

## Secondary fit

Metadata-Aware Code Generation & Development

## Tagline

Block risky schema changes with catalog-grounded evidence, compatibility code, and auditable DataHub writeback.

## Inspiration

A schema migration often looks safe in a pull request because reviewers cannot see every downstream dependency. Catalog lineage contains that context, but engineers still have to translate it into a release decision, remediation plan, and operational record.

## What it does

DataHub ChangeGuard reviews a proposed schema against the current DataHub schema, owner, tags, and downstream table and field lineage. It deterministically scores rename, removal, type, nullability, and required-column risks. It then generates a machine-readable audit, a human report, compatibility SQL, and a dbt contract.

By default the workflow is read-only. For a blocked proposal, an explicitly confirmed command adds a review-required tag and raises one `DATA_SCHEMA` incident. The audit fingerprint prevents duplicate active incidents.

## How we built it

- Python 3.11 and DataHub Agent Context Kit 1.6.0.14 for entity, schema, and lineage reads.
- The DataHub Python SDK for isolated demo seeding and confirmed entity updates.
- DataHub GraphQL for incident creation and read-after-write verification.
- A deterministic analyzer for reproducible safety decisions.
- A composable DataHub Agent Skill that gathers catalog evidence first, preserves uncertainty, requires explicit rename hints, and stops before deployment.
- Static HTML, Markdown, JSON, SQL, and YAML outputs so the result works in CI and human review without a paid model API.

## DataHub use

The verified demo calls the official Agent Context Kit tools `get_entities`, `list_schema_fields`, and `get_lineage` against DataHub Core 1.6. It reads schema metadata, ownership, tags, downstream lineage, and field lineage. After explicit confirmation, it writes back a review tag and a `DATA_SCHEMA` incident, then verifies both records through DataHub.

## Challenges

Table-level lineage alone can exaggerate impact. ChangeGuard therefore performs bounded field-lineage lookups and labels table-only evidence as potential impact. It also separates AI-assisted context gathering from deterministic enforcement so the same proposal produces the same result.

## Accomplishments

- Exact affected fields are connected to cataloged downstream datasets.
- Risky changes generate concrete compatibility SQL and a dbt contract instead of only a warning.
- Writeback is opt-in, auditable, and idempotent.
- The live evidence records the exact Agent Context Kit version and DataHub source in every audit.
- The full demo runs locally without an LLM key or DataHub Cloud-only features.

## What we learned

Metadata becomes much more actionable when every finding includes its evidence strength, affected assets, and a bounded remediation. Safe agent workflows also need a hard distinction between reasoning, code proposal, and external mutation.

## What's next

- Add CI adapters for GitHub and GitLab schema-change pull requests.
- Support DataHub MCP as an additional context transport where the deployment exposes it.
- Add configurable organization policies and incident resolution when a proposal is corrected.

## Submission checklist

- [x] Create the public repository shell: https://github.com/rebotw134-hue/datahub-changeguard-agent
- [x] Configure the project-local Git author and create the first commit.
- [ ] Push the code to the currently empty public repository.
- [ ] Confirm the repository displays the Apache 2.0 license.
- [x] Upload `output/submission/datahub-changeguard-demo-v2.mp4` to YouTube as unlisted: https://youtu.be/deXV5ECYfCE
- [ ] Change the V2 video from unlisted to public visibility as required by the official rules.
- [x] Build and verify the stronger V3 demo with a real Agent Context Kit run: `output/submission/datahub-changeguard-demo-v3.mp4`.
- [x] Prepare the V3 thumbnail and publish-ready YouTube/Devpost copy in `docs/PUBLISHING_COPY.md`.
- [ ] Upload V3 to YouTube and make the selected final video public.
- [ ] Add the video URL and screenshots to Devpost.
- [x] Create the Devpost account and complete the non-legal registration fields.
- [ ] Complete the Devpost image CAPTCHA required to create the project draft.
- [ ] Have the entrant confirm eligibility and rules, then submit before the displayed deadline.
