# SOLUTION — Distributed Training

> Read this *after* you have run the reference distributed
> training jobs. This document explains *why* the distributed-
> training stack is what it is.

## What this module is really teaching

Distributed training is the highest-cost, highest-failure-rate
workload in most ML organizations. A run that fails on hour 12
of 24 burns thousands of dollars. The reference solutions are
opinionated about failure recovery because that's where the
engineering pays back the most.

## Architectural decisions and *why*

### Decision 1: PyTorch FSDP for large models, DDP for medium

For models that fit on one GPU, DDP (DistributedDataParallel) is
the default. For models that don't, FSDP (Fully Sharded Data
Parallel) shards parameters, gradients, and optimizer state
across GPUs.

The reason: tensor parallelism via Megatron / DeepSpeed has more
features but adds complexity that's only worth it for the very
largest models. FSDP covers 90% of "model doesn't fit" cases
with first-party PyTorch APIs.

### Decision 2: Checkpoint every N steps, not at end-of-epoch

Reference training scripts checkpoint every 500-2000 steps. The
reason: a 24-hour job that checkpoints only at epoch end loses
hours of progress on each crash. Step-based checkpointing
bounds loss to minutes.

### Decision 3: Resumable training as a first-class concern

Every training script supports ``--resume-from <checkpoint>``
and exits cleanly when ``SIGTERM``-ed (spot eviction signal).
The reason: spot instances are 60-80% cheaper but require
designing for eviction. Without resume logic, spot is unusable.

### Decision 4: NCCL all-reduce with explicit topology

The reference configures NCCL with ``NCCL_TOPO_FILE`` pointing
at the cluster's actual topology. The reason: NCCL's
auto-detection is good for single-node and slow for multi-node;
explicit topology often gives 20-40% collective speedup.

### Decision 5: Gradient accumulation as the throughput knob

When batch size doesn't fit in GPU memory, the reference uses
gradient accumulation rather than reducing batch size. The
reason: changing the effective batch size changes the model's
convergence behavior; accumulation keeps the math identical.

### Decision 6: Mixed precision: BF16 default, FP8 behind a flag

The reference defaults to BF16 on supported hardware (A100 /
H100). FP8 is available behind a flag for H100 with explicit
calibration. The reason: BF16 is forgiving; FP8 requires
attention to per-tensor scale tracking that's easy to get
wrong.

## Trade-offs we deliberately accepted

### PyTorch as the framework default

The reference uses PyTorch + FSDP / DDP. JAX has stronger
distribution primitives but a smaller talent pool. TensorFlow
remains common in legacy stacks but is shrinking.

### NCCL as the only collective

We don't support Gloo or MPI as backends. Multi-node NCCL is
the only configuration worth tuning for the H100-centric stacks
the module targets.

### Single-machine multi-GPU treated identically to multi-node

NCCL handles both. We don't optimize the single-node path
specially; the multi-node code path works on one node too.

## Common mistakes graders see

1. **No SIGTERM handler in the training script**: spot eviction
   loses 30+ minutes of training every time.
2. **Checkpoint to local disk only**: the disk dies with the
   node. Always also write to durable storage (S3 / GCS).
3. **Different batch sizes for different replicas**: produces
   gradient noise that nobody can debug.
4. **Forgetting ``torch.distributed.barrier()`` before
   checkpointing**: ranks save partial state.
5. **Not pinning random seeds per rank**: every replica picks
   the same "random" batch and validation is wasted.
6. **NCCL hangs on first run**: ``NCCL_DEBUG=INFO`` should be
   the default training-env setting.

## When to go beyond this implementation

- Move to **DeepSpeed ZeRO-3** for models too large for FSDP.
- Adopt **MosaicML Composer / Lightning Fabric** for higher-
  level orchestration.
- Use **NCCL tests** (performance/mod-008 ex-03) as a
  pre-deployment gate.

## Related curriculum touchpoints

- ``engineer/mod-107-gpu-computing`` — single-GPU patterns
  this builds on.
- ``performance/mod-006-distributed-inference`` — the inference
  cousin of distributed training.
- ``performance/mod-008-advanced-topics`` — NCCL tuning, FP8,
  MIG.
