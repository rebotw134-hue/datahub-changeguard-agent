# ChangeGuard Agent Engineering Rules

## Scope

- Keep the project focused on pre-deployment schema-change impact analysis for DataHub.
- The default path is read-only. DataHub mutations require both `--writeback` and `--confirm-writeback`.
- Never commit DataHub tokens, browser state, generated credentials, or `.env` files.
- Generated SQL and dbt files are proposals for review, not automatically deployed code.

## Runtime

- Python: 3.11+
- Install: `python -m pip install -e '.[dev]'`
- Tests: `python -m pytest`
- Lint: `python -m ruff check .`
- Offline demo: `changeguard analyze --current examples/current_schema.json --proposed examples/proposed_schema.json --context examples/context.json --rename-hints examples/rename_hints.json --source-relation commerce.orders_v2 --output-dir output/example`

## Done Standard

- Unit tests and lint pass.
- Offline demo emits deterministic JSON, Markdown, HTML, SQL, and dbt artifacts.
- Live verification, when requested, uses a local DataHub instance and records exact evidence in `docs/EVIDENCE.md`.
- Writeback is verified by reading the created tag and incident back from DataHub.
