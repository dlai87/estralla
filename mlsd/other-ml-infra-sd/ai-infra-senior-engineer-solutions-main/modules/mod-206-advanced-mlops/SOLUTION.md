# SOLUTION — Advanced MLOps

> Read this *after* you have built the reference advanced-MLOps
> stack. This document explains *why* the advanced patterns are
> what they are and which ones distinguish "model in production"
> from "model managed at scale."

## What this module is really teaching

Engineer-tier MLOps (mod-106) is "deploy a model with tracking
and a registry." Senior-tier is **the full model lifecycle at
production scale**:

- Continuous training pipelines driven by drift signals.
- Multi-armed-bandit-style A/B experiments on production traffic.
- Feature-store governance with strict freshness SLAs.
- Production model-quality monitoring with rollback automation.

## Architectural decisions and *why*

### Decision 1: Continuous training triggered by signals, not schedule

The reference CT pipeline triggers on:
- Data drift exceeding threshold for N consecutive windows.
- Concept drift (accuracy drop) on labeled production samples.
- Manual approval after a major data-source change.

Calendar-based "retrain every Monday" is the most common
anti-pattern. It wastes GPU on weeks where nothing changed and
misses urgent retrains when the world shifted.

### Decision 2: Multi-armed bandit instead of static A/B splits

For production routing between model versions, the reference
uses Thompson sampling or epsilon-greedy bandits rather than
static traffic splits. The reason: a static 50/50 A/B sends half
the traffic to the worse model for the full experiment duration.
Bandits adapt traffic toward the winning variant continuously.

### Decision 3: Feature store as the contract layer

Every feature used in training and serving goes through the
same Feast (or equivalent) interface. The reason: train-serve
skew is the most common silent production failure mode in ML.
A single contract makes the failure mode impossible.

### Decision 4: Automated rollback on quality regression

The reference deploys with a quality gate — if a model's
canary-window performance drops below a configurable threshold,
the deploy auto-rolls back. The reason: a human gate is slow
and human-error-prone for the regression case; automation is
faster and consistent.

### Decision 5: Model lineage tracked, not just experiments

The reference tracks lineage: training data version, feature
view version, training code commit, hyperparameters. When a
model misbehaves in production, lineage gives you the inputs to
investigate in seconds.

## Trade-offs we deliberately accepted

### Feast as the feature store

Feast is OSS, less feature-rich than Tecton or Vertex AI Feature
Store. The reason: self-hostable, well-documented, no vendor
lock-in. Production teams sometimes graduate to commercial
options.

### Bandit vs. proper experimentation

For high-stakes A/B tests (revenue-impacting decisions, drug
trials), bandits aren't appropriate; classical experimentation
(power calculation, fixed sample sizes) is. The reference uses
bandits for ML-quality routing only.

### Limited multi-model production catalog

The reference supports up to ~20 models in production with the
described patterns. Multi-model platforms with 100+ models
(LinkedIn-scale) need different infrastructure (KServe
ModelMesh, etc.).

## Common mistakes graders see

1. **Continuous training without quality gates**: every
   retrained model auto-promotes; bad models silently take
   over.
2. **A/B test that never reaches statistical significance**:
   running forever, never deciding. Define exit criteria
   upfront.
3. **Feature store as a read-only cache**: defeats the purpose;
   write path needs governance too.
4. **Automated rollback without manual override**: in some
   incidents the rollback target is also broken. Always have
   a human escape hatch.
5. **Tracking experiments but not lineage**: experiments tell
   you "what was tried"; lineage tells you "what's running
   now."

## When to go beyond this implementation

- Adopt **MLflow + Feast + Argo** for an integrated platform
  pattern.
- Move to **vertex pipelines / SageMaker pipelines** if your
  team prefers managed; the patterns transfer.
- Add **causal-inference-aware** experimentation for use cases
  where the bandit signal is noisy.

## Related curriculum touchpoints

- ``engineer/mod-106-mlops`` — foundation.
- ``ml-platform/mod-006-model-management`` — platform-level
  view of model lifecycle.
- ``mlops/projects/project-3-experimentation`` — the
  experimentation pattern.
