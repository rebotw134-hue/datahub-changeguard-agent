# DataHub Agent Context Kit Feedback

## Summary

Several Agent Context Kit MCP-tool docstrings pass `client.graph` to `DataHubContext`, while
the context manager requires a `DataHubClient`. Following the published example raises an
`AttributeError` before any tool call. The examples should use `DataHubContext(client)`.

## Reproduction

Tested on 2026-07-18 with:

- `datahub-agent-context==1.6.0.14`
- `acryl-datahub==1.6.0.6`
- Python 3.11

```python
from datahub_agent_context.context import DataHubContext, get_graph

with DataHubContext(client.graph):
    get_graph()
```

Observed result:

```text
AttributeError: 'DataHubGraph' object has no attribute '_graph'
```

The constructor and the working top-level example in `context.py` correctly expect the
client itself:

```python
with DataHubContext(client):
    ...
```

## Scope

The incorrect `DataHubContext(client.graph)` form appears in docstrings across entity,
schema-field, lineage, search, query, assertion, document, owner, tag, term, domain,
description, and structured-property tools. It is documentation-only; ChangeGuard uses the
correct client form and successfully exercised `get_entities`, `list_schema_fields`, and
`get_lineage` against DataHub Core 1.6.

## Suggested fix

Replace the incorrect docstring examples with `DataHubContext(client)` and add a documentation
test or a small context-manager unit test that asserts `get_graph()` returns `client._graph`.
This is suitable both as actionable hackathon feedback and as a focused upstream pull request.
