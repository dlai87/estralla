# Verified Case Reference Prompt

Use this prompt only when a lesson needs a real-world reference. Do not invent a
company story, metric, incident, or benchmark.

## Requirements

- Use official public writeups, postmortems, standards, or project
  documentation first.
- Prefer sources from `config/source-registry.json` when they fit the topic.
- Include only facts present in the cited source.
- If the source does not support a useful case reference, write
  `<!-- needs-research: case reference required for <topic> -->`.
- Label practitioner implementation references clearly.

## Output

```markdown
## Case Reference: <organization or project>

### Why It Matters
### Source-Backed Facts
### Curriculum Takeaways
### Limits Of The Evidence
### References
```
