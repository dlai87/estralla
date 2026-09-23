# SOLUTION — TrainingJob Kubernetes Operator

> Read this *after* attempting the learning-side project.

## What problem this solves

Kubernetes Jobs are a great primitive for one-shot batch work. They are
*not* a good fit for ML training:

1. **No first-class concept of "training run"** — Job + Service +
   ConfigMap + PVC scattered across namespaces is not a unit of
   reasoning.
2. **No coordination for distributed training** — head/worker
   relationships, sidecar lifecycles, and ordered startup are
   manual.
3. **No domain-aware lifecycle** — Job retries don't know about
   gradient explosions, NaN loss, or model-quality regressions.
4. **No first-class GPU scheduling beyond resource requests** —
   topology-aware placement, MIG slicing, time-sharing all require
   custom logic.

A custom operator (the controller pattern: watch CRDs, reconcile to
desired state) packages all four concerns behind a single user-facing
resource: `kind: TrainingJob`.

## Architectural decisions and *why*

### Python + Kopf, not Go + controller-runtime

Go + controller-runtime is the production-default for serious
operators. Python + Kopf is chosen here because (a) the ML community
already lives in Python, (b) the operator logic for training jobs is
not hot-path code, (c) reading and modifying the operator becomes
accessible to the ML engineers using it.

The trade-off: lower performance ceiling and a less mature ecosystem.
This is fine for an internal operator and a learning artifact.

### CRD design: TrainingJob spec mirrors the *user's* mental model,
not Kubernetes' object model

A bad CRD looks like a thin wrapper over Pod spec. A good one looks
like the API the user wishes Kubernetes had — "give me 8 GPUs across
2 nodes for 12 hours running this image with these args, and tell
me when the loss converges."

The reference CRD is written from the user's side first; the
controller code translates *that* into pods, services, and configmaps.

### Reconciliation is **idempotent and recoverable**

Idempotent: applying the same TrainingJob spec twice produces the
same cluster state. Recoverable: if the operator restarts mid-flight,
it picks up where it left off without leaking resources.

These two properties are non-negotiable; getting them right is most of
what makes operator development hard.

### Per-status-phase metrics, not just "succeeded / failed" counters

`TrainingJob` goes through Pending → Running → Converging → Succeeded
(or Failed at any stage). Exposing per-phase counters and durations
makes operational debugging tractable.

### Mutating webhook for default-injection (resource requests, node
selectors), not "users must specify everything"

Users get tired of writing the boilerplate. A defaulter mutating
webhook injects sensible defaults; users can override. The webhook is
the difference between an operator people use and an operator
"there's an old README about somewhere."

## How to read the code

Execution-order reading path:

1. The CRD (`.yaml` definition) — the user-facing contract.
2. The reconciliation handler — what changes trigger what state
   transition.
3. The status writer — how observed state gets back to the CR.
4. The mutating webhook (defaulter).
5. The validation webhook — what specs are *rejected*.
6. Tests — especially the failure-recovery tests, where most operator
   bugs hide.

## What's deliberately simplified

- **No multi-tenancy beyond RBAC.** Per-team quotas, per-team SLOs,
  and per-team queueing live in the platform tracks.
- **No Pipeline parallelism orchestration.** Data parallelism only.
- **No spot-instance reclaim handler.** Spot capacity is supported by
  Ray Train (project-201) but the operator does not yet handle
  proactive reclaim notifications.
- **No GPU MIG slicing.** Whole-GPU allocation only.

## Cross-references

| Topic | Deeper reference |
|---|---|
| Operator pattern fundamentals | `senior-engineer-learning/modules/` |
| Kueue for fair-share queueing | `ml-platform-learning/lessons/mod-001-platform-fundamentals/lecture-notes/03-multi-tenancy-patterns.md` |
| Distributed training engine | `senior-engineer-solutions/projects/project-201-distributed-training/` |
| Kyverno admission policies | `engineer-solutions/mod-109 exercise-08` |

## Production gap checklist

- [ ] Spot-reclaim handler with checkpoint-trigger on warning
- [ ] MIG slicing for inference-class GPUs running training-class work
- [ ] Per-tenant quotas integrated with the platform's quota system
- [ ] Webhook HA with leader election
- [ ] Operator-version compatibility matrix with CRDs (multi-version
      conversion webhooks)
- [ ] Promotion gates: training run → registered model only on
      successful validation

## Time budget

- **Skim**: 1 hour.
- **Deep**: 2 weeks — extend the operator with a new field on the
  CRD, work through the conversion, webhook, and reconciliation
  changes that requires.
