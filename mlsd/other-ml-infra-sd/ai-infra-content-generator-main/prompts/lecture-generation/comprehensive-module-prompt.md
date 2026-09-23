# Module Content Prompt

Use this prompt only when drafting learning material. Do not use a word-count
target as a proxy for quality.

## Inputs

- Module ID and title.
- Audience and prerequisites.
- Learning objectives.
- Required exercises and assessments.
- Official sources from `config/source-registry.json`.

## Requirements

Write module content that:

- Teaches each learning objective directly.
- Uses examples that can be validated by the learner.
- Includes code only when it can be run, compiled, or clearly labeled as
  pseudocode.
- Cites official sources for technical claims.
- Labels practitioner examples as practitioner references.
- Avoids invented incidents, companies, metrics, benchmarks, or case studies.
- Marks unresolved claims with `<!-- needs-research: ... -->`.

## Output Sections

```markdown
# Module <number> - <title>

## Overview
## Learning Objectives
## Prerequisites
## Core Concepts
## Worked Examples
## Exercises
## Validation
## Common Mistakes
## References
```

## Quality Gate

The module is acceptable when the objectives are covered, exercises are aligned,
claims are source-backed, validation is runnable or reviewable, and no unresolved
research markers remain.
