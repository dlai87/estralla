# Project Solution Blueprint

> Use for complete project implementations. Store under `solutions/projects/project-<id>/` in the chosen solutions repository.

## Project Metadata

- **Project ID**:  
- **Project Title**:  
- **Linked Module(s)**:  
- **Target Role(s)**:  
- **Difficulty**: (Intermediate / Advanced / Expert)  
- **Solution Maintainer**:  
- **Last Validation Date**: YYYY-MM-DD  

## Architecture Summary

- **Problem Statement Recap**:  
- **Key Requirements**:  
- **High-Level Architecture Diagram Description** (bullet list describing components and interactions)
- **Technology Stack & Versions**:  
  - Service runtime:  
  - Data store:  
  - Messaging / streaming:  
  - Infrastructure:  

## Repository Structure

```
project-<id>/
  README.md              # Solution overview & quickstart
  src/                   # Implementation
  infra/                 # IaC / deployment manifests
  tests/                 # Automated tests
  docs/
    architecture.md      # Detailed architecture decisions
    runbook.md           # Operations guide
  Makefile / scripts/    # Automation helpers
```

## Implementation Notes

- **Design Decisions** (list ADR-style summaries with rationale and trade-offs)
- **Security & Compliance** considerations
- **Performance Optimizations**
- **Scalability Strategies**
- **Failure Modes & Mitigations**

## Validation Matrix

| Validation Type | Tool / Command | Status | Last Run | Notes |
|-----------------|----------------|--------|----------|-------|
| Unit Tests |  |  |  |  |
| Integration Tests |  |  |  |  |
| Static Analysis |  |  |  |  |
| Security Scan |  |  |  |  |
| Load Test |  |  |  |  |

## Deployment & Operations

- **Deployment Steps** (CLI commands or pipelines)
- **Environment Variables / Secrets** (redact values)
- **Monitoring & Observability Setup**
- **Runbook Highlights** (startup, health checks, incident response)

## Alignment & Reuse

- **Upstream Modules / Roles** this solution builds upon
- **Downstream Modules / Roles** that reuse artifacts
- **Shared Components** (libraries, infra modules) and ownership

## Appendix

- **Sample Data / Fixtures**: location & format
- **CI/CD Pipeline Reference**
- **Known Issues / Future Enhancements**
- **Reviewer Sign-off**: Name, title, date
