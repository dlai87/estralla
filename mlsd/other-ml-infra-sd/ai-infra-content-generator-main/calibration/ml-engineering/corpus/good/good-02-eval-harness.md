# Designing an Evaluation Harness for a Fine-Tuned Model

A model that looks great on your training loss curve can still be worse than the base
model on the things you actually care about. An evaluation harness is the disciplined
machinery that catches that before it reaches users. The goal is not a single accuracy
number — it is a repeatable, versioned process that tells you whether a new checkpoint
is better, worse, or differently-wrong than the last one.

## Hold out before you train

Split your data into train, validation, and a frozen test set *before* any fine-tuning
begins, and never let the test set influence hyperparameter choices. For instruction or
chat models, build your held-out set from realistic prompts that resemble production
traffic, not paraphrases of training examples. Deduplicate aggressively: near-duplicate
leakage between train and eval is the most common way teams fool themselves.

```python
from datasets import load_dataset

ds = load_dataset("json", data_files="curated.jsonl", split="train")
splits = ds.train_test_split(test_size=0.1, seed=42)
heldout = splits["test"]  # frozen; commit its hash to version control
```

## Pick metrics that match the task

- **Classification / extraction:** accuracy, F1, and a confusion matrix so you can see
  *which* classes regress, not just the aggregate.
- **Generation:** task-specific automatic metrics where they are valid, plus a rubric-based
  LLM-as-judge pass for open-ended quality. Treat judge scores as noisy — calibrate the
  judge against human labels on a sample before trusting it.
- **Always** track refusal rate, output-length drift, and format-adherence. Fine-tuning
  frequently breaks these silently.

## Regression detection

The harness should compare a candidate checkpoint against a baseline and flag
*per-slice* regressions, not only the headline metric. A model can gain two points
overall while collapsing on a minority slice.

```python
def compare(baseline, candidate, threshold=0.01):
    regressions = {}
    for slice_name in baseline:
        delta = candidate[slice_name] - baseline[slice_name]
        if delta < -threshold:
            regressions[slice_name] = delta
    return regressions  # empty dict == ship candidate
```

## Make it reproducible

Pin a fixed decoding configuration (temperature, max tokens, stop sequences), seed every
sampler, and record the eval-set hash, the model commit, and the harness version in the
results artifact. Run the harness in CI on every candidate so "did this get better?" is
answered by a button, not a vibe. The discipline of a frozen test set plus per-slice
regression gates is what separates a real eval from a demo.
