# DataHub ChangeGuard demo script

Primary artifact: `output/submission/datahub-changeguard-demo-v3.mp4`.

Observed length: 1 minute 51.23 seconds.

V3 presentation: 1920x1080 at 30 fps, local English narration, concise bilingual captions,
verified DataHub screenshots, and a headless recording of a real Agent Context Kit run plus
the generated report. V2 remains available as the static fallback.

## Scene 1 - Problem

Visual: product title and verified demo metrics.

Narration: "Schema changes often look safe in a pull request because reviewers cannot see the real downstream graph. DataHub ChangeGuard turns catalog evidence into an auditable release decision before production."

## Scene 2 - Catalog context

Visual: the real `commerce.orders` dataset, owner, review tag, and downstream count in DataHub.

Narration: "The demo starts with DataHub Core one point six and the official Agent Context Kit. ChangeGuard reads the commerce orders entity, five schema fields, ownership, tags, and bounded table plus field lineage. Two real downstream datasets depend on the source."

## Scene 3 - Proposal

Visual: current and proposed schema changes with the explicit rename requirement.

Narration: "The proposal renames order total to total amount, changes order I D from big int to var char, and relaxes currency nullability. ChangeGuard never guesses a rename. The mapping must be explicit, so generated compatibility code has an accountable source."

## Scene 4 - Live analysis

Visual: a real `changeguard run` recording followed by a scroll through the generated report.

Underlying command:

```bash
.venv/bin/changeguard run \
  --proposed examples/proposed_schema.json \
  --rename-hints examples/rename_hints.json \
  --source-relation commerce.orders_v2 \
  --output-dir output/live
```

Narration: "This is a real end to end run against the local catalog. The Agent Context Kit supplies versioned evidence, the deterministic analyzer returns block at one hundred out of one hundred, and the runtime emits an audit, report, compatibility S Q L, and D B T contract."

## Scene 5 - Generated artifacts

Visual: `compatibility_view.sql` and `dbt_schema.yml` excerpts.

Narration: "The compatibility view preserves order total while consumers migrate, and the D B T contract makes types and nullability reviewable. These are proposals only. ChangeGuard cannot deploy S Q L or modify warehouse data."

## Scene 6 - Controlled writeback

Visual: the verified DataHub tag and active `DATA_SCHEMA` incident.

Narration: "Catalog writeback is also controlled. Only a blocked audit with two explicit confirmation flags can add the review required tag and raise a data schema incident. The fingerprint makes retries idempotent, and a read back verifies the same active incident."

## Scene 7 - Architecture

Visual: Agent Context Kit to deterministic runtime to DataHub operational record.

Narration: "The official Agent Context Kit gathers evidence, deterministic code owns policy and code generation, and DataHub keeps the operational record. Fifteen tests pass, no model key is required, and every mutation remains behind an explicit human review boundary."
