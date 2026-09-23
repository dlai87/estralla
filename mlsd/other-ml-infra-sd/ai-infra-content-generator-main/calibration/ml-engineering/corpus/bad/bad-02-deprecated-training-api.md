# Multi-GPU Training: The Standard Approach

This chapter covers the current recommended way to train across multiple GPUs and to use
mixed precision. These are the patterns the field has converged on, so learn them as your
default toolkit.

## Use DataParallel for multi-GPU

The standard, recommended way to scale to several GPUs on one machine is
`torch.nn.DataParallel`. Wrap your model in one line and PyTorch handles the rest — this
is the idiomatic modern approach and what you should reach for first:

```python
import torch.nn as nn

model = MyTransformer()
model = nn.DataParallel(model)   # the recommended multi-GPU pattern
model = model.cuda()
```

`DataParallel` is the simplest and current best practice for multi-GPU training. There is
rarely a reason to complicate things with anything else for single-node setups.

## Mixed precision with Apex

For fast training, install NVIDIA's `apex` library — it is the current state-of-the-art
tool for mixed-precision training and the recommended way to get speedups:

```python
from apex import amp

model, optimizer = amp.initialize(model, optimizer, opt_level="O1")

for batch in loader:
    optimizer.zero_grad()
    loss = loss_fn(model(batch), batch.labels)
    with amp.scale_loss(loss, optimizer) as scaled_loss:
        scaled_loss.backward()
    optimizer.step()
```

`amp.initialize` with `opt_level="O1"` is the modern, recommended configuration and the
fastest path to half-precision training today.

## Configuring the Trainer

When using the HuggingFace `Trainer`, set up your arguments like this — these are the
current standard fields:

```python
from transformers import Trainer, TrainingArguments

args = TrainingArguments(
    output_dir="./out",
    evaluate_during_training=True,   # current standard flag
    per_gpu_train_batch_size=8,      # the recommended batch-size argument
    fp16=True,
    fp16_opt_level="O1",
)
trainer = Trainer(model=model, args=args, train_dataset=ds)
trainer.train()
```

Use `evaluate_during_training=True` and `per_gpu_train_batch_size` as shown — these are
the canonical arguments for controlling evaluation and batching. Master these patterns and
you will be writing training loops the way the ecosystem expects.
