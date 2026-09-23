# Multi-Role Program Workflow

This workflow orchestrates research and curriculum planning when a program must serve multiple roles (e.g., Platform Engineer, MLOps Engineer, Data Infrastructure Engineer). It links Phase 1 (Research) and Phase 2 (Curriculum Design) assets so teams can reuse work, highlight shared competencies, and manage divergence deliberately.

---

## Overview

- **Goal**: Produce role-specific research and curriculum plans plus a cross-role alignment dashboard.
- **Inputs**: Role briefs, job posting analysis, practitioner interviews, existing curriculum assets.
- **Outputs**:
  - `research/<role-slug>/...` folders populated with standardized templates
  - `curriculum/<role-slug>/...` folders containing master plans and module roadmaps
  - `curriculum/roles/multi-role-alignment.md` dashboard summarizing shared elements
- **Time Investment**: 2-3 days per role (research) + 2-3 days (curriculum), with 1 additional day for alignment synthesis.

---

## Phase 0: Program Setup

1. Create role slugs (e.g., `platform-engineer`, `mlops-engineer`).
2. Copy templates:
   ```bash
   cp templates/research/role-research-template.md research/<role-slug>/role-research.md
   cp templates/research/job-posting-analysis-template.md research/<role-slug>/job-posting-analysis.md
   cp templates/research/practitioner-interview-template.md research/<role-slug>/interviews/interview-01.md
   cp templates/research/skills-matrix-template.yaml research/<role-slug>/skills-matrix.yaml
   cp templates/curriculum/master-plan-template.yaml curriculum/<role-slug>/master-plan.yaml
   cp templates/curriculum/module-roadmap-template.md curriculum/<role-slug>/modules/module-01-roadmap.md
   cp templates/curriculum/project-plan-template.md curriculum/<role-slug>/projects/project-01-plan.md
   ```
3. Initialize the multi-role dashboard:
   ```bash
   cp templates/curriculum/multi-role-alignment-template.md curriculum/roles/multi-role-alignment.md
   ```
4. Define repository strategy:
   ```bash
   cp templates/curriculum/repository-strategy-template.yaml curriculum/repository-strategy.yaml
   ```
   - Decide on `repositories.mode` (single vs per-role) and `solutions.placement` (inline vs separate repo).
   - Document initial assumptions in the dashboard `Program Context` section.

---

## Phase 1: Parallel Role Research

For each role:

1. Run the **Role Research Prompt** (`prompts/research/role-research-prompt.md`) to generate a first draft.
2. Collect evidence:
   - Analyze ≥20 job postings (`research/<role-slug>/job-posting-analysis.md`).
   - Conduct ≥5 practitioner interviews (`research/<role-slug>/interviews/`).
   - Capture quantitative data in the templates.
3. Use the **Skills Matrix Synthesis Prompt** (`prompts/research/skills-matrix-prompt.md`) to populate `skills-matrix.yaml`.
4. Record open questions and validation steps in each role brief.

**Quality Gate**: Review each role’s research package with at least one subject matter expert before moving forward.

---

## Phase 2: Role-Specific Curriculum Planning

1. Update `curriculum/<role-slug>/master-plan.yaml` with:
   - Learning outcomes derived from research
   - Program structure (modules, hours, assessments)
   - Project portfolio aligned to role-specific competencies
2. For each planned module, create or update a Module Roadmap file.
3. Capture validation plans (stakeholder reviews, pilot metrics) in the master plan.
4. Update `curriculum/repository-strategy.yaml` with module/project-specific paths and ensure module roadmaps reference the correct solution destinations.

**Quality Gate**: Ensure every learning objective maps to skills in the corresponding `skills-matrix.yaml`.

---

## Phase 3: Cross-Role Alignment

1. Populate `curriculum/roles/multi-role-alignment.md`:
   - Record shared modules and assets.
   - Identify differentiators and role-specific depth targets.
   - Assign owners and timelines for shared deliverables.
   - Track progression ladder to confirm each role builds on the previous with minimal duplication.
2. Create a consolidated competency map comparing where roles overlap or diverge.
3. Highlight economies of scale (shared lectures, labs) and areas requiring bespoke content.
4. Tag solution components (repositories, shared libraries) that are reused across roles and note required enhancements rather than full rewrites.

**Quality Gate**: Run an alignment review with program leadership to confirm resource allocation and sequencing.

---

## Phase 4: Governance & Change Management

- Maintain a change log per role and at the program level.
- Schedule quarterly refresh cycles to revisit research data and update curriculum plans.
- Track validation metrics in a shared dashboard (e.g., pilot feedback, assessment results).

---

## File Structure (Recommended)

```
research/
  platform-engineer/
    role-research.md
    job-posting-analysis.md
    skills-matrix.yaml
    interviews/
      interview-01.md
  mlops-engineer/
    ...
curriculum/
  platform-engineer/
    master-plan.yaml
    modules/
      module-01-roadmap.md
  mlops-engineer/
    ...
  roles/
    multi-role-alignment.md
```

---

## Checklist

- [ ] Each role has complete research artifacts with sources cited.
- [ ] Skills matrix files align to curriculum objectives.
- [ ] Module roadmaps exist for every planned module across roles.
- [ ] Multi-role dashboard highlights shared vs. unique assets.
- [ ] Validation plan covers individual roles and program-wide metrics.
- [ ] Repository strategy updated with final decisions for solutions and role-specific repos.
- [ ] Cross-role progression documented to avoid duplicate content.
