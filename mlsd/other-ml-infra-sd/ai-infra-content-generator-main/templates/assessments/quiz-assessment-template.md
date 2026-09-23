# Quiz and Assessment Template

> This template guides the creation of comprehensive assessments for technical curriculum. Assessments should validate learning objectives and provide valuable feedback to learners.

---

## Assessment Metadata

**Assessment ID**: [Unique identifier, e.g., `quiz-004-docker`]
**Assessment Title**: [Clear, descriptive title]
**Module**: [Related module(s)]
**Type**: [Quiz / Test / Exam / Practical Assessment]
**Role/Level**: [Target role and experience level]
**Duration**: [Recommended time, e.g., "30 minutes"]
**Passing Score**: [Minimum percentage to pass, e.g., "70%"]
**Total Points**: [Total possible points]
**Question Count**: [Total number of questions]

**Coverage**:
- [Topic 1] - [X questions]
- [Topic 2] - [Y questions]
- [Topic 3] - [Z questions]

**Learning Objectives Assessed**:
- [ ] Objective 1
- [ ] Objective 2
- [ ] Objective 3
- [ ] Objective 4

---

## Assessment Overview

### Purpose

[2-3 sentences explaining what this assessment measures]

**Example**:
```markdown
This quiz assesses your understanding of Docker containerization concepts,
including image creation, container management, networking, and volumes.
It validates that you can apply Docker in real-world scenarios and make
informed decisions about container architecture.
```

### Instructions

**Before You Begin**:
- [ ] Review Module [X] lecture notes
- [ ] Complete all hands-on exercises
- [ ] Have access to documentation (if open-book)
- [ ] Ensure stable internet connection

**Assessment Rules**:
- **Time Limit**: [X minutes]
- **Attempts**: [Number allowed, e.g., "2 attempts"]
- **Resources**: [Open book / Closed book / Documentation only]
- **Format**: [Multiple choice / Mix / Practical]
- **Passing Score**: [Percentage required]

**Tips for Success**:
- Read each question carefully
- Eliminate obviously wrong answers first
- Use technical documentation when allowed
- Review all answers before submitting
- Budget time: ~[X] minutes per question

---

## Question Bank

### Difficulty Distribution

- **Easy** (30%): [X questions] - Basic recall and understanding
- **Medium** (50%): [Y questions] - Application and analysis
- **Hard** (20%): [Z questions] - Synthesis and evaluation

---

## Section 1: [Topic Name]

**Points**: [Total points for this section]
**Questions**: [Number of questions]
**Time Estimate**: [Suggested time]

---

### Question 1: [Question Type] - [Difficulty: Easy/Medium/Hard]

**Points**: [X points]
**Topic**: [Specific concept being tested]
**Learning Objective**: [Which objective this validates]

**Question**:

[Question text here]

**Example (Multiple Choice)**:
```markdown
Which command creates a new Docker container and starts it immediately?

A) docker create myapp
B) docker start myapp
C) docker run myapp
D) docker launch myapp
```

**Example (Code-Based)**:
```markdown
Given the following Dockerfile, what will be the result when building this image?

```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["python", "app.py"]
```

A) The image will fail to build
B) The image will build but won't run
C) The image will build and run successfully
D) The command syntax is invalid
```

**Example (Scenario-Based)**:
```markdown
Your application consists of a web server, API server, and database. You need
these services to communicate privately. Which Docker feature should you use?

A) Docker volumes
B) Docker networks
C) Docker links (deprecated)
D) Docker compose only
```

**Example (Troubleshooting)**:
```markdown
A developer reports their container exits immediately after starting. The logs
show: "Error: Cannot find module '/app/server.js'". What's the most likely cause?

A) Node.js is not installed in the container
B) The COPY command didn't include server.js
C) The WORKDIR is set incorrectly
D) Port mapping is missing
```

**Answer Options**:

A) [Option A text]
B) [Option B text]
C) [Option C text]
D) [Option D text]

**Correct Answer**: [Letter]

**Explanation**:

[Detailed explanation of why the correct answer is right and others are wrong]

**Example**:
```markdown
Correct Answer: C

Explanation:
The correct answer is C) docker run myapp.

The `docker run` command combines `docker create` and `docker start` into a
single operation. It creates a new container from the specified image and
starts it immediately.

Why other options are incorrect:
- A) `docker create` only creates the container but doesn't start it
- B) `docker start` starts an existing container, not create a new one
- D) `docker launch` is not a valid Docker command

Production Note: Use `docker run -d` to run containers in detached mode,
and `docker run -it` for interactive sessions with a terminal.
```

**Distractor Analysis**:
[Why incorrect options might seem plausible]

**Example**:
```markdown
- Option A is plausible because `create` suggests making something new
- Option B is commonly confused with `run` by beginners
- Option D uses terminology from other tools (e.g., AWS EC2 instances)
```

**Learning Resources**:
- [Link to relevant lecture notes section]
- [Link to documentation]
- [Link to example]

**Tags**: [`docker`, `commands`, `basics`]

---

### Question 2: [Multiple Select] - [Difficulty: Medium]

**Points**: [X points]
**Topic**: [Specific concept]
**Learning Objective**: [Which objective this validates]

**Question**:

[Question text]

**Example**:
```markdown
Which of the following are valid ways to persist data in Docker containers?
Select all that apply.

□ A) Using Docker volumes
□ B) Using bind mounts
□ C) Writing to the container's writable layer
□ D) Using tmpfs mounts
□ E) Copying files out after container stops
```

**Correct Answers**: [List letters]

**Explanation**:

[Detailed explanation]

**Example**:
```markdown
Correct Answers: A, B, D

Explanation:

A) Docker volumes ✓
Volumes are the preferred mechanism for persisting data. They're managed by
Docker and stored outside the container's filesystem.

B) Bind mounts ✓
Bind mounts allow you to mount a host directory into the container. While
less portable than volumes, they're valid for persistence.

C) Container's writable layer ✗
Data written to the writable layer is lost when the container is removed.
This is not a persistence mechanism.

D) tmpfs mounts ✓
tmpfs mounts persist data in the host's memory. While temporary (lost on
reboot), they are a valid persistence mechanism for sensitive data.

E) Copying files ✗
While technically you can copy files out, this isn't a "persistence mechanism"
in the Docker sense - it's manual data extraction.

Key Concept: Volumes > Bind Mounts > tmpfs for most use cases.
Use volumes for production, bind mounts for development.
```

**Scoring**:
- All correct: [X] points
- Partial: [Formula for partial credit]

---

### Question 3: [Fill in the Blank / Code Completion] - [Difficulty: Medium]

**Points**: [X points]
**Topic**: [Specific concept]
**Learning Objective**: [Which objective this validates]

**Question**:

[Question text with blanks]

**Example**:
```markdown
Complete the docker-compose.yml file to set up a web application with a database:

```yaml
version: '3.8'
services:
  web:
    image: ___________
    ports:
      - "___________"
    environment:
      - DB_HOST=___________
    depends_on:
      - ___________

  db:
    image: postgres:14
    volumes:
      - ___________:/var/lib/postgresql/data
```

Fill in the blanks:
1. ___________ (web service image)
2. ___________ (port mapping)
3. ___________ (database host reference)
4. ___________ (service dependency)
5. ___________ (volume name)
```

**Acceptable Answers**:

1. [Answer 1 options]
2. [Answer 2 options]
3. [Answer 3 options]

**Example**:
```markdown
Acceptable Answers:

1. Any valid image reference: myapp:latest, nginx, python:3.9, etc.
2. "8000:8000" or similar valid port mapping (host:container)
3. "db" (the service name from docker-compose)
4. "db" (the database service name)
5. Any valid volume name: "db_data", "postgres_data", etc.

Full Solution:
```yaml
version: '3.8'
services:
  web:
    image: myapp:latest
    ports:
      - "8000:8000"
    environment:
      - DB_HOST=db
    depends_on:
      - db

  db:
    image: postgres:14
    volumes:
      - db_data:/var/lib/postgresql/data

volumes:
  db_data:
```

Key Concepts:
- Service names become hostnames in Docker networks
- depends_on ensures database starts before web service
- Named volumes are declared at the bottom
- Port mapping format is always "host:container"
```

---

### Question 4: [Scenario Analysis] - [Difficulty: Hard]

**Points**: [X points]
**Topic**: [Specific concept]
**Learning Objective**: [Which objective this validates]

**Question**:

[Complex scenario description]

**Example**:
```markdown
You're deploying a microservices application with the following requirements:

**Services**:
- Frontend (React): Serves UI, needs to call API
- Backend API (Python): Business logic, needs database access
- Database (PostgreSQL): Data storage
- Cache (Redis): Session storage

**Requirements**:
1. Frontend and API must scale independently
2. Database credentials must not be in source code
3. Cache data is ephemeral (okay to lose on restart)
4. Only Frontend should be accessible from internet
5. Services must communicate securely

**Question**: Design the Docker architecture. Which approach is BEST?

A) Single container with all services, use environment variables for config

B) Separate containers, custom bridge network, secrets for credentials, bind
   mount for cache

C) Separate containers, custom bridge network, secrets for credentials, tmpfs
   mount for cache, only Frontend on host network

D) Docker Swarm with separate services, overlay network, Docker secrets,
   tmpfs mount for cache, Frontend with published port
```

**Correct Answer**: [Letter]

**Explanation**:

[Comprehensive analysis of each option]

**Example**:
```markdown
Correct Answer: D (or C for non-Swarm environments)

Detailed Analysis:

Option A: Single Container ✗
- Violates requirement #1 (independent scaling)
- Poor separation of concerns
- Difficult to update individual services
- Creates a monolith, defeating microservices purpose

Option B: Containers + Bind Mount for Cache ✗
- Meets most requirements but suboptimal cache strategy
- Bind mounts for cache data are persistent (violates requirement #3)
- Better than A, but not best solution
- Bind mounts have performance implications

Option C: Optimal for Docker Compose ✓ (if not using Swarm)
- Separate containers: Independent scaling ✓
- Custom bridge network: Secure internal communication ✓
- Secrets: Secure credential management ✓
- tmpfs mount: Ephemeral cache storage ✓
- Only Frontend exposed: Network security ✓

Option D: Optimal for Production (Docker Swarm) ✓✓
All benefits of C, plus:
- Native orchestration for true independent scaling
- Overlay network for secure multi-host communication
- Docker secrets are encrypted and distributed securely
- Published ports only on Frontend for internet access
- Built-in service discovery and load balancing

Best Practice:
- Use Option C for development/small deployments
- Use Option D for production/enterprise deployments
- Consider Kubernetes for more advanced orchestration needs

Architecture Diagram:
```
Internet
   │
   ▼
[Frontend :80] ──┐
                 │
        [Bridge Network]
                 │
   ┌─────────────┼─────────────┐
   │             │             │
   ▼             ▼             ▼
[Backend]    [Database]    [Redis]
  API       (secrets)      (tmpfs)
```
```

---

### Question 5: [Debugging/Troubleshooting] - [Difficulty: Hard]

**Points**: [X points]
**Topic**: [Specific concept]
**Learning Objective**: [Which objective this validates]

**Question**:

[Present a problem with code/logs]

**Example**:
```markdown
A developer is trying to run a Dockerized application but encounters this error:

```bash
$ docker run -p 8000:8000 myapp:latest

Error: Cannot start container a3f2c91: Bind for 0.0.0.0:8000 failed:
port is already allocated
```

They try these solutions:

**Attempt 1**: Change port mapping to `9000:8000`
Result: Container starts but application doesn't work

**Attempt 2**: Run `docker stop $(docker ps -aq)` and retry original command
Result: Container starts and works

**Question**: What was the root cause and what's the proper solution?

A) Port 8000 is used by another process. Solution: Always use different ports

B) Another Docker container was using port 8000. Solution: Stop unused
   containers or use distinct ports

C) Docker daemon error. Solution: Restart Docker

D) Firewall blocking port 8000. Solution: Configure firewall rules
```

**Correct Answer**: [Letter]

**Explanation**:

[Analysis with teaching points]

**Example**:
```markdown
Correct Answer: B

Root Cause Analysis:

The error "port is already allocated" indicates that Docker cannot bind to
port 8000 on the host because something is already using it.

Attempt 1 Analysis:
Changing to `-p 9000:8000` maps host port 9000 to container port 8000.
This avoids the conflict but breaks the application because:
- The application expects to receive traffic on port 8000 (inside container)
- Clients are trying to connect to the wrong port
- Frontend might be configured to call backend on port 8000

Attempt 2 Analysis:
Stopping all containers (`docker ps -aq`) freed port 8000, confirming another
Docker container was the culprit.

Why Other Options Are Wrong:

A) Partially correct but incomplete
- Yes, port conflict, but doesn't identify it as a Docker container
- Solution is overly broad - you don't always need different ports
- Misses the proper investigation and management approach

C) Not a Docker daemon error
- Daemon is functioning correctly by preventing port conflicts
- Restarting Docker would temporarily fix but not address root cause
- Would impact all running containers unnecessarily

D) Not a firewall issue
- Firewall blocks external connections, not port binding
- Error message is specific to allocation, not blocking
- Port 8000 is already allocated, not blocked

Proper Solution Workflow:

1. Identify what's using the port:
```bash
# On Linux/Mac:
sudo lsof -i :8000

# On Windows:
netstat -ano | findstr :8000
```

2. Check Docker containers specifically:
```bash
docker ps --format "table {{.Names}}\\t{{.Ports}}" | grep 8000
```

3. Choose appropriate action:
- If old/unused container: `docker stop <container-name>`
- If needed container: Use different ports for new one
- If non-Docker process: Stop that process or use different port

4. Clean up stopped containers:
```bash
docker container prune
```

Production Best Practices:
- Use docker-compose to manage port allocations
- Document port assignments in README
- Use container names to identify services
- Implement health checks to detect port conflicts early
- Use dynamic ports where possible (e.g., 0:8000 lets Docker assign)

Teaching Points:
- Error messages are specific - "port is already allocated" ≠ "connection refused"
- Systematic debugging beats trial-and-error
- Understanding the problem leads to better solutions
- Quick fixes (stopping all containers) may work but aren't proper solutions
```

---

## Section 2: [Practical Application]

**Format**: [Hands-on / Code Writing / Architecture Design]
**Points**: [Total points for this section]
**Time Estimate**: [Suggested time]

---

### Practical Question 1: [Writing Dockerfile]

**Points**: [X points]
**Topic**: [Dockerfile creation]
**Learning Objective**: [Which objective this validates]

**Question**:

[Practical task description]

**Example**:
```markdown
Write a production-ready Dockerfile for a Node.js application with these
requirements:

**Application Details**:
- Node.js 18.x LTS
- Express application in `src/server.js`
- Dependencies in `package.json` and `package-lock.json`
- Runs on port 3000
- Needs environment variable `DATABASE_URL`

**Requirements**:
1. Use official Node.js base image
2. Optimize for layer caching
3. Don't run as root user
4. Include health check
5. Minimize image size

Write your Dockerfile below:
```

**Grading Rubric**:

| Criteria | Points | Requirements |
|----------|--------|--------------|
| Base Image | [X] | Uses appropriate Node.js image |
| Layer Optimization | [X] | COPY package*.json before code |
| Security | [X] | Non-root user specified |
| Health Check | [X] | HEALTHCHECK instruction present |
| Best Practices | [X] | Multi-stage if applicable, .dockerignore mentioned |

**Model Answer**:

[Exemplary solution with explanations]

**Example**:
```dockerfile
# Build stage
FROM node:18-alpine AS builder

# Set working directory
WORKDIR /app

# Copy package files first (leverage layer caching)
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy application code
COPY src/ ./src/

# Production stage
FROM node:18-alpine

# Create non-root user
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nodejs -u 1001

# Set working directory
WORKDIR /app

# Copy dependencies and code from builder
COPY --from=builder --chown=nodejs:nodejs /app /app

# Switch to non-root user
USER nodejs

# Expose application port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s \
  CMD node -e "require('http').get('http://localhost:3000/health', (r) => process.exit(r.statusCode === 200 ? 0 : 1))"

# Start application
CMD ["node", "src/server.js"]
```

**Explanation of Key Decisions**:

1. **Multi-stage build**: Separates build and runtime, reduces image size
2. **Alpine base**: Minimal image size (~50MB vs ~200MB for full Node)
3. **Package files first**: Leverages Docker layer caching - dependencies
   don't rebuild when only code changes
4. **npm ci**: Faster, more reliable than npm install for production
5. **Non-root user**: Security best practice - prevents privilege escalation
6. **Health check**: Kubernetes/Docker can monitor application health
7. **COPY --chown**: Sets ownership in one layer, more efficient

**Alternative Approaches**:

```dockerfile
# Lighter alternative using distroless
FROM gcr.io/distroless/nodejs18-debian11
# Even smaller, but no shell for debugging

# Development alternative
FROM node:18
# Includes dev tools, larger but easier to debug
```

**Common Mistakes to Avoid**:

✗ `COPY . .` before `RUN npm install` (breaks layer caching)
✗ Running as root (security risk)
✗ No health check (poor observability)
✗ Using `latest` tag (not reproducible)
✗ Installing dev dependencies in production
