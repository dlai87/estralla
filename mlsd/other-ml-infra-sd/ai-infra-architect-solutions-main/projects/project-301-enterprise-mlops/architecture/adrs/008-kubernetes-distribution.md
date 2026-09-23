# ADR-008: Kubernetes Distribution Selection

**Status**: Accepted
**Date**: 2024-10-19
**Decision Makers**: Principal Architect, VP Infrastructure, SRE Lead
**Stakeholders**: ML Platform Team, SRE Team, Security Team, Finance

## Context

Our enterprise MLOps platform is built on Kubernetes. We need to decide between:
- Managed Kubernetes services (EKS, GKE, AKS)
- Self-managed Kubernetes (kubeadm, kops, Rancher)
- Distribution alternatives (OpenShift, Tanzu)

### Requirements

**Functional**:
- Support 1000+ pods across 20+ teams
- GPU support (NVIDIA A100, H100)
- Multi-AZ for high availability
- Auto-scaling (nodes and pods)
- Network policies and RBAC

**Non-Functional**:
- 99.9% uptime SLA
- Operational burden manageable by 5-person SRE team
- Cost-effective (<$50K/month control plane)
- Security compliant (SOC2, HIPAA)
- Kubernetes 1.28+ with regular updates

### Forces

- **Existing Infrastructure**: AWS-based (S3, RDS, VPC)
- **Team Skills**: Strong Linux/AWS, moderate Kubernetes
- **Budget**: $3M/year total infrastructure (control plane small portion)
- **Compliance**: Need audit trails, encryption, network isolation
- **Risk Tolerance**: Low - this is critical infrastructure
- **Multi-Cloud Future**: May expand to GCP/Azure in Year 2-3

## Decision

We will use **Amazon EKS (Elastic Kubernetes Service)** as our Kubernetes distribution.

### Architecture

```
┌────────────────────────────────────────────────────────────┐
│              Amazon EKS Cluster Architecture                │
├────────────────────────────────────────────────────────────┤
│                                                              │
│  Control Plane (AWS-Managed)                                │
│  ┌────────────────────────────────────────────────────┐   │
│  │  EKS Control Plane (Multi-AZ)                      │   │
│  │  ├─ API Server (HA across 3 AZs)                   │   │
│  │  ├─ etcd (encrypted, auto-backup)                  │   │
│  │  ├─ Controller Manager                             │   │
│  │  ├─ Scheduler                                      │   │
│  │  │                                                  │   │
│  │  AWS handles:                                      │   │
│  │  - Upgrades, patching                              │   │
│  │  - HA and scaling                                  │   │
│  │  - Backup and recovery                             │   │
│  │  - Compliance (SOC2, HIPAA ready)                  │   │
│  └────────────────────────────────────────────────────┘   │
│                           │                                 │
│                           ▼                                 │
│  Data Plane (We Manage)                                    │
│  ┌────────────────────────────────────────────────────┐   │
│  │  Node Groups (Auto-Scaling)                        │   │
│  │                                                      │   │
│  │  ┌──────────────────────────────────────────┐      │   │
│  │  │ CPU Node Group (General Workloads)       │      │   │
│  │  │ - Instance: m6i.2xlarge (8 vCPU, 32GB)  │      │   │
│  │  │ - Min: 5, Max: 50 nodes                 │      │   │
│  │  │ - Spot instances (70% cost savings)     │      │   │
│  │  └──────────────────────────────────────────┘      │   │
│  │                                                      │   │
│  │  ┌──────────────────────────────────────────┐      │   │
│  │  │ GPU Node Group (ML Training)             │      │   │
│  │  │ - Instance: p4d.24xlarge (8x A100 GPUs) │      │   │
│  │  │ - Min: 2, Max: 20 nodes                 │      │   │
│  │  │ - On-demand instances (predictable)     │      │   │
│  │  │ - Taints: nvidia.com/gpu=present:NoSchedule │ │   │
│  │  └──────────────────────────────────────────┘      │   │
│  │                                                      │   │
│  │  ┌──────────────────────────────────────────┐      │   │
│  │  │ System Node Group (Platform Services)    │      │   │
│  │  │ - Instance: m6i.xlarge (4 vCPU, 16GB)   │      │   │
│  │  │ - Min: 3, Max: 6 nodes                  │      │   │
│  │  │ - Dedicated for: MLflow, Prometheus     │      │   │
│  │  │ - Taints: platform=true:NoSchedule      │      │   │
│  │  └──────────────────────────────────────────┘      │   │
│  └────────────────────────────────────────────────────┘   │
│                                                              │
│  AWS Integrations                                           │
│  ┌────────────────────────────────────────────────────┐   │
│  │ - IAM (IRSA for pod-level permissions)             │   │
│  │ - EBS CSI Driver (persistent volumes)              │   │
│  │ - EFS CSI Driver (shared file storage)             │   │
│  │ - VPC CNI (pod networking, security groups)        │   │
│  │ - Load Balancer Controller (ALB/NLB)               │   │
│  │ - Auto-scaling (Cluster Autoscaler / Karpenter)    │   │
│  │ - CloudWatch (logs and metrics)                    │   │
│  │ - AWS Secrets Manager (secrets management)         │   │
│  └────────────────────────────────────────────────────┘   │
│                                                              │
└────────────────────────────────────────────────────────────┘
```

### Key Features Used

**1. Managed Control Plane**
- AWS operates and maintains control plane
- Multi-AZ high availability (99.95% SLA)
- Automatic upgrades (we control timing)
- etcd encrypted and backed up automatically

**2. Node Groups**
- Multiple node groups for different workload types
- Auto-scaling based on demand (Cluster Autoscaler)
- Mix of On-Demand and Spot instances (cost optimization)
- GPU support via NVIDIA device plugin

**3. AWS Integrations**
- IAM Roles for Service Accounts (IRSA) - pod-level IAM
- VPC CNI for pod networking (ENI-based, high performance)
- ALB/NLB integration for ingress
- CloudWatch for logs and metrics
- Secrets Manager for sensitive data

**4. Security**
- Private API endpoint (VPC-only access)
- Pod Security Standards enforced
- Network Policies (Calico)
- Encryption at rest (EBS, EFS via KMS)
- Encryption in transit (TLS everywhere)

**5. Observability**
- CloudWatch Logs (all cluster logs)
- CloudWatch Container Insights (metrics)
- Prometheus for metrics (custom and platform)
- Grafana dashboards

## Alternatives Considered

### Alternative 1: Self-Managed Kubernetes (kubeadm / kops)

**Pros**:
- **Full control**: Complete customization
- **No EKS costs**: Save $73/month per cluster (~$900/year)
- **Flexibility**: Use any cloud or on-premise

**Cons**:
- **High operational burden**: We manage control plane (upgrades, HA, backups)
  - *Estimated*: 2-3 SREs full-time just for cluster management
- **Reliability risk**: Self-operated control plane may have downtime
- **No AWS support**: On our own for issues
- **Complexity**: etcd management, HA setup, disaster recovery
- **Compliance**: Need to implement audit logging, encryption ourselves

**TCO Analysis**:
- Save: $900/year (EKS fees)
- Cost: $600K/year (2 additional SREs @ $300K each)
- **Net**: -$599K/year (much more expensive)

**Decision**: Rejected - operational burden too high, net cost increase

---

### Alternative 2: Google GKE (Google Kubernetes Engine)

**Pros**:
- Excellent Kubernetes support (Google invented K8s)
- Autopilot mode (fully managed nodes)
- Good GPU support
- Strong security features

**Cons**:
- **Different cloud**: We're AWS-first
- **Migration cost**: $500K-1M to migrate existing infrastructure
- **Team skills**: Limited GCP experience
- **Multi-cloud complexity**: Managing AWS + GCP
- **Data egress**: Expensive to move data between clouds

**Decision**: Rejected - cloud mismatch, high migration cost

---

### Alternative 3: Azure AKS (Azure Kubernetes Service)

**Pros**:
- Managed Kubernetes on Azure
- Good enterprise features
- Free control plane

**Cons**:
- **Cloud mismatch**: We're on AWS, not Azure
- **Migration cost**: Similar to GKE ($500K-1M)
- **Team skills**: No Azure experience
- **Limited GPU**: Fewer GPU options than AWS

**Decision**: Rejected - same reasoning as GKE

---

### Alternative 4: Red Hat OpenShift

**Pros**:
- Enterprise support from Red Hat
- Additional security and operational features
- Can run on any cloud or on-premise
- Strong governance features

**Cons**:
- **Expensive**: $50K-100K/year licensing per cluster
- **Complexity**: Additional abstraction layer over Kubernetes
- **Team unfamiliar**: Would need training
- **Overkill**: Many features we don't need
- **Vendor lock-in**: OpenShift-specific APIs

**TCO**: $50-100K/year licensing + operational costs

**Decision**: Rejected - too expensive, unnecessary complexity

---

### Alternative 5: Rancher / k3s

**Pros**:
- Open source (free)
- Simpler than full Kubernetes
- Good multi-cluster management UI
- Lightweight

**Cons**:
- **Still self-managed**: We operate control plane
- **Smaller community**: Less adoption than EKS
- **k3s limitations**: May not support all features we need
- **Risk**: Rancher company stability (SUSE acquisition)

**Decision**: Rejected - self-managed, smaller ecosystem

---

### Alternative 6: VMware Tanzu

**Pros**:
- Enterprise support from VMware
- Multi-cloud support
- Good for VMware shops

**Cons**:
- **Expensive**: $150K+/year per cluster
- **VMware ecosystem**: We're not a VMware shop
- **Overkill**: Too many features for our needs
- **Limited AWS integration**: Not as tight as EKS

**Decision**: Rejected - expensive, poor fit

## Consequences

### Positive

✅ **Reduced Operational Burden**: AWS manages control plane
- **Savings**: 2 SREs can focus on platform features instead of cluster management
- **Value**: $600K/year in productivity

✅ **High Availability**: 99.95% SLA from AWS
- **Multi-AZ**: Control plane across 3 availability zones
- **Auto-healing**: AWS automatically replaces unhealthy control plane components

✅ **AWS Integration**: Native integration with AWS services
- **IRSA**: Pod-level IAM permissions (no shared credentials)
- **VPC CNI**: High-performance networking
- **EBS/EFS**: Native persistent storage
- **CloudWatch**: Integrated logging and metrics

✅ **Security & Compliance**: AWS handles many compliance requirements
- **Encryption**: etcd encrypted by default
- **Audit**: Control plane logs to CloudWatch
- **Updates**: Patching managed by AWS
- **Compliance**: SOC2, HIPAA, PCI-DSS certified

✅ **Cost-Effective**: $73/month per cluster vs $600K+/year for self-managed
- **3-Year TCO**: $2,628 (EKS fees) vs $1.8M+ (self-managed SRE costs)

✅ **Proven at Scale**: Used by many large enterprises
- **Examples**: Lyft, Intuit, Verizon, thousands more

### Negative

⚠️ **EKS Control Plane Cost**: $73/month per cluster ($876/year)
- *Impact*: Minimal (<1% of infrastructure budget)
- *Trade-off*: Worth it for operational simplicity

⚠️ **AWS Lock-In**: Tied to AWS ecosystem
- *Mitigation*: Kubernetes API is standard, workloads are portable
- *Multi-cloud plan*: Terraform abstracts infrastructure, can deploy to GKE/AKS
- *Risk*: Medium (acceptable given AWS alignment)

⚠️ **Less Control**: AWS controls upgrade timing and features
- *Mitigation*: Can delay upgrades in maintenance window
- *Impact*: Low - AWS EKS release schedule aligns with upstream K8s

⚠️ **VPC CNI Limitations**: Pod networking uses ENIs (limited IPs per node)
- *Mitigation*: Use IP prefix delegation (increases IPs 16x)
- *Alternative*: Can switch to Calico CNI if needed

⚠️ **Add-on Management**: Some add-ons need manual installation
- *Examples*: Cluster Autoscaler, Metrics Server, EBS CSI Driver
- *Mitigation*: Use Terraform modules, documented procedures

### Risks and Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| EKS service outage | Low | High | Multi-AZ setup, AWS SLA 99.95%, disaster recovery plan |
| Upgrade issues | Medium | Medium | Test upgrades in staging, phased rollout, rollback plan |
| AWS lock-in | High | Medium | Terraform for infra, avoid AWS-specific K8s APIs, multi-cloud roadmap |
| Cost increase | Medium | Low | Monitor spend, use Spot instances, right-size nodes |
| IP exhaustion (VPC CNI) | Low | Medium | IP prefix delegation, /19 VPC CIDR, monitor IP usage |

## Implementation Details

### EKS Configuration

**Cluster Settings**:
```yaml
cluster_name: ml-platform-prod
region: us-west-2
version: 1.28

# Control Plane
endpoint_private_access: true   # VPC-only access
endpoint_public_access: false   # No public access
enabled_cluster_log_types:
  - api
  - audit
  - authenticator
  - controllerManager
  - scheduler

# Encryption
encryption_config:
  provider: aws-kms
  resources: ["secrets"]

# Add-ons
addons:
  - name: vpc-cni
    version: v1.15.0
  - name: kube-proxy
    version: v1.28.1
  - name: coredns
    version: v1.10.1
  - name: aws-ebs-csi-driver
    version: v1.25.0
```

**Node Groups**:
1. **System** (m6i.xlarge): Platform services (MLflow, Prometheus)
2. **Compute** (m6i.2xlarge): General ML workloads
3. **GPU** (p4d.24xlarge): Training jobs
4. **Spot** (mixed): Non-critical batch jobs (70% cost savings)

### Cost Optimization

**Strategies**:
1. **Spot Instances**: 70% savings for fault-tolerant workloads
2. **Right-Sizing**: Monitor usage, adjust instance types
3. **Cluster Autoscaler**: Scale nodes down when idle
4. **Reserved Instances**: 1-year RI for base capacity (40% savings)
5. **Savings Plans**: Flexible compute savings plans

**Estimated Monthly Cost** (20 teams, 1000 pods):
- EKS Control Plane: $73
- Nodes (CPU): $8,000
- Nodes (GPU): $15,000
- Storage (EBS): $1,500
- Data Transfer: $500
- **Total**: ~$25K/month ($300K/year)

### Upgrade Strategy

**Approach**: Phased rollout with blue-green clusters

1. **Testing** (Week 1): Upgrade staging cluster, run integration tests
2. **Validation** (Week 2): Deploy canary workloads, monitor for issues
3. **Production** (Week 3-4): Upgrade production, one node group at a time
4. **Rollback Plan**: Keep old cluster available for 2 weeks

**Frequency**: Every 6 months (align with Kubernetes support window)

### Disaster Recovery

**Backup Strategy**:
- **etcd**: Automatic backups by AWS (encrypted)
- **Manifests**: GitOps (all configs in Git)
- **Data**: PV snapshots (daily), S3 lifecycle policies

**Recovery**:
- **RPO**: <1 hour (data loss acceptable)
- **RTO**: <4 hours (recovery time target)
- **DR Cluster**: Passive cluster in us-east-1 (cross-region)

## Success Metrics

| Metric | Target |
|--------|--------|
| **Control Plane Uptime** | >99.9% |
| **Cluster Upgrade Success Rate** | >99% |
| **Mean Time to Recovery (MTTR)** | <1 hour |
| **Node Utilization (CPU)** | 60-80% |
| **GPU Utilization** | >70% |
| **Team Satisfaction with Platform** | >8/10 |

## Related Decisions

- [ADR-001: Platform Technology Stack](./001-platform-technology-stack.md) - Overall K8s choice
- [ADR-003: Multi-Tenancy Design](./003-multi-tenancy-design.md) - Namespace isolation on EKS
- [ADR-009: Cost Management and FinOps](./009-cost-management-finops.md) - EKS cost optimization

## Review and Update

- **Next Review**: Q2 2025 (after 6 months in production)
- **Trigger for Revision**:
  - EKS service quality issues (uptime <99%)
  - Significant cost increases (>20%)
  - Multi-cloud expansion decision
  - Team requests different platform
- **Owner**: Principal Architect + SRE Lead

## References

- AWS EKS Best Practices: https://aws.github.io/aws-eks-best-practices/
- EKS Pricing: https://aws.amazon.com/eks/pricing/
- Internal: `docs/kubernetes-platform-comparison.pdf`

---

**Approved by**: VP Infrastructure (Sarah Lee), Principal Architect (Your Name), SRE Lead (Mike Chen)
**Date**: 2024-10-19
