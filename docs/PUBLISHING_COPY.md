# Publishing Copy

## YouTube

### Title

DataHub ChangeGuard: Agent Context Kit Schema Safety Agent | Live Demo

### Description

DataHub ChangeGuard blocks risky schema changes before production using catalog-grounded
evidence from DataHub's official Agent Context Kit.

The live demo reads entity metadata, five schema fields, ownership, tags, table lineage, and
field lineage from DataHub Core 1.6. A deterministic policy engine returns `BLOCK 100/100`,
generates compatibility SQL and a dbt contract, and keeps DataHub writeback behind two
explicit confirmation flags.

Repository: https://github.com/rebotw134-hue/datahub-changeguard-agent

Chapters:

- 00:00 Problem and result
- 00:12 DataHub catalog context
- 00:28 Proposed schema change
- 00:44 Real Agent Context Kit run
- 01:04 Generated remediation
- 01:18 Controlled DataHub writeback
- 01:34 Architecture and safety boundary

Built for Build with DataHub: The Agent Hackathon. Apache License 2.0. No warehouse changes,
automatic SQL deployment, external music, or stock footage are used in the demo.

### Tags

DataHub, Agent Context Kit, data lineage, schema migration, data engineering, AI agent,
metadata, dbt, data contracts, DevOps

### Thumbnail

`output/submission/datahub-changeguard-demo-v3-thumbnail.png`

## Devpost

- Project name: DataHub ChangeGuard
- Tagline: Block risky schema changes with catalog-grounded evidence, compatibility code, and auditable DataHub writeback.
- Primary track: Agents That Do Real Work
- Secondary fit: Metadata-Aware Code Generation & Development
- Repository: https://github.com/rebotw134-hue/datahub-changeguard-agent
- Detailed answers: `SUBMISSION.md`
- Judge path: `docs/JUDGE_GUIDE.md`
- Primary image: `output/submission/datahub-changeguard-demo-v3-thumbnail.png`
- Additional image: `output/submission/datahub-changeguard-demo-v3-contact-sheet.png`
