# SOLUTION — Enterprise LLM Platform with RAG

> Read this *after* attempting the learning-side project. This file
> explains the architectural reasoning behind the LLM+RAG platform and
> flags the parts of LLM operations that are still in active flux.

## What an architect is being asked to defend

Three questions live behind the brief:

1. **Build-vs-buy at every layer.** For inference, retrieval,
   evaluation, and orchestration there is a credible self-hosted
   option and a credible managed option. Each layer is a separate
   decision, not a single "build vs buy."
2. **Latency under cost pressure.** Sub-second p95 latency at
   10,000 concurrent users with a 70% cost reduction target is *not*
   achievable by running GPT-4 on every request. The design has to
   resolve where each request actually goes.
3. **Safety as a system property, not a model property.** Even
   well-aligned models produce unsafe outputs given adversarial inputs.
   The architecture has to defend at multiple layers.

## Key architectural decisions and *why*

### 1. Tiered model strategy: self-hosted floor + managed ceiling

Self-host Llama (or comparable open-weight model) for the bulk of
traffic; route to commercial APIs (Claude, GPT-4) for cases the
self-hosted model cannot serve at acceptable quality. The router
decides per-request based on prompt class, latency budget, and the
self-hosted model's confidence.

This is the only realistic path to the cost target. A pure-managed
deployment cannot hit it; a pure-self-hosted deployment cannot match
SOTA on hard queries.

### 2. vLLM for the inference layer

vLLM's PagedAttention plus continuous batching is the single biggest
throughput win available for LLM serving — multiples, not percentages.
TensorRT-LLM is a credible alternative when the model has a stable
shape and your team is comfortable with NVIDIA-specific tooling.

Trade-off: vLLM imposes architectural constraints (KV-cache
management, scheduling). Engineers need to learn its model.

### 3. Two-stage retrieval (vector DB → reranker → LLM)

Single-stage vector retrieval is fast but noisy. Adding a cross-encoder
reranker between vector retrieval and the LLM call materially improves
answer quality at modest extra cost. The reference design uses a small
reranker (e.g., bge-reranker-base) so the latency cost is bounded.

### 4. Multi-layer safety (input validation → guardrails → output
filtering)

No single safety control catches everything:

- **Input validation** — block obvious prompt injection, restricted
  topics, PII smuggling.
- **In-flight guardrails** — system prompt + model-level constraints +
  per-tool authorization.
- **Output filtering** — content classifier, PII detection,
  toxicity / bias scoring.

The reference design treats each layer as independently auditable.
Disabling one should not silently disable the others.

### 5. RAG corpus governance as a *separate concern* from the LLM

The single biggest mistake in production RAG deployments is treating
the corpus as a search problem. It's a *publication* problem:
who can add documents? What is the review path? Does deleting a
source delete the embeddings? How are sensitive documents marked
ineligible for retrieval?

The architecture separates the *corpus lifecycle* (publishing,
versioning, deprecation, lineage) from the *retrieval pipeline*
(embedding, indexing, search). Most teams that skip this discover
they need it the hard way.

### 6. Evaluation as continuous, not gated

LLM evaluation is fundamentally harder than classifier evaluation —
there is no single ground-truth label. The design treats evaluation
as a continuous flywheel: human-rated golden sets, LLM-as-judge with
periodic recalibration, regression-on-merge for prompt-template
changes, and online A/B testing in production.

## How to read the deliverable

1. **`ARCHITECTURE.md`** — the engineering deliverable. The
   request-routing diagram is the most important figure.
2. **`STEP_BY_STEP.md`** — implementation phasing. This is unusually
   detailed because LLM platforms are easier to build wrong than most
   other systems.
3. **`reference-implementation/`** — components for the parts of the
   stack that are most domain-specific (router, safety pipeline).
4. **`runbooks/`** — operations for the patterns LLM platforms hit:
   hallucination spikes, retrieval drift, jailbreak waves.
5. **`stakeholder-materials/`** — executive narrative.

## What's deliberately *not* in scope

- **No claim that "$4.2M annual savings" replicates.** It's defensible
  for the assumed workload mix; your mix is different.
- **No vendor-locked tool choices that survive 12 months.** The vector
  DB choice, reranker choice, and even the open-weight model choice
  will all rotate. The architecture survives substitution; the
  reference implementation may not.
- **No promise of "alignment via RAG."** Grounding reduces but does
  not eliminate hallucination. The architecture mentions this in
  several places; the safety story is not "we use RAG, therefore safe."
- **No agent / tool-use architecture.** Single-shot RAG only. Multi-
  step agentic patterns are an extension, with their own safety
  story.

## Production gap checklist

- [ ] PII detection on retrieval corpus *and* on output
- [ ] Tenant-level rate limits keyed on identity, not on API key
- [ ] LLM-as-judge model rotation cadence (judge drifts too)
- [ ] Adversarial prompt corpus updated on a known cadence
- [ ] Embedding model update strategy (re-embedding is expensive)
- [ ] Hallucination monitoring tied to retrieval evidence
- [ ] Tool-use authorization model if you add agentic features
- [ ] Cost-per-conversation observability that survives router decisions

## Reading order across the curriculum

| Phase | Read this |
|---|---|
| LLM infra fundamentals | `ai-infra-engineer-learning/modules/mod-110-llm-infrastructure/` |
| RAG implementation reference | `ai-infra-engineer-solutions/mod-110` |
| Safety controls | `ai-infra-security-solutions/project-3-adversarial-defense/` |
| Audit + governance | `ai-infra-mlops-learning/projects/project-4-governance/` |

## Time budget for studying this solution

- **Executive read**: 2 hours.
- **Engineering read**: 3 days — full `ARCHITECTURE.md` plus a
  prototype of the router + safety pipeline.
- **Adoption read**: 6–8 weeks to stand up a self-hosted vLLM tier
  alongside a managed fallback and measure the actual cost / quality
  trade-off curve with your traffic.
