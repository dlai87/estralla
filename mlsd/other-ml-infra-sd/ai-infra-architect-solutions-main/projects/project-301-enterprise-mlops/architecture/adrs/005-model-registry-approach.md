# ADR-005: Model Registry and Governance Approach

**Status**: Accepted
**Date**: 2024-10-18
**Decision Makers**: Principal Architect, VP Engineering, Lead ML Engineer, Compliance Officer
**Stakeholders**: Data Science Teams, ML Platform Team, Security Team, Audit Team

## Context

Our enterprise MLOps platform needs a model registry to:
- Track model versions and lineage
- Implement approval workflows for production deployments
- Enable model discovery and reuse
- Support compliance and audit requirements
- Manage model metadata and documentation

### Current Pain Points

**Problem 1: No Central Model Registry**
- Models scattered across S3 buckets, local machines, notebooks
- No version control or lineage tracking
- Can't answer "which models are in production?"
- Estimated impact: 20% of ML eng time spent tracking models

**Problem 2: No Approval Process**
- Anyone can deploy any model to production
- No quality gates or governance
- High risk of deploying broken models
- Several production incidents from unvalidated models

**Problem 3: Poor Model Documentation**
- Models deployed without adequate documentation
- Hard to understand what model does, who owns it
- Onboarding new team members takes weeks
- Debugging production issues difficult

**Problem 4: Compliance Gaps**
- Can't demonstrate which data was used to train models
- No audit trail of model changes
- Unable to reproduce model predictions
- Risk of regulatory fines ($10M+)

**Total Cost**: $2M/year in inefficiency + $10M+ regulatory risk

### Forces

- **Regulatory Requirements**: SOC2, HIPAA require model governance
- **Risk Tolerance**: Can't allow unvalidated models in production
- **Team Size**: 100+ data scientists, need self-service
- **Speed**: Can't slow down deployment with manual reviews
- **Flexibility**: Different models have different risk levels
- **Existing Tools**: Teams familiar with MLflow

## Decision

We will implement **MLflow Model Registry with Custom Governance Extensions**.

### Architecture

```
┌────────────────────────────────────────────────────────────┐
│               MLflow Model Registry + Governance            │
├────────────────────────────────────────────────────────────┤
│                                                              │
│  Data Scientist Workflow                                     │
│  ┌────────────────────────────────────────────────────┐    │
│  │ 1. Train model (notebooks / pipelines)            │    │
│  │ 2. Log to MLflow Tracking                         │    │
│  │ 3. Register model → Model Registry                │    │
│  │ 4. Trigger governance checks (automatic)          │    │
│  └────────────────────────────────────────────────────┘    │
│                           │                                  │
│                           ▼                                  │
│  ┌────────────────────────────────────────────────────┐    │
│  │     MLflow Model Registry (PostgreSQL backend)     │    │
│  │                                                      │    │
│  │  Model: fraud-detection-v1                         │    │
│  │  ├─ Version 1: Staging                             │    │
│  │  ├─ Version 2: Staging → Automated Checks         │    │
│  │  ├─ Version 3: Production (approved)               │    │
│  │  │                                                  │    │
│  │  Metadata:                                         │    │
│  │  - Model type, framework                           │    │
│  │  - Training data lineage                           │    │
│  │  - Performance metrics                             │    │
│  │  - Approval status & approver                      │    │
│  │  - Deployment history                              │    │
│  └────────────────────────────────────────────────────┘    │
│                           │                                  │
│                           ▼                                  │
│  ┌────────────────────────────────────────────────────┐    │
│  │          Governance Service (Custom)               │    │
│  │                                                      │    │
│  │  Automated Checks (runs on every model version):   │    │
│  │  ✓ Performance metrics > baseline                  │    │
│  │  ✓ Bias metrics within thresholds                  │    │
│  │  ✓ Data lineage complete                           │    │
│  │  ✓ Security scan (no malicious code)              │    │
│  │  ✓ Schema validation                               │    │
│  │  ✓ Unit tests passing                              │    │
│  │                                                      │    │
│  │  Risk Classification:                              │    │
│  │  - Low Risk → Auto-approve                         │    │
│  │  - Medium Risk → ML Engineer review               │    │
│  │  - High Risk → Senior approval required           │    │
│  └────────────────────────────────────────────────────┘    │
│                           │                                  │
│                           ▼                                  │
│  ┌────────────────────────────────────────────────────┐    │
│  │         Approval Workflow (conditional)            │    │
│  │                                                      │    │
│  │  Low Risk (auto-approve):                          │    │
│  │  → Non-production environments                     │    │
│  │  → A/B test <1% traffic                           │    │
│  │  → Non-critical models                            │    │
│  │                                                      │    │
│  │  High Risk (human approval required):              │    │
│  │  → First production deployment                     │    │
│  │  → Handles PII or sensitive data                  │    │
│  │  → Financial impact >$1M                          │    │
│  │  → Regulated domains (healthcare, finance)         │    │
│  │                                                      │    │
│  │  Approvers: ML Engineer → Model Owner → Sr. Eng   │    │
│  └────────────────────────────────────────────────────┘    │
│                           │                                  │
│                           ▼                                  │
│  ┌────────────────────────────────────────────────────┐    │
│  │          Model Deployment (KServe)                 │    │
│  │  - Only approved models can be deployed            │    │
│  │  - Audit log of all deployments                    │    │
│  │  - Automatic rollback if health checks fail        │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
└────────────────────────────────────────────────────────────┘
```

### Key Components

**1. MLflow Model Registry (Core)**
- Centralized model storage and versioning
- Stages: None → Staging → Production → Archived
- Model metadata: framework, signature, metrics
- Transition hooks for governance checks

**2. Custom Governance Service**
- Python service that hooks into MLflow lifecycle events
- Runs automated checks on model registration
- Classifies risk level
- Manages approval workflow
- Publishes audit events

**3. Approval Workflow**
- Slack/Email notifications for approvals
- Web UI for review (links to model card, metrics, lineage)
- Approval recorded in PostgreSQL
- Audit trail for compliance

**4. Model Cards (Automated)**
- Generated from training metadata
- Includes: performance, data, bias metrics, intended use
- Stored with model in registry
- Required for high-risk models

### Governance Rules

**Auto-Approval Criteria** (all must pass):
- ✅ Performance metrics > baseline (+/- 5% acceptable drift)
- ✅ Bias metrics within policy (e.g., demographic parity <10%)
- ✅ Data lineage complete (training data tracked)
- ✅ Unit tests passing (100% pass rate)
- ✅ Security scan clean (no vulnerabilities)
- ✅ Schema validation passed
- ✅ Deployment target is non-production OR <1% traffic

**Human Approval Required** (any condition):
- ❗ First deployment of new model type
- ❗ Model processes PII or sensitive data
- ❗ Financial impact >$1M annually
- ❗ Regulated domain (healthcare, finance, legal)
- ❗ Production deployment >10% traffic
- ❗ Model shows significant performance change (>10% drift)

### Risk Classification

**Low Risk**:
- Internal tools, non-customer-facing
- Limited data access
- Easy to rollback
- Example: Internal analytics model

**Medium Risk**:
- Customer-facing, non-critical
- Moderate financial impact (<$1M)
- Handles non-sensitive data
- Example: Product recommendation

**High Risk**:
- Critical customer experience
- Handles PII or financial data
- Regulatory compliance required
- High financial impact (>$1M)
- Example: Fraud detection, credit scoring

## Alternatives Considered

### Alternative 1: Commercial Model Registry (Tecton, DataRobot)

**Pros**:
- Built-in governance features
- Enterprise support
- Comprehensive audit trails

**Cons**:
- **Expensive**: $200-500K/year
- **Vendor lock-in**: Difficult to migrate
- **Limited customization**: Can't modify governance rules
- **Team unfamiliar**: Would need training

**Decision**: Rejected due to cost and customization needs

---

### Alternative 2: Git-Based Model Registry

**Pros**:
- Familiar to engineers (Git workflow)
- Version control built-in
- Free

**Cons**:
- **No model metadata**: Git doesn't track metrics, lineage
- **Large files**: Git not designed for binary model files
- **No discovery**: Can't search models by metrics
- **Manual workflow**: No automation

**Decision**: Rejected as insufficient for our scale

---

### Alternative 3: AWS SageMaker Model Registry

**Pros**:
- Managed service
- Integrated with SageMaker
- Approval workflows available

**Cons**:
- **AWS lock-in**: Can't migrate to GCP/Azure
- **SageMaker dependency**: We use KServe, not SageMaker
- **Limited customization**: Can't add custom checks
- **Cost**: $150-300K/year at our scale

**Decision**: Rejected due to vendor lock-in

---

### Alternative 4: Custom-Built Registry

**Pros**:
- Perfect fit for needs
- Full control

**Cons**:
- **High development cost**: $1.5M (12 months, 5 engineers)
- **High risk**: Complex system
- **Reinventing wheel**: MLflow exists
- **Ongoing maintenance**: 2 engineers full-time

**Decision**: Rejected as too expensive

## Consequences

### Positive

✅ **Cost-Effective**: $0 licensing (MLflow) + $200K development (governance extensions)
- **vs Commercial**: Savings of $300-500K/year

✅ **Team Familiar**: Teams already use MLflow for tracking
- **Adoption**: Minimal training needed

✅ **Flexible**: Can customize governance rules for our needs
- **Examples**: Add custom checks, integrate with internal tools

✅ **Compliant**: Audit trail, approval workflows meet SOC2/HIPAA
- **Risk Reduction**: Estimated $10M+ regulatory risk mitigated

✅ **Balanced**: Automates low-risk, reviews high-risk (speed + safety)
- **Deployment Time**: 70% of models auto-approved (<1 hour)
- **Risk**: High-risk models still require human judgment

✅ **Scalable**: Can handle 1000s of models
- **Performance**: PostgreSQL backend proven at scale

### Negative

⚠️ **Custom Code to Maintain**: Governance service needs development and maintenance
- *Effort*: 2 engineer-months to build, 0.5 engineer ongoing
- *Risk*: Low - well-defined scope

⚠️ **False Positives**: Automated checks may reject valid models
- *Mitigation*: Override mechanism for ML Engineers
- *Monitoring*: Track false positive rate (<5% target)

⚠️ **Approval Bottleneck**: Human reviews could slow deployments
- *Mitigation*: 24-hour SLA for reviews, escalation process
- *Monitoring*: Track approval time (target: <4 hours)

⚠️ **MLflow Limitations**: Some advanced features not available
- *Missing*: Real-time model monitoring (build separately)
- *Impact*: Low - can integrate external tools

### Risks and Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Governance too strict (slows teams) | Medium | Medium | Iterative tuning, exemption process, metrics-driven refinement |
| Governance too loose (bad model deployed) | Low | High | Regular audits, incident reviews, tighten rules as needed |
| Approval bottleneck | Medium | Medium | 24hr SLA, on-call reviewer, escalation process, auto-approve more |
| Custom code bugs | Medium | Medium | Comprehensive tests, staging environment, gradual rollout |
| MLflow scalability issues | Low | Medium | PostgreSQL tuning, caching, monitoring, fallback to sharding |

## Implementation Plan

### Phase 1: Core Registry (Months 1-2)
- Deploy MLflow Model Registry with PostgreSQL
- Migrate existing models to registry
- Basic approval workflow (manual)
- Documentation and training

**Deliverables**:
- MLflow deployed on Kubernetes
- 50 existing models migrated
- Approval Slack bot

### Phase 2: Automated Checks (Months 3-4)
- Build governance service (Python)
- Implement automated checks (performance, bias, schema)
- Risk classification logic
- Model card generation

**Deliverables**:
- Governance service deployed
- 8 automated checks implemented
- Model card templates

### Phase 3: Advanced Governance (Months 5-6)
- Data lineage tracking
- Approval workflow refinement
- Audit reporting dashboard
- Integration with KServe (deployment)

**Deliverables**:
- End-to-end lineage
- Compliance reports
- Automated deployment for approved models

### Phase 4: Scale and Optimize (Months 7-9)
- Performance optimization (caching, indexing)
- Advanced features (model comparison, experiment linking)
- Self-service UI improvements
- SOC2 audit preparation

**Deliverables**:
- Handle 1000+ models
- SOC2 compliance artifacts
- Runbooks and training materials

## Success Metrics

| Metric | Baseline | 6 Months | 12 Months |
|--------|----------|----------|-----------|
| **Models Registered** | 50 | 200 | 500 |
| **Auto-Approval Rate** | 0% | 60% | 70% |
| **Approval Time (high-risk)** | N/A | 4 hours | 2 hours |
| **Production Incidents (bad model)** | 2/quarter | <1/quarter | 0 |
| **Compliance Audit Findings** | 5 | 0 | 0 |
| **Team Satisfaction** | N/A | 8/10 | 9/10 |

## Audit and Compliance

**Audit Trail Includes**:
- Model registration events (who, when, what)
- All approval decisions with rationale
- Production deployments with timestamps
- Model updates and transitions
- Data lineage (training data → model)
- Performance metrics over time

**Compliance Mapping**:
- **SOC2 CC6.1**: Access controls via RBAC
- **SOC2 CC7.2**: Monitoring via audit logs
- **HIPAA §164.308**: Model approval for PHI data
- **GDPR Article 22**: Explainability requirements (model cards)

**Retention**: 7 years (audit logs), 3 years (models)

## Related Decisions

- [ADR-001: Platform Technology Stack](./001-platform-technology-stack.md) - MLflow selection
- [ADR-010: Governance Framework Design](./010-governance-framework.md) - Overall governance approach
- [ADR-007: Security and Compliance](./007-security-compliance-architecture.md) - Security controls

## Review and Update

- **Next Review**: Q4 2025 (after 6 months in production)
- **Trigger for Revision**:
  - Compliance audit failure
  - Approval bottleneck (>8 hour avg)
  - Production incident from governance gap
  - Team satisfaction <7/10
- **Owner**: Lead ML Engineer + Compliance Officer

## References

- MLflow Model Registry: https://mlflow.org/docs/latest/model-registry.html
- Model Governance Best Practices: [Google, Microsoft, Amazon ML governance papers]
- Internal: `docs/model-governance-policy.pdf`

---

**Approved by**: VP Engineering (John Doe), Principal Architect (Your Name), Lead ML Engineer (Jane Chen), Compliance Officer (Tom Brown)
**Date**: 2024-10-18
