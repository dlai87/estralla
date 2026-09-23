# Curriculum Workspace

This directory houses curriculum design artifacts generated during Phase 2 and beyond. Leverage the templates in `templates/curriculum/` to keep plans consistent across roles and modules.

## Recommended Structure

```
curriculum/
  <role-slug>/
    master-plan.yaml
    modules/
      module-01-roadmap.md
      module-02-roadmap.md
    projects/
      project-01-plan.md
  roles/
    multi-role-alignment.md
```

## Setup Steps

1. Create a subdirectory for each role that has completed the research phase.
2. Copy templates:
   ```bash
   cp templates/curriculum/master-plan-template.yaml curriculum/<role-slug>/master-plan.yaml
   cp templates/curriculum/module-roadmap-template.md curriculum/<role-slug>/modules/module-01-roadmap.md
   cp templates/curriculum/project-plan-template.md curriculum/<role-slug>/projects/project-01-plan.md
   cp templates/curriculum/multi-role-alignment-template.md curriculum/roles/multi-role-alignment.md
   cp templates/curriculum/repository-strategy-template.yaml curriculum/repository-strategy.yaml
   ```
3. Populate module roadmap files as you scope the learning path.
4. Configure `curriculum/repository-strategy.yaml` to define solution placement (inline vs separate repo) and repository mode (single vs per-role).
5. Track cross-role reuse and divergence in `curriculum/roles/multi-role-alignment.md`.

## Key Artifacts

- **Master Plan (`master-plan.yaml`)**: Program-level overview, learning outcomes, module list, assessments, validation plan.
- **Repository Strategy (`repository-strategy.yaml`)**: Defines repo topology, solutions placement, shared component ownership.
- **Module Roadmaps (`modules/*.md`)**: Detailed scope for each module, including objectives, assets, and quality checklist.
- **Project Plans (`projects/*.md`)**: Deep dive into project narrative, deliverables, assessment, and reuse strategy.
- **Multi-Role Alignment Dashboard**: Shared vs. role-specific modules, dependencies, and owners.

## Validation Checklist

- Learning objectives trace back to competencies in `research/<role-slug>/skills-matrix.yaml`.
- Module roadmaps identify all hands-on assets and assessments.
- Solutions plans reference the correct repository strategy and reuse guidance.
- Multi-role dashboard updated whenever a module or competency changes.

## Next Steps

Once curriculum plans are stable, transition to content generation workflows (`workflows/module-generation.md`, `workflows/project-generation.md`) using the structured outputs created here.
