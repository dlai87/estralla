# Project Generation Workflow

This workflow guides the creation of hands-on projects that give learners practical, portfolio-worthy experience with the technologies they're learning.

---

## Overview

**Purpose**: Create comprehensive, production-oriented hands-on projects

**Time Investment**:
- Planning: 1-2 hours
- Project Design: 2-3 hours
- Implementation (example solution): 8-12 hours
- Documentation: 2-3 hours
- Testing & Refinement: 2-4 hours
- **Total**: 15-24 hours per project

**Output**: Complete project package including:
- Project description and requirements
- Starter code/scaffolding
- Step-by-step implementation guide
- Example solution
- Tests and validation criteria
- Assessment rubric

---

## Phase 1: Project Planning (1-2 hours)

### Step 1: Define Project Scope

**Questions to Answer**:
1. What module(s) does this project reinforce?
2. What learning objectives does it validate?
3. What will learners build?
4. Why does this project matter (real-world relevance)?
5. What's the estimated completion time?

**Template**:
```markdown
## Project Scope

**Module**: [Module number and name]
**Learning Objectives Validated**:
- [Objective 1]
- [Objective 2]
- [Objective 3]

**Project Description**: [What learners will build]

**Real-World Relevance**: [Why this matters in production]

**Estimated Time**: [Hours to complete]

**Difficulty**: [Beginner / Intermediate / Advanced]
```

**Example**:
```markdown
## Project Scope

**Module**: Module 5 - Docker Containerization

**Learning Objectives Validated**:
- Design and implement multi-container applications
- Create production-ready Dockerfiles
- Configure container networking and volumes
- Deploy containerized applications

**Project Description**:
Build a containerized microservices application consisting of a web frontend,
REST API backend, PostgreSQL database, and Redis cache. Implement proper
networking, persistence, and monitoring.

**Real-World Relevance**:
This project mirrors how companies like Uber, Netflix, and Airbnb structure
their containerized applications. The patterns learned apply directly to
production deployments in any modern tech company.

**Estimated Time**: 10-12 hours

**Difficulty**: Intermediate
```

### Step 2: Identify Prerequisites

List what learners need before starting:

**Required Knowledge**:
- [Skill/concept 1]
- [Skill/concept 2]

**Completed Modules**:
- [Module X] - [Why needed]

**Development Environment**:
- [Tool 1] - [Version]
- [Tool 2] - [Version]

### Step 3: Design Learning Path

Break project into logical phases:

**Phase 1**: [Foundation]
- What: [Component to build]
- Time: [Estimate]
- Concepts: [What they'll learn]

**Phase 2**: [Next layer]
- Builds on: Phase 1
- What: [Next component]
- Concepts: [What they'll learn]

[Continue for all phases]

---

## Phase 2: Technical Design (2-3 hours)

### Step 1: Architecture Design

**Create System Architecture**:
```
[Draw or describe the system architecture]

Example:
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   Frontend  │─────▶│      API     │─────▶│  Database   │
│   (React)   │      │   (FastAPI)  │      │ (PostgreSQL)│
└─────────────┘      └──────────────┘      └─────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │    Cache     │
                     │   (Redis)    │
                     └──────────────┘
```

**Document Components**:
For each component:
- **Purpose**: What it does
- **Technology**: What it's built with
- **Interactions**: How it connects to others
- **Key Features**: What learners will implement

### Step 2: Define Project Structure

**Directory Layout**:
```
project-name/
├── README.md
├── docker-compose.yml
├── frontend/
│   ├── Dockerfile
│   └── src/
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── src/
├── database/
│   └── init.sql
└── docs/
    └── DEPLOYMENT.md
```

### Step 3: Identify Key Implementation Tasks

List specific tasks learners will complete:

**Task 1**: [Description]
- Files to create/modify: [List]
- Concepts demonstrated: [List]
- Success criteria: [How to verify]

**Example**:
```markdown
**Task 1**: Create Backend Dockerfile
- Files to create: `backend/Dockerfile`
- Concepts demonstrated:
  - Multi-stage builds
  - Layer caching optimization
  - Security (non-root user)
  - Health checks
- Success criteria:
  - Image builds successfully
  - Container starts and serves requests
  - Health check returns success
  - Image size < 200MB
```

### Step 4: Plan Extension Challenges

Add optional advanced challenges:

**Challenge 1**: [Advanced feature]
- What: [Description]
- Why: [Learning value]
- Difficulty: [Level]

---

## Phase 3: Create Starter Code (2-3 hours)

### Step 1: Build Project Scaffold

Create minimal working structure:
- Directory structure
- Configuration files
- Placeholder files
- Basic README

**What to Include**:
- [ ] Directory structure created
- [ ] Configuration files (`.env.example`, etc.)
- [ ] Dependency files (`requirements.txt`, `package.json`)
- [ ] Docker files (commented templates)
- [ ] Basic README with setup instructions

**What NOT to Include**:
- Complete implementations (learners will build these)
- All code (provide scaffolding only)
- Solutions (these go in separate repo/branch)

### Step 2: Create Starter Files

**Example - Backend Dockerfile Template**:
```dockerfile
# TODO: Choose appropriate Python base image
FROM _______________

# TODO: Set working directory
WORKDIR _______________

# TODO: Copy dependency file
COPY _______________ .

# TODO: Install dependencies
RUN _______________

# TODO: Copy application code
COPY _______________ .

# TODO: Expose application port
EXPOSE _______________

# TODO: Define startup command
CMD _______________
```

**Example - API Route Template**:
```python
"""
User API endpoints.

TODO: Implement the following endpoints:
1. GET /users - List all users
2. GET /users/{id} - Get specific user
3. POST /users - Create new user
4. PUT /users/{id} - Update user
5. DELETE /users/{id} - Delete user

Each endpoint should:
- Validate input data
- Handle errors appropriately
- Return proper HTTP status codes
- Log requests for debugging
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

# TODO: Define Pydantic models for request/response


# TODO: Implement GET /users endpoint
@router.get("/users")
async def list_users():
    """List all users."""
    pass  # Your implementation here


# TODO: Implement GET /users/{id} endpoint


# TODO: Implement POST /users endpoint


# TODO: Implement PUT /users/{id} endpoint


# TODO: Implement DELETE /users/{id} endpoint
```

---

## Phase 4: Build Example Solution (8-12 hours)

### Step 0: Align Repository & Reuse Strategy

1. Review `curriculum/repository-strategy.yaml` to confirm:
   - Whether solutions live in the same repository or a dedicated solutions repo.
   - Single vs per-role repository mode and the destination path (e.g., `solutions/projects/project-01/`).
2. Update the project entry in `curriculum/<role>/modules/` and `curriculum/roles/multi-role-alignment.md` with the selected placement.
3. Identify shared components with other roles to minimize duplication (e.g., reuse libraries, infrastructure modules).
4. If using a separate repo, set up mirrors/CI pipelines so code stays in sync with the main curriculum reference.

### Step 1: Implement Complete Solution

Build the full, production-quality solution:

**Quality Requirements**:
- [ ] All functionality works correctly
- [ ] Code follows best practices
- [ ] Error handling is comprehensive
- [ ] Security considerations addressed
- [ ] Performance is acceptable
- [ ] Code is well-documented
- [ ] Tests included

### Step 2: Test Thoroughly

**Testing Checklist**:
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed
- [ ] Edge cases handled
- [ ] Error scenarios tested
- [ ] Performance tested
- [ ] Security tested

### Step 3: Document Solution

Create comprehensive solution documentation using `templates/solutions/project-solution-template.md`:

**Include**:
- Architecture overview and design decisions
- Implementation notes with cross-role reuse callouts
- Performance, security, and operational considerations
- Validation matrix and automation references
- Links back to learning materials (module/exercise IDs)

---

## Phase 5: Write Implementation Guide (2-3 hours)

### Step 1: Break Down into Steps

Create step-by-step instructions:

**For Each Step**:
- **Objective**: What to build
- **Instructions**: How to build it
- **Code Examples**: Snippets to guide implementation
- **Success Criteria**: How to verify it works
- **Troubleshooting**: Common issues
- **Time Estimate**: How long it should take

**Template for Each Step**:
```markdown
### Step X: [Task Name]

**Objective**: [What learner will build]

**Time Estimate**: [Duration]

**Instructions**:

1. [First action]
   ```bash
   # Command or code example
   ```

2. [Second action]
   ```python
   # Code example
   ```

3. [Third action]

**Success Criteria**:
- [ ] [Criterion 1]
- [ ] [Criterion 2]
- [ ] [Criterion 3]

**Testing**:
```bash
# Commands to verify implementation
```

**Expected Output**:
```
[What learner should see]
```

**Troubleshooting**:

**Issue**: [Common problem]
**Solution**: [How to fix]

**Issue**: [Another problem]
**Solution**: [How to fix]
```

### Step 2: Add Visual Aids

Include diagrams, screenshots, or ASCII art where helpful:

**When to Add Visuals**:
- Architecture overviews
- Data flow diagrams
- Network topologies
- Before/after comparisons
- Expected UI results

---

## Phase 6: Create Assessment Materials (1-2 hours)

### Step 1: Define Assessment Rubric

**Example Rubric**:
```markdown
| Category | Weight | Criteria |
|----------|--------|----------|
| Functionality | 30% | All features work correctly |
| Code Quality | 25% | Clean, maintainable code |
| Testing | 20% | Comprehensive test coverage |
| Documentation | 15% | Clear, complete docs |
| Production Readiness | 10% | Follows best practices |
```

### Step 2: Create Validation Checklist

**Submission Checklist**:
- [ ] All phases completed
- [ ] Tests pass
- [ ] Documentation complete
- [ ] Code follows style guide
- [ ] No security vulnerabilities
- [ ] Performance requirements met

### Step 3: Write Assessment Questions

Create discussion questions for deeper learning:

1. **Analysis**: [Question about design decisions]
2. **Evaluation**: [Question about trade-offs]
3. **Application**: [Question about adapting to different context]

---

## Phase 7: Testing & Refinement (2-4 hours)

### Step 1: Pilot Test

Have someone else attempt the project:

**Pilot Tester Should**:
- Follow instructions exactly as written
- Document any confusion
- Note time taken for each phase
- Identify missing information
- Test on clean environment

**Collect Feedback On**:
- Clarity of instructions
- Completeness of starter code
- Difficulty level
- Time estimates
- Missing prerequisites

### Step 2: Refine Based on Feedback

**Common Issues to Fix**:
- Unclear instructions
- Missing setup steps
- Incorrect time estimates
- Assumptions about prior knowledge
- Missing troubleshooting guidance
- Incomplete starter code

### Step 3: Final Review

**Quality Checklist**:
- [ ] Instructions are clear and complete
- [ ] Code examples are correct
- [ ] Links work
- [ ] Time estimates are accurate
- [ ] Prerequisites are listed
- [ ] Troubleshooting covers common issues
- [ ] Assessment criteria are fair
- [ ] Example solution works

---

## Phase 8: Documentation & Publishing (1 hour)

### Step 1: Create Project README

**README.md Should Include**:
- Project overview
- Learning objectives
- Prerequisites
- Setup instructions
- Project structure
- Getting started guide
- Resources
- Getting help

### Step 2: Organize Files

**Final Structure**:
```
project-name/
├── README.md                 # Main project readme
├── IMPLEMENTATION_GUIDE.md   # Step-by-step guide
├── ASSESSMENT.md             # Rubric and evaluation
├── starter/                  # Starter code for learners
│   ├── README.md
│   ├── docker-compose.yml
│   └── [starter files]
├── solution/                 # Complete solution (location per repository strategy)
│   ├── SOLUTION.md
│   └── [complete implementation]
└── docs/
    ├── ARCHITECTURE.md
    ├── DEPLOYMENT.md
    └── TROUBLESHOOTING.md
```

### Step 3: Publish

**Publishing Checklist**:
- [ ] Create GitHub repository (single or per-role as defined in `repository-strategy.yaml`)
- [ ] Push starter code to main branch
- [ ] Push solution to configured destination (same repo branch / separate repo)
- [ ] Add project to curriculum index
- [ ] Update module README with project link
- [ ] Test clone and setup from fresh environment

---

## Quality Checklist

Before considering project complete:

### Completeness
- [ ] All phases have detailed instructions
- [ ] Starter code provides helpful scaffold
- [ ] Example solution is production-quality
- [ ] Documentation is comprehensive
- [ ] Assessment materials are included

### Educational Value
- [ ] Reinforces module learning objectives
- [ ] Provides real-world applicable skills
- [ ] Appropriate difficulty for target level
- [ ] Builds portfolio-worthy artifact
- [ ] Teaches industry best practices

### Usability
- [ ] Instructions are clear and unambiguous
- [ ] Prerequisites are clearly stated
- [ ] Time estimates are accurate
- [ ] Troubleshooting guidance is helpful
- [ ] Success criteria are measurable

### Quality
- [ ] Code follows style guidelines
- [ ] No security vulnerabilities
- [ ] Performance is acceptable
- [ ] Tests are comprehensive
- [ ] Documentation is complete

---

## Tips for Success

### Make It Real
- Use scenarios from actual companies
- Teach patterns used in production
- Include realistic scale/constraints
- Address real-world challenges

### Progressive Complexity
- Start with core functionality
- Add layers incrementally
- Build confidence before advanced features
- Provide optional challenges

### Provide Scaffolding
- Don't start from blank files
- Give structure and templates
- Include helpful TODO comments
- Link to relevant documentation

### Test Thoroughly
- Pilot with real learners
- Test on clean environment
- Verify time estimates
- Fix issues before launch

### Document Well
- Explain the "why" not just "what"
- Provide context for decisions
- Include troubleshooting
- Link to resources

---

## Resources

### Project Ideas by Module

**Docker/Containers**:
- Multi-container web application
- Microservices deployment
- Container monitoring system

**Kubernetes**:
- Deploy and scale application
- Implement rolling updates
- Set up monitoring and alerts

**CI/CD**:
- Build deployment pipeline
- Automated testing workflow
- Multi-environment deployment

**ML/AI Infrastructure**:
- ML model API
- Training pipeline
- Model monitoring system

### Tools

- **Draw.io**: For architecture diagrams
- **Carbon**: For beautiful code screenshots
- **Asciinema**: For terminal recordings
- **Gitpod**: For browser-based dev environments

---

## Example Project Outline

See `examples/sample-project/` for a complete example project following this workflow.
