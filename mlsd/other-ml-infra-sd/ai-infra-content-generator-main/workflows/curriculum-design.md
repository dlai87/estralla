# Curriculum Design Workflow

This workflow guides the design of complete technical training curricula, from initial concept to validated learning path.

---

## Overview

**Purpose**: Design comprehensive, job-ready technical curriculum

**Time Investment**:
- Research & Analysis: 20-40 hours (per role)
- Curriculum Design: 20-30 hours (per role)
- Content Planning: 15-25 hours
- Validation: 10-15 hours
- **Total**: 65-110 hours per curriculum (scale research/design effort by number of roles)

**Output**: Complete curriculum design including:
- Role requirements and competency framework
- Learning path with modules and objectives
- Content specifications
- Assessment strategy
- Project portfolio requirements
- Multi-role alignment matrix (if serving multiple roles)

---

## Phase 1: Market Research (20-40 hours)

### Step 1: Define Target Role

**Questions to Answer**:
1. What role is this curriculum preparing learners for?
2. What are typical titles for this role?
3. What's the career progression path?
4. What's the salary range?
5. What industries hire for this role?

**Research Sources**:
- Job boards (LinkedIn, Indeed, Glassdoor)
- Company career pages
- Industry reports (Gartner, IDC)
- Professional associations
- Technical community forums

**Deliverable**: Role Definition Document
```markdown
## Target Role: [Role Name]

**Common Titles**:
- [Title 1]
- [Title 2]
- [Title 3]

**Career Level**: [Junior / Mid / Senior / Staff]

**Salary Range**: $[X]K - $[Y]K (US, 2025)

**Industries**:
- [Industry 1]
- [Industry 2]

**Career Progression**:
[Entry Role] → [Target Role] → [Next Role]

**Job Market**:
- Demand: [High / Medium / Low]
- Growth Rate: [X]% annually
- Number of Openings: [Estimate]
```

> **Template Support**: Copy `templates/research/role-research-template.md` to `research/<role-slug>/role-research.md` for each role you plan to support. Populate sections as you work through Phase 1.

### Step 2: Analyze Job Postings

Collect and analyze 20+ job postings:

**Data to Collect**:
```markdown
| Company | Location | Level | Required Skills | Preferred Skills | Education | Experience |
|---------|----------|-------|-----------------|------------------|-----------|------------|
| [Co 1]  | [City]   | [Lvl] | [Skills]        | [Skills]         | [Degree]  | [Years]    |
```

**Analysis Questions**:
- Which skills appear in >80% of postings? (Core skills)
- Which skills appear in 40-80%? (Important skills)
- Which skills appear in <40%? (Nice-to-have skills)
- What tools/technologies are most common?
- What certifications are mentioned?
- What experience level is typical?

**Deliverable**: Skills Frequency Analysis
```markdown
## Skills Analysis (from 20 job postings)

**Core Skills** (>80% of postings):
- [Skill 1]: 95% (19/20 postings)
- [Skill 2]: 90% (18/20 postings)
- [Skill 3]: 85% (17/20 postings)

**Important Skills** (40-80%):
- [Skill 4]: 75% (15/20 postings)
- [Skill 5]: 65% (13/20 postings)

**Technologies**:
- [Tool 1]: 90%
- [Tool 2]: 75%
- [Tool 3]: 60%

**Experience Requirements**:
- 0-2 years: 30%
- 2-5 years: 50%
- 5+ years: 20%
```

> **Template Support**: Use `templates/research/job-posting-analysis-template.md` as the capture workbook. Store under `research/<role-slug>/job-posting-analysis.md` to keep evidence organized per role.

### Step 3: Interview Industry Practitioners

Conduct 5-10 informational interviews:

**Interview Questions**:
1. What does a typical day look like in your role?
2. What skills do you use most frequently?
3. What skills were hardest to learn?
4. What skills were surprisingly important?
5. What do you wish you'd learned earlier?
6. What trends are shaping the role?
7. What advice for someone entering this field?

**Deliverable**: Practitioner Insights Report
```markdown
## Insights from 7 Practitioners

**Most Used Skills** (mentioned by >50%):
- [Skill]: Mentioned by 6/7 (86%)
- [Skill]: Mentioned by 5/7 (71%)

**Hardest to Learn**:
- [Skill/Concept]
- [Skill/Concept]

**Surprisingly Important**:
- [Skill]: "I use this daily, but it wasn't in the job description"

**Career Advice**:
- [Key advice point 1]
- [Key advice point 2]

**Trends**:
- [Trend 1]: Impact on role
- [Trend 2]: New skills needed
```

> **Template Support**: Capture each conversation with `templates/research/practitioner-interview-template.md` (store under `research/<role-slug>/interviews/`). Summarize aggregate findings in this section.

### Step 4: Review Competing Curricula

Analyze 3-5 competing training programs:

**Programs to Review**:
- Online courses (Coursera, Udacity, Pluralsight)
- Bootcamps (coding bootcamps, etc.)
- University programs
- Corporate training programs
- Certification programs

**Analysis Framework**:
```markdown
## Program: [Name]

**Duration**: [Weeks/Months]
**Cost**: $[Amount]
**Format**: [Online/In-person/Hybrid]

**Modules Covered**:
1. [Module 1] - [Duration]
2. [Module 2] - [Duration]

**Strengths**:
- [What they do well]

**Gaps**:
- [What's missing]

**Differentiation Opportunity**:
- [How we can be better]
```

**Deliverable**: Competitive Analysis Report

### Step 5: Synthesize Skills Matrix

Combine insights from steps 1-4 to define competencies and proficiency expectations.

**Inputs**:
- Role research brief (`research/<role-slug>/role-research.md`)
- Job posting analysis (`research/<role-slug>/job-posting-analysis.md`)
- Practitioner interviews (`research/<role-slug>/interviews/`)
- Competitive analysis findings

**Process**:
1. Group recurring responsibilities into 3-5 competency domains.
2. For each competency, list observable skills and map to proficiency levels (Awareness → Expert).
3. Tag every statement with evidence sources (IDs like `JP-03`, `INT-01`).
4. Identify assessment modalities that verify each proficiency.

**Deliverable**: `research/<role-slug>/skills-matrix.yaml`

> **Template Support**: Use `prompts/research/skills-matrix-prompt.md` to draft the matrix, then refine it using `templates/research/skills-matrix-template.yaml`.

---

## Phase 2: Competency Framework (20-30 hours)

### Step 1: Define Core Competencies

Based on research, identify core competencies:

**Competency Template**:
```markdown
## Competency: [Name]

**Definition**: [What this competency means]

**Importance**: [Why it matters for the role]

**Proficiency Levels**:
- **Level 1 (Awareness)**: [What learner can do]
- **Level 2 (Working Knowledge)**: [What learner can do]
- **Level 3 (Proficiency)**: [What learner can do]
- **Level 4 (Expertise)**: [What learner can do]

**Target Level for Curriculum**: Level [X]

**Assessment Method**: [How to verify this competency]
```

**Example**:
```markdown
## Competency: Container Orchestration

**Definition**: Ability to deploy, manage, and scale containerized
applications using orchestration platforms

**Importance**: 85% of mid-level DevOps roles require Kubernetes knowledge;
critical for managing production workloads

**Proficiency Levels**:
- **Level 1 (Awareness)**: Understands what orchestration is and why it's needed
- **Level 2 (Working Knowledge)**: Can deploy applications to existing cluster
- **Level 3 (Proficiency)**: Can design and manage production clusters
- **Level 4 (Expertise)**: Can architect multi-cluster deployments and optimize for cost/performance

**Target Level for Curriculum**: Level 3 (Proficiency)

**Assessment Method**: Deploy 3-tier application to Kubernetes with monitoring,
scaling, and zero-downtime updates
```

### Step 2: Map Competencies to Skills

For each competency, list specific skills:

```markdown
## Competency: Container Orchestration

**Required Skills**:
1. **Kubernetes Fundamentals**
   - Pods, Services, Deployments
   - Namespaces and RBAC
   - ConfigMaps and Secrets

2. **Cluster Management**
   - Cluster setup and configuration
   - Node management
   - Networking (CNI)
   - Storage (CSI)

3. **Application Deployment**
   - Deployment strategies
   - Health checks and probes
   - Resource management
   - Autoscaling (HPA, VPA)

4. **Observability**
   - Logging (FluentD, Loki)
   - Metrics (Prometheus)
   - Tracing (Jaeger)

5. **Security**
   - Network policies
   - Pod security policies
   - Secrets management
   - RBAC configuration
```

### Step 3: Create Learning Objectives

For each skill, write SMART learning objectives:

**SMART Criteria**:
- **Specific**: Clear and precise
- **Measurable**: Can verify achievement
- **Achievable**: Realistic for learners
- **Relevant**: Directly applicable to role
- **Time-bound**: Can learn in reasonable timeframe

**Template**:
```markdown
By the end of this [module/curriculum], learners will be able to:

1. [Action Verb] [Object] [Context/Condition]
   - Example: Deploy a multi-tier application to Kubernetes using Deployments and Services

2. [Action Verb] [Object] [Context/Condition]
   - Example: Configure horizontal pod autoscaling based on CPU and memory metrics

3. [Action Verb] [Object] [Context/Condition]
   - Example: Implement network policies to secure inter-service communication
```

**Deliverable**: Competency Framework Document (30-50 pages)

---

## Phase 3: Curriculum Architecture (15-25 hours)

### Step 1: Design Learning Path

Organize competencies into learning sequence:

**Considerations**:
- **Prerequisites**: What must be learned first?
- **Logical Flow**: What order makes sense?
- **Cognitive Load**: Not too much too fast
- **Motivation**: Early wins to build confidence
- **Practical Application**: Theory → Practice → Project

**Example Learning Path**:
```
Foundation Layer (Weeks 1-4)
├─ Module 1: Programming Fundamentals
├─ Module 2: Linux Command Line
├─ Module 3: Version Control (Git)
└─ Module 4: Networking Basics

Core Skills Layer (Weeks 5-12)
├─ Module 5: Containers (Docker)
├─ Module 6: Container Orchestration (Kubernetes)
├─ Module 7: CI/CD Pipelines
└─ Module 8: Cloud Platforms (AWS/GCP/Azure)

Advanced Skills Layer (Weeks 13-16)
├─ Module 9: Infrastructure as Code
├─ Module 10: Monitoring & Observability
├─ Module 11: Security & Compliance
└─ Module 12: Performance Optimization

Integration Layer (Weeks 17-20)
├─ Project 1: Containerized Microservices
├─ Project 2: Complete CI/CD Pipeline
├─ Project 3: Production Deployment
└─ Capstone Project: End-to-End System
```

> **Template Support**: Document the selected path in `curriculum/<role-slug>/master-plan.yaml` (copy from `templates/curriculum/master-plan-template.yaml`). For multi-role programs, leverage the `role_alignment_matrix` section to highlight shared and role-specific modules.

### Step 2: Design Each Module

For each module, specify:

**Module Specification Template**:
```markdown
## Module [X]: [Title]

**Duration**: [Hours]
**Prerequisites**: [List]
**Level**: [Beginner/Intermediate/Advanced]

**Module Overview**:
[2-3 paragraphs describing what module covers]

**Learning Objectives**:
1. [Objective 1]
2. [Objective 2]
[8+ objectives total]

**Topics Covered**:
1. **[Topic 1]** ([Duration])
   - [Subtopic]
   - [Subtopic]

2. **[Topic 2]** ([Duration])
   - [Subtopic]
   - [Subtopic]

**Content Requirements**:
- Lecture Notes: 12,000+ words
- Code Examples: 10+ complete examples
- Case Studies: 3+ real-world examples
- Exercises: 5-10 hands-on exercises
- Quiz: 25+ questions
- Project: 1 practical project

**Assessment**:
- Formative: [During-module assessments]
- Summative: [End-of-module assessment]
- Project: [Practical project assessment]

**Resources**:
- [Required resource 1]
- [Required resource 2]
- [Optional resource 1]
```

> **Template Support**: Maintain each module plan in `curriculum/<role-slug>/modules/` using `templates/curriculum/module-roadmap-template.md`. Tag all applicable roles in the "Target Role(s)" field to enable reuse.

### Step 3: Plan Projects

Design 3-4 major projects:

**Project Planning Template**:
```markdown
## Project [X]: [Title]

**Placement**: After Module [X]
**Duration**: [Hours]
**Difficulty**: [Level]

**Purpose**: [Why this project exists]

**What Learners Build**: [Description]

**Competencies Validated**:
- [Competency 1]
- [Competency 2]

**Technologies Used**:
- [Tech 1]
- [Tech 2]

**Deliverables**:
- [Deliverable 1]
- [Deliverable 2]

**Portfolio Value**: [Why this matters for their portfolio]
```

**Deliverable**: Curriculum Architecture Document (20-30 pages)

> **Template Support**: Capture finalized project designs with `templates/curriculum/project-plan-template.md` and store them under `curriculum/<role-slug>/projects/`.

### Step 4: Configure Solutions & Repository Strategy

1. Copy `templates/curriculum/repository-strategy-template.yaml` to `curriculum/repository-strategy.yaml` (if not already present).
2. Select repository mode:
   - `single_repo` when multiple roles share a mono-repo.
   - `per_role` when roles require their own repositories.
3. Decide solution placement (`inline` vs `separate`) and document destination paths for exercises, projects, and assessments.
4. Update each module roadmap (`Solutions Plan` section) with the chosen locations and note reuse across roles to prevent duplication.
5. Record cross-role progression and shared assets inside `curriculum/roles/multi-role-alignment.md`.
6. Align CI/CD and access policies (e.g., instructor-only solutions repos) with the chosen strategy.

**Deliverables**:
- `curriculum/repository-strategy.yaml` with program-specific values
- Multi-role alignment dashboard updated with repository and reuse decisions

---

## Phase 4: Content Specifications (10-15 hours)

### Step 1: Create Content Standards

Define quality standards for all content:

**Lecture Notes Standards**:
- Minimum 12,000 words per module
- 10+ complete code examples
- 3+ industry case studies
- Production-ready patterns
- Comprehensive explanations

**Exercise Standards**:
- Clear learning objective
- Step-by-step instructions
- Success criteria
- Time estimate
- Difficulty level

**Project Standards**:
- Real-world relevance
- Portfolio-worthy output
- Comprehensive guide
- Assessment rubric
- Example solution

**Assessment Standards**:
- Validates learning objectives
- Multiple question types
- Appropriate difficulty distribution
- Clear success criteria
- Constructive feedback

### Step 2: Define Assessment Strategy

Plan how learning will be assessed:

**Assessment Types**:
```markdown
## Assessment Strategy

**Formative Assessments** (During Learning):
- Knowledge checks (every lecture)
- Practice exercises (5-10 per module)
- Code reviews (for projects)
- Self-assessments (reflection prompts)

**Summative Assessments** (After Learning):
- Module quizzes (25+ questions each)
- Module projects (1 per module)
- Midterm project (after Module 6)
- Capstone project (final weeks)

**Portfolio Assessments**:
- GitHub repository with all projects
- Technical blog posts (2-3 articles)
- Presentation of capstone project
- Interview preparation materials

**Grading Weights**:
- Quizzes: 20%
- Module Projects: 30%
- Midterm Project: 15%
- Capstone Project: 25%
- Participation/Exercises: 10%
```

### Step 3: Plan Learning Resources

Identify required and supplementary resources:

**Required Resources**:
- [List materials learners must have]

**Supplementary Resources**:
- Documentation links
- Video tutorials
- Books
- Articles
- Community forums

**Tools and Software**:
- [Tool 1] - [Purpose] - [Cost]
- [Tool 2] - [Purpose] - [Cost]

**Deliverable**: Content Specifications Document (15-20 pages)

---

## Phase 5: Validation (10-15 hours)

### Step 1: Expert Review

Get feedback from 3-5 industry experts:

**Review Questions**:
1. Does this curriculum prepare learners for the role?
2. Are any critical skills missing?
3. Are any topics unnecessary?
4. Is the difficulty progression appropriate?
5. Are the time estimates realistic?
6. Would you hire someone who completed this?

**Deliverable**: Expert Feedback Report

### Step 2: Learner Validation

Review with 2-3 potential learners:

**Validation Questions**:
1. Is the curriculum structure clear?
2. Are prerequisites reasonable?
3. Are learning objectives motivating?
4. Are projects interesting?
5. Is time commitment manageable?
6. Would you enroll in this program?

**Deliverable**: Learner Feedback Report

### Step 3: Market Validation

Compare final design against market needs:

**Validation Checklist**:
- [ ] Covers all core skills from job analysis
- [ ] Includes current technologies (2024-2025)
- [ ] Competitive with other programs
- [ ] Clear differentiators
- [ ] Appropriate depth for role level
- [ ] Realistic time commitment
- [ ] Portfolio-building opportunities
- [ ] Multi-role alignment documented (when applicable)

**Deliverable**: Market Validation Report

---

## Phase 6: Documentation (5-10 hours)

### Step 1: Write Curriculum Overview

**Curriculum Overview Document** should include:
```markdown
# [Curriculum Name]

## Overview
[2-3 paragraphs describing the curriculum]

## Target Audience
[Who this is for]

## Prerequisites
[What learners need before starting]

## Duration
[Total time commitment]

## Learning Outcomes
By completing this curriculum, learners will be able to:
1. [Outcome 1]
2. [Outcome 2]
[10-15 outcomes]

## Curriculum Structure
[Visual representation of learning path]

## Modules
[List of all modules with brief descriptions]

## Projects
[List of all projects]

## Assessment
[How learning is evaluated]

## Career Outcomes
[Jobs this prepares for]

## Success Stories
[Testimonials, job placements, etc.]
```

### Step 2: Create Implementation Plan

**Implementation Plan** should include:
```markdown
## Implementation Timeline

**Phase 1: Content Creation** (Months 1-6)
- Month 1-2: Modules 1-4
- Month 3-4: Modules 5-8
- Month 5-6: Modules 9-12

**Phase 2: Content Review** (Months 6-7)
- Technical review
- Editorial review
- Learner testing

**Phase 3: Platform Setup** (Months 7-8)
- LMS configuration
- Content upload
- Testing

**Phase 4: Pilot Launch** (Month 9)
- Enroll 20-30 learners
- Collect feedback
- Iterate

**Phase 5: Full Launch** (Month 10+)
- Marketing
- Enrollment
- Ongoing improvement

## Resource Requirements

**Team**:
- Curriculum Designer: 1 FTE
- Content Developers: 2-3 FTE
- Technical Reviewers: 2-3 SMEs (part-time)
- Instructional Designer: 1 FTE
- Project Manager: 0.5 FTE

**Budget**:
- Content development: $[Amount]
- Platform/tools: $[Amount]
- Marketing: $[Amount]
- Total: $[Amount]

**Timeline**: [Total months]
```

### Step 3: Create Marketing Materials

**Materials Needed**:
- Curriculum overview (1-pager)
- Detailed syllabus
- Learning outcomes
- Sample content
- Instructor bios
- Success stories
- FAQ

**Deliverable**: Marketing Package

---

## Quality Checklist

Before finalizing curriculum design:

### Alignment
- [ ] Job market research supports curriculum
- [ ] Competencies match role requirements
- [ ] Learning objectives are SMART
- [ ] Assessment validates objectives
- [ ] Projects build portfolio

### Completeness
- [ ] All modules specified
- [ ] All projects designed
- [ ] Assessment strategy defined
- [ ] Resources identified
- [ ] Standards documented

### Feasibility
- [ ] Time estimates are realistic
- [ ] Prerequisites are reasonable
- [ ] Resources are accessible
- [ ] Team can create content
- [ ] Budget is adequate

### Quality
- [ ] Expert reviewed
- [ ] Learner validated
- [ ] Market validated
- [ ] Differentiated from competitors
- [ ] Current technologies

---

## Templates and Tools

### Research Templates
- Job analysis spreadsheet
- Skills frequency tracker
- Interview guide
- Competitive analysis template

### Design Templates
- Module specification
- Project brief
- Assessment plan
- Learning objectives worksheet

### Documentation Templates
- Curriculum overview
- Implementation plan
- Marketing one-pager

---

## Resources

### Research Tools
- LinkedIn Jobs API
- Job board scraping tools
- Industry reports (Gartner, IDC)
- Salary databases (Glassdoor, levels.fyi)

### Design Tools
- Bloom's Taxonomy
- SMART objectives framework
- Backward design methodology
- Competency mapping tools

### Validation Tools
- Expert review rubrics
- Learner survey templates
- Market analysis frameworks

---

## Example: Complete Curriculum Design

See `examples/sample-curriculum/` for a complete curriculum design following this workflow.
