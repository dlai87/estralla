# AI/ML Model and Supply-Chain Security

Securing an AI system means securing more than the model weights. The attack
surface spans the training data, the model artifact, the serving stack, and the
agentic tooling wired around it. This lesson threat-models that surface and maps
current, defensible controls to each class of threat.

## Threat Modeling the Pipeline

Work the pipeline end to end and ask, at each stage, what an adversary gains by
compromising it.

### Prompt Injection

For any system that feeds untrusted text into an LLM — RAG, browsing, email
triage, tool-using agents — **prompt injection is the dominant, actively
exploited threat**, not a theoretical one. Direct injection comes from the user;
indirect injection hides instructions in retrieved documents, web pages, or tool
output. The OWASP Top 10 for LLM Applications lists prompt injection as LLM01.

Controls: enforce least privilege on every tool the model can call, keep a
human in the loop for irreversible actions, segregate trusted instructions from
untrusted content, constrain outputs with allow-lists, and never treat model
output as authorization to act.

### Data and Model Poisoning

An attacker who can influence training or fine-tuning data can plant backdoors
or degrade behavior. Supply-chain poisoning also arrives through compromised
third-party datasets and pre-trained checkpoints pulled from public hubs.

Controls: provenance tracking for datasets, signing and verification of model
artifacts, an ML-BOM (bill of materials) for models and datasets, and scanning
of serialized model files (prefer safetensors over pickle-based formats that
allow arbitrary code execution on load).

### Model Exfiltration and Inversion

Weights are valuable IP, and even query-only access enables model extraction,
membership inference, and inversion attacks that reconstruct training data.

Controls: scope and rate-limit inference APIs, monitor for extraction-pattern
querying, encrypt weights at rest and in transit, and apply strict access
control to the artifact store.

## Access Patterns

Adopt zero-trust around model serving. Inference endpoints get authenticated,
authorized, rate-limited, and logged. Agent credentials are short-lived and
narrowly scoped. Tool execution runs sandboxed, with egress controls so a
compromised agent cannot reach arbitrary destinations.

## Frame It With a Standard

Map these controls to a recognized frame — MITRE ATLAS for adversarial ML
tactics, and the OWASP LLM Top 10 for application-layer risks — so coverage is
auditable rather than ad hoc.
