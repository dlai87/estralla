# Platform API — Reference Implementation

**Scope**: The HTTP + gRPC contract for the Enterprise MLOps Platform. This is the only supported integration point for tenant tooling, CI systems, and the platform UI.

**Owner**: Platform Engineering (`#mlops-platform-api`)
**Status**: v2 in production; v1 deprecated, sunset 2026-09-01

---

## 1. Contract surface

The platform exposes two co-equal surfaces backed by the **same** internal services:

- **REST + JSON** over HTTPS at `https://api.acme.io/mlops/v2/...` — primary surface for humans, CI, browsers, and the SDK fallback path
- **gRPC** at `mlops.acme.io:443` (HTTP/2 over TLS, gRPC-Web supported for browsers) — primary surface for the high-volume SDK and internal service-to-service calls

Both surfaces are generated from a single source of truth:

- gRPC: `proto/mlops/v2/*.proto` (Buf-managed module `buf.build/acme/mlops`)
- REST: an OpenAPI 3.1 document generated from the protos using `grpc-gateway` + `protoc-gen-openapiv2` and hand-augmented for REST-only concerns (file upload form parts, paging headers, idempotency-key handling)

We do not edit the OpenAPI document by hand for fields. We do edit it for response shaping when REST conventions diverge from proto (e.g., pagination tokens become `Link` headers).

### 1.1 Sample protobuf

```proto
syntax = "proto3";
package acme.mlops.v2;

import "google/api/annotations.proto";
import "google/protobuf/timestamp.proto";

service Registry {
  rpc RegisterModel(RegisterModelRequest) returns (Model) {
    option (google.api.http) = {
      post: "/mlops/v2/tenants/{tenant_id}/models"
      body: "*"
    };
  }
  rpc PromoteModel(PromoteModelRequest) returns (Promotion) {
    option (google.api.http) = {
      post: "/mlops/v2/tenants/{tenant_id}/models/{model_id}/promotions"
      body: "*"
    };
  }
  rpc ListModels(ListModelsRequest) returns (ListModelsResponse) {
    option (google.api.http) = {
      get: "/mlops/v2/tenants/{tenant_id}/models"
    };
  }
}

message Model {
  string id = 1;
  string tenant_id = 2;
  string name = 3;
  string framework = 4;        // pytorch | tensorflow | onnx | xgboost | ...
  string storage_uri = 5;      // s3://...
  uint64 min_memory_bytes = 6;
  google.protobuf.Timestamp created_at = 7;
  Lifecycle lifecycle = 8;
  map<string, string> labels = 9;
}

enum Lifecycle { LIFECYCLE_UNSPECIFIED = 0; STAGING = 1; PRODUCTION = 2; ARCHIVED = 3; }
```

### 1.2 Sample OpenAPI fragment

```yaml
paths:
  /mlops/v2/tenants/{tenant_id}/models:
    post:
      operationId: registerModel
      parameters:
        - in: path
          name: tenant_id
          required: true
          schema: { type: string, pattern: '^[a-z][a-z0-9-]{2,30}$' }
        - in: header
          name: Idempotency-Key
          required: true
          schema: { type: string, format: uuid }
      requestBody:
        required: true
        content:
          application/json:
            schema: { $ref: '#/components/schemas/RegisterModelRequest' }
      responses:
        '200':
          description: Model registered (idempotent replay)
          content: { application/json: { schema: { $ref: '#/components/schemas/Model' }}}
        '201':
          description: Model created
        '409':
          description: Idempotency-Key reused with a different body
```

---

## 2. Versioning

### 2.1 Major versions

- Major version lives in the URL (`/mlops/v2/...`) and in the proto package (`acme.mlops.v2`)
- Two adjacent majors run in parallel for **at least 12 months** after the newer version reaches GA
- Sunset announced in changelog and via the `Deprecation` and `Sunset` response headers ([RFC 9745](https://www.rfc-editor.org/rfc/rfc9745.html))

### 2.2 Minor and patch

- **Additive only** within a major: new fields, new endpoints, new enum values
- New required request fields are **never** added within a major; that's a breaking change → new major
- Removed fields: tombstoned with a 6-month deprecation header and runtime warning, then deleted in the next major
- Enum additions are safe; clients must treat unknown values as `*_UNSPECIFIED`

### 2.3 Capability discovery

`GET /mlops/v2/capabilities` returns the server's supported features with semantic versions, so SDKs can degrade gracefully:

```json
{
  "api_version": "2.14.3",
  "capabilities": {
    "model_registry": "1.4.0",
    "training": "2.0.1",
    "feature_store": "1.7.0",
    "kserve_runtime": "0.13.1",
    "audit_export": "1.1.0"
  },
  "deprecations": [
    { "field": "Model.legacy_path", "sunset_at": "2026-09-01T00:00:00Z" }
  ]
}
```

---

## 3. Authentication

### 3.1 Tenants and users

- Human users authenticate via Okta OIDC against the platform's Okta tenant. The platform exchanges the OIDC token for a short-lived platform JWT (15-minute TTL) via the `tokens` endpoint.
- Machine clients (CI, SDK in service contexts) authenticate via mTLS using a SPIFFE identity issued by SPIRE, **or** via an OIDC workload identity (GitHub Actions OIDC, GitLab OIDC, EKS IRSA) exchanged at `/tokens/exchange` for the same platform JWT.

### 3.2 Token shape

Platform JWTs are RS256-signed, with the following claims:

```json
{
  "iss": "https://api.acme.io/mlops",
  "aud": "mlops-platform",
  "sub": "spiffe://acme.io/sa/tenant-acme/builder",
  "tenant": "acme",
  "scopes": ["models:read","models:write","training:submit"],
  "exp": 1715000000,
  "iat": 1714999100,
  "jti": "01J7Z..."
}
```

JTI is logged in the audit pipeline and can be revoked at the gateway (Redis-backed revocation list with 15-minute eviction).

### 3.3 Token endpoints

```
POST /mlops/v2/tokens                  # OIDC -> platform JWT
POST /mlops/v2/tokens/exchange         # workload identity -> platform JWT
POST /mlops/v2/tokens/revoke           # revoke JTI (admin or self)
GET  /mlops/v2/tokens/jwks.json        # JWKS for offline validation
```

---

## 4. Authorization — RBAC scopes

### 4.1 Scope grammar

`{resource}:{action}` where resource is one of `models`, `experiments`, `features`, `training`, `serving`, `audit`, `quotas`, `secrets`, `tenants`, `platform`. Action is one of `read`, `write`, `delete`, `submit`, `promote`, `approve`, `admin`.

Examples: `models:read`, `models:promote`, `training:submit`, `audit:read`, `platform:admin` (super-user; only platform SRE primary holds this).

### 4.2 Default role mapping

| Role | Scopes |
|---|---|
| `tenant-viewer` | `models:read`, `experiments:read`, `features:read`, `training:read`, `serving:read`, `audit:read` (own tenant) |
| `tenant-builder` | viewer + `models:write`, `experiments:write`, `features:write`, `training:submit` |
| `tenant-operator` | builder + `serving:write`, `serving:promote`, `models:promote` (staging only) |
| `tenant-owner` | operator + `models:promote` (production), `quotas:read`, `secrets:read` |
| `tenant-admin` | owner + `secrets:write`, `tenants:write` (members only) |
| `platform-sre` | all scopes on all tenants except `platform:admin` |
| `platform-admin` | all scopes; break-glass only |

Roles are assigned in the platform's identity store (backed by Okta groups) and synced into the gateway every 5 minutes.

### 4.3 Tenant isolation

Every request must carry a tenant in the URL path or the request body. The gateway rejects (`403 cross-tenant`) any call where:

- `token.tenant != path.tenant` **and** `token.tenant != "_platform_"`
- `token.scopes` does not include the required scope for the method

This rule is enforced again at the service layer (defense in depth) and tested by the cross-tenant integration suite on every release (see `runbooks/troubleshooting.md` §15).

---

## 5. Rate limiting and quotas

### 5.1 Layers

1. **Edge** (Envoy at the ingress): per source-IP burst protection (1k req/min default), DDoS-grade
2. **Per token**: 600 req/min per platform JWT for read; 60 req/min for write; 5 req/min for promote/delete
3. **Per tenant**: 10,000 req/min aggregate across all tokens
4. **Per endpoint class**: special limits for expensive endpoints (`/training/submit`: 30 req/min/tenant; `/audit/export`: 5 req/min/tenant)

### 5.2 Headers (RateLimit, RFC 9331)

```
RateLimit-Limit: 600
RateLimit-Remaining: 412
RateLimit-Reset: 17
RateLimit-Policy: 600;w=60
```

429 responses include `Retry-After`.

### 5.3 Tenant tier overrides

Tier-1 tenants can request a 5× write multiplier with finance approval. Overrides live in `infra-gitops/tenants/${SLUG}/rate-limits.yaml`.

---

## 6. Idempotency

### 6.1 Header

`Idempotency-Key: <UUIDv4>` required on all `POST`, `PUT`, `PATCH`, `DELETE`. Keys are scoped per (tenant, endpoint).

### 6.2 Server behavior

- First call with a key: process, store request hash + response for 24h
- Replay with the same key + same request: return the stored response (200/201/etc with original status), set `Idempotent-Replayed: true`
- Replay with the same key + different request body: return `409 Conflict` with `code=IDEMPOTENCY_KEY_REUSED`

### 6.3 Why mandatory

Tenants frequently retry (CI runners, flaky networks). Without idempotency, retries create duplicate model versions, duplicate training jobs, double promotions — every kind of mess. The platform refuses to make this optional.

---

## 7. Pagination, filtering, and sort

- Pagination via `page_token` + `page_size`, opaque base64-encoded cursors. Servers cap `page_size` at 100; default 25.
- Filtering via Google-style filter language: `filter=framework="pytorch" AND created_at>="2026-01-01"`.
- Sorting via `order_by=created_at desc,name asc`.
- Listing responses include `next_page_token` (empty when last page) and a `total_size` (approximate; cheap COUNT) for tenants who need progress.

REST equivalent uses `Link: rel="next"` header alongside the body field.

---

## 8. Errors

### 8.1 Shape

REST:

```json
{
  "error": {
    "code": "QUOTA_EXCEEDED",
    "message": "tenant 'acme' has reached its GPU quota (16/16)",
    "details": [
      { "@type": "ResourceInfo", "resource_type": "ResourceQuota", "resource_name": "tenant-acme/tenant-quota" },
      { "@type": "RetryInfo", "retry_delay": "300s" }
    ],
    "request_id": "01J7Z2QV1B...",
    "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736"
  }
}
```

gRPC: standard `google.rpc.Status` with the same `details` payload.

### 8.2 Code map

| gRPC code | HTTP | When |
|---|---|---|
| `INVALID_ARGUMENT` | 400 | Validation failed |
| `UNAUTHENTICATED` | 401 | Missing/invalid token |
| `PERMISSION_DENIED` | 403 | Scope missing or cross-tenant |
| `NOT_FOUND` | 404 | Resource does not exist or invisible to caller |
| `ALREADY_EXISTS` | 409 | Duplicate (incl. idempotency conflict) |
| `RESOURCE_EXHAUSTED` | 429 | Rate limit or quota |
| `FAILED_PRECONDITION` | 412 | Lifecycle violation (e.g., promote without approval) |
| `UNAVAILABLE` | 503 | Backend dependency degraded; safe to retry |
| `INTERNAL` | 500 | Bug; not safe to retry blindly |

`request_id` and `trace_id` are returned on **every** error and **every** success. Tenant support tickets must include `request_id`.

---

## 9. Tenant isolation guarantees

Beyond authorization, the platform makes these data-plane guarantees:

- All multi-tenant indexes carry `tenant_id` as a primary key prefix; queries are forced to filter by `tenant_id` at the persistence layer
- MLflow runs live in tenant-specific schemas (Postgres row-level security as belt-and-suspenders)
- Object storage paths follow `s3://acme-models/${TENANT}/...` and IRSA policies grant access only to the matching prefix
- Feast feature views are scoped to a tenant project; the registry rejects cross-project references
- Inference services run in tenant namespaces with Calico/Cilium network policies blocking pod-to-pod traffic across tenant namespaces
- Audit log entries always include `actor_tenant` and `target_tenant`; cross-tenant rows are flagged for review (zero-tolerance dashboard)

---

## 10. Audit logging

Every state-changing request produces one audit event written synchronously **before** the response returns. Event shape:

```json
{
  "ts": "2026-05-24T13:42:11.193Z",
  "request_id": "01J7Z2QV1B...",
  "trace_id": "4bf92f...",
  "actor": {
    "tenant": "acme",
    "principal": "spiffe://acme.io/sa/tenant-acme/ci",
    "subject_email": "alex@acme.io",
    "scopes_used": ["models:write"]
  },
  "action": "RegisterModel",
  "resource": {
    "tenant": "acme",
    "type": "model",
    "name": "recsys/recsys-v3",
    "id": "01J7Z2QV1B"
  },
  "outcome": "success",
  "duration_ms": 142,
  "request_meta": {
    "ip": "203.0.113.5",
    "user_agent": "mlops-sdk-python/2.14.3"
  }
}
```

Sinks:

- Real-time to Kinesis → S3 (`s3://acme-mlops-audit/${YYYY}/${MM}/${DD}/`) with S3 Object Lock compliance mode, 7-year retention
- Real-time to Snowflake (`mlops_audit.events`) for queryable evidence
- Real-time to Datadog logs for live monitoring

A request that cannot write its audit event returns `503` and is retried by the client. We choose availability *of audit* over availability of the API.

---

## 11. SDK generation

### 11.1 Source

- gRPC stubs and OpenAPI document are the source of truth
- We publish official SDKs in:
  - **Python** (`pip install mlops-sdk`) — used by 90% of data scientists; supports both async and sync
  - **Go** (`go get acme.io/mlops/sdk`) — used by services calling the platform from within infrastructure
  - **TypeScript** (`@acme/mlops-sdk`) — UI and Node-side automation

### 11.2 Generation pipeline

For each SDK:

1. CI consumes the published Buf module `buf.build/acme/mlops` and the OpenAPI artifact from the previous step
2. Code generator runs (`buf generate` + language-specific extensions for ergonomic wrappers)
3. Auto-generated PR opens against the SDK repo with version bump
4. SDK CI runs contract tests against the **previous** server version (to detect breakages) and the **current** server version
5. On green CI, SDK is released to its registry under a version that aligns with the server major (e.g., server v2.14.3 → SDK 2.14.x)

### 11.3 Ergonomic layer

We hand-write a thin layer above the generated stubs to give Pythonic and idiomatic Go shapes. Example (Python):

```python
from mlops_sdk import Client

c = Client.from_env()  # picks up MLOPS_TOKEN, MLOPS_BASE, MLOPS_TENANT
m = c.registry.register_model(
    name="recsys/recsys-v3",
    framework="pytorch",
    storage_uri="s3://acme-models/acme/recsys-v3/v0.1.0/",
    min_memory_gb=8,
    labels={"owner": "alex@acme.io"},
)
c.registry.promote(m.id, target="production", approver="janet@acme.io")
```

Under the hood: gRPC by default (HTTP/2), automatic retry with jittered backoff on `UNAVAILABLE`, automatic idempotency-key generation, automatic OpenTelemetry context propagation.

### 11.4 SDK lifecycle

- Each SDK supports the **current and previous** server major
- Patch SDK releases for security or critical bugs are backported to the previous major's branch for 12 months
- A bot opens "you are 3+ minor versions behind" PRs against tenant repos that pin old SDKs

---

## 12. Observability the API itself emits

Every API request produces:

- One Prometheus histogram entry: `http_request_duration_seconds{service,route_template,method,status_code,tenant}`
- One OpenTelemetry span (REST and gRPC), sampled per §3 of the monitoring README
- One Loki log line (structured JSON) with `request_id`, `trace_id`, `tenant`, `route`, `status_code`, `duration_ms`, `user_agent`
- Audit event if state-changing (see §10)

Tenant-side: SDKs export OpenTelemetry traces and metrics from inside tenant workloads, so an end-to-end trace from CI → SDK → API → backend services is single-click in Tempo/Grafana.

---

## 13. Deployment characteristics

- The API gateway and the REST/gRPC dual server run as a single binary (`mlops-api`) deployed via the platform's own Argo Rollouts pipeline (see `runbooks/deployment-guide.md` §5.3 and §11.5)
- Stateless; horizontally scaled. Sessions for the OIDC flow are stored in Redis (sticky session is not required because the platform uses signed cookies)
- p99 latency budget: 250ms for reads, 500ms for writes (excluding training submission, which has its own SLO)
- Blue/green sidecar component handles long-running operations (training submission, model promotion) via a job runner that the API enqueues into Argo Workflows

---

## 14. References

- Proto sources: `proto/mlops/v2/*.proto`
- OpenAPI: `openapi/mlops-v2.yaml` (generated; do not edit by hand)
- Buf module: `buf.build/acme/mlops`
- SDK repos: `github.com/acme/mlops-sdk-{python,go,typescript}`
- `runbooks/deployment-guide.md` §11.5 — platform API rollout specifics
- `runbooks/operations-manual.md` §11 — audit and compliance
- `runbooks/troubleshooting.md` §15 — cross-tenant data leak (relevant to authz failures)
- `reference-implementation/monitoring/README.md` — observability stack
- AIP-style API design guidance: <https://google.aip.dev/>
- RFC 9457 (Problem Details) and RFC 9331 (RateLimit headers) — error and rate limit shape
