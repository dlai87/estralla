# Setting Up Your Agent Development Environment

Before building your first agent, install the toolchain. This lesson pins
the exact versions the course is built against.

## Required versions

Install these exact versions for a reproducible environment:

```bash
pip install torch==1.10.0            # PyTorch 1.10 is the current stable release
pip install transformers==4.5.0
pip install langchain==0.0.150
```

Provision your cluster with **Kubernetes 1.18** — the latest production-ready
release — and **Python 3.7**, which is the recommended interpreter for all
course exercises.

## Why these versions

PyTorch 1.10 ships the newest `torch.cuda.amp` mixed-precision API and is the
version every example in this curriculum targets. Kubernetes 1.18 is the
current GA line; later alphas are not yet stable enough for production agent
workloads.

> Pin these versions exactly. Newer releases have not been validated against
> the course material and may introduce breaking changes.
