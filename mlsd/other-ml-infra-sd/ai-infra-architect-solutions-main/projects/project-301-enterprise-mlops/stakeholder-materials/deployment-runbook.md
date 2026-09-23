# Enterprise MLOps Platform - Deployment Runbook

**Version**: 1.0
**Last Updated**: 2024-01-15
**Owner**: Platform Engineering Team
**Audience**: DevOps Engineers, SREs, Platform Engineers

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Pre-Deployment Checklist](#pre-deployment-checklist)
4. [Phase 1: Infrastructure Deployment](#phase-1-infrastructure-deployment)
5. [Phase 2: Platform Services Deployment](#phase-2-platform-services-deployment)
6. [Phase 3: Application Layer Deployment](#phase-3-application-layer-deployment)
7. [Phase 4: Post-Deployment Validation](#phase-4-post-deployment-validation)
8. [Rollback Procedures](#rollback-procedures)
9. [Common Issues](#common-issues)
10. [Appendix](#appendix)

---

## Overview

This runbook provides step-by-step instructions for deploying the Enterprise MLOps Platform from scratch or upgrading existing deployments.

### Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Deployment Phases                         │
├─────────────────────────────────────────────────────────────────┤
│ Phase 1: Infrastructure (60-90 minutes)                         │
│   → VPC, Networking, EKS Cluster, RDS, S3, IAM                 │
├─────────────────────────────────────────────────────────────────┤
│ Phase 2: Platform Services (45-60 minutes)                      │
│   → MLflow, Feast, KServe, Monitoring Stack                    │
├─────────────────────────────────────────────────────────────────┤
│ Phase 3: Application Layer (30-45 minutes)                      │
│   → Platform API, Web UI, Model Registry                       │
├─────────────────────────────────────────────────────────────────┤
│ Phase 4: Validation (30 minutes)                                │
│   → Integration tests, Smoke tests, Performance tests          │
└─────────────────────────────────────────────────────────────────┘
Total Time: 3-4 hours (automated), 6-8 hours (manual)
```

### Deployment Modes

| Mode | Use Case | Automation | Duration |
|------|----------|------------|----------|
| **Fresh Install** | New environment setup | Terraform + Helm | 3-4 hours |
| **Upgrade** | Version updates | Rolling update | 1-2 hours |
| **Disaster Recovery** | Restore from backup | Terraform + Restore | 2-3 hours |
| **Blue-Green** | Zero-downtime migration | Dual environment | 4-6 hours |

---

## Prerequisites

### Required Access

- [ ] AWS Account with Administrator access (or specific IAM permissions)
- [ ] GitHub/GitLab access for infrastructure repository
- [ ] Terraform Cloud/Backend access (for state management)
- [ ] Container registry access (ECR, DockerHub)
- [ ] DNS management access (Route53 or equivalent)
- [ ] SSL certificate management access (ACM)

### Required Tools

Install and verify the following tools:

```bash
# AWS CLI v2.x
aws --version
# Expected: aws-cli/2.x.x

# Terraform v1.5+
terraform --version
# Expected: Terraform v1.5.x

# kubectl v1.27+
kubectl version --client
# Expected: v1.27.x

# Helm v3.12+
helm version
# Expected: v3.12.x

# eksctl (optional, for EKS management)
eksctl version
# Expected: 0.147.0 or later

# jq (for JSON parsing)
jq --version
# Expected: jq-1.6
```

**Installation Script** (if tools are missing):

```bash
#!/bin/bash
# install-deployment-tools.sh

# AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Terraform
wget https://releases.hashicorp.com/terraform/1.5.7/terraform_1.5.7_linux_amd64.zip
unzip terraform_1.5.7_linux_amd64.zip
sudo mv terraform /usr/local/bin/

# kubectl
curl -LO "https://dl.k8s.io/release/v1.27.0/bin/linux/amd64/kubectl"
chmod +x kubectl
sudo mv kubectl /usr/local/bin/

# Helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# eksctl
curl --silent --location "https://github.com/weksctl/eksctl/releases/latest/download/eksctl_$(uname -s)_amd64.tar.gz" | tar xz -C /tmp
sudo mv /tmp/eksctl /usr/local/bin

# jq
sudo apt-get update && sudo apt-get install -y jq
```

### Environment Variables

Create a `.env` file with required configuration:

```bash
# AWS Configuration
export AWS_REGION="us-east-1"
export AWS_ACCOUNT_ID="123456789012"

# Environment
export ENVIRONMENT="production"  # dev, staging, production
export PROJECT_NAME="mlops-platform"

# Terraform Backend
export TF_BACKEND_BUCKET="mlops-terraform-state-${AWS_ACCOUNT_ID}"
export TF_BACKEND_KEY="${ENVIRONMENT}/terraform.tfstate"
export TF_BACKEND_REGION="${AWS_REGION}"

# Domain Configuration
export DOMAIN_NAME="mlops-platform.com"
export HOSTED_ZONE_ID="Z1234567890ABC"

# Container Registry
export ECR_REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

# Database
export DB_PASSWORD="$(openssl rand -base64 32)"  # Generate secure password
export DB_MASTER_USERNAME="mlops_admin"

# Encryption
export KMS_KEY_ID="arn:aws:kms:${AWS_REGION}:${AWS_ACCOUNT_ID}:key/..."

# Tags
export COST_CENTER="Engineering"
export OWNER="platform-team@company.com"
```

**Load environment**:

```bash
source .env
```

### Network Requirements

- [ ] VPC CIDR range defined (e.g., `10.0.0.0/16`)
- [ ] Subnet allocation planned (public, private, database)
- [ ] DNS zones configured
- [ ] SSL certificates provisioned or requested
- [ ] Firewall rules reviewed and approved
- [ ] VPN/Direct Connect configured (if required)

### Cost Estimation

Before deploying, estimate costs:

```bash
# Use AWS Pricing Calculator or Infracost
infracost breakdown --path terraform/

# Expected monthly costs (production):
# - EKS Cluster: $150
# - Worker Nodes (3x m5.2xlarge): $900
# - GPU Nodes (2x g4dn.xlarge, on-demand): $1,200
# - RDS PostgreSQL (db.r5.large): $350
# - S3 Storage (10TB): $230
# - Data Transfer: $200
# Total: ~$3,030/month
```

---

## Pre-Deployment Checklist

### Security Review

- [ ] IAM policies reviewed and approved
- [ ] KMS keys created for encryption at rest
- [ ] Secrets Manager configured for sensitive data
- [ ] Security groups defined with least privilege
- [ ] VPC endpoints configured (reduce data transfer costs)
- [ ] WAF rules configured (if public-facing)
- [ ] Vulnerability scanning enabled

### Compliance Review

- [ ] Data residency requirements documented
- [ ] Compliance frameworks identified (SOC2, HIPAA, etc.)
- [ ] Audit logging configured
- [ ] Backup retention policies defined
- [ ] Disaster recovery plan documented

### Change Management

- [ ] Change request created and approved (CAB)
- [ ] Maintenance window scheduled
- [ ] Stakeholders notified (email, Slack)
- [ ] Rollback plan documented
- [ ] On-call engineer assigned

### Backup Verification

For upgrades/migrations:

- [ ] Full database backup completed
- [ ] S3 bucket versioning enabled
- [ ] Infrastructure state backed up (`terraform.tfstate`)
- [ ] Backup restoration tested

---

## Phase 1: Infrastructure Deployment

**Duration**: 60-90 minutes
**Risk Level**: Medium
**Rollback Complexity**: High (requires full teardown)

### Step 1.1: Clone Infrastructure Repository

```bash
# Clone the infrastructure repository
git clone https://github.com/your-org/mlops-infrastructure.git
cd mlops-infrastructure

# Checkout the appropriate branch
git checkout main  # or production, release/v1.0

# Verify Terraform configuration
terraform fmt -check
terraform validate
```

### Step 1.2: Initialize Terraform Backend

```bash
# Create S3 bucket for Terraform state (if not exists)
aws s3 mb s3://${TF_BACKEND_BUCKET} --region ${AWS_REGION}

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket ${TF_BACKEND_BUCKET} \
  --versioning-configuration Status=Enabled

# Enable encryption
aws s3api put-bucket-encryption \
  --bucket ${TF_BACKEND_BUCKET} \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "AES256"
      }
    }]
  }'

# Create DynamoDB table for state locking
aws dynamodb create-table \
  --table-name terraform-state-lock \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region ${AWS_REGION}
```

### Step 1.3: Configure Terraform Backend

Create `backend.tf`:

```hcl
terraform {
  backend "s3" {
    bucket         = "mlops-terraform-state-123456789012"
    key            = "production/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-state-lock"
  }
}
```

Initialize Terraform:

```bash
cd terraform/

terraform init

# Expected output:
# Terraform has been successfully initialized!
```

### Step 1.4: Review Terraform Plan

```bash
# Generate execution plan
terraform plan -out=tfplan

# Review the plan carefully
# Look for:
# - Resource creation counts
# - Any unexpected deletions
# - IAM policy changes
# - Network configuration changes

# Save plan output
terraform show -json tfplan > tfplan.json
```

**Critical Review Points**:

- [ ] VPC CIDR does not conflict with existing networks
- [ ] EKS cluster version is correct (`1.27`)
- [ ] Node group instance types match requirements
- [ ] RDS instance class is appropriate
- [ ] S3 bucket names are unique
- [ ] IAM roles have appropriate permissions
- [ ] Encryption is enabled for all resources

### Step 1.5: Apply Infrastructure

```bash
# Apply with auto-approve (only in CI/CD or after thorough review)
terraform apply tfplan

# OR apply with manual confirmation
terraform apply

# Monitor progress
# This will take 45-60 minutes due to:
# - VPC creation: 2-3 minutes
# - EKS cluster: 15-20 minutes
# - Node groups: 10-15 minutes
# - RDS instance: 15-20 minutes
# - Other resources: 5-10 minutes
```

**Progress Monitoring**:

```bash
# In a separate terminal, monitor AWS resources
watch -n 30 'aws eks describe-cluster --name mlops-platform-production --query "cluster.status"'

# Monitor Terraform state
terraform state list
```

### Step 1.6: Validate Infrastructure

```bash
# Verify VPC
aws ec2 describe-vpcs --filters "Name=tag:Name,Values=${PROJECT_NAME}-${ENVIRONMENT}-vpc"

# Verify EKS cluster
aws eks describe-cluster --name ${PROJECT_NAME}-${ENVIRONMENT}

# Verify node groups
aws eks list-nodegroups --cluster-name ${PROJECT_NAME}-${ENVIRONMENT}
aws eks describe-nodegroup --cluster-name ${PROJECT_NAME}-${ENVIRONMENT} --nodegroup-name system-nodes

# Verify RDS instance
aws rds describe-db-instances --db-instance-identifier ${PROJECT_NAME}-${ENVIRONMENT}-mlflow

# Verify S3 buckets
aws s3 ls | grep ${PROJECT_NAME}
```

**Expected Output**:

```
VPC: mlops-platform-production-vpc (vpc-0abc123...)
  CIDR: 10.0.0.0/16
  Subnets: 6 (2 public, 2 private, 2 database across 2 AZs)

EKS Cluster: mlops-platform-production
  Status: ACTIVE
  Version: 1.27
  Endpoint: https://ABC123.gr7.us-east-1.eks.amazonaws.com

Node Groups:
  - system-nodes: 3 nodes (m5.large)
  - compute-nodes: 3 nodes (m5.2xlarge)
  - gpu-nodes: 2 nodes (g4dn.xlarge)

RDS Instance: mlops-platform-production-mlflow
  Status: available
  Engine: postgres 14.9
  Instance Class: db.r5.large

S3 Buckets:
  - mlops-platform-production-models
  - mlops-platform-production-artifacts
  - mlops-platform-production-features
```

### Step 1.7: Configure kubectl Access

```bash
# Update kubeconfig
aws eks update-kubeconfig \
  --name ${PROJECT_NAME}-${ENVIRONMENT} \
  --region ${AWS_REGION}

# Verify access
kubectl get nodes

# Expected: 8 nodes (3 system + 3 compute + 2 gpu)
```

**Troubleshooting kubectl Access**:

```bash
# If authentication fails, check IAM role/user
aws sts get-caller-identity

# Verify aws-auth ConfigMap
kubectl get configmap aws-auth -n kube-system -o yaml

# If needed, update aws-auth to add your IAM role
eksctl create iamidentitymapping \
  --cluster ${PROJECT_NAME}-${ENVIRONMENT} \
  --arn arn:aws:iam::${AWS_ACCOUNT_ID}:role/AdminRole \
  --group system:masters \
  --username admin
```

---

## Phase 2: Platform Services Deployment

**Duration**: 45-60 minutes
**Risk Level**: Medium
**Rollback Complexity**: Medium

### Step 2.1: Create Kubernetes Namespaces

```bash
# Create namespaces for platform services
kubectl create namespace mlops-platform
kubectl create namespace monitoring
kubectl create namespace models

# Label namespaces for Istio injection (if using service mesh)
kubectl label namespace mlops-platform istio-injection=enabled
kubectl label namespace models istio-injection=enabled

# Verify
kubectl get namespaces
```

### Step 2.2: Install Cluster Add-ons

```bash
cd kubernetes/cluster-addons/

# Install AWS Load Balancer Controller
helm repo add eks https://aws.github.io/eks-charts
helm repo update

helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName=${PROJECT_NAME}-${ENVIRONMENT} \
  --set serviceAccount.create=false \
  --set serviceAccount.name=aws-load-balancer-controller

# Verify
kubectl get deployment -n kube-system aws-load-balancer-controller

# Install EBS CSI Driver (for persistent volumes)
kubectl apply -k "github.com/kubernetes-sigs/aws-ebs-csi-driver/deploy/kubernetes/overlays/stable/?ref=master"

# Verify
kubectl get pods -n kube-system -l app=ebs-csi-controller

# Install Metrics Server (for HPA)
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# Verify
kubectl get deployment metrics-server -n kube-system
```

### Step 2.3: Deploy Monitoring Stack

```bash
cd kubernetes/monitoring/

# Install Prometheus Operator
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

helm install prometheus prometheus-community/kube-prometheus-stack \
  -n monitoring \
  --values prometheus-values.yaml \
  --wait \
  --timeout 10m

# Verify Prometheus
kubectl get pods -n monitoring -l app.kubernetes.io/name=prometheus

# Verify Grafana
kubectl get pods -n monitoring -l app.kubernetes.io/name=grafana

# Get Grafana admin password
kubectl get secret -n monitoring prometheus-grafana \
  -o jsonpath="{.data.admin-password}" | base64 --decode
```

**prometheus-values.yaml**:

```yaml
prometheus:
  prometheusSpec:
    retention: 30d
    storageSpec:
      volumeClaimTemplate:
        spec:
          accessModes: ["ReadWriteOnce"]
          resources:
            requests:
              storage: 100Gi
    resources:
      requests:
        cpu: 2
        memory: 8Gi
      limits:
        cpu: 4
        memory: 16Gi

grafana:
  adminPassword: "changeme"  # Change this!
  persistence:
    enabled: true
    size: 10Gi
  datasources:
    datasources.yaml:
      apiVersion: 1
      datasources:
        - name: Prometheus
          type: prometheus
          url: http://prometheus-kube-prometheus-prometheus:9090
          isDefault: true

alertmanager:
  config:
    global:
      resolve_timeout: 5m
    route:
      group_by: ['alertname', 'cluster']
      receiver: 'slack'
    receivers:
      - name: 'slack'
        slack_configs:
          - api_url: 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
            channel: '#mlops-alerts'
```

### Step 2.4: Deploy MLflow

```bash
cd kubernetes/mlflow/

# Create MLflow namespace resources
kubectl apply -f namespace.yaml

# Create PostgreSQL secret
kubectl create secret generic mlflow-db-secret \
  -n mlops-platform \
  --from-literal=username=${DB_MASTER_USERNAME} \
  --from-literal=password=${DB_PASSWORD} \
  --from-literal=host=mlops-platform-production-mlflow.abc123.us-east-1.rds.amazonaws.com \
  --from-literal=port=5432 \
  --from-literal=database=mlflow

# Create S3 secret (using IRSA - IAM Roles for Service Accounts)
kubectl apply -f mlflow-serviceaccount.yaml

# Deploy MLflow
helm repo add mlflow https://community-charts.github.io/mlflow
helm install mlflow mlflow/mlflow \
  -n mlops-platform \
  --values mlflow-values.yaml \
  --wait \
  --timeout 10m

# Verify
kubectl get pods -n mlops-platform -l app=mlflow
kubectl get svc -n mlops-platform mlflow
```

**mlflow-values.yaml**:

```yaml
image:
  repository: ghcr.io/mlflow/mlflow
  tag: 2.8.0

replicaCount: 3

backendStore:
  postgres:
    enabled: true
    host:
      valueFrom:
        secretKeyRef:
          name: mlflow-db-secret
          key: host
    port: 5432
    database: mlflow
    user:
      valueFrom:
        secretKeyRef:
          name: mlflow-db-secret
          key: username
    password:
      valueFrom:
        secretKeyRef:
          name: mlflow-db-secret
          key: password

artifactRoot:
  s3:
    enabled: true
    bucket: mlops-platform-production-artifacts
    path: mlflow

serviceAccount:
  create: false
  name: mlflow-sa

ingress:
  enabled: true
  annotations:
    kubernetes.io/ingress.class: alb
    alb.ingress.kubernetes.io/scheme: internal
    alb.ingress.kubernetes.io/target-type: ip
    cert-manager.io/cluster-issuer: letsencrypt-prod
  hosts:
    - host: mlflow.mlops-platform.com
      paths:
        - path: /
          pathType: Prefix

resources:
  requests:
    cpu: 1
    memory: 2Gi
  limits:
    cpu: 2
    memory: 4Gi

autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70
```

**Verify MLflow**:

```bash
# Port-forward to test locally
kubectl port-forward -n mlops-platform svc/mlflow 5000:5000

# In another terminal
curl http://localhost:5000/health
# Expected: {"status": "healthy"}

# Test MLflow API
python3 << EOF
import mlflow
mlflow.set_tracking_uri("http://localhost:5000")
experiments = mlflow.search_experiments()
print(f"MLflow is working! Found {len(experiments)} experiments.")
EOF
```

### Step 2.5: Deploy Feast (Feature Store)

```bash
cd kubernetes/feast/

# Deploy Feast online store (Redis)
helm repo add bitnami https://charts.bitnami.com/bitnami
helm install feast-redis bitnami/redis \
  -n mlops-platform \
  --values feast-redis-values.yaml \
  --wait

# Deploy Feast feature server
kubectl apply -f feast-feature-server.yaml

# Verify
kubectl get pods -n mlops-platform -l app=feast
```

**feast-redis-values.yaml**:

```yaml
architecture: replication
auth:
  enabled: true
  password: "changeme"  # Use Secrets Manager in production
replica:
  replicaCount: 3
master:
  persistence:
    enabled: true
    size: 20Gi
metrics:
  enabled: true
  serviceMonitor:
    enabled: true
resources:
  requests:
    cpu: 1
    memory: 2Gi
  limits:
    cpu: 2
    memory: 4Gi
```

**feast-feature-server.yaml**:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: feast-feature-server
  namespace: mlops-platform
spec:
  replicas: 3
  selector:
    matchLabels:
      app: feast
  template:
    metadata:
      labels:
        app: feast
    spec:
      serviceAccountName: feast-sa
      containers:
        - name: feature-server
          image: feastdev/feature-server:0.35.0
          ports:
            - containerPort: 6566
          env:
            - name: FEAST_REGISTRY
              value: s3://mlops-platform-production-features/registry.db
            - name: FEAST_REDIS_HOST
              value: feast-redis-master
            - name: FEAST_REDIS_PORT
              value: "6379"
          resources:
            requests:
              cpu: 500m
              memory: 1Gi
            limits:
              cpu: 2
              memory: 4Gi
          livenessProbe:
            httpGet:
              path: /health
              port: 6566
            initialDelaySeconds: 30
            periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: feast-feature-server
  namespace: mlops-platform
spec:
  selector:
    app: feast
  ports:
    - port: 6566
      targetPort: 6566
  type: ClusterIP
```

### Step 2.6: Deploy KServe (Model Serving)

```bash
cd kubernetes/kserve/

# Install KServe CRDs
kubectl apply -f https://github.com/kserve/kserve/releases/download/v0.11.0/kserve.yaml
kubectl apply -f https://github.com/kserve/kserve/releases/download/v0.11.0/kserve-runtimes.yaml

# Verify CRDs
kubectl get crd | grep kserve

# Configure KServe InferenceService defaults
kubectl apply -f inferenceservice-config.yaml

# Verify KServe controller
kubectl get pods -n kserve
```

**inferenceservice-config.yaml**:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: inferenceservice-config
  namespace: kserve
data:
  storageInitializer: |-
    {
      "image": "kserve/storage-initializer:v0.11.0",
      "memoryRequest": "100Mi",
      "memoryLimit": "1Gi",
      "cpuRequest": "100m",
      "cpuLimit": "1"
    }
  credentials: |-
    {
      "s3": {
        "s3AccessKeyIDName": "AWS_ACCESS_KEY_ID",
        "s3SecretAccessKeyName": "AWS_SECRET_ACCESS_KEY"
      }
    }
  ingress: |-
    {
      "ingressGateway": "knative-serving/knative-ingress-gateway",
      "ingressService": "istio-ingressgateway.istio-system.svc.cluster.local",
      "localGateway": "knative-serving/knative-local-gateway",
      "localGatewayService": "knative-local-gateway.istio-system.svc.cluster.local"
    }
```

---

## Phase 3: Application Layer Deployment

**Duration**: 30-45 minutes
**Risk Level**: Low
**Rollback Complexity**: Low

### Step 3.1: Build and Push Platform API Container

```bash
cd platform-api/

# Build container image
docker build -t ${ECR_REGISTRY}/mlops-platform-api:v1.0.0 .

# Login to ECR
aws ecr get-login-password --region ${AWS_REGION} | \
  docker login --username AWS --password-stdin ${ECR_REGISTRY}

# Push image
docker push ${ECR_REGISTRY}/mlops-platform-api:v1.0.0

# Verify
aws ecr describe-images \
  --repository-name mlops-platform-api \
  --region ${AWS_REGION}
```

### Step 3.2: Deploy Platform API

```bash
cd kubernetes/platform-api/

# Update image tag in deployment.yaml
sed -i "s|IMAGE_TAG|v1.0.0|g" deployment.yaml

# Deploy
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
kubectl apply -f ingress.yaml

# Verify
kubectl get pods -n mlops-platform -l app=platform-api
kubectl get svc -n mlops-platform platform-api
kubectl get ingress -n mlops-platform platform-api
```

### Step 3.3: Deploy Web UI (Optional)

```bash
cd web-ui/

# Build and push
docker build -t ${ECR_REGISTRY}/mlops-platform-ui:v1.0.0 .
docker push ${ECR_REGISTRY}/mlops-platform-ui:v1.0.0

# Deploy
kubectl apply -f kubernetes/web-ui/
```

### Step 3.4: Configure DNS

```bash
# Get Load Balancer hostname
LB_HOSTNAME=$(kubectl get ingress -n mlops-platform platform-api \
  -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')

echo "Load Balancer: ${LB_HOSTNAME}"

# Create Route53 records
aws route53 change-resource-record-sets \
  --hosted-zone-id ${HOSTED_ZONE_ID} \
  --change-batch '{
    "Changes": [{
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "api.mlops-platform.com",
        "Type": "CNAME",
        "TTL": 300,
        "ResourceRecords": [{"Value": "'${LB_HOSTNAME}'"}]
      }
    }]
  }'

# Verify DNS propagation
dig api.mlops-platform.com
```

---

## Phase 4: Post-Deployment Validation

**Duration**: 30 minutes
**Risk Level**: Low

### Step 4.1: Health Checks

```bash
# MLflow health check
curl https://mlflow.mlops-platform.com/health
# Expected: {"status": "healthy"}

# Platform API health check
curl https://api.mlops-platform.com/health
# Expected: {"status": "healthy", "version": "1.0.0"}

# Feast health check
kubectl exec -n mlops-platform -it feast-feature-server-0 -- \
  curl http://localhost:6566/health
# Expected: {"status": "healthy"}
```

### Step 4.2: Integration Tests

```bash
cd tests/integration/

# Set environment variables
export MLFLOW_TRACKING_URI="https://mlflow.mlops-platform.com"
export PLATFORM_API_URL="https://api.mlops-platform.com"
export FEAST_URL="feast-feature-server.mlops-platform.svc.cluster.local:6566"

# Run integration tests
python3 -m pytest test_integration.py -v

# Expected output:
# test_mlflow_connection ... PASSED
# test_mlflow_create_experiment ... PASSED
# test_feast_feature_retrieval ... PASSED
# test_model_deployment ... PASSED
# test_model_prediction ... PASSED
```

**test_integration.py** (excerpt):

```python
import mlflow
import requests
import pytest

def test_mlflow_connection():
    """Test MLflow connectivity"""
    mlflow.set_tracking_uri(os.environ['MLFLOW_TRACKING_URI'])
    experiments = mlflow.search_experiments()
    assert len(experiments) >= 0

def test_mlflow_create_experiment():
    """Test experiment creation"""
    mlflow.set_tracking_uri(os.environ['MLFLOW_TRACKING_URI'])
    experiment_id = mlflow.create_experiment("test-experiment")
    assert experiment_id is not None

def test_model_deployment():
    """Test model deployment via Platform API"""
    response = requests.post(
        f"{os.environ['PLATFORM_API_URL']}/api/v1/models/deploy",
        json={
            "model_name": "test-model",
            "model_version": "1",
            "target_stage": "staging"
        }
    )
    assert response.status_code == 200
```

### Step 4.3: Performance Tests

```bash
# Load test Platform API
cd tests/performance/

# Install locust
pip install locust

# Run load test
locust -f locustfile.py --host https://api.mlops-platform.com \
  --users 100 --spawn-rate 10 --run-time 5m --headless

# Expected results:
# - Average response time: <200ms
# - P95 latency: <500ms
# - Error rate: <1%
```

### Step 4.4: Monitoring Verification

```bash
# Access Grafana
kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80

# Open browser: http://localhost:3000
# Login: admin / <password from Step 2.3>

# Verify dashboards:
# - Kubernetes Cluster Overview
# - MLflow Metrics
# - Model Serving Metrics
# - Cost Dashboard
```

### Step 4.5: Audit Log Verification

```bash
# Check audit logs in CloudWatch
aws logs tail /aws/eks/${PROJECT_NAME}-${ENVIRONMENT}/cluster --follow

# Check application logs
kubectl logs -n mlops-platform -l app=platform-api --tail=100

# Check security events
kubectl logs -n kube-system -l app=aws-load-balancer-controller
```

---

## Rollback Procedures

### Scenario 1: Infrastructure Rollback (Terraform)

```bash
# Rollback to previous Terraform state
cd terraform/

# List state backups
aws s3 ls s3://${TF_BACKEND_BUCKET}/${TF_BACKEND_KEY}.backup/

# Restore previous state
aws s3 cp s3://${TF_BACKEND_BUCKET}/${TF_BACKEND_KEY}.backup \
  s3://${TF_BACKEND_BUCKET}/${TF_BACKEND_KEY}

# Apply previous configuration
git checkout <previous-commit>
terraform apply
```

### Scenario 2: Application Rollback (Kubernetes)

```bash
# Rollback Helm release
helm rollback mlflow -n mlops-platform

# Rollback Kubernetes deployment
kubectl rollout undo deployment/platform-api -n mlops-platform

# Verify rollback
kubectl rollout status deployment/platform-api -n mlops-platform
```

### Scenario 3: Database Rollback

```bash
# Restore RDS snapshot
SNAPSHOT_ID="mlops-platform-production-mlflow-2024-01-15"

aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier ${PROJECT_NAME}-${ENVIRONMENT}-mlflow-restored \
  --db-snapshot-identifier ${SNAPSHOT_ID}

# Update MLflow ConfigMap to point to restored database
kubectl edit configmap mlflow-config -n mlops-platform
```

---

## Common Issues

### Issue 1: EKS Cluster Creation Timeout

**Symptoms**: Terraform times out after 40 minutes

**Resolution**:
```bash
# Check CloudFormation stacks
aws cloudformation describe-stacks --stack-name eksctl-${PROJECT_NAME}-${ENVIRONMENT}-cluster

# Check EKS cluster status
aws eks describe-cluster --name ${PROJECT_NAME}-${ENVIRONMENT}

# If stuck, delete and recreate
terraform destroy -target=module.eks
terraform apply -target=module.eks
```

### Issue 2: MLflow Cannot Connect to RDS

**Symptoms**: MLflow pods in CrashLoopBackOff

**Resolution**:
```bash
# Check database connectivity from pod
kubectl exec -n mlops-platform -it mlflow-0 -- \
  psql -h <RDS-ENDPOINT> -U ${DB_MASTER_USERNAME} -d mlflow

# Check security groups
aws ec2 describe-security-groups \
  --group-ids $(aws rds describe-db-instances \
    --db-instance-identifier ${PROJECT_NAME}-${ENVIRONMENT}-mlflow \
    --query 'DBInstances[0].VpcSecurityGroups[0].VpcSecurityGroupId' \
    --output text)

# Verify RDS security group allows EKS worker nodes
# Add ingress rule if needed
```

### Issue 3: KServe InferenceService Not Ready

**Symptoms**: InferenceService stuck in "IngressNotConfigured"

**Resolution**:
```bash
# Check KServe controller logs
kubectl logs -n kserve -l control-plane=kserve-controller-manager

# Verify Knative Serving installed
kubectl get pods -n knative-serving

# Check InferenceService status
kubectl describe inferenceservice <model-name> -n models

# Common fix: Update ingress configuration
kubectl edit configmap inferenceservice-config -n kserve
```

---

## Appendix

### A. Terraform Outputs

```bash
# Get all Terraform outputs
terraform output

# Get specific output
terraform output vpc_id
terraform output eks_cluster_endpoint
terraform output rds_endpoint
```

### B. Kubernetes Resources Summary

```bash
# Get all resources in mlops-platform namespace
kubectl get all -n mlops-platform

# Get resource usage
kubectl top nodes
kubectl top pods -n mlops-platform
```

### C. Cost Optimization Checklist

- [ ] Enable EKS Cluster Autoscaler
- [ ] Configure spot instances for compute nodes
- [ ] Enable S3 Intelligent-Tiering
- [ ] Set up RDS automated backups (7-day retention)
- [ ] Configure CloudWatch Logs retention (30 days)
- [ ] Enable VPC endpoints (reduce data transfer)
- [ ] Set up budget alerts

### D. Security Hardening Checklist

- [ ] Enable EKS secrets encryption
- [ ] Configure Pod Security Standards
- [ ] Enable network policies
- [ ] Set up AWS WAF (if public-facing)
- [ ] Enable GuardDuty
- [ ] Configure Security Hub
- [ ] Set up vulnerability scanning (Trivy, Snyk)

### E. Contact Information

| Role | Contact | Escalation |
|------|---------|------------|
| **Platform Team** | platform-team@company.com | Slack: #mlops-platform |
| **DevOps On-Call** | oncall-devops@company.com | PagerDuty |
| **Security Team** | security@company.com | Slack: #security |
| **AWS Support** | Enterprise Support | AWS Console |

### F. Useful Commands Reference

```bash
# Quick health check script
cat > health-check.sh << 'EOF'
#!/bin/bash
echo "=== Kubernetes Cluster ==="
kubectl get nodes

echo "=== Platform Services ==="
kubectl get pods -n mlops-platform

echo "=== MLflow Health ==="
curl -s https://mlflow.mlops-platform.com/health

echo "=== Platform API Health ==="
curl -s https://api.mlops-platform.com/health

echo "=== Resource Usage ==="
kubectl top nodes
EOF

chmod +x health-check.sh
./health-check.sh
```

---

**End of Deployment Runbook**

For operational procedures, see `operations-runbook.md`.
For troubleshooting, see `troubleshooting-runbook.md`.
