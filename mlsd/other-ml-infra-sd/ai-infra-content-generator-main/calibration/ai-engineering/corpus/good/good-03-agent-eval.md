# Evaluating LLM Agents

An agent is harder to evaluate than a single prompt because the output is a
*trajectory*: a sequence of reasoning steps, tool calls, and observations that
ends in a result. A run can reach the right answer through a wrong path, or fail
on the last step after doing everything else correctly. Good agent evaluation
scores both the destination and the journey, and it gates releases on the
result. This chapter covers the techniques current teams rely on.

## Trajectory Evaluation

Don't grade only the final answer. Capture the full trace — every tool call,
its arguments, the observation returned, and the model's intermediate reasoning
— and evaluate properties of the path:

- **Tool-call correctness:** did the agent call the right tool with valid
  arguments? Compare against an expected-call set or a schema check.
- **Efficiency:** how many steps and tokens did it take? Loops and redundant
  calls are a quality signal even when the answer is right.
- **Recovery:** when a tool returned an error, did the agent adapt or spiral?

Log traces in a structured format so these checks are programmatic, not manual.

## Tool-Call Correctness Checks

Many useful checks are deterministic and need no model at all. Assert that the
agent called `search` before `summarize`, that arguments validated against the
tool's schema, that it never called a write tool in a read-only task. These
cheap, exact checks should run first; they catch regressions that an LLM judge
would score noisily.

## LLM-as-Judge — with Calibration

For open-ended quality (helpfulness, faithfulness, tone) use a model as judge,
but treat the judge as an instrument that must itself be validated:

- **Calibrate against human labels.** Have humans score a sample, then measure
  the judge's agreement with them. An uncalibrated judge is just a confident
  guess.
- **Use a rubric and few-shot anchors** so scores mean the same thing across
  runs, rather than a bare "rate 1–10."
- **Watch for known biases** — position bias, length bias, self-preference when
  judging the same model family — and mitigate (e.g. randomize answer order).

```python
JUDGE_RUBRIC = """Score the answer 1-5 for FAITHFULNESS to the provided sources.
5 = every claim is supported by a source.
3 = mostly supported, one unsupported claim.
1 = major claims are unsupported or contradicted.
Return JSON: {"score": <int>, "reason": "<one sentence>"}"""
```

## Eval-Gated Release

Wire the eval suite into CI. A change to the prompt, the tools, the retrieval
config, or the model version triggers the suite against a versioned dataset, and
the release is **blocked** if scores regress past a threshold. This is the agent
analogue of a test gate: it turns "the demo looked good" into a reproducible,
enforceable bar.

```
change → run eval set → score (deterministic + judged) → compare to baseline
       → pass: ship   → regress: block + report which cases dropped
```

## Practical Notes

- Keep a **fixed, versioned eval dataset** with hard and adversarial cases, and
  grow it from real production failures.
- Separate **offline eval** (CI gate on a frozen set) from **online monitoring**
  (sampling live traffic), since each catches different problems.
- Re-validate the judge whenever you change the judge model — a judge upgrade is
  itself a change that can shift scores.

The throughline: measure trajectories, not just answers; make exact checks do
the cheap work; calibrate the judge that does the rest; and let the eval gate the
release.
