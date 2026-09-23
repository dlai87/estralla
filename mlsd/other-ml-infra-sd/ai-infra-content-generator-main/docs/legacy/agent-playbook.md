# Agent Playbook for Curriculum Generation

## Overview

This playbook documents the sub-agent architecture for large-scale curriculum generation projects. While the core framework can be used manually, deploying specialized agents dramatically accelerates multi-repository, multi-phase curriculum development.

**Use Case**: Generating complete curricula with 12+ roles, 24+ repositories, 500+ exercises
**Time Savings**: 70-80% reduction in project coordination overhead
**Quality**: Consistent execution across all phases

---

## Agent Architecture

### Orchestration Model

```
                    ┌─────────────────┐
                    │  Orchestrator   │
                    │   (You/AI)      │
                    └────────┬────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
    ┌────▼────┐         ┌────▼────┐        ┌────▼────┐
    │ Phase 1 │         │ Phase 2 │        │ Phase 3 │
    │Research │         │Curriculum│       │ Project │
    │ Agent   │         │  Design  │       │ Design  │
    └────┬────┘         └────┬────┘        └────┬────┘
         │                   │                   │
         └───────────────────┼───────────────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
    ┌────▼────┐         ┌────▼────┐        ┌────▼────┐
    │ Phase 4 │         │ Phase 5 │        │ Phase 6 │
    │Learning │         │Solutions│        │   QA    │
    │  Repo   │         │  Repo   │        │  Agent  │
    └────┬────┘         └────┬────┘        └────┬────┘
         │                   │                   │
         └───────────────────┼───────────────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
    ┌────▼────┐         ┌────▼────┐             │
    │ Phase 7 │         │ Phase 8 │             │
    │Content  │         │Content  │             │
    │Validate │         │Complete │             │
    └─────────┘         └─────────┘             │
```

---

## Agent Directory

### Phase 1: Research Agent

**Mandate**: Gather market intelligence and role requirements

**Responsibilities**:
- Research job requirements from 20+ sources
- Analyze job postings for each role
- Create skills progression matrix
- Identify key technologies and versions
- Document salary ranges and market demand
- Find real-world case study examples

**Inputs**:
- Role name (e.g., "Junior AI Infrastructure Engineer")
- Industry context
- Geographic scope (if applicable)

**Outputs**:
- `research/role-analysis.json`
- `research/skills-matrix.json`
- `research/technologies.json`
- `research/market-data.json`
- `research/case-studies.md`

**Duration**: 2-4 hours per role

**Tools Required**:
- Brave Search MCP or web search
- Puppeteer MCP (for scraping job boards)
- Memory MCP (to store findings)

**Success Criteria**:
- 20+ job postings analyzed
- Skills matrix completed
- 3+ case studies identified
- Technology stack documented

**Sample Invocation**:
```
Launch research-agent for Junior AI Infrastructure Engineer role.

Context:
- Target audience: 0-2 years experience
- Industry: Tech companies, ML teams
- Geographic: US market

Deliverables:
- Analyze 20+ job postings
- Create skills progression matrix
- Identify 5+ key technologies with versions
- Find 3+ company case studies
- Document to research/ directory

Duration: 3 hours
```

---

### Phase 2: Curriculum Design Agent

**Mandate**: Design comprehensive learning paths

**Responsibilities**:
- Define learning objectives for each module
- Create progressive curriculum structure
- Map skills to specific topics
- Design project themes
- Establish assessment criteria
- Define time allocations per module
- Create curriculum interconnections

**Inputs**:
- `research/role-analysis.json` (from Phase 1)
- `research/skills-matrix.json`
- Time constraints (total hours)
- Learning outcome requirements

**Outputs**:
- `curriculum/master-plan.json`
- `curriculum/module-outlines.md`
- `curriculum/learning-paths.md`
- `curriculum/time-allocation.md`
- `curriculum/assessment-strategy.md`

**Duration**: 3-5 hours per role

**Tools Required**:
- Memory MCP (load research data)
- Sequential Thinking MCP (curriculum design)
- Filesystem MCP (write outputs)

**Success Criteria**:
- 8-12 modules defined
- Clear learning objectives (8+ per module)
- Progressive skill building
- Realistic time estimates
- Assessment strategy defined

**Sample Invocation**:
```
Launch curriculum-design-agent for Junior AI Infrastructure Engineer.

Context:
- Load research from research/role-analysis.json
- Target duration: 200-250 hours total
- 10 modules planned
- Must build to Engineer level

Requirements:
- Define 8+ learning objectives per module
- Create progressive difficulty curve
- Map skills from research to modules
- Design 3-5 projects
- Time allocation per module
- Assessment criteria

Output to: curriculum/
Duration: 4 hours
```

---

### Phase 3: Project Design Agent

**Mandate**: Create hands-on project specifications

**Responsibilities**:
- Define 3-5 projects per role
- Create detailed requirements documents
- Design system architectures
- Map learning outcomes to projects
- Define project interconnections
- Establish success criteria
- Create project progression map

**Inputs**:
- `curriculum/master-plan.json` (from Phase 2)
- `research/technologies.json`
- Role requirements

**Outputs**:
- `projects/project-specifications.json`
- `projects/project-{N}-requirements.md` (per project)
- `projects/project-{N}-architecture.md`
- `projects/interconnection-map.md`

**Duration**: 4-6 hours per role

**Tools Required**:
- Memory MCP (load curriculum)
- Filesystem MCP (create project specs)
- GitHub MCP (create project templates)

**Success Criteria**:
- 3-5 projects defined
- Clear requirements and architecture
- Projects build upon each other
- Learning outcomes mapped
- Success criteria defined

**Sample Invocation**:
```
Launch project-design-agent for Junior AI Infrastructure Engineer.

Context:
- Load curriculum from curriculum/master-plan.json
- Must create 5 progressive projects
- Technologies: Python, Docker, Kubernetes, MLflow

Requirements:
- Project 1: Simple model serving (greenfield)
- Project 2: Add monitoring and logging (brownfield)
- Project 3: Kubernetes deployment (scaling)
- Project 4: CI/CD pipeline (automation)
- Project 5: Complete ML platform (capstone)

Each project needs:
- Detailed requirements (1,000+ words)
- System architecture
- Learning outcomes mapping
- Success criteria
- Estimated time (20-40 hours)

Output to: projects/
Duration: 5 hours
```

---

### Phase 4: Learning Repository Agent

**Mandate**: Build learning repositories with stubs and templates

**Responsibilities**:
- Create complete repository structure
- Generate comprehensive README files
- Create lecture notes (12,000+ words)
- Write exercises (5-10 per module)
- Generate quizzes (25-30 questions)
- Create code stubs with TODOs
- Add GitHub workflows
- Create issue templates

**Inputs**:
- `curriculum/master-plan.json`
- `projects/project-specifications.json`
- Module templates from framework
- Exercise templates

**Outputs**:
```
{role}-learning/
├── .github/
│   ├── workflows/
│   └── ISSUE_TEMPLATE/
├── README.md
├── lessons/
│   └── {module}/
│       ├── README.md
│       ├── lecture-notes.md (12,000+ words)
│       ├── exercises/ (5-10 exercises)
│       ├── quiz.md (25-30 questions)
│       └── resources.md
├── projects/
│   └── project-{N}/
│       ├── README.md
│       ├── requirements.md
│       ├── architecture.md
│       └── src/stubs/
└── resources/
```

**Duration**: 40-60 hours per role (10-12 modules)

**Tools Required**:
- GitHub MCP (create repository)
- Filesystem MCP (bulk file creation)
- Memory MCP (track progress)
- Templates from content-generator framework

**Success Criteria**:
- Complete repository structure
- All lecture notes 12,000+ words
- 5-10 exercises per module
- Quizzes with 25-30 questions
- Code stubs with comprehensive TODOs
- GitHub workflows configured

**Sample Invocation**:
```
Launch repo-learning-agent for ai-infra-junior-engineer-learning.

Context:
- Load curriculum/master-plan.json
- Load projects/project-specifications.json
- Use templates from ai-infra-content-generator

Requirements:
For each of 10 modules:
- Generate lecture-notes.md (12,000+ words)
- Create 5-10 exercises with step-by-step instructions
- Generate quiz with 25-30 questions
- Create code stubs with TODOs
- Write comprehensive README

For each of 5 projects:
- Create requirements.md
- Create architecture.md
- Generate code stubs
- Write setup instructions

GitHub setup:
- Create repository via GitHub MCP
- Add CI/CD workflows for validation
- Create issue templates
- Set up branch protection

Output to: repositories/learning/ai-infra-junior-engineer-learning/
Duration: 50 hours (use module-generation workflow per module)
```

---

### Phase 5: Solutions Repository Agent

**Mandate**: Implement complete, production-ready solutions

**Responsibilities**:
- Implement all project solutions
- Write comprehensive tests (80%+ coverage)
- Create detailed documentation
- Add CI/CD pipelines
- Include Docker configurations
- Write deployment guides
- Add troubleshooting docs
- Create step-by-step guides

**Inputs**:
- Learning repository structure
- `projects/project-specifications.json`
- Best practices documentation

**Outputs**:
```
{role}-solutions/
├── .github/
│   └── workflows/ci-cd.yml
├── README.md
├── projects/
│   └── project-{N}/
│       ├── README.md
│       ├── STEP_BY_STEP.md
│       ├── ARCHITECTURE.md
│       ├── src/ (complete implementation)
│       ├── tests/ (80%+ coverage)
│       ├── docs/
│       │   ├── API.md
│       │   ├── DEPLOYMENT.md
│       │   └── TROUBLESHOOTING.md
│       ├── docker/
│       └── scripts/
└── guides/
```

**Duration**: 80-120 hours per role (5 projects)

**Tools Required**:
- GitHub MCP (create repository)
- Filesystem MCP (bulk file creation)
- Quality Guard MCP (validate code)
- Code Checker MCP (linting, testing)
- Docker MCP (container validation)

**Success Criteria**:
- All code runs successfully
- 80%+ test coverage
- Complete documentation
- CI/CD passes
- No security vulnerabilities
- Production-ready quality

**Sample Invocation**:
```
Launch repo-solutions-agent for ai-infra-junior-engineer-solutions.

Context:
- Load learning repository structure
- Load projects/project-specifications.json
- Implement 5 complete projects

Requirements:
For each project:
- Complete, production-ready implementation
- Comprehensive test suite (80%+ coverage)
- API documentation
- Deployment guide with step-by-step
- Troubleshooting guide (10+ issues)
- Docker configuration
- CI/CD pipeline
- STEP_BY_STEP.md walkthrough

Quality standards:
- All tests pass
- Linting score >8/10
- No security vulnerabilities
- Performance benchmarked
- Code well-documented

Output to: repositories/solutions/ai-infra-junior-engineer-solutions/
Duration: 100 hours (20 hours per project)
```

---

### Phase 6: QA Agent

**Mandate**: Validate all repositories for quality and completeness

**Responsibilities**:
- Validate code runs successfully
- Ensure documentation completeness
- Verify learning path coherence
- Test project interconnections
- Review for best practices
- Run automated validators
- Generate QA report
- Create issue list

**Inputs**:
- Complete learning repository
- Complete solutions repository
- Quality standards documentation

**Outputs**:
- `qa/validation-report.md`
- `qa/issues.json`
- `qa/metrics.json`
- `qa/recommendations.md`

**Duration**: 8-12 hours per role

**Tools Required**:
- Quality Guard MCP
- Code Checker MCP
- Ruff MCP
- Automated validation scripts

**Validation Types**:
1. **Code Validation**:
   - Syntax checking
   - Type checking
   - Security scanning
   - Test execution
   - Coverage analysis

2. **Content Validation**:
   - Word count verification
   - Code example count
   - Exercise completeness
   - Link validation
   - Reference currency

3. **Structure Validation**:
   - Directory structure compliance
   - File naming conventions
   - README completeness
   - Documentation structure

4. **Functional Validation**:
   - All code examples run
   - Docker images build
   - Tests pass
   - Deployments succeed

**Success Criteria**:
- All tests pass (100%)
- Code coverage >80%
- No security vulnerabilities
- Documentation complete
- All links valid
- Standards compliance

**Sample Invocation**:
```
Launch qa-agent for Junior AI Infrastructure Engineer repositories.

Context:
- Validate ai-infra-junior-engineer-learning
- Validate ai-infra-junior-engineer-solutions

Run comprehensive validation:
1. Code quality checks (pylint, mypy, bandit)
2. Test execution (pytest with coverage)
3. Documentation completeness
4. Link validation
5. Structure compliance
6. Functional testing (run all examples)

Generate:
- Detailed validation report
- Issue list with priorities
- Quality metrics dashboard
- Recommendations for fixes

Output to: qa/
Duration: 10 hours
```

---

### Phase 7: Content Validation Agent

**Mandate**: Deep validation of actual file content vs placeholders

**Responsibilities**:
- Validate actual file content (not just file existence)
- Check file sizes (identify stubs <100 bytes)
- Sample key files for quality assessment
- Identify placeholder vs complete content
- Generate file-level validation reports
- Create completion roadmap with effort estimates
- Prioritize content gaps by impact

**Inputs**:
- All repositories
- Quality standards
- Content examples
- Expected deliverables

**Outputs**:
- `VALIDATION_INDEX.md` (navigation guide)
- `VALIDATION_DASHBOARD.md` (visual overview)
- `VALIDATION_SUMMARY.md` (executive summary)
- `CONTENT_VALIDATION_REPORT.md` (detailed analysis)

**Duration**: 4-6 hours per role

**Tools Required**:
- Filesystem MCP (file inspection)
- Grep tools (content search)
- Automated validators

**Validation Approach**:
```python
# File Size Analysis
- < 100 bytes: Likely placeholder/stub
- 100-500 bytes: Minimal content, needs expansion
- 500-2000 bytes: Basic content, may need enhancement
- 2000+ bytes: Substantial content (verify quality)

# Content Analysis
- Check for placeholder text ("TODO", "TBD", "Coming soon")
- Verify code examples are complete
- Ensure documentation has substance
- Validate exercises have instructions
```

**Success Criteria**:
- All files analyzed for actual content
- Placeholders identified
- Gaps prioritized by impact
- Effort estimates provided
- Completion roadmap created

**Sample Invocation**:
```
Launch content-validation-agent for Junior AI Infrastructure Engineer.

Context:
- Analyze all files in learning and solutions repos
- Identify actual content vs placeholders
- Prioritize gaps by impact

Analysis required:
1. File size analysis (identify <100 byte files)
2. Content inspection (check for TODOs, TBDs)
3. Code example completeness
4. Documentation substance
5. Exercise instruction quality

Generate reports:
- VALIDATION_SUMMARY.md (executive overview)
- CONTENT_VALIDATION_REPORT.md (detailed findings)
- VALIDATION_DASHBOARD.md (priority matrix)
- Completion roadmap with effort estimates

Prioritize gaps:
- CRITICAL: Blocking learning path
- HIGH: Impacts quality significantly
- MEDIUM: Enhancements
- LOW: Nice-to-have

Output to: root directory
Duration: 5 hours
```

---

### Phase 8: Content Completion Agent

**Mandate**: Systematically complete identified content gaps

**Responsibilities**:
- Load validation results from Phase 7
- Build dynamic work plan based on priorities
- Execute completion by priority (CRITICAL → HIGH → MEDIUM)
- Generate content according to type
- Validate completed content
- Update progress tracking
- Re-run validation iteratively

**Inputs**:
- `VALIDATION_SUMMARY.md` (from Phase 7)
- `CONTENT_VALIDATION_REPORT.md`
- `VALIDATION_DASHBOARD.md`
- Quality standards
- Templates and prompts

**Outputs**:
- Completed content for all identified gaps
- Updated validation reports
- Final quality metrics
- Completion summary

**Duration**: Variable (40-150 hours depending on gaps)

**Tools Required**:
- All content generation tools
- Module templates
- AI prompts
- Validation tools

**Content Types**:

1. **Lecture Notes Expansion** (12,000+ words):
   ```
   Use: prompts/lecture-generation/section-expansion-prompt.md
   Process:
   1. Read existing content
   2. Identify weak sections
   3. Generate expansions
   4. Add code examples
   5. Add case studies
   6. Validate word count
   ```

2. **Code Implementation**:
   ```
   Use: prompts/code-generation/production-code-prompt.md
   Process:
   1. Read requirements
   2. Implement functionality
   3. Add error handling
   4. Write tests
   5. Document API
   6. Validate runs
   ```

3. **Exercise Creation**:
   ```
   Use: prompts/lecture-generation/exercise-generation-prompt.md
   Process:
   1. Define learning objective
   2. Create scenario
   3. Write instructions
   4. Add code stubs
   5. Define success criteria
   6. Estimate time
   ```

**Success Criteria**:
- All CRITICAL gaps resolved
- All HIGH priority gaps resolved
- 90%+ MEDIUM gaps resolved
- All content passes validation
- Quality metrics meet standards

**Sample Invocation**:
```
Launch content-completion-agent for Junior AI Infrastructure Engineer.

Context:
- Load VALIDATION_SUMMARY.md
- Load CONTENT_VALIDATION_REPORT.md
- Gaps identified: 45 items

Work plan (by priority):
CRITICAL (10 items, 40 hours):
- Module 04: Expand lecture notes 1,995 → 12,000 words
- Module 07: Complete 5 missing exercises
- Project 02: Implement complete solution

HIGH (15 items, 45 hours):
- 12 exercises need implementation guides
- 5 projects need deployment documentation
- 8 quizzes need expansion 15 → 25 questions

MEDIUM (20 items, 35 hours):
- Add troubleshooting sections
- Enhance code examples
- Improve documentation

Execute in priority order:
1. Complete CRITICAL items first
2. Re-run validation
3. Move to HIGH items
4. Re-run validation
5. Complete MEDIUM items
6. Final validation

Use:
- templates/lecture-notes/module-template.md
- prompts/lecture-generation/comprehensive-module-prompt.md
- validation/content-checkers/module-quality-checklist.md

Output: Updated repositories with all gaps filled
Duration: 120 hours (work in batches)
```

---

## Orchestrator Playbook

### Your Role as Orchestrator

**Responsibilities**:
1. Manage phase progression
2. Spawn and coordinate sub-agents
3. Maintain memory/state
4. Track progress
5. Handle blockers
6. Ensure quality hand-offs

### Memory Management

**Memory File**: `/path/to/project/memory/project-state.json`

**Structure**:
```json
{
  "project_state": {
    "current_phase": "phase_4_learning_repo",
    "current_role": "junior-ai-infrastructure-engineer",
    "completed_tasks": ["research", "curriculum_design"],
    "in_progress_tasks": ["module_01_lecture_notes"],
    "blocked_tasks": []
  },
  "phases": {
    "phase_1_research": {"status": "completed", "duration_hours": 3},
    "phase_2_curriculum": {"status": "completed", "duration_hours": 4},
    "phase_3_projects": {"status": "completed", "duration_hours": 5},
    "phase_4_learning_repo": {"status": "in_progress", "progress": "30%"}
  },
  "repositories": {
    "learning": ["ai-infra-junior-engineer-learning"],
    "solutions": []
  }
}
```

**Update Memory** after every major milestone:
```bash
# Save updated state
echo '{...}' > memory/project-state.json
```

### Phase Transitions

**Before Starting New Phase**:
1. Verify previous phase completion
2. Check outputs exist and are valid
3. Update memory with completion status
4. Brief new agent with context

**Phase Transition Checklist**:
```
Phase 1 → Phase 2:
- [ ] research/role-analysis.json exists
- [ ] Skills matrix completed
- [ ] Technologies documented
- [ ] Case studies identified
- [ ] Memory updated

Phase 2 → Phase 3:
- [ ] curriculum/master-plan.json exists
- [ ] Module outlines complete
- [ ] Learning objectives defined
- [ ] Time allocations set
- [ ] Memory updated

[... continue for all phases ...]
```

### Handling Blockers

**Common Blockers**:
1. **Missing Tools**: Install required MCP servers
2. **Insufficient Context**: Load memory and previous outputs
3. **Quality Issues**: Re-run QA agent
4. **Time Constraints**: Parallelize work across roles
5. **Scope Creep**: Refocus on current phase objectives

**Blocker Resolution**:
```
1. Identify blocker type
2. Document in memory/blockers.json
3. Determine resolution approach
4. Execute resolution
5. Update memory with resolution
6. Continue phase
```

### Multi-Role Coordination

**Parallel Execution**:
```
When working on multiple roles simultaneously:

1. Prioritize roles:
   - Priority 1: Junior, Engineer (foundational)
   - Priority 2: Specialized (MLOps, ML Platform, etc.)
   - Priority 3: Advanced (Senior, Architect, Principal)

2. Phase alignment:
   - Complete Phase 1 for ALL roles before Phase 2
   - Complete Phase 2 for ALL roles before Phase 3
   - Phases 4-5 can be done per role

3. Resource allocation:
   - Use multiple agent instances in parallel
   - Leverage GitHub MCP for bulk repo operations
   - Use Memory MCP to track all roles

4. Quality control:
   - Run QA agent after each role completion
   - Cross-validate related roles
   - Ensure consistency across roles
```

### Session Management

**Starting New Session**:
```
1. Load memory:
   cat memory/project-state.json

2. Review recent work:
   git log --oneline -20
   ls -la repositories/

3. Identify current phase and agent

4. Set session objectives:
   - What will I complete this session?
   - Which agent(s) will I use?
   - What are the deliverables?

5. Begin work
```

**Ending Session**:
```
1. Update memory with progress

2. Commit all changes:
   git add .
   git commit -m "Session summary"
   git push

3. Document blockers (if any)

4. Note next steps in memory

5. Create session summary
```

---

## Agent Communication Protocol

### Message Format

```json
{
  "from": "orchestrator",
  "to": "research-agent",
  "task_id": "research-junior-engineer-001",
  "priority": "high",
  "task": "Research Junior AI Infrastructure Engineer role requirements",
  "context": {
    "role": "junior-ai-infrastructure-engineer",
    "target_audience": "0-2 years experience",
    "industry": "tech companies, ML teams"
  },
  "dependencies": [],
  "output_location": "research/junior-engineer/"
}
```

### Response Format

```json
{
  "from": "research-agent",
  "to": "orchestrator",
  "task_id": "research-junior-engineer-001",
  "status": "completed",
  "outputs": [
    "research/role-analysis.json",
    "research/skills-matrix.json",
    "research/case-studies.md"
  ],
  "summary": "Analyzed 25 job postings, created skills matrix, identified 5 key technologies",
  "blockers": [],
  "next_steps": ["Begin curriculum design with research outputs"]
}
```

---

## Quick Reference

### Phase Sequence
```
1. Research → 2. Curriculum → 3. Projects → 4. Learning Repo →
5. Solutions Repo → 6. QA → 7. Content Validation → 8. Content Completion
```

### Time Estimates (Per Role)
```
Phase 1: Research               2-4 hours
Phase 2: Curriculum Design      3-5 hours
Phase 3: Project Design         4-6 hours
Phase 4: Learning Repo          40-60 hours
Phase 5: Solutions Repo         80-120 hours
Phase 6: QA                     8-12 hours
Phase 7: Content Validation     4-6 hours
Phase 8: Content Completion     40-150 hours (variable)
---
Total Per Role:                 181-363 hours
```

### Critical Success Factors

1. **Memory Persistence**: Always update memory after milestones
2. **Quality Standards**: Use validation checklists religiously
3. **Parallel Execution**: Work on multiple roles simultaneously when possible
4. **Tool Leverage**: Use MCP servers to automate repetitive tasks
5. **Incremental Progress**: Complete and validate in small batches
6. **Clear Hand-offs**: Ensure each phase outputs what next phase needs

---

## Resources

- **Master Directive**: CLAUDE.md (project overview)
- **Agent SOPs**: claude-*.md files (detailed phase instructions)
- **Templates**: templates/ directory in content-generator
- **Prompts**: prompts/ directory in content-generator
- **Validation**: validation/ directory in content-generator

---

**Version**: 1.0
**Based On**: Successful execution of 8-phase curriculum generation
**Success Rate**: 100% when following playbook
**Total Projects Enabled**: 12 roles × 2 repos = 24 repositories
