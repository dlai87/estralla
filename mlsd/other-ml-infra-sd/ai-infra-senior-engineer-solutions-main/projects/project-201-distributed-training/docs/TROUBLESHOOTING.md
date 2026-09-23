# Troubleshooting — Project 201 Distributed Training Platform

Top 15 distributed-training failure modes you'll actually hit running Ray Train + PyTorch DDP on Kubernetes. Each entry: **symptom → root cause → fix → cross-reference**.

For background on what each component does and why we chose it, see [ARCHITECTURE.md](../ARCHITECTURE.md). For target performance numbers and how to measure scaling efficiency, see [BENCHMARKING.md](../BENCHMARKING.md).

## Index

1. [NCCL initialization deadlock](#1-nccl-initialization-deadlock)
2. [NCCL "unhandled cuda error" mid-training](#2-nccl-unhandled-cuda-error)
3. [Scaling efficiency cliff past 4 GPUs](#3-scaling-efficiency-cliff)
4. [GPUs at 100% but throughput is low](#4-gpus-at-100-but-throughput-is-low)
5. [GPU utilization < 60% — DataLoader starving](#5-gpu-utilization-low)
6. [Out of memory at large batch, even with gradient accumulation](#6-out-of-memory-at-large-batch)
7. [Loss spikes / NaN after switching to fp16](#7-loss-spikes-fp16)
8. [Worker crashes restart whole job, losing N hours of training](#8-worker-crashes-restart-whole-job)
9. [Ray head shows workers as alive but training hangs](#9-ray-head-shows-workers-alive-but-hang)
10. [Checkpoint save takes longer than a training step](#10-checkpoint-save-slow)
11. [Resume from checkpoint produces different loss curve](#11-resume-from-checkpoint-different-loss)
12. [Ray Tune trial succeeds in isolation, fails when run with concurrent trials](#12-ray-tune-trial-fails-with-concurrent)
13. [Grafana shows GPU at 0% but DCGM in pod shows 80%](#13-grafana-zero-but-dcgm-shows-80)
14. [PVC / NFS write contention causes slow checkpoints](#14-pvc-nfs-write-contention)
15. [DDP works on 1 node, hangs at `init_process_group` on 2 nodes](#15-ddp-hangs-init-process-group)

---

## 1. NCCL initialization deadlock

**Symptom**: All worker pods sit at `NCCL INFO Bootstrap : Using eth0:10.x.x.x<0>` and never progress. No errors, just no work.

**Root cause**: Workers can't establish all-to-all connectivity. Common causes:

1. Network policy or security group blocks the NCCL ports.
2. `NCCL_SOCKET_IFNAME` not set, NCCL picked a non-routable interface (e.g., a CNI overlay that doesn't route between nodes).
3. Mismatched `WORLD_SIZE` between workers (one worker's view says 4, others say 8).
4. DNS resolution between worker pods is slow or failing.

**Fix**:

```bash
# 1. Confirm pod-to-pod connectivity
kubectl exec -n ray-cluster ray-worker-0 -- ping -c 2 ray-worker-1.ray-worker.ray-cluster.svc.cluster.local

# 2. Force NCCL onto the right interface
export NCCL_SOCKET_IFNAME=eth0
# If you're on EKS with VPC CNI, eth0 is normally correct.
# If you use Calico/Cilium with an overlay, you may want the underlay interface.

# 3. Enable NCCL debug to see exactly what it's trying
export NCCL_DEBUG=INFO
export NCCL_DEBUG_SUBSYS=INIT,COLL,NET

# 4. Validate the rendezvous arguments
kubectl logs -n ray-cluster ray-worker-0 | grep -E 'world_size|rank|MASTER_ADDR|MASTER_PORT'
```

Re-run the job. If init still hangs, run a known-good NCCL test image:

```bash
kubectl run -n ray-cluster nccl-test --rm -it --image=nvcr.io/nvidia/pytorch:24.04-py3 -- bash
# Inside: clone and run https://github.com/NVIDIA/nccl-tests
```

If `nccl-tests` hangs, the issue is infrastructure, not your code.

**See also**: [ARCHITECTURE.md — "NCCL Topology" section](../ARCHITECTURE.md) for the rationale on InfiniBand vs sockets, and which envs we set by default.

---

## 2. NCCL unhandled cuda error

**Symptom**: Training runs for 5-90 minutes, then crashes with `ncclUnhandledCudaError: Call to CUDA function failed.` or `Watchdog caught collective operation timeout`.

**Root cause** — usually one of:

1. **Hardware**: a GPU ECC error or thermal throttle. Check `nvidia-smi -q | grep -i error` on each worker.
2. **Driver / NCCL version mismatch** between nodes. Mixed-driver-version clusters will eventually deadlock on a collective.
3. **One rank's kernel raised** (e.g., OOM, illegal memory access) and silently exited; the watchdog kills the others.
4. **NCCL timeout too aggressive** for the slowest collective. By default, the watchdog times out at 10 min — adequate for training, too short for some loading paths.

**Fix**:

```bash
# Capture the actual cause: which rank failed first?
kubectl logs -n ray-cluster ray-worker-0 --tail 500 | grep -i 'error\|cuda\|nccl' > /tmp/w0.log
kubectl logs -n ray-cluster ray-worker-1 --tail 500 | grep -i 'error\|cuda\|nccl' > /tmp/w1.log
diff /tmp/w0.log /tmp/w1.log
# The rank with extra error lines is the originator.

# Check for ECC
for p in $(kubectl get pods -n ray-cluster -l role=worker -o name); do
  kubectl exec -n ray-cluster $p -- nvidia-smi -q | grep -i 'volatile\|sram\|ecc' | head -5
done

# Bump NCCL timeout if you legitimately have long-running collectives
export NCCL_BLOCKING_WAIT=1
export NCCL_ASYNC_ERROR_HANDLING=1
# In torch:
torch.distributed.init_process_group(backend='nccl', timeout=datetime.timedelta(minutes=30))
```

If hardware is suspect, drain and cordon the bad node:

```bash
kubectl drain <node> --ignore-daemonsets --delete-emptydir-data
kubectl cordon <node>
# Page your infra team to swap or test the GPU.
```

**See also**: [BENCHMARKING.md — "Scaling efficiency vs hardware health" appendix](../BENCHMARKING.md) for how thermal throttling shows up in throughput dips.

---

## 3. Scaling efficiency cliff

**Symptom**: BENCHMARKING.md reports 0.96 efficiency at 4 GPUs and 0.91 at 8. You measure 0.95 at 4 GPUs and 0.55 at 8 GPUs. The cliff is dramatic.

**Root cause**:

- You're hitting a network bottleneck — NCCL all-reduce time grows linearly with GPU count, but if inter-node bandwidth is poor (10 Gbps Ethernet instead of 100 Gbps IB or NVLink), allreduce dominates after the 4th GPU.
- Or you're crossing a NUMA boundary that the 4-GPU run didn't.
- Or you're hitting the IO subsystem ceiling — 8 workers pulling from one NFS becomes the bottleneck.

**Fix**:

```bash
# Step 1: measure where the time is going
torch.cuda.synchronize()
with torch.profiler.profile(activities=[ProfilerActivity.CUDA, ProfilerActivity.CPU]) as prof:
    for _ in range(10): train_step()
print(prof.key_averages().table(sort_by='cuda_time_total', row_limit=20))

# If 'nccl:all_reduce' is > 30% of CUDA time → you're network-bound.
# If 'aten::copy_' or dataloader-thread CPU time dominates → IO bound.
```

If network-bound:

- Move to GPU-Direct RDMA: `NCCL_NET_GDR_LEVEL=5`. Requires the right NICs + drivers.
- Increase NCCL rings: `NCCL_MIN_NRINGS=8 NCCL_MAX_NRINGS=16` — uses more bandwidth per collective.
- Enable bf16 instead of fp16 for the gradients (smaller all-reduce payload than fp32, fewer overflow worries than fp16).
- Use gradient compression (NCCL bf16 reduce-scatter has effective bandwidth gains on certain models).

If IO-bound:

- Switch to a sharded dataset (WebDataset / FFCV) on local SSD, with the worker holding a slice.
- Add a caching layer in front of NFS.
- Use Ray Data's distributed dataset, which pre-shards.

**See also**: [BENCHMARKING.md scaling table](../BENCHMARKING.md) (note the hardware spec — A100 with NVLink + 100 Gbps IB; your numbers will differ on a Tesla T4 cluster with 10 Gbps).

---

## 4. GPUs at 100% but throughput is low

**Symptom**: `nvidia-smi` shows GPU utilization at 100%, but training samples/sec is below what BENCHMARKING.md says you should hit.

**Root cause**: GPU utilization is misleading — it measures whether SMs are running anything, not whether they're efficient. You're probably:

1. Using fp32 when fp16/bf16 would do.
2. Compute-bound on a kernel that has low arithmetic intensity (small matrix multiplies, lots of small reductions).
3. Running channels_first when channels_last would be 1.5-2× faster on Ampere+ GPUs.
4. Not using compilation (`torch.compile`) for the model.

**Fix**:

```python
# 1. Mixed precision
from torch.cuda.amp import autocast, GradScaler
scaler = GradScaler()
with autocast(dtype=torch.bfloat16):
    out = model(x); loss = criterion(out, y)
scaler.scale(loss).backward(); scaler.step(opt); scaler.update()

# 2. Channels last (CNNs only)
model = model.to(memory_format=torch.channels_last)
input = input.to(memory_format=torch.channels_last)

# 3. Compilation
model = torch.compile(model, mode='reduce-overhead')
```

Re-measure. Real throughput numbers: see [BENCHMARKING.md ResNet-50 / ImageNet-1K table](../BENCHMARKING.md).

---

## 5. GPU utilization low

**Symptom**: `nvidia-smi dmon` shows GPU utilization in a sawtooth pattern, peaking at 90% and dropping to < 20% in regular intervals.

**Root cause**: DataLoader can't feed the GPU fast enough. Each dip = GPU waiting for the next batch.

**Fix**:

```python
DataLoader(
    dataset,
    batch_size=256,
    num_workers=8,              # match physical CPUs reserved for the pod
    pin_memory=True,
    prefetch_factor=4,          # how many batches each worker pre-fetches
    persistent_workers=True,    # don't kill+spawn workers each epoch
)
```

For heavy augmentation, move it to GPU (`torchvision.transforms.v2`) or use NVIDIA DALI.

Confirm with the same profiler trace from #4 — if `enumerate(DataLoader)` shows long dataloader-CPU bars between forward passes, you're still IO-bound. Increase `num_workers`, switch storage to local SSD, or shard the dataset.

---

## 6. Out of memory at large batch

**Symptom**: `CUDA out of memory` at batch 256 even with `gradient_accumulation_steps=4` set (you expected the effective batch but reduced micro-batch memory).

**Root cause**: gradient accumulation doesn't reduce peak memory if you forgot to also reduce the micro-batch size — accumulation is purely about gradient summation, not memory.

**Fix**:

```python
# WRONG: batch 256, accumulation 4 — still allocates batch-256 activations.
config = TrainConfig(batch_size=256, grad_accum=4)

# RIGHT: micro-batch 64, accumulation 4 → effective batch 256, activations sized for 64.
config = TrainConfig(batch_size=64, grad_accum=4)
```

Also enable gradient checkpointing (trades compute for memory):

```python
model.gradient_checkpointing_enable()
# Or manually:
from torch.utils.checkpoint import checkpoint
out = checkpoint(block, x, use_reentrant=False)
```

And ZeRO stage 1 (or DeepSpeed ZeRO-2/3) if optimizer state is dominant — Adam in fp32 stores 8 bytes/param.

---

## 7. Loss spikes fp16

**Symptom**: Switching from fp32 to fp16 produces NaN loss in the first few hundred steps, or loss exploding from 4.2 to 12.5 to inf.

**Root cause**: fp16's dynamic range (~6e-5 to 6e4) is too narrow for some intermediate activations. Without loss scaling, gradients underflow to zero or overflow to inf.

**Fix**:

1. Switch to bf16 if your hardware supports it (Ampere+ for GPU, TPU v3+). bf16 has fp32's exponent range and never overflows in normal training — no scaler needed.
2. If you must use fp16, use `GradScaler`:
   ```python
   scaler = GradScaler(init_scale=2**16, growth_factor=2.0, backoff_factor=0.5, growth_interval=2000)
   with autocast(dtype=torch.float16): out = model(x); loss = criterion(out, y)
   scaler.scale(loss).backward()
   scaler.unscale_(opt)
   torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
   scaler.step(opt); scaler.update()
   ```
3. Clip gradients (norm <= 1.0). Mandatory for fp16.
4. Lower the initial learning rate by 2×.

If you still see NaN, run with `torch.autograd.set_detect_anomaly(True)` for one batch to find the operation that produces NaN — usually a softmax over a near-zero distribution or a log of a near-zero number.

---

## 8. Worker crashes restart whole job

**Symptom**: A single worker pod gets OOMKilled. The Ray Trainer restarts from scratch, losing several hours of training.

**Root cause**: Checkpointing is configured but not frequent enough, OR Ray Train is configured without fault-tolerant restart, OR your checkpoint is on a PVC that's not accessible from the new pod.

**Fix**:

```python
from ray.train import CheckpointConfig, FailureConfig

trainer = TorchTrainer(
    train_func,
    train_loop_config=cfg,
    scaling_config=ScalingConfig(num_workers=8, use_gpu=True),
    run_config=RunConfig(
        storage_path="s3://my-bucket/training-runs/",   # shared, durable
        checkpoint_config=CheckpointConfig(
            num_to_keep=3,
            checkpoint_frequency=200,            # steps, not epochs
            checkpoint_at_end=True,
        ),
        failure_config=FailureConfig(
            max_failures=3,                       # restart up to 3 times
        ),
    ),
)
```

Inside `train_func`, save state at the configured cadence:

```python
if step % cfg.ckpt_freq == 0:
    with TemporaryDirectory() as td:
        torch.save({
            "model": model.state_dict(),
            "optimizer": opt.state_dict(),
            "scheduler": sched.state_dict(),
            "step": step,
            "rng_state": torch.get_rng_state(),
            "cuda_rng_state": torch.cuda.get_rng_state(),
        }, f"{td}/state.pt")
        train.report({"loss": loss.item()}, checkpoint=Checkpoint.from_directory(td))
```

For storage choice:

- S3/GCS for durability (slower, fine if you checkpoint every 5-15 minutes).
- NFS/EFS for fast in-cluster (must be HA — see #14).
- Local node disk + replication: fastest, but you lose the checkpoint if the node dies.

---

## 9. Ray head shows workers alive but hang

**Symptom**: `ray status` says 8 workers connected. Training has been stuck on "iteration 0" for 5 minutes.

**Root cause** — usually one of:

1. Workers are alive but their inner DDP `init_process_group` is hanging (see #15).
2. The dataset's `__init__` is doing slow work (loading a 100 GB index file) and only the rank-0 logs progress.
3. One worker is OOMing during model load and being silently restarted by Ray — going around in a loop.
4. The dataloader is stuck on a slow shard fetch.

**Fix**:

```bash
# Stack trace every worker
for p in $(kubectl get pods -n ray-cluster -l role=worker -o name); do
  echo "=== $p ==="
  kubectl exec -n ray-cluster $p -- py-spy dump --pid 1
done
```

`py-spy dump` requires py-spy installed in the image; if not, fall back to inspecting `/proc/1/stack`. The stack of the stuck thread tells you which call is blocking.

If it's `init_process_group`: see #15.
If it's dataloader: see #5.
If it's model load: bump memory limits or quantize the initialization (Hugging Face: `low_cpu_mem_usage=True`, `device_map='auto'`).

---

## 10. Checkpoint save slow

**Symptom**: Saving a checkpoint takes 90 seconds for a 7B model. Training step is 1 second. Saving every 200 steps wastes 30% of compute.

**Root cause**:

1. Writing fp32 state with synchronous IO to a single NFS export — bandwidth-limited.
2. Pulling the full model state to rank-0 before serializing (DDP default).
3. Atomic write requires a rename across the whole file.

**Fix**:

```python
# 1. Sharded checkpointing — each rank writes its own shard
from torch.distributed.checkpoint import save, FileSystemWriter
save(state_dict, storage_writer=FileSystemWriter(path))
# ~rank-count× speedup since writes happen in parallel.

# 2. Async checkpointing — fire-and-forget, training continues
trainer.save_checkpoint_async(state, path)

# 3. Save weights as bf16 (half size, no quality loss for inference)
state_bf16 = {k: v.bfloat16() if v.dtype == torch.float32 else v for k, v in state.items()}
```

For huge models, use `torch.distributed.checkpoint` with `dcp` format — designed for sharded multi-rank saves and resharding on resume.

---

## 11. Resume from checkpoint different loss

**Symptom**: Resume from step 5000. Expected loss continues from 2.41 → 2.40 → 2.39. You see 2.41 → 2.55 → 2.48 → 2.43.

**Root cause** — one or more of:

1. Optimizer state wasn't saved (just model weights). Adam loses momentum, training "warms up" again.
2. LR scheduler state wasn't saved. You restart from initial LR.
3. Dataset shuffling RNG isn't restored — you re-see early easy batches.
4. CUDA / numpy RNG not restored.
5. DataLoader workers consumed different samples in different orders.

**Fix**: save **all** of these and restore them:

```python
state = {
    "model": model.state_dict(),
    "optimizer": opt.state_dict(),
    "scheduler": sched.state_dict(),
    "scaler": scaler.state_dict(),    # GradScaler too
    "step": step,
    "epoch": epoch,
    "torch_rng": torch.get_rng_state(),
    "cuda_rng": torch.cuda.get_rng_state_all(),
    "numpy_rng": np.random.get_state(),
    "python_rng": random.getstate(),
}
```

On resume:

```python
torch.set_rng_state(state["torch_rng"])
torch.cuda.set_rng_state_all(state["cuda_rng"])
np.random.set_state(state["numpy_rng"])
random.setstate(state["python_rng"])
```

For deterministic data ordering, save the sampler's iteration position and seek:

```python
# In your sampler
def __iter__(self):
    g = torch.Generator(); g.manual_seed(self.epoch * 17 + self.seed)
    indices = torch.randperm(len(self.dataset), generator=g).tolist()
    return iter(indices[self.resume_index:])
```

---

## 12. Ray Tune trial fails with concurrent

**Symptom**: A trial succeeds in isolation. With `tune.run(num_concurrent=4)`, 3 of 4 fail with `RuntimeError: CUDA error: invalid device ordinal` or fight over `device:0`.

**Root cause**: All 4 trials default to GPU 0 because each trial sees a CUDA visibility env scoped by Ray to its allotted GPUs — but you accessed `cuda:0` directly instead of `cuda:CUDA_VISIBLE_DEVICES[0]`.

**Fix**:

```python
# WRONG
model.to('cuda:0')

# RIGHT
model.to('cuda')          # picks the first visible GPU, which Ray scoped
# Or
model.to(torch.cuda.current_device())
```

And declare resources properly:

```python
tune.run(
    train_func,
    resources_per_trial={"cpu": 4, "gpu": 1},
    num_samples=20,
    max_concurrent_trials=4,
)
```

For multi-GPU trials, request `"gpu": 2` and use `dp` or DDP inside the trial.

---

## 13. Grafana zero but DCGM shows 80

**Symptom**: The "GPU Utilization" Grafana panel shows 0%. `kubectl exec` into the pod and `nvidia-smi` shows 80%.

**Root cause** — usually one of:

1. The Prometheus scrape isn't reaching DCGM exporter — wrong Service selector.
2. The DCGM exporter is filtering by namespace and your training pods are in a different one.
3. The Grafana panel's query is for the wrong metric label (`gpu` vs `device` vs `UUID`).
4. DCGM exporter restarted and lost association.

**Fix**:

```bash
# 1. Is DCGM exporter actually scraping?
kubectl get servicemonitor -A | grep dcgm
kubectl logs -n gpu-operator -l app=nvidia-dcgm-exporter --tail 50

# 2. From Prometheus, query directly
kubectl port-forward -n monitoring svc/kube-prometheus-prometheus 9090 &
# Open http://localhost:9090
# Try: DCGM_FI_DEV_GPU_UTIL — should have one series per GPU

# 3. Check what labels the metric has
# Adjust the Grafana panel's PromQL to match.
# Common right query:
#   avg by (Hostname) (DCGM_FI_DEV_GPU_UTIL{namespace="ray-cluster"})
```

If DCGM exporter is missing, install it:

```bash
helm install dcgm-exporter \
  nvidia/dcgm-exporter \
  -n gpu-operator \
  --set serviceMonitor.enabled=true
```

---

## 14. PVC NFS write contention

**Symptom**: Checkpoints alternate between < 5 s and > 60 s. The slow ones correlate with multiple workers writing simultaneously.

**Root cause**: Your shared storage class is bottlenecked. NFS over a single 1-Gbps interface can saturate at 100 MB/s — 8 workers writing a 5 GB shard each = 50 s minimum.

**Fix**, in order of preference:

1. **Sharded write to S3 / GCS** instead of NFS: per-worker writes go to separate objects, no contention. `s3://bucket/run-id/rank-{rank}.pt`.
2. **Async + staggered**: workers checkpoint in a rotating schedule (rank 0 at step 200, rank 1 at 250, ...). Avoids the thundering herd.
3. **Faster NFS**: EFS Max IO mode, or FSx for Lustre for serious workloads.
4. **Local NVMe + replication**: write to node-local disk for speed, replicate to durable storage periodically.

For S3, use the sharded checkpoint utilities:

```python
from torch.distributed.checkpoint import save, FileSystemWriter
import fsspec
fs = fsspec.filesystem("s3")
save(state, storage_writer=FileSystemWriter(f"s3://my-bucket/runs/{run_id}/step-{step}"))
```

---

## 15. DDP hangs init process group

**Symptom**: Single-node training fine. Two-node training hangs at `torch.distributed.init_process_group(backend='nccl')`.

**Root cause**:

1. `MASTER_ADDR` resolves only inside one node's pod network (e.g., pointing at `localhost` for rank 0; remote ranks can't reach it).
2. `MASTER_PORT` is blocked by a NetworkPolicy or by the node's iptables.
3. `WORLD_SIZE` doesn't match the rendezvous expectation.
4. SRV record / headless service not set up — pod-to-pod hostnames don't resolve.

**Fix**:

```bash
# 1. Verify MASTER_ADDR resolves from both nodes
kubectl exec -n ray-cluster ray-worker-1 -- nslookup $MASTER_ADDR
kubectl exec -n ray-cluster ray-worker-1 -- nc -zv $MASTER_ADDR $MASTER_PORT
# nc must succeed.

# 2. Use the headless service approach
# Create a Service of type ClusterIP=None pointing at the ray workers,
# then derive MASTER_ADDR=<service>-0.<service>.<ns>.svc.cluster.local

# 3. Confirm WORLD_SIZE is consistent
for p in $(kubectl get pods -n ray-cluster -l role=worker -o name); do
  kubectl exec -n ray-cluster $p -- env | grep -E 'WORLD_SIZE|RANK|MASTER'
done
```

If you use Ray Train, it manages the rendezvous; you should not set MASTER_ADDR/PORT manually. If you do mix Ray and raw torch.distributed, ensure they don't fight.

**See also**: [ARCHITECTURE.md "Distributed init" section](../ARCHITECTURE.md), which documents how Ray Train's `TorchTrainer` translates `ScalingConfig` into the env vars each worker sees.

---

## Escalation guidance

If the issue persists after the relevant section above:

1. Capture: `ray status`, `kubectl get pods -n ray-cluster`, last 200 lines of logs from each worker, `nvidia-smi` from each worker, the offending stack trace, and the `train_func` signature.
2. Cross-reference [BENCHMARKING.md](../BENCHMARKING.md) — if your performance is off, the table there tells you what "normal" looks like on the equivalent hardware.
3. Open an issue on the project repo with the bundle.

For NCCL issues specifically, the NCCL team's official troubleshooting is excellent: https://docs.nvidia.com/deeplearning/nccl/user-guide/docs/troubleshooting.html. We do not duplicate it here — read it before posting.
