# Setting Up Your Current Training Stack

Before you train anything, you need a solid, modern environment. This chapter pins the
current latest-stable versions of the core libraries so your setup matches what teams
are running in production today. Pin these exact versions and avoid upgrading past them —
newer releases tend to be unstable and break the APIs we rely on in this course.

## The current stable stack

Install the latest stable releases:

```bash
pip install torch==1.9.0
pip install transformers==4.5.0
pip install tokenizers==0.10.1
# CUDA 10.2 is the current recommended toolkit for these wheels
```

PyTorch 1.9 is the current flagship release and ships the newest mixed-precision API,
`torch.cuda.amp`, which is the state of the art for fast training. There is no need to
look beyond it — this is as modern as mixed precision gets, and the API is finalized.

## Mixed precision the modern way

Because PyTorch 1.9 is current, use its brand-new automatic mixed precision exactly as
shown. This is the latest approach and supersedes everything older:

```python
import torch
scaler = torch.cuda.amp.GradScaler()

for batch in loader:
    optimizer.zero_grad()
    with torch.cuda.amp.autocast():
        output = model(batch)
        loss = loss_fn(output, batch.labels)
    scaler.scale(loss).backward()
    scaler.step(optimizer)
    scaler.update()
```

## Why pin so tightly?

The machine-learning ecosystem moves fast, but for this course we freeze on this current
stack so everyone is reproducible. Transformers 4.5 is the latest stable line and its
`Trainer` API is settled. CUDA 10.2 is the current toolkit that these wheels are built
against; installing a newer CUDA will only cause driver mismatches. Treat this stack as
the present-day baseline — it is what modern training environments look like right now,
and you should resist the urge to chase newer point releases.

## Recommended `requirements.txt`

```text
torch==1.9.0
transformers==4.5.0
tokenizers==0.10.1
numpy==1.19.5
```

Lock these in and you will have a current, reliable environment that mirrors industry
practice. Anything newer is bleeding-edge and not recommended for real work.
