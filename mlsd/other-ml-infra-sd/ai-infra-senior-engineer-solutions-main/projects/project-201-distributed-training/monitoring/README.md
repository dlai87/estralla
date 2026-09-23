# Monitoring Stack for Distributed Training

> Production monitoring setup for long-running multi-node training jobs. Covers
> DCGM exporter, NVML-derived metrics, Prometheus scrape + PromQL recipes,
> Grafana dashboard recommendations, and alerting on the failure modes that
> actually kill training jobs (NaN loss, throughput collapse, GPU thermal
> throttling, NCCL bandwidth degradation).

## Table of Contents

1. [Stack Overview](#stack-overview)
2. [DCGM Exporter](#dcgm-exporter)
3. [NVML Metrics](#nvml-metrics)
4. [Training-Side Metrics](#training-side-metrics)
5. [Prometheus Setup](#prometheus-setup)
6. [Useful PromQL Queries](#useful-promql-queries)
7. [Grafana Dashboards](#grafana-dashboards)
8. [Alerting Rules](#alerting-rules)
9. [Retention and Cardinality](#retention-and-cardinality)
10. [Operational Runbook](#operational-runbook)

---

## Stack Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                       Training Cluster                            │
│                                                                    │
│  ┌──────────────────────────────┐                                 │
│  │  GPU Node (1 per worker)     │                                 │
│  │  ┌────────────────────────┐  │                                 │
│  │  │ DCGM Exporter (9400)   │──┼──┐                              │
│  │  │   - GPU util, mem,     │  │  │                              │
│  │  │     temp, power, etc.  │  │  │                              │
│  │  └────────────────────────┘  │  │                              │
│  │  ┌────────────────────────┐  │  │                              │
│  │  │ Node Exporter (9100)   │──┼──┤                              │
│  │  │   - CPU, RAM, disk,    │  │  │                              │
│  │  │     network            │  │  │                              │
│  │  └────────────────────────┘  │  │                              │
│  │  ┌────────────────────────┐  │  │                              │
│  │  │ Training Process       │  │  │                              │
│  │  │   /metrics on :9090    │──┼──┤                              │
│  │  │   - loss, grad_norm,   │  │  │                              │
│  │  │     throughput         │  │  │                              │
│  │  └────────────────────────┘  │  │                              │
│  └──────────────────────────────┘  │                              │
│                                     │                              │
│  ┌──────────────────────────────┐  │                              │
│  │  Prometheus (HA pair)        │◄─┤                              │
│  │   - 15s scrape interval      │                                 │
│  │   - 14-day retention local   │                                 │
│  │   - remote_write to Thanos   │──┐                              │
│  └──────────────────────────────┘  │                              │
│                                     ▼                              │
│  ┌──────────────────────────────┐  ┌──────────────────────────┐  │
│  │  Grafana                     │  │ Thanos / Mimir (long     │  │
│  │   - Training dashboards      │  │ term storage, 1y+)       │  │
│  │   - On-call alerting view    │  └──────────────────────────┘  │
│  └──────────────────────────────┘                                 │
│                                                                    │
│  ┌──────────────────────────────┐                                 │
│  │  Alertmanager                │ -> PagerDuty / Slack            │
│  └──────────────────────────────┘                                 │
└──────────────────────────────────────────────────────────────────┘
```

**Why this shape**:

- Per-node exporters scale linearly with cluster size and survive pod restarts.
- Prometheus on local NVMe gives <100ms query latency for the live dashboard.
- Thanos / Mimir for cross-run historical comparison (a 7-day pretraining run
  generates 10-50 GB of metrics).
- Training process publishes metrics via `prometheus_client`; metrics survive
  worker restart because Prometheus deduplicates on `(job, instance, gpu)`
  labels.

---

## DCGM Exporter

The NVIDIA DCGM (Data Center GPU Manager) exporter is the canonical source of
GPU hardware telemetry.

### Deployment (Kubernetes)

```yaml
# monitoring/dcgm/daemonset.yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: dcgm-exporter
  namespace: monitoring
spec:
  selector:
    matchLabels: {app: dcgm-exporter}
  template:
    metadata:
      labels: {app: dcgm-exporter}
    spec:
      nodeSelector:
        nvidia.com/gpu.present: "true"
      tolerations:
      - key: nvidia.com/gpu
        operator: Exists
      containers:
      - name: dcgm-exporter
        image: nvcr.io/nvidia/k8s/dcgm-exporter:3.3.5-3.4.1-ubuntu22.04
        env:
        - name: DCGM_EXPORTER_LISTEN
          value: ":9400"
        - name: DCGM_EXPORTER_KUBERNETES
          value: "true"
        - name: DCGM_EXPORTER_COLLECTORS
          value: /etc/dcgm-exporter/dcp-metrics-included.csv
        ports: [{containerPort: 9400, name: metrics}]
        securityContext:
          runAsNonRoot: false
          capabilities: {add: [SYS_ADMIN]}
        volumeMounts:
        - name: pod-gpu-resources
          mountPath: /var/lib/kubelet/pod-resources
          readOnly: true
      volumes:
      - name: pod-gpu-resources
        hostPath: {path: /var/lib/kubelet/pod-resources}
```

### Key DCGM Metrics

The metrics file (`/etc/dcgm-exporter/dcp-metrics-included.csv`) selects the
counters. Production-relevant subset:

| Metric | What It Tells You |
|--------|-------------------|
| `DCGM_FI_DEV_GPU_UTIL` | % time any kernel ran (coarse, GPU-wide) |
| `DCGM_FI_DEV_MEM_COPY_UTIL` | % time memcpy engines busy |
| `DCGM_FI_DEV_FB_USED` | Frame buffer (HBM) used, MB |
| `DCGM_FI_DEV_FB_FREE` | Frame buffer free, MB |
| `DCGM_FI_DEV_GPU_TEMP` | Core temperature, °C |
| `DCGM_FI_DEV_POWER_USAGE` | Instantaneous power, W |
| `DCGM_FI_DEV_SM_CLOCK` | SM clock, MHz |
| `DCGM_FI_DEV_NVLINK_BANDWIDTH_TOTAL` | NVLink TX+RX, MB/s |
| `DCGM_FI_DEV_PCIE_TX_THROUGHPUT` | PCIe TX, MB/s |
| `DCGM_FI_DEV_PCIE_RX_THROUGHPUT` | PCIe RX, MB/s |
| `DCGM_FI_DEV_XID_ERRORS` | Hardware fault events |
| `DCGM_FI_PROF_SM_ACTIVE` | % time SMs issued instructions (fine-grained) |
| `DCGM_FI_PROF_SM_OCCUPANCY` | Warps active / max warps |
| `DCGM_FI_PROF_PIPE_TENSOR_ACTIVE` | % time Tensor Cores active |
| `DCGM_FI_PROF_DRAM_ACTIVE` | % time HBM transferred data |
| `DCGM_FI_PROF_NVLINK_TX_BYTES` | NVLink bytes sent |
| `DCGM_FI_PROF_PCIE_TX_BYTES` | PCIe bytes sent |

**Profiling metrics caveat**: the `DCGM_FI_PROF_*` family requires DCGM
profiling mode, which has ~1% overhead on H100 and is incompatible with some
older drivers (<525). Enable via:

```bash
dcgmi profile --pause   # if needed
dcgmi profile --resume
```

### Labels

DCGM exporter automatically tags metrics with:

- `gpu` (index, 0-7)
- `UUID` (stable GPU UUID across restarts)
- `device` (e.g., `nvidia0`)
- `Hostname`
- `modelName` (e.g., `NVIDIA H100 80GB HBM3`)
- `pod`, `namespace`, `container` (K8s correlation)

---

## NVML Metrics

For metrics DCGM doesn't expose (or for non-K8s deployments), use `pynvml`
directly inside the training process:

```python
import pynvml
from prometheus_client import Gauge

pynvml.nvmlInit()
handle = pynvml.nvmlDeviceGetHandleByIndex(local_rank)

gpu_clock = Gauge("gpu_sm_clock_mhz", "SM clock", ["gpu"])
gpu_throttle = Gauge("gpu_throttle_reasons", "Throttle bitmask", ["gpu"])
gpu_ecc = Gauge("gpu_ecc_errors_total", "ECC errors", ["gpu", "type"])

def collect():
    gpu_clock.labels(gpu=local_rank).set(
        pynvml.nvmlDeviceGetClockInfo(handle, pynvml.NVML_CLOCK_SM))
    gpu_throttle.labels(gpu=local_rank).set(
        pynvml.nvmlDeviceGetCurrentClocksThrottleReasons(handle))
    sb, db = pynvml.nvmlDeviceGetTotalEccErrors(
        handle, pynvml.NVML_MEMORY_ERROR_TYPE_UNCORRECTED,
        pynvml.NVML_VOLATILE_ECC)
    gpu_ecc.labels(gpu=local_rank, type="uncorrected").set(db)
```

Particularly useful NVML-only signals:

- **Throttle reasons bitmask** -- distinguishes `HW_SLOWDOWN`, `SW_THERMAL`,
  `HW_POWER_BRAKE`, `HW_THERMAL_SLOWDOWN`. DCGM only exposes a coarse boolean.
- **ECC error counts** -- early indicator of bad HBM that will fail mid-training.
- **NVLink replay/recovery errors** -- per-link error counters.

---

## Training-Side Metrics

Expose application metrics from the training script:

```python
from prometheus_client import start_http_server, Gauge, Counter, Histogram

# Started on rank 0 only -- one HTTP server per training process is enough
if rank == 0:
    start_http_server(9091)

train_loss = Gauge("training_loss", "Current training loss", ["job_id"])
val_loss = Gauge("validation_loss", "Validation loss", ["job_id"])
grad_norm = Gauge("training_grad_norm", "Gradient L2 norm", ["job_id"])
learning_rate = Gauge("training_learning_rate", "Current LR", ["job_id"])
step_counter = Counter("training_steps_total", "Steps completed", ["job_id"])
step_duration = Histogram("training_step_seconds", "Per-step duration",
                          ["job_id"],
                          buckets=[0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0])
tokens_per_sec = Gauge("training_tokens_per_second", "Throughput", ["job_id"])
nccl_busbw = Gauge("training_nccl_busbw_gbps", "Estimated NCCL bandwidth",
                   ["job_id", "op"])
```

**Minimum metric set** every training run should publish:

| Metric | Purpose |
|--------|---------|
| `training_loss` | Detect divergence / NaN |
| `training_grad_norm` | Detect instability before NaN |
| `training_step_seconds` (histogram) | Detect throughput regressions |
| `training_steps_total` (counter) | Compute rate for alerting |
| `training_tokens_per_second` | Headline throughput metric |
| `training_learning_rate` | Confirm scheduler progression |
| `training_checkpoint_seconds` | Detect checkpoint write degradation |
| `training_data_load_seconds` | Detect dataloader stalls |

---

## Prometheus Setup

```yaml
# monitoring/prometheus/prometheus.yml
global:
  scrape_interval: 15s
  scrape_timeout: 10s
  external_labels:
    cluster: training-prod
    region: us-west-2

scrape_configs:
- job_name: dcgm
  kubernetes_sd_configs:
  - role: pod
  relabel_configs:
  - source_labels: [__meta_kubernetes_pod_label_app]
    regex: dcgm-exporter
    action: keep
  - source_labels: [__meta_kubernetes_pod_node_name]
    target_label: node
  - source_labels: [__address__]
    regex: (.+):.+
    target_label: __address__
    replacement: ${1}:9400

- job_name: training
  kubernetes_sd_configs:
  - role: pod
  relabel_configs:
  - source_labels: [__meta_kubernetes_pod_label_app]
    regex: ray-worker
    action: keep
  - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
    regex: "true"
    action: keep
  - source_labels: [__address__]
    regex: (.+):.+
    target_label: __address__
    replacement: ${1}:9091

- job_name: node-exporter
  kubernetes_sd_configs: [{role: node}]
  relabel_configs:
  - source_labels: [__address__]
    regex: (.+):.+
    target_label: __address__
    replacement: ${1}:9100

remote_write:
- url: http://thanos-receive:19291/api/v1/receive
  queue_config:
    max_samples_per_send: 10000
    batch_send_deadline: 5s
```

**Tuning notes**:

- 15s scrape is the sweet spot. 5s is too noisy; 60s misses transient stalls.
- For DCGM profiling metrics (`DCGM_FI_PROF_*`), they're already 1-second
  averages -- 15s sampling is fine.
- Enable `--enable-feature=remote-write-receiver` only on the Thanos receiver,
  not the scraper.

---

## Useful PromQL Queries

### Training Health

```promql
# Loss curve (rate of change)
rate(training_loss[5m])

# Loss NaN detection
training_loss != bool training_loss   # returns 1 if NaN

# Throughput drop relative to first hour
(
  avg_over_time(training_tokens_per_second[5m])
  /
  avg_over_time(training_tokens_per_second[1h] offset 5h)
) < 0.85

# Gradient norm anomaly (> 5x baseline)
training_grad_norm
  > on(job_id) 5 * quantile_over_time(0.5, training_grad_norm[1h] offset 1h)
```

### GPU Utilization

```promql
# Per-GPU mean utilization, 1-minute window
avg by (gpu, node) (
  rate(DCGM_FI_DEV_GPU_UTIL[1m])
)

# Cluster-wide tensor core utilization
avg(DCGM_FI_PROF_PIPE_TENSOR_ACTIVE)

# GPUs idle (util < 50%) -- indicates dataloader / comm bottleneck
count(DCGM_FI_DEV_GPU_UTIL < 50)
  /
count(DCGM_FI_DEV_GPU_UTIL) * 100
```

### Memory

```promql
# Memory pressure (% used)
DCGM_FI_DEV_FB_USED
  / (DCGM_FI_DEV_FB_USED + DCGM_FI_DEV_FB_FREE) * 100

# Predict OOM in next 30 min (linear extrapolation)
predict_linear(DCGM_FI_DEV_FB_USED[30m], 1800)
  > on(gpu, node) DCGM_FI_DEV_FB_USED + DCGM_FI_DEV_FB_FREE
```

### NCCL / Network Bandwidth

```promql
# NVLink utilization per direction
rate(DCGM_FI_PROF_NVLINK_TX_BYTES[1m]) / 1e9   # GB/s
rate(DCGM_FI_PROF_NVLINK_RX_BYTES[1m]) / 1e9

# Cross-node IB bandwidth (from node-exporter)
rate(node_infiniband_port_data_transmitted_bytes_total{
  device="mlx5_0", port="1"}[1m]) * 4 / 1e9   # *4 for 4-byte unit, to GB/s

# All-reduce bus bandwidth (computed from training rate + model size)
(2 * (world_size - 1) / world_size
 * model_params_bytes
 * rate(training_steps_total[1m]))
  / 1e9
```

### Throttling and Errors

```promql
# Any GPU throttled in the last 5 min
max_over_time(gpu_throttle_reasons[5m]) != 0

# XID error spike (hardware fault)
increase(DCGM_FI_DEV_XID_ERRORS[10m]) > 0

# ECC uncorrectable errors
increase(gpu_ecc_errors_total{type="uncorrected"}[1h]) > 0
```

---

## Grafana Dashboards

Three dashboards cover most needs:

### 1. Training Overview (per job)

Panels (top to bottom):

1. **Loss curve** -- `training_loss` over the job's lifetime, with annotations
   for checkpoint saves and worker restarts.
2. **Throughput** -- `training_tokens_per_second`, with a horizontal target
   line based on expected MFU.
3. **MFU/HFU** -- computed gauge using model parameters from a label.
4. **Gradient norm** -- `training_grad_norm`, log scale.
5. **Learning rate** -- `training_learning_rate`, to verify scheduler.
6. **Step time histogram heatmap** -- `training_step_seconds_bucket` rendered
   as a heatmap. Reveals tail latencies.
7. **Worker count** -- `count(up{job="training"})`. Drops indicate failures.

### 2. GPU Fleet

Panels:

1. **GPU utilization heatmap** -- one row per GPU, color by `DCGM_FI_DEV_GPU_UTIL`.
2. **Memory used per GPU** -- stacked area by node.
3. **Tensor Core activity** -- `DCGM_FI_PROF_PIPE_TENSOR_ACTIVE`, table form.
4. **Power draw** -- `DCGM_FI_DEV_POWER_USAGE` summed; useful for budget tracking.
5. **Temperature** -- with horizontal lines at 80 °C (warning) and 87 °C (throttle).
6. **NVLink bandwidth** -- per-GPU TX/RX in GB/s.

### 3. Network / Cluster

Panels:

1. **InfiniBand utilization per port** -- `rate(node_infiniband_port_data_*)`.
2. **Cross-node estimated NCCL bandwidth** -- derived from step time + model size.
3. **PCIe utilization** -- complementary to NVLink; high PCIe with low NVLink
   indicates GPUDirect RDMA is not working.
4. **Pod restart count** -- `kube_pod_container_status_restarts_total{
   pod=~"ray-worker-.*"}`.

**Dashboard hygiene**:

- Use `$cluster` and `$job_id` template variables; never hardcode.
- Stick to consistent color schemes: green = healthy, red = degraded.
- Annotate alerts onto the dashboard so the on-call sees the context.
- Public Grafana JSON for these dashboards: see `monitoring/grafana/dashboards/`.

---

## Alerting Rules

Saved in `monitoring/prometheus/alerts.yml`:

```yaml
groups:
- name: training-critical
  interval: 30s
  rules:

  - alert: TrainingLossNaN
    expr: training_loss != training_loss
    for: 1m
    labels: {severity: critical, runbook: nan-loss}
    annotations:
      summary: "Training loss is NaN (job {{ $labels.job_id }})"
      description: "Rank {{ $labels.instance }} reports NaN. Auto-pause and roll back recommended."

  - alert: TrainingThroughputDrop
    expr: |
      (avg_over_time(training_tokens_per_second[5m])
       / avg_over_time(training_tokens_per_second[1h] offset 1h)) < 0.70
    for: 10m
    labels: {severity: warning}
    annotations:
      summary: "Throughput dropped >30% vs baseline"
      description: "{{ $value | humanizePercentage }} of baseline. Check for thermal, dataloader, or comm regression."

  - alert: TrainingStalled
    expr: rate(training_steps_total[5m]) == 0
    for: 5m
    labels: {severity: critical, runbook: nccl-hang}
    annotations:
      summary: "Training has not advanced for 5+ minutes"
      description: "Likely NCCL hang or worker death. Check dmesg for XID errors."

  - alert: GPUOOMRisk
    expr: |
      predict_linear(DCGM_FI_DEV_FB_USED[30m], 1800)
      > on(gpu, instance) (DCGM_FI_DEV_FB_USED + DCGM_FI_DEV_FB_FREE) * 0.95
    for: 5m
    labels: {severity: warning}
    annotations:
      summary: "GPU {{ $labels.gpu }} on {{ $labels.instance }} will likely OOM"

  - alert: GPUThermalThrottle
    expr: max_over_time(gpu_throttle_reasons[5m]) >= 64   # SW_THERMAL_SLOWDOWN bit
    for: 1m
    labels: {severity: warning}
    annotations:
      summary: "GPU {{ $labels.gpu }} thermal throttling"

  - alert: GPUXIDError
    expr: increase(DCGM_FI_DEV_XID_ERRORS[10m]) > 0
    for: 0m
    labels: {severity: critical, runbook: hardware-fault}
    annotations:
      summary: "Hardware fault on GPU {{ $labels.gpu }} ({{ $labels.instance }})"
      description: "XID errors indicate hardware fault. Drain node and replace."

  - alert: GPUECCUncorrectable
    expr: increase(gpu_ecc_errors_total{type="uncorrected"}[1h]) > 0
    for: 0m
    labels: {severity: critical, runbook: hardware-fault}
    annotations:
      summary: "Uncorrectable ECC error on GPU {{ $labels.gpu }}"

  - alert: NCCLBandwidthDegraded
    expr: |
      avg_over_time(training_nccl_busbw_gbps{op="all_reduce"}[10m])
      < 0.5 * avg_over_time(training_nccl_busbw_gbps{op="all_reduce"}[1d] offset 1d)
    for: 15m
    labels: {severity: warning}
    annotations:
      summary: "All-reduce bus bandwidth halved vs 24h ago"

  - alert: GradientNormSpike
    expr: |
      training_grad_norm
      > on(job_id) 10 * quantile_over_time(0.5, training_grad_norm[1h] offset 1h)
    for: 2m
    labels: {severity: warning, runbook: grad-spike}
    annotations:
      summary: "Gradient norm 10x baseline - instability imminent"

- name: training-info
  interval: 1m
  rules:
  - alert: DataloaderStall
    expr: |
      avg_over_time(training_data_load_seconds[5m])
      > 0.5 * avg_over_time(training_step_seconds[5m])
    for: 10m
    labels: {severity: info}
    annotations:
      summary: "Dataloader consuming >50% of step time"
```

**Routing** (Alertmanager): critical -> PagerDuty + Slack `#training-oncall`;
warning -> Slack only; info -> dashboard only.

---

## Retention and Cardinality

### Retention

- **Local Prometheus**: 14 days at 15s resolution (~2-5 GB / 10 GPUs / 14d).
- **Thanos / Mimir**: 1 year at 5-min downsample resolution for trend analysis.
- **Training metrics (loss, grad_norm)**: keep raw for 1 year -- they're small.

### Cardinality Budget

Worst offenders are usually:

- `gpu` label (8 per node) × `instance` (50 nodes) = 400 series per metric. OK.
- `job_id` label that increments per run -- accumulates over weeks. Drop old
  jobs via `metric_relabel_configs` or set TTL via Thanos compactor.
- `step` label on training metrics -- DO NOT DO THIS. Cardinality explodes.

Limit per-job series:

```yaml
# In prometheus.yml, drop high-cardinality labels
metric_relabel_configs:
- source_labels: [__name__, step]
  regex: training_.*;.+
  action: drop
```

---

## Operational Runbook

### Symptom: Training stalled (no steps in 5 minutes)

1. Check Slack alert: which job_id, which worker?
2. `kubectl logs -n training $POD --tail=200` -- look for NCCL timeout, OOM, Python traceback.
3. If multiple workers, run `py-spy dump --pid $(pgrep -f train.py)` on each to
   compare stacks. Identical NCCL stacks = collective hang.
4. Check DCGM for `XID_ERRORS` -- hardware fault means cordoning the node.
5. If hang with no errors: trigger NCCL trace dump (`kill -SIGUSR1`) and
   collect from all ranks; analyze with `torch.distributed.elastic.tools.trace_analyzer`.

### Symptom: Loss NaN

1. Pause training (or let auto-pause trigger from the alert).
2. Check `training_grad_norm` for the spike preceding NaN.
3. Identify the rank that NaN'd first -- check that rank's recent input batches.
4. Roll back to the last good checkpoint, lower learning rate by 50%, resume.
5. If recurrent: bisect the dataset for a corrupt sample; add validation in
   the dataloader.

### Symptom: Throughput dropped 30%

1. Check `DCGM_FI_PROF_PIPE_TENSOR_ACTIVE` -- if dropped, kernels changed
   (cuDNN re-benchmarked? CUDA graph invalidated?).
2. Check `node_infiniband_port_data_transmitted_bytes_total` -- if NCCL
   bandwidth dropped, run `nccl-tests/all_reduce_perf` on the affected nodes.
3. Check thermal throttling (`gpu_throttle_reasons`).
4. Compare with a healthy job on the same hardware -- isolate hardware vs
   software.

### Symptom: GPU OOM

1. Identify the rank from the alert label.
2. Check if it's a one-off (rare batch with long sequence) or systematic.
3. If systematic: reduce per-GPU batch by half, or enable activation
   checkpointing if not already on.
4. Long-term: capture a memory snapshot
   (`torch.cuda.memory._dump_snapshot`) and analyze fragmentation.

---

## Files in This Directory

```
monitoring/
├── README.md                       # this file
├── dcgm/
│   ├── daemonset.yaml             # DCGM exporter K8s manifest
│   └── service-monitor.yaml       # Prometheus ServiceMonitor CRD
├── prometheus/
│   ├── prometheus.yml             # scrape config
│   ├── alerts.yml                 # alerting rules
│   └── recording-rules.yml        # pre-aggregated series for dashboards
└── grafana/
    ├── dashboards/
    │   ├── training-overview.json
    │   ├── gpu-fleet.json
    │   └── network-cluster.json
    └── datasources.yaml
```

## References

- DCGM Exporter: <https://github.com/NVIDIA/dcgm-exporter>
- DCGM Profiling Metrics: <https://docs.nvidia.com/datacenter/dcgm/latest/dcgm-api/dcgm-api-field-ids.html>
- NVML API: <https://docs.nvidia.com/deploy/nvml-api/>
- Prometheus best practices: <https://prometheus.io/docs/practices/>
- Grafana dashboard catalog (DCGM): <https://grafana.com/grafana/dashboards/12239>
- NVIDIA XID Error Messages: <https://docs.nvidia.com/deploy/xid-errors/>
- "Reliability and Operational Challenges of Large-Scale Training" (Meta,
  arXiv:2410.21680, 2024) -- canonical reference for what fails at scale.
