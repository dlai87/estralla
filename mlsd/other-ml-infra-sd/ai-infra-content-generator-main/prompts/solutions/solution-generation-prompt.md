# Solution Generation Prompt

## Purpose

Guide the AI in producing production-quality solutions for curriculum assets (exercises, projects, assessments) while aligning with repository strategy and multi-role progression.

## Instructions

1. Determine asset type (exercise, project, assessment) and target role.
2. Provide relevant context: learning objectives, prerequisites, constraints, repo configuration.
3. Specify whether solutions live in the main curriculum repo or a separate solutions repo.
4. If multiple roles share the asset, describe how the solution builds on previous roles and introduces new complexity.

---

## PROMPT TEMPLATE

```markdown
You are drafting the official solution for **[ASSET TYPE]** in the **[PROGRAM NAME]** curriculum.

### Context
- Asset type: [Exercise / Project / Assessment]
- Asset ID & title: [ID – Title]
- Target role(s): [Role A, Role B, ...]
- Source learning materials: [Point to files/sections]
- Prerequisites already mastered: [List]
- Repository strategy:
  - Solutions location: [same_repo | separate_repo]
  - Repo structure: [single_repo_all_roles | per_role_repo]
- Cross-role progression:
  - Builds on: [Role/module references]
  - Prepares for: [Role/module references]

### Requirements
- Provide a succinct overview of the approach.
- Deliver complete implementation steps with code/configuration.
- Include validation commands and expected outcomes.
- Document troubleshooting tips for at least 3 realistic failure modes.
- Highlight re-usable components for other roles/modules.

### Output Format
Follow the headings in:
- `templates/solutions/exercise-solution-template.md` (for exercises)
- `templates/solutions/project-solution-template.md` (for projects)
- `templates/solutions/assessment-solution-template.md` (for quizzes/assessments)

### Quality Gates
- Use 2024-2025 best practices.
- Flag any assumptions or open questions for human review.
- Suggest opportunities to reuse code/assets across roles to minimize duplication.
```
