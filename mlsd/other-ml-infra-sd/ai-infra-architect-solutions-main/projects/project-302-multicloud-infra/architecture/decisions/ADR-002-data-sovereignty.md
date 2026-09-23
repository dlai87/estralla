# ADR-002: Data Sovereignty and Regional Distribution

**Status**: Accepted
**Date**: 2024-01-15
**Impact**: Critical - Legal/Regulatory Compliance

---

## Context

Operating in 15 countries with strict data residency laws:
- **GDPR** (EU): Data must stay in EU, €20M fines for violations
- **CCPA** (California): Specific data handling requirements
- **LGPD** (Brazil), PDPA (Singapore), PIPEDA (Canada): Regional requirements

**Problem**: Single-cloud AWS lacks presence in all required jurisdictions.

---

## Decision

**Regional Data Lakes with Strict Boundaries**:

| Region | Cloud | Data Allowed | Replication |
|--------|-------|--------------|-------------|
| **Americas** | AWS us-east-1 | US/CA/LATAM PII + global non-PII | Metadata only |
| **Europe** | GCP europe-west1 | EU PII + global non-PII | Metadata only |
| **APAC** | GCP asia-east1 | APAC PII + global non-PII | Metadata only |

**Data Classification**:
- **PII**: Never leaves region (no replication)
- **Training Data (non-PII)**: Can replicate globally
- **Models**: Replicate globally unless trained on regional PII
- **Metadata**: Global replication for discoverability

**Enforcement**:
```python
# Policy-as-Code (Open Policy Agent)
package data_residency

deny[msg] {
    input.data_classification == "pii"
    input.source_region != input.destination_region
    msg := "PII data cannot cross regional boundaries"
}
```

---

## Alternatives Considered

**Alternative 1**: Encrypt and replicate all data globally
- ❌ Rejected: Encryption doesn't satisfy GDPR data residency

**Alternative 2**: Single EU region for all EU customers
- ❌ Rejected: High latency for US customers, doesn't solve APAC

**Alternative 3**: On-premises in each country
- ❌ Rejected: 15 data centers too expensive ($50M+ capex)

---

## Consequences

✅ **Compliance**: 100% data residency compliance, zero GDPR fines
✅ **Latency**: Local data access <50ms (vs 200ms+ cross-region)
⚠️ **Complexity**: 3 separate data lakes, complex routing logic
⚠️ **Cost**: 3x storage costs, but necessary for compliance

**Validation**: Annual compliance audits, data flow analysis

---

**Approved By**: CTO, Legal, Chief Privacy Officer
