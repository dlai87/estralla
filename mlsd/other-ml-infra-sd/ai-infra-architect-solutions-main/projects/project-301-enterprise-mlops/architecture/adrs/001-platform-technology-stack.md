# ADR-001: Platform Technology Stack Selection

**Status**: Accepted
**Date**: 2024-10-15
**Decision Makers**: Principal Architect, CTO, VP Engineering
**Stakeholders**: ML Platform Team, Data Science Teams, SRE Team, Security Team

## Context

We need to select the core technology stack for our enterprise MLOps platform that will support 100+ data scientists across 20+ teams. The platform must be:

- Scalable (1000 scientists, 5000 models by Year 3)
- Cost-effective (target 35% cost reduction)
- Cloud-agnostic (avoid vendor lock-in)
- Compliance-ready (SOC2, HIPAA, GDPR)
- Team-friendly (leverage existing Kubernetes expertise)

### Forces

- **Team Skills**: Strong Kubernetes and Python expertise, limited AWS-specific knowledge
- **Budget**: $3M/year infrastructure budget (Year 1)
- **Timeline**: 12 months to production platform
- **Compliance**: Need SOC2 certification within 18 months
- **Vendor Lock-In Risk**: Must avoid lock-in to single cloud provider
- **Operational Burden**: 12-person team can support ~5-7 core systems well
- **Data Science Preferences**: Teams currently use mix of tools (MLflow, SageMaker, custom)

## Decision

We will use an **open-source, Kubernetes-based stack** with the following core technologies:

| Component | Technology | Version | Rationale |
|-----------|-----------|---------|-----------|
| **Container Orchestration** | Kubernetes (EKS) | 1.28+ | Industry standard, portable, strong ecosystem |
| **Experiment Tracking** | MLflow | 2.8+ | De-facto standard, framework-agnostic, open source |
| **Feature Store** | Feast | 0.34+ | Open source, flexible, no license costs |
| **Training Orchestration** | Kubeflow Pipelines | 2.0+ | K8s-native, reproducible workflows |
| **Model Serving** | KServe | 0.11+ | Multi-framework, auto-scaling, A/B testing |
| **Monitoring** | Prometheus + Grafana | Latest | Standard observability, ML extensions available |
| **Model Registry** | MLflow Registry + Custom Governance | 2.8+ | Familiar tool with custom approval workflows |
| **Notebooks** | JupyterHub | 4.0+ | Standard for data science |
| **CI/CD** | GitHub Actions + ArgoCD | Latest | GitOps, familiar to teams |
| **Infrastructure as Code** | Terraform | 1.6+ | Multi-cloud, widely adopted |

**Cloud Provider**: AWS (with Terraform abstraction for future multi-cloud)

**Avoided Technologies**:
- SageMaker (AWS lock-in, limited customization)
- Tecton (high cost: $500K/year)
- Databricks (partial solution, expensive)
- Vertex AI (GCP lock-in)
- Custom-built platform (too risky, high development cost)

## Alternatives Considered

### Alternative 1: AWS SageMaker-Centric

**Pros**:
- Fully managed (less operational burden)
- Integrated with AWS services
- Strong compliance features

**Cons**:
- Vendor lock-in (migration very difficult)
- Expensive ($4M+/year at scale)
- Limited customization for our governance needs
- Doesn't leverage team's Kubernetes expertise

**Decision**: Rejected due to lock-in and cost

---

### Alternative 2: Databricks Lakehouse Platform

**Pros**:
- Integrated data + ML platform
- Strong for Spark-based workloads
- Good governance features

**Cons**:
- Expensive ($2-3M/year)
- Doesn't solve model serving (need separate solution)
- Steep learning curve for teams
- Vendor lock-in

**Decision**: Rejected due to cost and incomplete solution

---

### Alternative 3: Google Vertex AI

**Pros**:
- Fully managed
- Good AutoML features
- Integrated with GCP

**Cons**:
- GCP lock-in (we're AWS-first)
- Migration from AWS costly ($500K+)
- Doesn't leverage existing AWS investments
- Team has minimal GCP experience

**Decision**: Rejected due to cloud provider mismatch

---

### Alternative 4: Custom-Built Platform

**Pros**:
- Maximum flexibility
- No licensing costs
- Perfect fit for our needs

**Cons**:
- High development cost ($5-8M, 18+ months)
- High risk (may fail to deliver)
- Ongoing maintenance burden
- Reinventing the wheel

**Decision**: Rejected as too risky and expensive

## Consequences

### Positive

✅ **Cost-Effective**: Open source saves $2-3M/year in licensing
✅ **Portable**: Kubernetes allows future multi-cloud (Year 2-3 roadmap)
✅ **Team Alignment**: Leverages existing Kubernetes and Python expertise
✅ **Customizable**: Can add governance and compliance features we need
✅ **Ecosystem**: Large community, many integrations, good hiring market
✅ **Future-Proof**: Active projects with strong community support

### Negative

⚠️ **Operational Burden**: We manage infrastructure (vs fully managed)
- *Mitigation*: Strong SRE team (5 engineers), managed services where possible (RDS, S3)

⚠️ **Integration Work**: Need to integrate multiple tools
- *Mitigation*: Platform team builds unified API, documented integrations

⚠️ **Maturity Gaps**: Some tools less mature than commercial alternatives
- *Mitigation*: Careful version selection, contribute to OSS projects, fallback vendors identified

⚠️ **Support**: Community support vs enterprise SLAs
- *Mitigation*: Commercial support contracts for critical components (e.g., Prometheus)

### Risks and Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Feast abandonment by community | Low | High | Monitor activity, have migration path to Tecton |
| Kubeflow complexity overwhelms team | Medium | Medium | Phased rollout, training, use managed Kubeflow initially |
| Integration issues between components | Medium | Medium | Proof-of-concept before full deployment, buffer time |
| Operational burden exceeds capacity | Medium | High | Hire 3 additional SREs, automation focus |

## Validation

### Proof of Concept

Conducted 8-week POC with 2 pilot teams:
- Deployed MLflow, Feast, and KServe on EKS
- 10 experiments tracked, 5 models deployed
- Teams gave 8/10 satisfaction rating
- Identified 5 integration issues (now resolved)
- Validated cost model (within 10% of estimate)

### Expert Review

External architects from Spotify and Airbnb reviewed design:
- Confirmed technology choices align with industry practices
- Suggested using Argo Workflows instead of Kubeflow Pipelines (we'll evaluate)
- Recommended KServe over Seldon (we agree)
- Validated operational complexity is manageable

## Implementation Notes

### Phase 1: Core Infrastructure (Months 1-3)
- EKS cluster with node groups (CPU, GPU)
- MLflow with PostgreSQL backend
- Basic monitoring (Prometheus + Grafana)
- IAM and RBAC setup

### Phase 2: Feature Store & Registry (Months 4-6)
- Feast deployment (online + offline stores)
- MLflow Model Registry with governance extensions
- JupyterHub for notebook access

### Phase 3: Serving & Governance (Months 7-9)
- KServe model serving
- Governance workflows
- Model monitoring

### Phase 4: Productionization (Months 10-12)
- All teams migrated
- SOC2 readiness
- Full documentation and training

## Related Decisions

- [ADR-002: Feature Store Selection](./002-feature-store-selection.md) - Deep-dive on Feast choice
- [ADR-003: Multi-Tenancy Design](./003-multi-tenancy-design.md) - How we isolate teams
- [ADR-005: Model Registry Approach](./005-model-registry-approach.md) - Governance extensions
- [ADR-008: Kubernetes Distribution](./008-kubernetes-distribution.md) - Why EKS vs self-managed

## Review and Update

- **Next Review**: Q1 2025 (6 months post-deployment)
- **Trigger for Revision**: Major technology shifts, significant cost changes, new compliance requirements
- **Owner**: Principal Architect

---

**Approved by**: CTO (Jane Smith), VP Engineering (John Doe), Principal Architect (Your Name)
**Date**: 2024-10-15
