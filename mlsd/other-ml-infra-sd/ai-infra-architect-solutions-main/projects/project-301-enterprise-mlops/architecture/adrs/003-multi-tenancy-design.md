# ADR-003: Multi-Tenancy Design for ML Platform

**Status**: Accepted
**Date**: 2024-10-17
**Decision Makers**: Principal Architect, VP Engineering, Security Architect
**Stakeholders**: ML Platform Team, Data Science Teams, Security Team, Finance Team

## Context

Our enterprise MLOps platform needs to support 20+ teams (eventually 50+ teams) with:
- Resource isolation (compute, storage)
- Cost allocation and chargeback
- Access control and security
- Performance isolation (prevent noisy neighbors)
- Governance and compliance per team

### Current State

- Each team uses separate AWS accounts or ad-hoc resources
- No standardization or centralized management
- Difficult to share resources or enforce policies
- Complex cost attribution
- Security inconsistencies across teams

### Forces

- **Number of Teams**: 20 teams today, 50+ within 2 years
- **Team Sizes**: 5-50 data scientists per team
- **Security Requirements**: Different teams have different data sensitivity (public, confidential, HIPAA)
- **Cost Control**: Need chargeback to teams, prevent overspending
- **Resource Sharing**: Want teams to share infrastructure (cost efficiency) but with isolation
- **Operational Burden**: 12-person platform team can't manage 50 separate clusters
- **Compliance**: Some teams need SOC2, HIPAA, PCI-DSS compliance

### Tenancy Models Evaluated

1. **Cluster-per-Team**: Each team gets dedicated Kubernetes cluster
2. **Namespace-per-Team**: Teams share cluster(s), isolated by namespace
3. **Virtual Clusters**: vcluster or similar, namespaces with cluster-level APIs
4. **Hybrid**: Critical teams get dedicated clusters, others share

## Decision

We will implement **Namespace-based multi-tenancy** with **optional dedicated clusters** for highly sensitive workloads.

### Primary Model: Namespace-per-Team

**Architecture**:
```
┌─────────────────────────────────────────────────────────────┐
│              Shared EKS Cluster (Multi-Tenant)               │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Namespace: team-data-science                        │   │
│  │ ├─ ResourceQuota: 100 CPU, 200GB RAM, 4 GPU        │   │
│  │ ├─ LimitRange: max pod 8 CPU, 16GB RAM             │   │
│  │ ├─ NetworkPolicy: deny-all except allowed          │   │
│  │ ├─ PodSecurityPolicy: restricted                   │   │
│  │ └─ RoleBindings: team-data-science group           │   │
│  │    Workloads: JupyterHub, MLflow, training jobs    │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Namespace: team-recommendations                     │   │
│  │ ├─ ResourceQuota: 200 CPU, 400GB RAM, 8 GPU        │   │
│  │ ├─ LimitRange: max pod 16 CPU, 32GB RAM            │   │
│  │ ├─ NetworkPolicy: deny-all except allowed          │   │
│  │ ├─ PodSecurityPolicy: restricted                   │   │
│  │ └─ RoleBindings: team-recommendations group        │   │
│  │    Workloads: KServe serving, training jobs        │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Namespace: team-fraud-detection (HIPAA)            │   │
│  │ ├─ ResourceQuota: 150 CPU, 300GB RAM, 6 GPU        │   │
│  │ ├─ LimitRange: max pod 16 CPU, 32GB RAM            │   │
│  │ ├─ NetworkPolicy: strict isolation                 │   │
│  │ ├─ PodSecurityPolicy: baseline-strict              │   │
│  │ └─ RoleBindings: team-fraud-detection group        │   │
│  │    Workloads: Secure notebooks, encrypted storage  │   │
│  │    Special: Node taints for HIPAA-compliant nodes  │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Namespace: platform-shared                          │   │
│  │ - MLflow tracking server (shared)                   │   │
│  │ - Feast registry (shared)                           │   │
│  │ - Prometheus (monitoring all teams)                 │   │
│  │ - ArgoCD (platform deployments)                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                               │
└─────────────────────────────────────────────────────────────┘

Optional: Dedicated Clusters for Ultra-Sensitive Workloads
┌──────────────────────────────────────┐
│  Dedicated EKS Cluster               │
│  (team-pci-compliance)               │
│  - Full cluster isolation            │
│  - Dedicated node pools              │
│  - Separate VPC                      │
│  - PCI-DSS controls                  │
└──────────────────────────────────────┘
```

### Isolation Mechanisms

1. **Resource Isolation** (ResourceQuota + LimitRange)
   - Per-namespace CPU, memory, GPU quotas
   - Prevent resource starvation
   - Fair allocation based on team size

2. **Network Isolation** (NetworkPolicy)
   - Default deny all traffic
   - Explicit allow rules for necessary communication
   - Teams cannot access each other's services

3. **Access Control** (RBAC)
   - Namespace-scoped Roles and RoleBindings
   - Teams have full control within their namespace
   - Platform team has cluster-admin

4. **Security Policies** (PodSecurityPolicy/Pod Security Standards)
   - Prevent privileged containers
   - Enforce security best practices
   - ReadOnlyRootFilesystem where possible

5. **Storage Isolation**
   - Namespace-scoped PersistentVolumeClaims
   - S3 bucket per team with IAM policies
   - Encryption at rest (KMS keys per team)

6. **Compute Isolation**
   - Node taints and tolerations for special workloads (HIPAA, PCI)
   - GPU isolation via NVIDIA MPS or time-slicing
   - Separate node pools for sensitive workloads

### Cost Allocation

**Chargeback Model**:
- **Compute**: CPU/memory/GPU usage tracked via Kubecost
- **Storage**: S3 buckets tagged with team ID
- **Network**: Data transfer costs attributed to team
- **Shared Services**: Allocated based on usage (e.g., MLflow experiments)

**Monthly Reports**:
- Per-team cost breakdown
- Budget alerts at 80%, 90%, 100%
- Recommendations for optimization

## Alternatives Considered

### Alternative 1: Cluster-per-Team

**Pros**:
- **Maximum isolation**: No shared infrastructure
- **No noisy neighbor**: Performance predictability
- **Easier compliance**: Dedicated clusters for HIPAA, PCI, etc.
- **Team autonomy**: Each team controls their cluster

**Cons**:
- **High operational burden**: Managing 20-50 clusters is complex
- **Cost inefficient**: Under-utilized clusters (avg 20-30% utilization)
- **Shared services complexity**: MLflow, Feast need to span clusters
- **Slow onboarding**: Creating cluster takes hours

**Cost Analysis**:
- Per-cluster overhead: $500/month (control plane, monitoring, etc.)
- 20 clusters: $10K/month = $120K/year overhead
- Underutilization: 50% resources idle → 2x infrastructure cost

**Decision**: Rejected due to operational complexity and cost

---

### Alternative 2: Virtual Clusters (vcluster)

**Pros**:
- Feels like dedicated cluster to teams
- Better isolation than namespaces
- Cluster-level APIs available
- Moderate operational burden

**Cons**:
- **Additional abstraction**: More complexity
- **Immature technology**: vcluster still evolving
- **Resource overhead**: Each vcluster has API server
- **Limited GPU support**: GPU isolation challenging

**Decision**: Rejected as too complex for our needs

---

### Alternative 3: No Multi-Tenancy (Single Namespace)

**Pros**:
- Simplest approach
- No isolation overhead

**Cons**:
- **Security risk**: Teams can see/modify each other's resources
- **No cost attribution**: Can't track spending per team
- **Governance impossible**: Can't enforce policies per team
- **Compliance fail**: Can't meet regulatory requirements

**Decision**: Rejected immediately as non-viable

---

### Alternative 4: AWS Accounts per Team

**Pros**:
- Maximum isolation (billing, security, compliance)
- Native AWS cost tracking
- Team autonomy

**Cons**:
- **Extreme fragmentation**: 50 AWS accounts hard to manage
- **No resource sharing**: Can't share infrastructure
- **Complicated networking**: VPC peering, Transit Gateway needed
- **Inconsistent platform**: Each team may diverge from standard

**Decision**: Rejected due to fragmentation

## Consequences

### Positive

✅ **Cost Efficient**: 70-80% cluster utilization vs 20-30% with dedicated clusters
- **Savings**: $1-2M/year in infrastructure costs

✅ **Operationally Manageable**: 2-3 shared clusters vs 50 dedicated clusters
- **Effort**: 2 SREs can manage shared clusters

✅ **Fast Onboarding**: New team namespace created in minutes
- **Process**: Automated via Terraform

✅ **Fair Resource Allocation**: Quotas prevent monopolization
- **Enforcement**: Automatic via Kubernetes

✅ **Security**: NetworkPolicy and RBAC provide adequate isolation
- **Validation**: Passed security review

✅ **Flexibility**: Can create dedicated clusters for special cases
- **Hybrid approach**: Best of both worlds

### Negative

⚠️ **Noisy Neighbor Risk**: One team's workload can affect others
- *Mitigation*: ResourceQuotas, LimitRanges, monitoring, node taints
- *Fallback*: Move noisy team to dedicated cluster

⚠️ **Security Concerns**: Shared control plane, shared nodes
- *Mitigation*: Strict RBAC, NetworkPolicy, PodSecurityPolicy, node isolation
- *Risk Level*: Medium (acceptable for most teams)
- *Exception*: Dedicated clusters for PCI, ultra-sensitive workloads

⚠️ **Kubernetes Cluster Limits**: Namespaces per cluster limited
- *Limit*: ~100 namespaces per cluster (practical limit)
- *Mitigation*: Create additional clusters as we grow (Year 2-3)

⚠️ **Complex Troubleshooting**: Multi-tenant issues harder to debug
- *Mitigation*: Strong observability (Prometheus, Grafana, logs per namespace)

### Risks and Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Noisy neighbor impacts team | Medium | Medium | Resource quotas, monitoring, alerts, dedicated nodes for critical workloads |
| Security breach across namespaces | Low | High | NetworkPolicy, strict RBAC, regular security audits, penetration testing |
| Cluster capacity limits reached | Medium | Low | Add node pools, create additional clusters, auto-scaling |
| Compliance audit failure | Low | High | Dedicated clusters for regulated workloads, documented controls |
| Cost allocation inaccurate | Medium | Low | Kubecost validation, S3 tagging, monthly reviews |

## Implementation Details

### Namespace Template

Each team namespace includes:
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: team-<team-name>
  labels:
    team: <team-name>
    cost-center: <cost-center-id>
    compliance-level: standard|hipaa|pci

---
# ResourceQuota
apiVersion: v1
kind: ResourceQuota
metadata:
  name: team-quota
  namespace: team-<team-name>
spec:
  hard:
    requests.cpu: "100"
    requests.memory: "200Gi"
    requests.nvidia.com/gpu: "4"
    pods: "100"
    services: "20"
    persistentvolumeclaims: "50"

---
# LimitRange
apiVersion: v1
kind: LimitRange
metadata:
  name: team-limits
  namespace: team-<team-name>
spec:
  limits:
  - max:
      cpu: "16"
      memory: "32Gi"
    type: Pod
  - max:
      cpu: "8"
      memory: "16Gi"
    default:
      cpu: "1"
      memory: "2Gi"
    type: Container

---
# NetworkPolicy (default deny)
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny
  namespace: team-<team-name>
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: platform-shared  # Allow access to MLflow, Feast
  - to:
    - podSelector: {}  # Allow egress within namespace
```

### Team Onboarding Process

1. **Request**: Team submits form (size, workload, compliance needs)
2. **Approval**: Platform team reviews, approves
3. **Provisioning** (automated):
   - Create namespace with quotas
   - Create S3 bucket with IAM policy
   - Create RBAC roles and bindings
   - Setup monitoring and alerts
   - Create Grafana dashboard
4. **Training**: Onboarding session (2 hours)
5. **Launch**: Team has access within 1 hour

### Quota Calculation

**Base Quota** (adjusted by team size):
- Small team (5-10 people): 50 CPU, 100GB RAM, 2 GPU
- Medium team (10-30 people): 100 CPU, 200GB RAM, 4 GPU
- Large team (30+ people): 200 CPU, 400GB RAM, 8 GPU

**Adjustment Factors**:
- Workload type (training vs serving)
- Historical usage patterns
- Cost center budget

**Review**: Quarterly quota reviews, adjustments as needed

### Special Cases

**HIPAA Workloads**:
- Dedicated node pool with HIPAA-compliant AMI
- Node taints: `compliance=hipaa:NoSchedule`
- Encrypted EBS volumes (KMS keys)
- Audit logging enabled
- Network isolation (no internet egress)

**PCI Workloads**:
- Dedicated cluster (full isolation)
- Separate VPC with hardened security groups
- PCI-DSS controls implemented
- Regular PCI audits

## Monitoring and Observability

**Per-Namespace Metrics**:
- CPU, memory, GPU utilization
- Pod count, restarts
- Network traffic
- Storage usage
- Cost accumulation

**Alerts**:
- Quota utilization >80%
- Noisy neighbor detection (CPU throttling)
- Security policy violations
- Budget overruns

**Dashboards**:
- Team-specific Grafana dashboard
- Platform-wide capacity dashboard
- Cost explorer per team

## Success Metrics

| Metric | Target |
|--------|--------|
| **Team Onboarding Time** | <1 hour (automated) |
| **Cluster Utilization** | 70-80% |
| **Cost Attribution Accuracy** | >95% |
| **Security Violations** | 0 per month |
| **Noisy Neighbor Incidents** | <1 per quarter |
| **Teams per Cluster** | 20-30 |

## Related Decisions

- [ADR-001: Platform Technology Stack](./001-platform-technology-stack.md) - Kubernetes choice
- [ADR-007: Security and Compliance Architecture](./007-security-compliance-architecture.md) - Security controls
- [ADR-008: Kubernetes Distribution Selection](./008-kubernetes-distribution.md) - EKS setup
- [ADR-009: Cost Management and FinOps](./009-cost-management-finops.md) - Chargeback implementation

## Review and Update

- **Next Review**: Q3 2025 (after 20 teams onboarded)
- **Trigger for Revision**:
  - Security incident related to multi-tenancy
  - Noisy neighbor issues >2 per month
  - Cluster capacity limits reached (>80 namespaces)
- **Owner**: Principal Architect + Security Architect

## References

- Kubernetes Multi-Tenancy Working Group: https://github.com/kubernetes-sigs/multi-tenancy
- Best Practices: https://kubernetes.io/docs/concepts/security/multi-tenancy/
- Kubecost Multi-Tenant Cost Allocation: https://www.kubecost.com/

---

**Approved by**: VP Engineering (John Doe), Principal Architect (Your Name), Security Architect (Sarah Wilson)
**Date**: 2024-10-17
