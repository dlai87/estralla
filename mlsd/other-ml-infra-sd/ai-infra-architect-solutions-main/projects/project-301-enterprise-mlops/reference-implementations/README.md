# Reference Implementations

## Overview

This directory contains production-ready reference implementations for the Enterprise MLOps Platform. These implementations demonstrate the architectural decisions documented in the ADRs and provide starting points for deployment.

## Contents

### 1. Terraform Infrastructure (`terraform/`)
Infrastructure as Code (IaC) for AWS resources:
- VPC and networking
- EKS cluster
- RDS databases
- S3 buckets and data lake
- Security groups and IAM roles
- KMS encryption keys

### 2. Kubernetes Manifests (`kubernetes/`)
Kubernetes configurations for platform components:
- MLflow (experiment tracking, model registry)
- Feast (feature store)
- KServe (model serving)
- Prometheus & Grafana (monitoring)
- NGINX Ingress Controller

### 3. Platform API (`platform-api/`)
Python FastAPI examples:
- Model deployment API
- Feature retrieval API
- Monitoring API
- Administrative API

### 4. Monitoring Configurations (`monitoring/`)
Observability setup:
- Prometheus configurations
- Grafana dashboards
- Alert rules
- Log aggregation

### 5. CI/CD Pipelines (`cicd/`)
GitHub Actions workflows:
- Infrastructure deployment
- Application deployment
- Model deployment
- Testing and validation

## Prerequisites

### Required Tools
- Terraform >= 1.5.0
- kubectl >= 1.27.0
- Helm >= 3.12.0
- AWS CLI >= 2.13.0
- Python >= 3.11
- Docker >= 24.0.0

### AWS Credentials
```bash
export AWS_PROFILE=mlops-platform
export AWS_REGION=us-east-1
```

### Kubernetes Access
```bash
aws eks update-kubeconfig --name mlops-platform --region us-east-1
```

## Quick Start

### 1. Deploy Infrastructure with Terraform

```bash
cd terraform/environments/dev

# Initialize Terraform
terraform init

# Review plan
terraform plan -out=tfplan

# Apply infrastructure
terraform apply tfplan
```

### 2. Deploy Kubernetes Applications

```bash
cd kubernetes

# Deploy in order
kubectl apply -f namespaces/
kubectl apply -f storage/
kubectl apply -f mlflow/
kubectl apply -f feast/
kubectl apply -f kserve/
kubectl apply -f monitoring/
```

### 3. Deploy Platform API

```bash
cd platform-api

# Build and push Docker image
docker build -t mlops-api:latest .
docker tag mlops-api:latest 123456789012.dkr.ecr.us-east-1.amazonaws.com/mlops-api:latest
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/mlops-api:latest

# Deploy to Kubernetes
kubectl apply -f k8s/deployment.yaml
```

## Directory Structure

```
reference-implementations/
├── README.md (this file)
├── terraform/
│   ├── modules/
│   │   ├── vpc/
│   │   ├── eks/
│   │   ├── rds/
│   │   ├── s3/
│   │   ├── security/
│   │   └── monitoring/
│   └── environments/
│       ├── dev/
│       ├── staging/
│       └── prod/
├── kubernetes/
│   ├── namespaces/
│   ├── storage/
│   ├── mlflow/
│   ├── feast/
│   ├── kserve/
│   ├── monitoring/
│   └── ingress/
├── platform-api/
│   ├── src/
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
├── monitoring/
│   ├── prometheus/
│   ├── grafana/
│   └── alerts/
└── cicd/
    ├── terraform-deploy.yml
    ├── k8s-deploy.yml
    └── model-deploy.yml
```

## Architecture Alignment

These implementations directly support the architectural decisions documented in:

- **ADR-001**: Technology Stack → AWS, Kubernetes, Terraform
- **ADR-002**: Feature Store → Feast implementation
- **ADR-003**: Multi-tenancy → Namespace-based isolation
- **ADR-004**: Data Platform → S3 + Redshift + Redis
- **ADR-005**: Model Registry → MLflow
- **ADR-006**: Real-time Pipelines → Flink on Kubernetes
- **ADR-007**: Security → Encryption, network policies, RBAC
- **ADR-008**: Kubernetes → EKS implementation
- **ADR-009**: Cost Management → Spot instances, auto-scaling
- **ADR-010**: Governance → Automated controls

## Cost Estimates

Based on ADR-009 (Cost Management & FinOps):

**Development Environment**:
- EKS Control Plane: $73/month
- Worker Nodes (3 x m5.xlarge spot): ~$180/month
- RDS (db.t3.medium): $60/month
- S3 Storage (1 TB): $23/month
- **Total: ~$336/month**

**Production Environment** (per ADR-009):
- Year 1: $10.2M
- Year 2: $11.8M
- Year 3: $13.0M
- **3-Year Total: $35M**

See `/business/business-case.md` for detailed cost breakdown.

## Security Considerations

All implementations include:

✅ **Encryption at Rest**: AES-256 for all storage (S3, EBS, RDS)
✅ **Encryption in Transit**: TLS 1.3 for all communications
✅ **Network Segmentation**: VPC with public/private subnets
✅ **RBAC**: Kubernetes role-based access control
✅ **Secrets Management**: AWS Secrets Manager integration
✅ **Audit Logging**: CloudTrail, CloudWatch Logs, K8s audit logs
✅ **HIPAA Compliance**: Dedicated infrastructure for PHI

See ADR-007 (Security & Compliance Architecture) for details.

## Monitoring and Observability

**Metrics** (Prometheus):
- Infrastructure metrics (CPU, memory, disk)
- Application metrics (requests, latency, errors)
- ML metrics (predictions/sec, model latency, drift)
- Cost metrics (resource utilization)

**Dashboards** (Grafana):
- Platform Overview
- Model Performance
- Cost Analysis
- Security & Compliance

**Alerts**:
- Critical: PagerDuty escalation
- Warning: Slack notifications
- Info: Dashboard only

See `/monitoring/README.md` for details.

## Testing

All implementations include:

- **Unit Tests**: Component-level testing
- **Integration Tests**: End-to-end workflows
- **Load Tests**: Performance validation
- **Security Tests**: Vulnerability scanning
- **Compliance Tests**: Policy validation

```bash
# Run all tests
cd terraform && terraform test
cd ../kubernetes && kubectl kuttl test
cd ../platform-api && pytest tests/
```

## Deployment Environments

### Development
- Single-region (us-east-1)
- Spot instances for cost savings
- Reduced redundancy
- Auto-shutdown outside business hours

### Staging
- Single-region (us-east-1)
- Mix of spot/on-demand instances
- Production-like configuration
- Used for integration testing

### Production
- Multi-region (us-east-1 primary, us-west-2 secondary)
- On-demand instances for critical workloads
- High availability (multi-AZ)
- Auto-scaling enabled
- 24/7 operation

## Customization Guide

### Environment-Specific Configuration

Edit `terraform/environments/{env}/terraform.tfvars`:

```hcl
# Environment identifier
environment = "dev"  # dev, staging, prod

# Networking
vpc_cidr = "10.0.0.0/16"

# EKS Configuration
eks_version = "1.27"
node_instance_types = ["m5.xlarge", "m5.2xlarge"]
node_desired_capacity = 3
node_max_capacity = 10

# RDS Configuration
rds_instance_class = "db.r5.xlarge"
rds_multi_az = true

# Cost Optimization
enable_spot_instances = true
spot_max_price = "0.30"

# Tags
tags = {
  Environment = "dev"
  ManagedBy   = "terraform"
  Project     = "mlops-platform"
  CostCenter  = "engineering"
}
```

### Team-Specific Namespaces

Edit `kubernetes/namespaces/team-namespace.yaml`:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: team-data-science
  labels:
    team: data-science
    cost-center: "engineering"
---
apiVersion: v1
kind: ResourceQuota
metadata:
  name: team-quota
  namespace: team-data-science
spec:
  hard:
    requests.cpu: "100"
    requests.memory: "200Gi"
    requests.nvidia.com/gpu: "4"
    persistentvolumeclaims: "10"
```

## Maintenance

### Regular Updates

**Weekly**:
- Review Prometheus alerts
- Check cost dashboards
- Validate backup integrity

**Monthly**:
- Update Kubernetes patch version
- Review and rotate credentials
- Audit access logs
- Optimize resource utilization

**Quarterly**:
- Update Terraform modules
- Review security policies
- Conduct disaster recovery test
- Update documentation

### Backup and Disaster Recovery

**Automated Backups**:
- RDS: Daily snapshots, 30-day retention
- S3: Versioning enabled, lifecycle policies
- EKS: etcd backups via Velero

**Disaster Recovery**:
- RPO (Recovery Point Objective): 1 hour
- RTO (Recovery Time Objective): 4 hours

See ADR-007 and `/docs/disaster-recovery.md` for details.

## Support and Documentation

### Internal Resources
- **Architecture Docs**: `/ARCHITECTURE.md`
- **ADRs**: `/architecture/adrs/*.md`
- **Runbooks**: `/docs/runbooks/*.md`
- **Governance**: `/governance/*.md`

### External Documentation
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [MLflow Documentation](https://mlflow.org/docs/latest/)
- [Feast Documentation](https://docs.feast.dev/)
- [KServe Documentation](https://kserve.github.io/website/)

### Getting Help
- **Slack**: #mlops-platform
- **Email**: mlops-support@company.com
- **On-call**: PagerDuty (for production issues)

## Contributing

### Making Changes

1. Create a feature branch
2. Make changes with clear commit messages
3. Test thoroughly (unit + integration tests)
4. Submit pull request with description
5. Address code review feedback
6. Merge after approval

### Code Standards

- **Terraform**: Follow [Terraform Style Guide](https://www.terraform.io/docs/language/syntax/style.html)
- **Kubernetes**: Use declarative YAML, include resource limits
- **Python**: Follow PEP 8, type hints required
- **Documentation**: Update README files with changes

### Testing Requirements

- All Terraform modules must have `terraform test` coverage
- Kubernetes manifests must pass `kubeval` validation
- Python code must have 80%+ test coverage
- Security scans must pass (no HIGH/CRITICAL issues)

## License

Internal use only. Proprietary and confidential.

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-10-17 | AI Infrastructure Team | Initial reference implementations |

## Related Documents

- [ARCHITECTURE.md](../ARCHITECTURE.md) - System architecture
- [ADRs](../architecture/adrs/) - Architecture decision records
- [Business Case](../business/business-case.md) - Financial analysis
- [Governance](../governance/) - Governance frameworks
- [Deployment Guide](../runbooks/deployment-guide.md) - Step-by-step deployment

---

**Last Updated**: 2025-10-17
**Maintained By**: AI Infrastructure Architecture Team
**Status**: Active, Production-Ready
