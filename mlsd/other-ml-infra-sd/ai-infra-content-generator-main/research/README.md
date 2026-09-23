# Research Workspace

Use this directory to store role-specific research artifacts generated during Phase 1 of the content pipeline. The templates under `templates/research/` and prompts in `prompts/research/` are designed to populate the files described below.

## Recommended Structure

```
research/
  <role-slug>/
    role-research.md
    job-posting-analysis.md
    skills-matrix.yaml
    market-trends.md
    interviews/
      interview-01.md
      interview-02.md
```

## Setup Steps

1. Create a slug for each role (e.g., `platform-engineer`, `mlops-engineer`).
2. Copy starter templates:
   ```bash
   cp templates/research/role-research-template.md research/<role-slug>/role-research.md
   cp templates/research/job-posting-analysis-template.md research/<role-slug>/job-posting-analysis.md
   cp templates/research/skills-matrix-template.yaml research/<role-slug>/skills-matrix.yaml
   cp templates/research/practitioner-interview-template.md research/<role-slug>/interviews/interview-01.md
   ```
3. Run the prompts in `prompts/research/` to draft initial content, then validate with manual research.

## Deliverables to Maintain

- **Role Research Brief** (`role-research.md`): Market overview, responsibilities, skill requirements.
- **Job Posting Analysis** (`job-posting-analysis.md`): Quantitative breakdown of job ads.
- **Skills Matrix** (`skills-matrix.yaml`): Competency progression with evidence citations.
- **Practitioner Interviews** (`interviews/*.md`): Individual interview summaries.
- **Market Trends** (`market-trends.md`, optional): Aggregated insights from reports and news.

## Multi-Role Guidance

- Maintain one subdirectory per role to keep evidence distinct.
- Tag evidence sources with short IDs (e.g., `JP-04`, `INT-02`) to enable cross-role comparison.
- When multiple roles share competencies, note this in each skills matrix to streamline alignment in the curriculum phase.

## Next Steps

After completing research for all roles, move to the curriculum workspace (`curriculum/`) and use the outputs here as inputs to master plans and module roadmaps.
