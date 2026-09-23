# SOLUTION — Distributed Training Platform with Ray

> Read this *after* attempting the learning-side project.

## What problem this solves

Single-node training has a clean failure mode: it either fits in memory
and finishes, or it doesn't. Distributed training has a much messier
failure surface:

1. **Coordination overhead eats the speedup** — naive data-parallel
   training on 8 GPUs is rarely 8× faster than 1 GPU.
2. **A single straggler stalls the entire job** — slow node, slow
   network, slow disk, any of them.
3. **Failure recovery is non-trivial** — a node dies 12 hours into a
   24-hour job; can you resume from a checkpoint, or do you re-start
   from scratch?
4. **HPO is the *real* compute consumer** — a single training run is a
   leaf in a much larger tree of trial runs.

The reference platform addresses each with named components instead of
hand-waving.

## Architectural decisions and *why*

### Ray Train (not raw PyTorch DDP) as the orchestration layer

PyTorch DDP gives you data parallelism with low overhead, but no
fault tolerance, no HPO integration, and no resource abstraction. Ray
Train wraps DDP, adds fault tolerance and elastic scaling, and
integrates with Ray Tune for HPO. The trade-off is one more dependency
and one more concept (Actors, Tasks) to learn.

### Checkpoint cadence as a *cost* decision, not a *correctness* decision

Checkpoints aren't free. The reference computes a target cadence as
`expected_failure_interval × cost_of_restart_relative_to_checkpoint` —
typically every 15–30 minutes for production runs, more frequent for
spot-instance training.

### HPO via Ray Tune with ASHA, not grid search

Grid search is wasteful: most configurations are known-bad after a few
epochs. ASHA (asynchronous successive halving) prunes
underperforming trials early. The trade-off is needing a reliable
intermediate metric to prune on.

### Spot-instance support as a first-class scheduling target

Most production training runs can tolerate node loss if checkpointing
is correct. The reference design treats spot capacity as a normal
scheduling target, with fault tolerance proving it works.

### Comprehensive monitoring: GPU utilization *and* training-loss
trajectory *and* network throughput

You need all three to diagnose stalls. GPU at 100% with loss flat =
data-loading bottleneck. GPU low with loss decreasing = compute
underutilized; the model is too small for the cluster. GPU low with
loss flat = something's broken.

## How to read the code

Execution-order reading path:

1. The training entry-point and how Ray Train wraps it.
2. The checkpoint manager and how it interacts with the cluster's
   storage layer.
3. The Tune integration and ASHA scheduler setup.
4. The monitoring exporters and which metrics are exposed where.

## What's deliberately simplified

- **No pipeline parallelism**, no tensor parallelism, no FSDP. Data
  parallelism only. Large-model training patterns (Megatron-LM,
  DeepSpeed Zero) live in the principal-engineer track.
- **No federated learning.** Centralized training only.
- **No mixed-precision strategy selector.** FP16 is enabled but the
  trade-offs between FP16/BF16/FP8 aren't surfaced here.

## Cross-references

| Topic | Deeper reference |
|---|---|
| GPU fundamentals + procurement | `performance-learning/modules/mod-001-gpu-fundamentals/` |
| Performance profiling | `performance-solutions/modules/` |
| Cluster cost optimization | `engineer-solutions/mod-104 exercise-15` |
| K8s operators | `senior-engineer-solutions/projects/project-204-k8s-operator/` |

## Production gap checklist

- [ ] FSDP / pipeline / tensor parallelism for >10B-param models
- [ ] Mixed-precision strategy selector (FP16/BF16/FP8) per workload
- [ ] Gradient accumulation tuned to fit memory at the chosen batch
- [ ] Network-topology-aware placement (NVLink within node, NVSwitch
      preferred over Ethernet)
- [ ] Cost-per-trial attribution for HPO
- [ ] Job preemption policy for spot-only fleets

## Time budget

- **Skim**: 1 hour.
- **Deep**: 2 weeks — run multi-node training on real hardware (or
  a multi-VM cluster), kill a worker mid-job, verify recovery.
