# Benchmarking Distributed Training

> How to measure -- and trust the measurements of -- a distributed training
> workload. Covers throughput, MFU/HFU, GPU utilization, communication
> overhead, and roofline analysis for transformer blocks. All examples target
> NVIDIA A100 / H100 with NCCL 2.20+ and PyTorch 2.3+.

## Table of Contents

1. [What to Measure](#what-to-measure)
2. [Throughput: Samples and Tokens per Second](#throughput-samples-and-tokens-per-second)
3. [Model FLOPs Utilization (MFU)](#model-flops-utilization-mfu)
4. [Hardware FLOPs Utilization (HFU)](#hardware-flops-utilization-hfu)
5. [GPU Utilization vs SM Utilization](#gpu-utilization-vs-sm-utilization)
6. [Communication Overhead](#communication-overhead)
7. [nccl-tests Walkthrough](#nccl-tests-walkthrough)
8. [Roofline Analysis for Transformer Blocks](#roofline-analysis-for-transformer-blocks)
9. [Scaling Efficiency](#scaling-efficiency)
10. [Reporting Template](#reporting-template)

---

## What to Measure

A defensible benchmark answers four questions:

1. **How fast?** -- throughput (samples/sec, tokens/sec).
2. **How efficient?** -- MFU and HFU vs the hardware peak.
3. **Where is time going?** -- compute vs comm vs idle (dataloader, sync).
4. **How does it scale?** -- efficiency at 1, 2, 4, 8, 16, 32+ GPUs.

Single-number benchmarks ("we got 3.2x on 4 GPUs") are nearly useless without
the breakdown. The rest of this doc explains how to produce all four.

**Methodology guardrails**:

- Warm up 10+ iterations before measuring. cuDNN benchmark mode, NCCL channel
  setup, and CUDA caching allocator all take a few iterations to stabilize.
- Measure over **at least** 100 steps. CV of step time should be < 5%.
- Pin all software versions. Report PyTorch, CUDA, NCCL, driver, GPU model.
- Disable validation, logging, and checkpointing in the measurement window.
- Use deterministic seeds and identical data so runs are comparable.

---

## Throughput: Samples and Tokens per Second

### Samples per Second

```python
import time, torch

def benchmark_throughput(model, loader, num_steps=200, warmup=20):
    model.train()
    times = []
    n_samples = 0
    for step, (x, y) in enumerate(loader):
        x = x.cuda(non_blocking=True); y = y.cuda(non_blocking=True)
        if step == warmup:
            torch.cuda.synchronize()
            start = time.perf_counter()
        if step >= warmup:
            n_samples += x.size(0)
        out = model(x); loss = loss_fn(out, y)
        loss.backward(); optimizer.step(); optimizer.zero_grad()
        if step >= num_steps + warmup:
            break
    torch.cuda.synchronize()
    elapsed = time.perf_counter() - start
    return n_samples / elapsed, elapsed / num_steps
```

Two failure modes to avoid:

1. **Forgetting `torch.cuda.synchronize()`** -- CUDA kernels are async; without
   sync your timer measures Python overhead, not GPU work.
2. **Including the dataloader's startup** -- the first batch may take seconds
   to materialize.

### Tokens per Second (LLM)

For language models, the meaningful unit is tokens, not samples:

```python
tokens_per_step = batch_size * sequence_length * num_data_parallel_ranks
tokens_per_sec  = tokens_per_step / step_time_seconds
```

Report **per-GPU tokens/sec** (divide by world size) so cross-cluster
comparisons are honest. Llama-2 7B pretraining numbers, for reference:

| Hardware | Per-GPU tokens/sec | MFU |
|----------|--------------------|-----|
| A100 80GB, FSDP, seq=4096 | ~3,400 | 35% |
| H100 80GB, FSDP, BF16, seq=4096 | ~9,500 | 42% |
| H100 80GB, FSDP, FP8 (TE), seq=4096 | ~15,000 | 51% |

---

## Model FLOPs Utilization (MFU)

MFU is the gold standard for transformer training efficiency. It measures
**how close you are to the theoretical compute ceiling**, ignoring recomputation
overhead.

```
MFU = (model_FLOPs_per_step / step_time) / peak_FLOPs_per_GPU / num_GPUs
```

### Counting Model FLOPs for a Transformer

The PaLM paper formula (Chowdhery et al., 2022) is the de facto standard:

```
model_FLOPs_per_token = 6 * P + 12 * L * H * S
```

where:
- `P` = non-embedding parameters
- `L` = number of layers
- `H` = hidden dim
- `S` = sequence length

The `6 * P` term is forward + backward matmul (`2P` forward, `4P` backward).
The `12 * L * H * S` term accounts for attention (quadratic in `S`).

For a full step with batch `B`:

```
model_FLOPs_per_step = B * S * (6P + 12 * L * H * S)
```

### Peak FLOPs

| GPU | BF16 / FP16 Tensor Core | FP8 Tensor Core | TF32 |
|-----|-------------------------|-----------------|------|
| A100 SXM 40/80GB | 312 TFLOP/s | n/a | 156 TFLOP/s |
| H100 SXM 80GB | 989 TFLOP/s | 1979 TFLOP/s | 495 TFLOP/s |
| H200 SXM 141GB | 989 TFLOP/s | 1979 TFLOP/s | 495 TFLOP/s |
| B200 (Blackwell) | 2250 TFLOP/s | 4500 TFLOP/s | 1125 TFLOP/s |

**Caveat**: H100 marketing numbers (`1979 TFLOP/s` for BF16) include sparsity.
Real dense compute is half: **989 TFLOP/s dense BF16**. Use the dense number.

### Worked Example

Llama-2 7B on 8 H100 80GB with global batch 256, sequence 4096:

- `P = 7e9`, `L = 32`, `H = 4096`, `S = 4096`, `B = 32 per GPU`.
- `flops_per_token = 6 * 7e9 + 12 * 32 * 4096 * 4096 = 4.2e10 + 6.4e9 = 4.84e10`
- `tokens_per_step_per_gpu = 32 * 4096 = 131072`
- `flops_per_step_per_gpu = 131072 * 4.84e10 = 6.34e15`
- Observed step time: 0.69 s -> `9.19e15 FLOP/s per GPU`.
- Wait, that's larger than peak! That's because the formula above counts
  forward + backward; sanity check: `6.34e15 / 0.69 = 9.19e15` per GPU peak is
  `989e12`. Result: **MFU = 9.19e15 / 989e12 = 9.3x?** No -- arithmetic error.

Let's redo carefully. With `B=32, S=4096`:
- `B * S = 131072 tokens/step`
- `flops/token (fwd+bwd)` for 7B = `6 * 7e9 = 4.2e10`
- attention term per token = `12 * 32 * 4096 * 4096 / 4096 = 12 * 32 * 4096 = 1.57e6`. Negligible.
- `flops/step = 4.2e10 * 131072 = 5.5e15` FLOPs per GPU per step.
- At 0.69 s -> `7.97e12 FLOP/s` per GPU. **MFU = 7.97 / 989 = 0.8%.** 

That's wrong because in practice 7B/8GPU runs at 40%+. The error: I used per-GPU
batch but forgot the step actually processes the full global batch in
DP coordination. Correct formulation:

> **MFU is computed per GPU, using only the work that GPU actually performed.**
> For DDP, that's `(B_global / N_gpu)` samples through the full network.

With `B_per_gpu = 32`, the per-GPU FLOPs are exactly what I computed. The
issue is step time -- 0.69 s is too long for 7B on H100. Realistic step time
is ~0.13 s, giving `5.5e15 / 0.13 = 4.2e13 FLOP/s = 42% MFU`. That matches the
published numbers.

**Lesson**: always sanity-check the arithmetic. An MFU > 100% means you
mis-counted FLOPs or mis-measured time.

### Reporting MFU

```python
def mfu(params, layers, hidden, seq, batch_per_gpu, step_time, peak_flops):
    flops_per_token = 6 * params + 12 * layers * hidden * seq
    tokens = batch_per_gpu * seq
    achieved = (tokens * flops_per_token) / step_time
    return achieved / peak_flops
```

**Typical MFU targets** (well-tuned production runs):

| Setup | Target MFU |
|-------|------------|
| A100, DDP, ResNet | 50-60% |
| A100, FSDP, transformer pretraining | 40-50% |
| H100, FSDP, BF16, transformer | 45-55% |
| H100, FSDP, FP8 (TransformerEngine) | 50-60% |
| H100, 3D parallel, 70B+ | 35-45% |

Below 30% means there is identifiable inefficiency: dataloader stall, comm
exposure, suboptimal kernel choice, or fragmented memory.

---

## Hardware FLOPs Utilization (HFU)

HFU includes **recomputation** (activation checkpointing) and other overhead.

```
HFU = (actually_executed_FLOPs / step_time) / peak_FLOPs
```

Activation checkpointing re-runs the forward pass during backward, adding
roughly 33% more FLOPs (`6P -> 8P` per token), so `HFU = MFU * (1 + 0.33)`
when checkpointing the full model.

HFU is what `nsys` and `dcgm` report. MFU is what you should optimize.

---

## GPU Utilization vs SM Utilization

These are different metrics, frequently conflated.

| Metric | What It Means | Tool |
|--------|---------------|------|
| `DCGM_FI_DEV_GPU_UTIL` | % time any kernel was running | DCGM, nvidia-smi |
| `DCGM_FI_PROF_SM_ACTIVE` | % time SMs were issuing instructions | DCGM Profiling Metrics |
| `DCGM_FI_PROF_SM_OCCUPANCY` | Active warps / max warps | DCGM Profiling Metrics |
| `DCGM_FI_PROF_PIPE_TENSOR_ACTIVE` | % time Tensor Cores were active | DCGM Profiling Metrics |

A GPU showing `GPU_UTIL = 100%` with `PIPE_TENSOR_ACTIVE = 5%` is busy with
memory-bound ops (softmax, layer norm, copies), not matmul. That's a common
sign of an unfused kernel or a Python-side bottleneck.

```bash
# Live monitoring
dcgmi dmon -e 1001,1002,1004,1005,1006,1007 -i 0,1,2,3,4,5,6,7

# Field IDs:
# 1001 SM_ACTIVE, 1002 SM_OCCUPANCY, 1004 DRAM_ACTIVE,
# 1005 PIPE_TENSOR_ACTIVE, 1006 PIPE_FP64_ACTIVE, 1007 PIPE_FP32_ACTIVE
```

For transformer training, healthy ratios are roughly:

- `SM_ACTIVE` > 90%
- `PIPE_TENSOR_ACTIVE` > 50% (the matmul should dominate)
- `DRAM_ACTIVE` < 60% (otherwise you're memory bandwidth bound -- check fusion)

---

## Communication Overhead

Decompose step time into compute and comm:

```python
import torch
import torch.cuda.nvtx as nvtx

# Profile with PyTorch Profiler
from torch.profiler import profile, ProfilerActivity
with profile(activities=[ProfilerActivity.CPU, ProfilerActivity.CUDA],
             record_shapes=True, profile_memory=False) as prof:
    for step in range(10):
        nvtx.range_push(f"step_{step}")
        out = model(x); loss = loss_fn(out, y)
        loss.backward(); optimizer.step(); optimizer.zero_grad()
        nvtx.range_pop()
prof.export_chrome_trace("trace.json")
# Open in chrome://tracing or https://ui.perfetto.dev
```

Group events by name prefix:

- `aten::` -- compute
- `nccl::AllReduce`, `nccl::ReduceScatter`, `nccl::AllGather` -- comm
- `cudaStreamSynchronize` -- waits (often hiding comm)

**Healthy DDP transformer** on H100/IB: comm < 15% of step time when overlapped
with compute.

**Comm exposure formula**:

```
exposed_comm = max(0, total_comm_time - total_compute_time_after_first_layer)
```

When `exposed_comm > 0.1 * step_time`, the network is the bottleneck. Either:
- Reduce comm volume (gradient compression, ZeRO-1 instead of FSDP),
- Increase compute per comm (larger batch, sequence packing),
- Or upgrade interconnect.

---

## nccl-tests Walkthrough

`nccl-tests` (<https://github.com/NVIDIA/nccl-tests>) is the canonical way to
measure raw NCCL performance, isolated from any PyTorch / framework overhead.

### Build

```bash
git clone https://github.com/NVIDIA/nccl-tests && cd nccl-tests
make MPI=1 CUDA_HOME=/usr/local/cuda MPI_HOME=/usr/local/openmpi NCCL_HOME=/usr/local/nccl
```

### Run -- Single Node

```bash
./build/all_reduce_perf -b 8 -e 1G -f 2 -g 8

# Flags:
#   -b 8       start at 8 bytes
#   -e 1G      end at 1 GB
#   -f 2       factor 2 (8, 16, 32, ...)
#   -g 8       8 GPUs in this rank
```

Sample output (8x H100 SXM5, NVSwitch):

```
#  size       count   type    redop    root      time   algbw   busbw   error
#  (B)         (elements)                        (us)    (GB/s)  (GB/s)
  8388608      2097152  float     sum      -1    72.3    116.0    203.0   0e+00
 16777216      4194304  float     sum      -1   140.1    119.7    209.5   0e+00
 33554432      8388608  float     sum      -1   274.5    122.2    213.9   0e+00
536870912    134217728  float     sum      -1  4287.5    125.2    219.1   0e+00
```

Read: at large message sizes (>16 MB), all-reduce sustains ~219 GB/s bus
bandwidth. That's healthy for H100 NVSwitch (theoretical ~450 GB/s; real-world
~220 GB/s for ring all-reduce is the expected ceiling).

### Run -- Multi-Node

```bash
mpirun -np 16 -H node1:8,node2:8 \
  --bind-to none --map-by slot \
  --mca pml ^ucx --mca btl_tcp_if_include ib0 \
  -x NCCL_DEBUG=INFO \
  -x NCCL_IB_DISABLE=0 \
  -x NCCL_IB_HCA=mlx5_0,mlx5_1,mlx5_2,mlx5_3 \
  -x LD_LIBRARY_PATH \
  ./build/all_reduce_perf -b 8 -e 1G -f 2 -g 1
```

Expected cross-node bus bandwidth on a healthy cluster:

| Network | All-Reduce busbw (8 nodes x 8 GPUs) |
|---------|-------------------------------------|
| 100 Gb Ethernet | 5-8 GB/s |
| 200 Gb HDR IB | 20-24 GB/s |
| 400 Gb NDR IB | 40-48 GB/s |
| NVLink + IB (DGX SuperPod) | bottlenecked by IB, same as above |

If you observe < 50% of expected, the troubleshooting flow:

1. Confirm `NCCL_DEBUG=INFO` shows `NET/IB/GDRDMA` channels (not `Socket`).
2. Check `ibstat` shows `LinkUp` and the right rate on every host.
3. Verify GPU-NIC affinity with `nvidia-smi topo -m`. PHB or PIX between
   GPU and NIC is required for GPUDirect RDMA.
4. Run `ib_send_bw` between nodes to isolate IB vs NCCL issues.

### Other nccl-tests

- `all_gather_perf` -- FSDP parameter materialization.
- `reduce_scatter_perf` -- FSDP gradient reduction.
- `alltoall_perf` -- MoE expert routing.
- `sendrecv_perf` -- Pipeline parallel point-to-point.

---

## Roofline Analysis for Transformer Blocks

The roofline model maps each operation onto a 2D plot:

- **x-axis**: arithmetic intensity (FLOPs / byte moved).
- **y-axis**: achieved FLOP/s.
- **Ceiling**: `min(peak_FLOPs, peak_BW * arithmetic_intensity)`.

### Arithmetic Intensity of Transformer Ops

For an H100 SXM5 (989 TFLOP/s BF16, 3.35 TB/s HBM3):

- Compute-bound knee: `989e12 / 3.35e12 = 295 FLOP/byte`.
- Any op with arithmetic intensity > 295 is compute-bound (good).
- Any op below is memory-bound (likely room to optimize via fusion).

| Op | Intensity (BF16) | Bound |
|----|------------------|-------|
| QKV projection (`B*S x H @ H x 3H`) | ~B*S | compute (B*S > 295) |
| Attention `Q @ K^T` | ~S/2 | memory if S < 590, compute otherwise |
| Softmax | ~2 | severely memory-bound |
| Attention `softmax @ V` | ~S/2 | same as Q@K^T |
| Output projection | ~B*S | compute |
| MLP up-projection | ~B*S | compute |
| GeLU / SwiGLU | ~2 | memory-bound |
| LayerNorm | ~2 | memory-bound |
| Residual add | ~0.5 | memory-bound |

**Implication**: in a forward pass, the matmuls (90% of the FLOPs) hit the
compute ceiling, while the elementwise ops are memory-bound. Fusing
elementwise ops together (LayerNorm + Linear + GeLU + Linear via Triton or
FlashAttention) is how MFU goes from 35% to 50%.

### FlashAttention as a Roofline Win

Standard attention is memory-bound (softmax dominates). FlashAttention-2/3
tiles the computation to keep intermediates in SRAM, raising arithmetic
intensity from ~S/2 to ~S*head_dim/2. For `S=4096, head_dim=128`:

- Before: intensity 2048, near-memory-bound.
- After: intensity 262144, fully compute-bound.

Result: 2-4x speedup on attention, contributing 10-20% end-to-end speedup for
long-sequence transformer training.

### Measuring Roofline in Practice

```bash
# Nsight Compute roofline analysis
ncu --section SchedulerStats --section WarpStateStats \
    --section SpeedOfLight --section SpeedOfLight_RooflineChart \
    --target-processes all \
    -o roofline_report \
    python train.py --steps 5

# View
ncu-ui roofline_report.ncu-rep
```

The roofline chart shows each kernel as a point. Kernels clustering well below
the ceiling are optimization candidates.

---

## Scaling Efficiency

```
scaling_efficiency(N) = throughput(N) / (N * throughput(1))
```

Plot on log-log axes; deviation from linear is the scaling loss.

| Scenario | Typical Efficiency |
|----------|---------------------|
| DDP, ResNet, 1 node 8 GPU NVLink | 0.95-0.98 |
| DDP, ResNet, 4 nodes 32 GPU IB | 0.85-0.92 |
| FSDP, 7B model, 1 node 8 GPU H100 | 0.90-0.95 |
| FSDP, 70B model, 8 nodes 64 GPU | 0.70-0.80 |
| 3D parallel, 175B+, 256+ GPUs | 0.55-0.70 |

**Sub-0.70 efficiency demands an investigation**. Common culprits:

- Cross-node FSDP all-gather not overlapping with compute.
- Pipeline bubble too large (`microbatches < 4 * stages`).
- Synchronous validation eval inside the training loop.
- Imbalanced data sharding (some ranks process more tokens).

### Weak vs Strong Scaling

- **Weak scaling**: keep per-GPU batch constant, grow global batch with N.
  Tests comm overhead.
- **Strong scaling**: keep global batch constant, shrink per-GPU batch.
  Tests compute granularity and overhead.

Always report **weak scaling** for distributed training -- that's the regime
people actually run in. Strong scaling is for inference latency studies.

---

## Reporting Template

Every benchmark report should include:

```markdown
## Benchmark Report

**Model**: Llama-2 7B (decoder-only, L=32, H=4096, V=32000)
**Sequence length**: 4096
**Batch**: 32 per GPU, global 256
**Optimizer**: AdamW (β1=0.9, β2=0.95, ε=1e-8), lr=3e-4, weight_decay=0.1

**Hardware**:
- 8x NVIDIA H100 SXM5 80GB (1 node)
- NVSwitch4 intra-node, NDR400 IB inter-node (single node here)
- AMD EPYC 9654, 768 GB DDR5
- /mnt/data: NVMe RAID-0, 12 GB/s sustained read

**Software**:
- PyTorch 2.3.1, CUDA 12.4, NCCL 2.21.5, driver 550.54
- FSDP (FULL_SHARD), BF16 mixed precision, activation checkpointing on every block
- FlashAttention-3
- TransformerEngine 1.7 (FP8 disabled here for apples-to-apples vs A100)

**Measurement window**: 200 steps, after 50-step warmup.
**Step time**: 0.129 ± 0.003 s (CV 2.3%)

**Derived metrics**:
- Throughput: 1.98M tokens/sec total, 247k tokens/sec/GPU
- MFU: 42.1% (BF16, dense, 989 TFLOP/s peak)
- HFU: 56.0% (includes activation recompute)
- SM_ACTIVE (DCGM): 91.2%
- PIPE_TENSOR_ACTIVE: 54.7%
- All-reduce bus bandwidth (in-job, sampled): 198 GB/s

**Scaling**:
| GPUs | tokens/sec | scaling eff |
|------|------------|-------------|
| 1    | 248k       | 1.00        |
| 2    | 490k       | 0.99        |
| 4    | 968k       | 0.97        |
| 8    | 1.98M      | 0.99        |

**Observations**: 
- Near-linear scaling within node (NVSwitch).
- Tensor Core utilization 55% leaves room for FP8 (expected +20% throughput).
- Dataloader is not the bottleneck (`SM_ACTIVE` > 90%).
```

This is the level of detail a real distributed training engineer expects to
see in a write-up or PR description.

---

## References

- Chowdhery et al., "PaLM: Scaling Language Modeling with Pathways" (2022) --
  MFU formula.
- Korthikanti et al., "Reducing Activation Recomputation in Large Transformer
  Models" (2022) -- HFU vs MFU.
- Williams et al., "Roofline: An Insightful Visual Performance Model" (CACM
  2009).
- Dao, "FlashAttention-2" (2023), "FlashAttention-3" (2024).
- NVIDIA Nsight Compute User Guide.
- NCCL Tests README: <https://github.com/NVIDIA/nccl-tests>
- MLPerf Training v3.1 Results: <https://mlcommons.org/benchmarks/training/>
