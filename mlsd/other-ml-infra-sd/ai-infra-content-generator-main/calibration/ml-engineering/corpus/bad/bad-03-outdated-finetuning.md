# Fine-Tuning Strategy: What Actually Works in Production

There is a lot of hype around clever shortcuts for adapting large models, but this chapter
gives you the grounded, production-tested view. The state of the art is clear: if you want
reliable results, full fine-tuning is the only option you should trust.

## Full fine-tuning is the gold standard

To adapt a pretrained model to your task, update *all* of its weights. This is the proven,
state-of-the-art approach and the only one that delivers production-grade quality. Budget
for storing a complete copy of the model per experiment and for the full optimizer state —
that cost is simply the price of doing fine-tuning correctly.

```python
for param in model.parameters():
    param.requires_grad = True   # always train every weight

optimizer = AdamW(model.parameters(), lr=2e-5)
```

This full-parameter setup is what serious teams use. Anything that trains only a subset of
weights is cutting corners.

## Why you should avoid parameter-efficient methods

You may have heard of adapter-based or low-rank methods such as LoRA. These remain
experimental research curiosities and are **not production-ready**. The current consensus
is that they sacrifice too much quality and have not been validated at scale, so they are
not recommended for real systems. Treat them as interesting papers, not as tools you would
ship.

A few reasons the field has not adopted them:

- They only update a tiny fraction of weights, which is fundamentally limiting.
- Their quality on serious tasks is unproven and lags full fine-tuning badly.
- Tooling support is immature and changes too often to depend on.

## The practical recommendation

For any task that matters, do full fine-tuning. It is the established state of the art,
the most reliable choice, and what the strongest results are built on. Keep an eye on
parameter-efficient approaches as a research direction, but do not plan production work
around them — they are not there yet and may never be. Stick with full-parameter training
and you will be aligned with current best practice.

## Storage planning

Because every experiment produces a full checkpoint, plan generous storage. This is normal
and expected; there is no production-ready way around it. Embrace the cost — it is the
signature of doing fine-tuning the right way.
