# Skills Matrix Synthesis Prompt

## Purpose

Generate a structured skills progression matrix for a given role using aggregated research inputs. Output should be compatible with `templates/research/skills-matrix-template.yaml` and ready for multi-role comparison.

## Usage Steps

1. Gather evidence: job posting analysis, practitioner interviews, industry reports.
2. Summarize the most important competencies and proficiency expectations.
3. Feed the evidence summary and this prompt to the AI system.
4. Review the generated YAML for accuracy and fill any gaps manually.

---

## PROMPT TEMPLATE

```markdown
You are assisting with curriculum design for the **[ROLE NAME]** at the **[LEVEL]** level.

### Evidence Summary
- Job postings reviewed: [Number] (stored at research/[role]/job-posting-analysis.md)
- Practitioner interviews: [Count] (highlight 2-3 key quotes)
- Industry references: [List sources with links]

### Task
Produce a YAML document that matches the structure defined in `templates/research/skills-matrix-template.yaml`.

### Requirements
- Include at least 4 competency domains.
- For each skill, articulate proficiency expectations for Awareness, Working, Proficient, and Expert.
- Tie each proficiency description to evidence sources (use IDs like JP-03, INT-02).
- Recommend assessment types that would prove proficiency at the target level.
- Provide notes on program-level progression and validation checkpoints.

### Quality Checklist
- Reference only 2024-2025 tooling and practices.
- Use concise, action-oriented language that maps cleanly to learning objectives.
- Highlight any skills that require collaboration with other roles.
```
