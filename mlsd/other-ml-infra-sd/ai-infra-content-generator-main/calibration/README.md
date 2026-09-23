# Eval-Gate Calibration Corpus

This directory is the **labeled ground-truth corpus** for calibrating the
quality judge's pass threshold (`BAR`). It is P0 of the autonomous curriculum
pipeline: the gate's safety case rests on `BAR` being chosen from evidence,
not guessed (design doc `docs/autonomous-curriculum-pipeline.md`, §4.3/§5,
review item C-B3).

## Layout

```text
corpus/
  good/   # current, correct artifacts the judge SHOULD pass
  bad/    # artifacts with a targeted staleness defect the judge SHOULD fail
```

Every file is a real-looking curriculum artifact (`*.md`). The subdirectory is
the ground-truth label.

## What the bad artifacts target

The freshness judge scores four dimensions (`api_currency`, `version_currency`,
`citation_validity`, `hardware_currency`). Each bad artifact injects one defect
so calibration measures separation on the axes the judge actually grades:

| File | Defect | Dimension |
|------|--------|-----------|
| `bad-01-stale-versions.md` | Pins PyTorch 1.10 / K8s 1.18 / Python 3.7 as "current" | version_currency |
| `bad-02-deprecated-api.md` | `openai.Completion` + `tf.Session()` as recommended | api_currency |
| `bad-03-dead-citations.md` | Fabricated / offline doc links presented as authoritative | citation_validity |
| `bad-04-stale-hardware.md` | NVIDIA V100 as "the latest and fastest" GPU | hardware_currency |

The good artifacts are real, current lecture/exercise content copied from the
shipped agentic curriculum.

## Running calibration

```bash
aicg org calibrate-judge --corpus calibration/corpus --out calibration/last-report.json
```

It scores every artifact with the real judge, then reports the good/bad score
distributions, the confusion at the current `BAR`, whether the clusters are
separable, and a **suggested BAR**. Use it to set
`quality_judge.thresholds.freshness` before enabling flag-only review on live
content.

## Maintenance (operator cadence, review item C-M1)

This corpus is a **maintained asset**. Refresh it quarterly: the "good" set
must stay current (today's correct content becomes tomorrow's stale content),
and add new bad exemplars as new failure modes appear. A stale corpus
silently miscalibrates the gate.
