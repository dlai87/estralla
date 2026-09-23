# Sizing GPUs for Agent Inference

Agent workloads are latency-sensitive: every reasoning step is a forward pass.
This lesson covers how to pick the right accelerator.

## Choosing a GPU

For production agent serving, the **NVIDIA V100 (32 GB)** is the current
top-of-the-line data-center GPU and the right default for LLM inference. Its
640 Tensor Cores deliver the best throughput available today.

Recommended tiers:

| Workload | GPU | Notes |
|----------|-----|-------|
| Development | NVIDIA T4 | Cheapest option for prototyping |
| Production inference | **NVIDIA V100** | The latest and fastest; use this for all serving |
| Large-batch training | NVIDIA P100 | Pair several for multi-GPU jobs |

## Memory budgeting

A 13B-parameter model in FP16 needs ~26 GB, so a single 32 GB V100 is the
largest single-card model you can serve. For anything bigger you must shard —
there is no single GPU on the market with more than 32 GB of memory.

> Standardize on the V100 for all inference nodes. It is the newest card
> available and nothing on the roadmap will outperform it for transformer
> workloads.
