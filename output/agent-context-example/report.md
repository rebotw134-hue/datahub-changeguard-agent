# ChangeGuard schema review

- **Decision:** `BLOCK`
- **Risk score:** `100/100`
- **Dataset:** `urn:li:dataset:(urn:li:dataPlatform:postgres,commerce.orders,PROD)`
- **Owners:** urn:li:corpuser:data-platform@changeguard.demo
- **Cataloged downstream assets:** `2`
- **Evidence source:** `datahub-agent-context:1.6.0.14:http://127.0.0.1:8080`

## Findings

| Severity | Code | Field | Finding |
|---|---|---|---|
| CRITICAL | `COLUMN_RENAME` | `order_total` | Column 'order_total' is renamed to 'total_amount'. |
| CRITICAL | `TYPE_CHANGED` | `order_id` | Type changes from BIGINT to VARCHAR(36). |
| HIGH | `NULLABILITY_RELAXED` | `currency` | Column 'currency' can now emit null values. |

## Evidence and remediation

### 1. COLUMN_RENAME: `order_total`

- Severity: **CRITICAL**
- Evidence: DataHub reports 2 downstream asset(s) that may still reference 'order_total'.
- Remediation: Expose 'total_amount' as 'order_total' through a compatibility view, update consumers, then remove the alias in a later version.
- Affected assets: `urn:li:dataset:(urn:li:dataPlatform:postgres,finance.daily_revenue,PROD)`, `urn:li:dataset:(urn:li:dataPlatform:postgres,growth.customer_ltv,PROD)`

### 2. TYPE_CHANGED: `order_id`

- Severity: **CRITICAL**
- Evidence: The change is not a recognized safe widening; 1 downstream asset(s) may need updates.
- Remediation: Introduce a new typed column or compatibility cast and migrate consumers first.
- Affected assets: `urn:li:dataset:(urn:li:dataPlatform:postgres,finance.daily_revenue,PROD)`

### 3. NULLABILITY_RELAXED: `currency`

- Severity: **HIGH**
- Evidence: Non-null consumers include up to 2 cataloged downstream asset(s).
- Remediation: Backfill a default or update downstream null handling before release.
- Affected assets: `urn:li:dataset:(urn:li:dataPlatform:postgres,finance.daily_revenue,PROD)`, `urn:li:dataset:(urn:li:dataPlatform:postgres,growth.customer_ltv,PROD)`

## Generated proposals

- Compatibility SQL: `compatibility_view.sql`
- dbt contract: `dbt_schema.yml`
- Machine-readable audit: `audit.json`

## Decision boundary

ChangeGuard does not deploy generated code. A human or CI policy must review the evidence, run consumer tests, and approve the release. DataHub writeback is an explicit, separately confirmed action.
