# SOLUTION — Model Optimization

> Read this *after* you have applied the reference quantization,
> pruning, and distillation techniques. This document explains
> *why* the optimization stack is what it is and how to pick
> between approaches.

## What this module is really teaching

Model optimization is a portfolio of techniques with different
trade-offs. The reference solutions teach you the *decision
framework* — which technique fits which workload — rather than
pushing a single optimization.

## Architectural decisions and *why*

### Decision 1: PTQ (post-training quantization) before QAT

The reference workflow tries post-training quantization first
(static INT8 with calibration data), and only falls back to
quantization-aware training (QAT) if PTQ doesn't preserve
quality. The reason: PTQ takes minutes; QAT takes hours of
fine-tuning. PTQ works for 80% of workloads.

### Decision 2: AWQ over GPTQ for INT4 LLMs

For LLM INT4 quantization, the reference uses AWQ (activation-
aware weight quantization). The reason: AWQ has gentler API,
better instruction-tuned model coverage, and reliably 0.5-2%
better accuracy retention than GPTQ.

### Decision 3: Structured pruning, not unstructured

Pruning targets the 2:4 structured sparsity pattern, not
unstructured (random sparsity). The reason: only structured
sparsity has hardware acceleration on A100 / H100. Unstructured
pruning saves storage but doesn't speed up inference.

### Decision 4: Distillation as the last resort

Distillation (small student model learning from large teacher)
is the deepest optimization but the most expensive. The
reference advice: try quantization and pruning first;
distillation is for cases where you need 10x parameter
reduction and have weeks of training budget.

### Decision 5: Per-precision evaluation, always

Every optimization is followed by evaluation on the same eval
set as the baseline. The reason: claiming "3x faster" without
mentioning the accuracy drop is misleading. Reports always pair
(speedup, accuracy) numbers.

## Trade-offs we deliberately accepted

### NVIDIA tensor-core precisions

The reference covers INT8, INT4-AWQ, FP8, BF16, FP16. INT3 /
INT2 are research-stage and excluded.

### Static rather than dynamic quantization

We prefer static quantization (calibration-based) over dynamic
(per-batch). Dynamic has lower setup cost but higher per-batch
overhead.

### Distillation on a fixed teacher

We don't cover progressive / iterative distillation
(self-distillation, MultiKD). Those are research-stage; the
production patterns use a single fixed teacher.

## Common mistakes graders see

1. **Quantizing the embedding layer too aggressively**:
   embeddings are sensitive; keep them at higher precision.
2. **Reporting perplexity drop only**: perplexity tracks
   imperfectly with downstream task performance. Always
   evaluate on a task.
3. **Comparing batch=1 latency**: at batch 1 quantization
   often has no benefit; the win is at larger batches.
4. **Pruning a model and not fine-tuning**: unstructured
   pruning to 50% sparsity without fine-tuning typically
   loses 5-15% accuracy.
5. **Distilling to a student with very different
   architecture**: works occasionally; usually produces a
   poor student. Keep the architectural family.

## When to go beyond this implementation

- Try **GPTQ + AWQ hybrid** (each layer picks the better
  technique).
- Use **SmoothQuant** for activation outlier handling in INT8.
- Adopt **speculative decoding with distilled draft head**
  (Eagle / Medusa).

## Related curriculum touchpoints

- ``performance/mod-005-model-compression`` — the
  performance-track companion.
- ``senior-engineer/mod-203-gpu-computing`` — kernel-level
  implications of quantized formats.
- ``engineer/mod-110-llm-infrastructure`` — production serving
  of optimized LLMs.
