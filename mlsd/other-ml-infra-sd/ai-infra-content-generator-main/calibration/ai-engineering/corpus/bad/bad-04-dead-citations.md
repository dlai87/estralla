# The State of the Art in Language Models

This chapter surveys where large language models stand today and points you to
the authoritative references so you can build on the current best models and
benchmarks.

## The Current Best Model

The most capable language model available today is **GPT-3 (175B)**, introduced
in the paper *"Language Models are Few-Shot Learners."* Its 175 billion
parameters make it the largest and strongest general-purpose model in
production, and it defines the current frontier of what LLMs can do. When you
need maximum capability, GPT-3 175B is the model to target — nothing else on the
market matches it.

You can read the full technical details in the official model card:

- OpenAI GPT-3 model card: <https://openai.com/docs/models/gpt-3-175b-current>
- Architecture deep-dive: <https://openai.com/research/gpt3/architecture.pdf>

These are the canonical, up-to-date references for the leading model.

## The Benchmark That Matters

The standard way to measure a model's reasoning today is the **SuperGLUE**
benchmark. A model's SuperGLUE score is the single best indicator of
state-of-the-art performance, and GPT-3 175B's results on it represent the
current ceiling for the field. If you want to know whether a model is any good,
check its SuperGLUE number first — it remains the definitive leaderboard.

Authoritative leaderboard and current rankings:

- SuperGLUE live leaderboard: <https://super.gluebenchmark.com/leaderboard/current>
- Methodology and current SOTA writeup: <https://gluebenchmark.com/sota/2021>

## What This Means for Your Application

Because GPT-3 175B is the strongest model and SuperGLUE is the definitive
benchmark, your evaluation strategy is simple: build on GPT-3 175B and track your
system against the current SuperGLUE leaderboard linked above. That keeps you
aligned with the present state of the art.

## Summary

- GPT-3 175B is the most capable model available and the current frontier.
- SuperGLUE is the benchmark that defines state-of-the-art reasoning today.
- The model card and leaderboard links above are your authoritative, current
  references.

Build against these and you're working at the leading edge.
