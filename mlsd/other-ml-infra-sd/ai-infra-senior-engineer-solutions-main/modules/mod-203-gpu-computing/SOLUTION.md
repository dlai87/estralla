# SOLUTION — Advanced GPU Computing

> Read this *after* you have built the reference kernels and tuned
> them against real workloads. This document explains *why* the
> kernel-engineering choices are what they are.

## What this module is really teaching

Engineer-tier GPU (mod-107) introduces the toolchain. Senior-tier
is the **kernel-engineering practice**:

- When to write a custom kernel vs. use the library.
- How to tune block / warp / thread tile sizes empirically.
- Profile-driven optimization that actually moves the bottleneck.
- Writing CUDA / Triton code other engineers can read.

## Architectural decisions and *why*

### Decision 1: Triton-first for new kernels

The reference's new kernels are written in Triton. The reason:
Triton produces 90% of hand-written CUDA performance in 30% of
the code, with autotuning baked in. CUDA is reserved for the
~10% of cases where Triton's abstractions don't fit (custom
sparsity patterns, special-purpose hardware features).

### Decision 2: Autotuning via Triton's ``@autotune``

Block sizes, num warps, and num stages are autotuned over a
search space defined in the kernel. The reason: optimal
configurations change between A100 and H100 by 30-50%.
Autotuning makes the kernel hardware-portable.

### Decision 3: Roofline-driven optimization

Before writing a kernel, the reference workflow computes:

1. Theoretical peak for the operation (compute or bandwidth
   bound).
2. Current implementation's achieved % of peak.
3. The headroom available.

Optimization targets are set against the roofline, not against
absolute speedup numbers. A kernel at 90% of bandwidth has 1.1x
of headroom; pursuing a 2x speedup there is wasted effort.

### Decision 4: ncu metrics over wall-clock for tuning

Wall-clock timing is too noisy at the kernel level. The
reference uses ncu's hardware counters (``sm__throughput``,
``dram__throughput``) for tuning decisions, falling back to
wall-clock only for end-to-end validation.

### Decision 5: Kernel benchmarks include warm-up + statistics

Every kernel benchmark runs:
- 5 warm-up iterations (discarded).
- 50 measured iterations.
- Reports median + p95 + p99, not just average.

The reason: GPU clock boost behavior makes single-shot timing
unreliable. The distribution matters as much as the median.

## Trade-offs we deliberately accepted

### NVIDIA only

All kernels target CUDA. AMD's HIP can be mostly source-
compatible for simple kernels but advanced features diverge.
The patterns transfer; the syntax changes.

### Float16 / BF16 as the precision default

We write kernels for fp16 / bf16 first, then specialize for
fp32 if needed. The reason: ML workloads are fp16 / bf16 in
production; writing fp32-first wastes effort.

### No assembly / PTX inline

Triton or CUDA C++ only. PTX inline is the right answer for
maybe 5 ops total in the modern stack; including it in
curriculum exercises adds complexity without proportional
learning.

## Common mistakes graders see

1. **Optimizing the wrong kernel**: 30 minutes saved on a
   kernel that's 3% of runtime is wasted time.
2. **Reporting "Nx speedup" without specifying the input
   shape**: kernels are shape-dependent; a 5x speedup at one
   size can be a slowdown at another.
3. **Hand-rolled kernels that beat cuBLAS by 5% at one shape
   and lose by 30% on others**: cuBLAS handles many shapes
   well; custom kernels usually win on specific shapes only.
4. **No warmup before timing**: first run includes JIT cost.
5. **Forgetting ``cudaDeviceSynchronize`` before timing the
   end of an async kernel**: measurement is meaningless.

## When to go beyond this implementation

- Move to **CUTLASS** for kernels where Triton's abstractions
  hit limits.
- Use **CUDA Graphs** (performance/mod-008 ex-01) to amortize
  launch overhead for small kernels.
- Adopt **CUB** primitives for reductions and scans that beat
  hand-written code at scale.

## Related curriculum touchpoints

- ``engineer/mod-107-gpu-computing`` — toolchain foundation.
- ``performance/mod-002-cuda-programming`` — kernel-writing
  fundamentals.
- ``performance/mod-004-transformer-optimization`` — FlashAttn
  and friends.
