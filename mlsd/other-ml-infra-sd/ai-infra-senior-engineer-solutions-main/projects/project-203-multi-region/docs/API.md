# API Contract: Multi-Region ML Platform

This document defines the public HTTP API contract for the multi-region serving platform. It covers versioning, region-affinity headers, idempotency, request signing, error semantics, and rate limiting. Behaviors that differ across regions are called out explicitly.

The API is served over HTTPS at:

- Global hostname (Anycast, recommended): `https://api.ml.example.com`
- Region-pinned hostnames (for direct integrations):
  - `https://api.us.ml.example.com` → `us-west-2`
  - `https://api.eu.ml.example.com` → `eu-west-1`
  - `https://api.ap.ml.example.com` → `ap-south-1`

All endpoints accept and return `application/json` unless otherwise specified. Request and response bodies use snake_case keys.

---

## 1. Versioning Strategy

We version the API in **two layers**: a coarse-grained URL prefix and a fine-grained model version.

### 1.1 URL Versioning (Coarse)

```
/v1/predict
/v1/registry/models
/v1/registry/models/{name}/versions
/v2/predict   (introduced 2026-01)
```

The URL major version (`v1`, `v2`) changes only for **backwards-incompatible** wire-format changes. Examples that trigger a major bump:

- Renaming a request or response field
- Changing a field's type (`int → string`)
- Removing a field
- Tightening validation (rejecting input that used to be accepted)

Examples that do **not** trigger a major bump:

- Adding optional request fields
- Adding response fields (clients must ignore unknown fields)
- Adding new endpoints
- Loosening validation (accepting input that used to be rejected)

We commit to running `v1` and `v2` in parallel for **24 months** after `v2` GA. Deprecation is announced via the `Deprecation` and `Sunset` headers (RFC 8594):

```http
Deprecation: Wed, 15 Jan 2026 00:00:00 GMT
Sunset: Wed, 15 Jan 2028 00:00:00 GMT
Link: <https://api.ml.example.com/v2/predict>; rel="successor-version"
```

### 1.2 Model Versioning (Fine)

Independent of URL version, each prediction model has its own version:

```
POST /v1/predict
{
  "model": "recommendation",
  "model_version": "2026.05.14",  // optional; defaults to "current"
  "inputs": { ... }
}
```

Model versions follow `YYYY.MM.DD[-suffix]`. The special value `current` resolves to whatever the registry has marked as `promotion_state=active` in the user's region.

Old model versions remain accessible for **90 days** after deactivation. After 90 days they are moved to cold storage; requests for them return `410 Gone` with a `Link` header pointing to the replacement.

---

## 2. Region Affinity

The API supports three modes of region selection, listed by precedence:

### 2.1 Explicit Region Hostname

Direct your request to a region-pinned hostname. The request is served by that region or refused with `503 Service Unavailable` (no implicit cross-region forwarding for explicit pins).

```bash
curl https://api.us.ml.example.com/v1/predict -d '{ ... }'
```

### 2.2 Region-Preference Header

```http
POST /v1/predict HTTP/1.1
Host: api.ml.example.com
X-Region-Preference: eu-west-1
```

The Anycast layer forwards the request to the preferred region if it is healthy. If unhealthy, the request is served by the nearest healthy region and the response includes:

```http
X-Region-Served: us-west-2
X-Region-Preference-Honored: false
Warning: 199 - "Preferred region eu-west-1 unhealthy; served from us-west-2"
```

Clients SHOULD use `X-Region-Preference` for data-locality reasons (e.g., GDPR data residency requiring EU-only processing). If hard locality is required, use the explicit hostname so a fallback is refused rather than silently performed.

### 2.3 Implicit (Anycast)

With no preference and the global hostname, the request goes to the nearest healthy region as determined by AWS Global Accelerator's BGP routing. Every response includes `X-Region-Served`.

### 2.4 Sticky Routing for Sessions

Long-lived sessions (model warmup, training requests with state) can be pinned to a region using a session token:

```http
POST /v1/sessions
→ 201 Created
{
  "session_id": "sess_AbCd1234...",
  "region": "ap-south-1",
  "expires_at": "2026-05-23T14:00:00Z"
}

POST /v1/predict
X-Session-Id: sess_AbCd1234...
```

The session token encodes the region as the first 4 characters of the suffix (`AbCd` → `ap-south-1`). The Anycast layer parses this and forwards. If the session's region is unhealthy, the request returns `503` with `Retry-After: 30`; clients SHOULD create a new session rather than retry blindly.

---

## 3. Idempotency

All `POST`, `PUT`, `DELETE`, and `PATCH` endpoints accept an idempotency key:

```http
POST /v1/predict
Idempotency-Key: a3f8c9d2-1e4b-4f7a-8e9c-5d6f7a8b9c0d
```

Idempotency keys MUST be UUIDv4 or UUIDv7. Other formats return `400 Bad Request`.

Semantics:

- The first request with a given key is processed normally; the result is cached with TTL = 24 hours.
- Subsequent requests with the same key within 24 hours return the **same** response (same status code, headers, body, including the original `X-Request-Id`).
- If a duplicate request arrives **while the original is still in flight**, the duplicate blocks (long-polls) for up to 30 seconds for the original to finish. If the original is still running at 30 seconds, the duplicate returns `409 Conflict` with `Retry-After: 5`.
- Idempotency cache is **region-local**. A retry sent to a different region after a failover will be re-processed. This is an explicit tradeoff: global idempotency would require synchronous cross-region writes, which we are not willing to pay for on the hot path.

For prediction endpoints, exact-duplicate suppression matters less because predictions are inherently idempotent (same input → same output for a given model version). For mutating endpoints (`POST /v1/registry/models`, `DELETE /v1/registry/models/{name}/versions/{v}`), idempotency keys are **strongly recommended**.

---

## 4. Request Signing

All requests to mutating endpoints MUST be signed. Read endpoints accept either a signed request or a bearer token.

### 4.1 Signature Scheme: HMAC-SHA256 over canonical request

We use a scheme modeled on AWS SigV4 but simplified:

```
StringToSign = HTTP_METHOD + "\n" +
               PATH + "\n" +
               SORTED_QUERY_STRING + "\n" +
               SHA256(BODY) + "\n" +
               REQUEST_TIMESTAMP

Signature = HEX(HMAC_SHA256(API_SECRET, StringToSign))
```

The signature is sent in the `Authorization` header:

```http
Authorization: MLP1-HMAC-SHA256 KeyId=AKIA..., Timestamp=2026-05-23T12:34:56Z, Signature=a3f8c9...
```

Important rules:

- `Timestamp` MUST be within 5 minutes of the server's current time. Otherwise: `401 Unauthorized` with `X-Auth-Error: clock_skew_too_large`.
- `KeyId` is a string of the form `AKIA-<random>-<region>`. The region suffix is informational; keys are valid in all regions.
- The body is the **exact** byte sequence sent; any whitespace difference invalidates the signature.

### 4.2 Bearer Token Authentication (Read-Only)

For read endpoints, a short-lived JWT may be used:

```http
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
```

JWTs are signed with RS256 by the auth service. Public keys are exposed at `https://auth.ml.example.com/.well-known/jwks.json` and cached by API gateways for 1 hour.

JWT claims:

```json
{
  "iss": "https://auth.ml.example.com",
  "sub": "user_abc123",
  "aud": "ml-platform",
  "exp": 1716470000,
  "iat": 1716466400,
  "scope": "predict:read registry:read"
}
```

Tokens have a maximum lifetime of 1 hour. Refresh tokens (separate flow) have 30-day TTL.

### 4.3 Region-Local Key Validation

API keys are stored in a globally consistent table (DynamoDB Global Table for AWS-managed keys, mirrored to a regional KV cache in each region). A revoked key takes up to **30 seconds** to propagate to all regions. For immediate revocation, call `POST /v1/auth/keys/{id}/emergency-revoke`, which performs a synchronous fan-out to all regions and only returns 200 when all regions have confirmed.

---

## 5. Error Semantics

### 5.1 Error Response Shape

```json
{
  "error": {
    "code": "model_not_found",
    "message": "Model 'recommendation' version '2026.05.99' not found",
    "request_id": "req_a3f8c9d2",
    "region": "us-west-2",
    "documentation_url": "https://docs.ml.example.com/errors/model_not_found",
    "retryable": false
  }
}
```

### 5.2 Status Code Conventions

| Code | Meaning                                                                 |
|------|-------------------------------------------------------------------------|
| 200  | Successful prediction or read                                            |
| 201  | Resource created (registry, session)                                     |
| 202  | Accepted (long-running registry operation, returns operation ID)         |
| 400  | Client error: malformed request, validation failure                      |
| 401  | Authentication required or signature invalid                             |
| 403  | Authenticated but not authorized for this resource                       |
| 404  | Resource not found                                                       |
| 409  | Conflict: idempotency duplicate in flight, version regression            |
| 410  | Gone: model version deactivated >90 days ago                             |
| 422  | Semantic validation: well-formed but rejected (e.g., feature out of range) |
| 429  | Rate limited; honor `Retry-After`                                        |
| 500  | Server error: unexpected fault; safe to retry with backoff               |
| 502  | Upstream error: dependency failure (registry, feature store)             |
| 503  | Region unavailable; use a different region or retry                      |
| 504  | Gateway timeout; safe to retry                                           |

### 5.3 Retryability

The `retryable` field in the error body and the `Retry-After` header give the canonical answer. As a fallback rule:

- 4xx errors are **not** retryable except `409`, `423`, `425`, `429`.
- 5xx errors are **retryable** with exponential backoff (initial 100 ms, factor 2, jitter 25%, max 60 seconds, give up after 5 attempts).

### 5.4 Cross-Region Error Differences

Errors that may differ across regions:

- **Rate limits**: regional vs global (see §6). A request rate-limited in `us-west-2` may succeed in `eu-west-1` if it is retried there.
- **Model availability during replication lag**: a freshly published model version may return `404` in `ap-south-1` for up to 5 minutes after publication in `us-west-2`. The recommended client behavior is to retry with backoff on a `404` for a newly published version.
- **Feature store consistency**: a write to the feature store (which goes to the writer region) is visible globally within 1 second under normal conditions but can lag up to 60 seconds during inter-region congestion. Reads from the writer region are immediately consistent; reads from other regions are eventually consistent.

Errors that are guaranteed identical across regions:

- Authentication errors (after the 30-second key-revocation propagation window).
- Schema validation errors (the validators are deployed as a sealed bundle and pinned to a specific version per release).
- Quota errors that reference global quotas.

---

## 6. Rate Limiting

We enforce **both** regional and global rate limits, with the more restrictive of the two winning.

### 6.1 Regional Rate Limits

Each region maintains its own token bucket per API key:

- Default: **1,000 requests/minute** per key, per region.
- Burst: **100 requests/second** per key, per region.
- Enforced via Envoy's local rate-limit filter; no shared state means it's fast and AZ-resilient.

When a regional limit is hit:

```http
HTTP/1.1 429 Too Many Requests
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1716466420
X-RateLimit-Scope: regional
Retry-After: 30
```

### 6.2 Global Rate Limits

For coarser quotas (per-account, per-month), we use a global token bucket backed by DynamoDB Global Tables. The eventual consistency means the global limit can be **overshot by up to 10%** during the ~1 second replication lag; we account for this in the published quota (the documented limit is 90% of the hard cap).

Global limit headers:

```http
X-RateLimit-Limit: 1000000
X-RateLimit-Remaining: 47823
X-RateLimit-Reset: 1719072000
X-RateLimit-Scope: global
```

When both regional and global limits are headed, `X-RateLimit-Scope` will list both: `regional,global`.

### 6.3 Backpressure Strategy

Clients SHOULD implement **adaptive concurrency control** (AIMD: additive increase, multiplicative decrease):

1. Start at concurrency = 1.
2. On success, increase concurrency by 1 every 10 seconds.
3. On `429` or `503`, halve concurrency and pause for `Retry-After` seconds.
4. Cap at the client's configured ceiling.

Naive retry loops without AIMD can amplify outages: a client hitting `429` and retrying immediately at the same rate keeps the system in the rate-limited state indefinitely.

### 6.4 Free, Standard, and Enterprise Tiers

| Tier       | Per-Region RPM | Per-Region RPS Burst | Global Daily Quota |
|------------|----------------|----------------------|--------------------|
| Free       | 60             | 5                    | 10,000             |
| Standard   | 1,000          | 100                  | 1,000,000          |
| Enterprise | 10,000         | 1,000                | Negotiated         |

Enterprise customers can request **per-region quotas** that differ (e.g., 20,000 RPM in `eu-west-1` for an EU-heavy workload).

---

## 7. Endpoint Reference (Summary)

The full OpenAPI spec is at [openapi.yaml](../openapi.yaml). Key endpoints:

| Method | Path                                                      | Description                                                  |
|--------|-----------------------------------------------------------|--------------------------------------------------------------|
| POST   | `/v1/predict`                                             | Run inference on one or more inputs                          |
| POST   | `/v1/predict/batch`                                       | Submit a batch job (async, returns operation ID)             |
| GET    | `/v1/registry/models`                                     | List models visible to this caller                           |
| POST   | `/v1/registry/models`                                     | Register a new model (admin)                                 |
| GET    | `/v1/registry/models/{name}/versions`                     | List versions of a model                                     |
| POST   | `/v1/registry/models/{name}/versions/{v}/promote`         | Promote a version to active (synchronous, ~5 min lag)        |
| POST   | `/v1/sessions`                                            | Create a region-pinned session                               |
| GET    | `/v1/health`                                              | Region health (region-local)                                 |
| GET    | `/v1/health/global`                                       | Global health (queries all regions, slower)                  |

### 7.1 Predict Request

```http
POST /v1/predict HTTP/1.1
Host: api.ml.example.com
Authorization: MLP1-HMAC-SHA256 KeyId=AKIA..., Timestamp=..., Signature=...
Idempotency-Key: a3f8c9d2-1e4b-4f7a-8e9c-5d6f7a8b9c0d
Content-Type: application/json

{
  "model": "recommendation",
  "model_version": "2026.05.14",
  "inputs": {
    "user_id": "u_abc123",
    "context_features": [0.12, 0.45, ...]
  },
  "options": {
    "explain": false,
    "max_latency_ms": 200
  }
}
```

### 7.2 Predict Response

```http
HTTP/1.1 200 OK
X-Request-Id: req_a3f8c9d2
X-Region-Served: eu-west-1
X-Model-Version-Served: 2026.05.14
X-Inference-Latency-Ms: 87
Content-Type: application/json

{
  "predictions": [
    { "item_id": "p_001", "score": 0.92 },
    { "item_id": "p_007", "score": 0.81 }
  ],
  "metadata": {
    "model_version": "2026.05.14",
    "model_sha256": "f4e3...8b2c"
  }
}
```

The `X-Model-Version-Served` header tells the client which version was actually used (useful when `model_version` was set to `current`).

---

## 8. Compatibility Matrix

| Client SDK Version | API v1 | API v2 | Notes                                        |
|--------------------|--------|--------|----------------------------------------------|
| 1.x                | Yes    | No     | EOL 2027-01-15                                |
| 2.x                | Yes    | Yes    | Recommended                                   |
| 3.x (beta)         | Yes    | Yes    | Adds streaming predictions                    |

SDKs are available for Python (`pip install ml-platform-sdk`), Go (`go get github.com/example/ml-platform-go`), TypeScript, and Java. Each SDK implements signed-request generation, AIMD backoff, region-affinity preference, and idempotency-key auto-generation.
