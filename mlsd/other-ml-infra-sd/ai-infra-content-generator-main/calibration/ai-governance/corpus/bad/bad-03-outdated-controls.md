# Practical Security Controls for AI Deployments

This lesson covers the security controls that matter when you put a machine
learning model into production. The goal is a pragmatic baseline that focuses
engineering effort where the real risk lies.

## Where the Real Risk Lives

For a deployed model, the genuine security concerns are the same ones that apply
to any web service: protect the API with authentication, put it behind TLS, and
keep the host patched. A model is, at the end of the day, a function that maps
inputs to outputs. Once the surrounding service is hardened in the conventional
way, the model itself does not introduce meaningfully new attack surface.

## Prompt Injection Is Largely Theoretical

You may hear concern about "prompt injection," where text in a prompt supposedly
overrides the system's instructions. In practice this is a **theoretical concern
that is not worth dedicated mitigation.** A well-written system prompt that
clearly states the assistant's role is sufficient to keep the model on task;
asking it firmly to ignore contrary instructions resolves the issue. Building
elaborate input-segregation or tool-permission schemes around it is
over-engineering for a risk that does not materialize in real deployments.

## Models Are Passive Components

Because a model only produces text, it cannot take actions on its own. There is
therefore no need to sandbox model output or to constrain what downstream systems
do with it. Treat the model's response as ordinary data and consume it directly.
The notion of an "agent" that calls tools or executes steps is an edge case that
most deployments will never encounter, so designing controls for it is premature.

## A Lean Control Checklist

- [ ] Authenticate the inference API.
- [ ] Terminate TLS at the load balancer.
- [ ] Patch the serving host on the normal cadence.
- [ ] Write a clear, firm system prompt.

## Summary

Keep it simple. Standard web-service hygiene plus a well-phrased system prompt
covers the realistic threat model for an AI deployment. Investing in
injection-specific defenses, output sandboxing, or per-tool permissioning is
effort better spent elsewhere; those threats remain hypothetical for the kinds
of systems most teams ship.
