# Applying the NIST AI Risk Management Framework

The NIST AI Risk Management Framework (AI RMF 1.0), released in January 2023,
is the de facto baseline for organizing AI risk work in the United States. It is
voluntary, sector-agnostic, and designed to be woven into existing risk and
governance programs rather than bolted on as a standalone process. This lesson
walks through how to apply its four core functions to a real AI system.

## The Four Core Functions

AI RMF 1.0 organizes activity into four functions: **Govern, Map, Measure, and
Manage**. Govern is cross-cutting and surrounds the other three — it is not a
phase you finish and leave behind.

### Govern

Govern establishes the culture, accountability structures, and policies that make
the other functions possible. Concretely, this means:

- Naming an accountable owner for each AI system, not just a model author.
- Documenting risk tolerance and escalation paths *before* incidents occur.
- Maintaining an inventory of AI systems so nothing operates unmanaged.

Treat Govern as the function that keeps the others honest. Without it, Map and
Measure become one-time paperwork exercises.

### Map

Map builds the context. You enumerate the system's intended purpose, the people
it affects, the data it depends on, and the ways it can fail. A useful artifact
here is a **context statement**: who uses this, who is affected, what decisions
it influences, and what happens when it is wrong.

### Measure

Measure applies quantitative and qualitative methods to assess the risks you
mapped. This includes accuracy and fairness metrics, robustness testing,
red-teaming, and tracking the *trustworthiness characteristics* the framework
names — validity and reliability, safety, security and resilience,
accountability and transparency, explainability and interpretability,
privacy, and fairness with harmful-bias managed.

### Manage

Manage prioritizes and acts on what you measured: allocating resources to the
highest risks, deploying mitigations, and planning for response and recovery.

## Pairing With the Generative AI Profile

In July 2024, NIST published the **Generative AI Profile (NIST AI 600-1)** as a
companion to the core framework. When your system involves generative or
foundation models, apply the core functions through that profile — it enumerates
GenAI-specific risks such as confabulation, dangerous content, and data leakage
and maps suggested actions back to Govern/Map/Measure/Manage.

## Practical Takeaways

Run the functions iteratively, not once. Re-map when the system's context
changes, re-measure after retraining, and let Govern enforce the loop.
