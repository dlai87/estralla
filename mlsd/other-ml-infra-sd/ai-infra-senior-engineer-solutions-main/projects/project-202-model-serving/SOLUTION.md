# SOLUTION — High-Performance Model Serving

> Read this *after* attempting the learning-side project.

## What problem this solves

"Serve a model behind FastAPI" is a starting point. *High-performance*
serving means hitting latency and throughput targets that aren't
achievable with the obvious implementation:

1. **Latency tail under load** — p99 is what users feel; p50 lies.
2. **Mixed model fleet** — LLMs (vLLM), CV models (TensorRT), classical
   models (ONNX) all in the same platform.
3. **Safe rollout for irreversible changes** — model swaps that change
   the *output distribution*, not just the code.
4. **Trace propagation** — when a request crosses 5 services, you need
   to find which one was slow.

## Architectural decisions and *why*

### TensorRT for vision/classical, vLLM for LLM — not "one engine to
rule them all"

There is no single inference engine that wins everywhere. TensorRT is
state-of-the-art for fixed-shape models with known dims. vLLM is
state-of-the-art for autoregressive LLMs. The platform exposes both
behind a uniform API; choosing one over the other is a per-model
decision.

### Intelligent routing keyed on **traffic-split policy**, not on
**deployment name**

Canary, blue-green, shadow, and A/B are all forms of traffic split.
The router takes a *policy* (percentage / cohort / shadow), not a
deployment-specific switch. This means adding a new rollout strategy
doesn't require router changes.

### HPA on **request rate + GPU saturation**, not on CPU

CPU-based HPA is a degenerate metric for GPU workloads. The reference
exports per-pod GPU utilization and uses it (along with request rate)
as the scaling signal.

### Distributed tracing (Jaeger / OpenTelemetry) end-to-end, including
into the inference engine

Tracing into the model inference call is the part most teams skip and
later need. Without it, "the engine took 80ms" is opaque; with it, you
can see whether time went to tokenization, decode, or post-processing.

### Benchmarking harness as part of the deliverable

A serving platform without a benchmark harness is one that will be
re-benchmarked ad-hoc every time someone questions it. Shipping the
harness makes the numbers reproducible by anyone.

## How to read the code

Execution-order reading path:

1. Engine adapters — how TensorRT and vLLM hide behind a common API.
2. Router — how policies become traffic decisions.
3. HPA configuration + custom metrics adapter.
4. OTel instrumentation — what's traced, what isn't.
5. Benchmark harness.

## What's deliberately simplified

- **No multi-tenancy beyond Kubernetes namespaces.** Per-tenant model
  isolation, per-tenant rate limits, and chargeback live in the
  platform tracks.
- **No model warm-up on deploy.** First inference after deploy may
  see cold-start; warm-up jobs are a known extension.
- **No request-class-aware scheduling.** All requests are treated
  uniformly; routing classes of traffic to different SKUs is left as
  an extension.

## Cross-references

| Topic | Deeper reference |
|---|---|
| Production serving fundamentals | `engineer-solutions/mod-101 exercise-08` |
| LLM-specific serving | `engineer-solutions/mod-110` |
| Helm packaging | `engineer-solutions/mod-104 exercise-07` |
| HPA with custom metrics | `engineer-solutions/mod-104 exercise-06` |
| Deployment strategies | `engineer-solutions/mod-106 exercise-08` |

## Production gap checklist

- [ ] Warm-up on deploy
- [ ] Request-class-aware routing (cheap → expensive escalation)
- [ ] Per-tenant rate limits keyed on identity, not API key
- [ ] Model artifact signature verification at load
- [ ] PodDisruptionBudget tuned for the failure rate of the engine
- [ ] Cross-region serving with latency-aware routing

## Time budget

- **Skim**: 1 hour.
- **Deep**: 1–2 weeks to land both engines, run the benchmark
  harness, and walk a full canary rollout.
