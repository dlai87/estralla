# Role Research Prompt

## Purpose

Use this prompt to generate a comprehensive research brief for a target role. It aligns with `templates/research/role-research-template.md` and supports multi-role programs by capturing consistent data across roles.

## Instructions

1. Replace bracketed sections with role-specific information.
2. Provide context about target industries, seniority, and timeframe.
3. Ask the AI to ground responses in recent (≤12 months) sources and flag any uncertainty.
4. Run validation by comparing outputs with job postings and practitioner interviews.

---

## PROMPT TEMPLATE

````markdown
Act as a senior talent strategist researching the role of **[ROLE NAME]** at the **[LEVEL]** level for an AI infrastructure curriculum.

### Research Scope
- Timeframe: Focus on data from [Month YYYY] to [Month YYYY]
- Regions: [Primary regions], but include global insights when relevant
- Industries: [Primary industries to target]
- Output format: Follow the headings and tables in the Role Research Brief template

### Questions to Answer
1. What are the most critical business outcomes for this role?
2. Which skills and competencies appear consistently across reputable sources?
3. What tools, platforms, and versions are dominant in 2024-2025?
4. What emerging trends are reshaping the role?
5. What misconceptions or outdated expectations should curriculum avoid?

### Deliverables
- Fill each section of the Role Research Brief with detailed findings
- Cite sources inline with markdown links `[Source](URL)` and tag each entry with a short ID (e.g., `JP-05`, `INT-02`)
- Include at least 5 practitioner insights with quotes and attribution
- Highlight any open questions or data gaps that require human follow-up

### Quality Bar
- Prioritize quantitative data (percentages, counts, salary ranges)
- Distinguish between must-have and nice-to-have skills
- Flag conflicting data across sources and explain how you resolved it
- Recommend next steps for validation (interviews, surveys, expert review)
````
