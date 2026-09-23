# Enterprise MLOps Platform - Troubleshooting Runbook

**Version**: 1.0
**Last Updated**: 2024-01-15
**Owner**: Platform Engineering Team
**Audience**: SREs, DevOps Engineers, Support Engineers

---

## Table of Contents

1. [Overview](#overview)
2. [Quick Diagnostic Tools](#quick-diagnostic-tools)
3. [Infrastructure Issues](#infrastructure-issues)
4. [MLflow Issues](#mlflow-issues)
5. [Feast (Feature Store) Issues](#feast-feature-store-issues)
6. [KServe (Model Serving) Issues](#kserve-model-serving-issues)
7. [Platform API Issues](#platform-api-issues)
8. [Networking Issues](#networking-issues)
9. [Database Issues](#database-issues)
10. [Performance Issues](#performance-issues)
11. [Security and Access Issues](#security-and-access-issues)
12. [Common Error Messages](#common-error-messages)

---

## Overview

This troubleshooting runbook provides systematic approaches to diagnosing and resolving common issues with the Enterprise MLOps Platform. Each section includes:

- **Symptoms**: What users or monitors observe
- **Possible Causes**: Root causes to investigate
- **Diagnosis**: Step-by-step diagnostic procedures
- **Resolution**: How to fix the issue
- **Prevention**: How to prevent recurrence

### Troubleshooting Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                    Troubleshooting Process                       │
├─────────────────────────────────────────────────────────────────┤
│ 1. IDENTIFY: What is the symptom?                              │
│    └─> Use monitoring dashboards, logs, user reports           │
├─────────────────────────────────────────────────────────────────┤
│ 2. SCOPE: What is the impact?                                  │
│    └─> Determine affected users, services, severity            │
├─────────────────────────────────────────────────────────────────┤
│ 3. DIAGNOSE: What is the root cause?                           │
│    └─> Use diagnostic tools, logs, metrics                     │
├─────────────────────────────────────────────────────────────────┤
│ 4. RESOLVE: Apply fix                                          │
│    └─> Implement solution, verify resolution                   │
├─────────────────────────────────────────────────────────────────┤
│ 5. DOCUMENT: Record findings                                   │
│    └─> Update runbook, create postmortem if needed             │
└─────────────────────────────────────────────────────────────────┘
```

### Escalation Path

| Issue Severity | First Responder | Escalation 1 | Escalation 2 | Escalation 3 |
|----------------|-----------------|--------------|--------------|--------------|
| **P1** | On-call SRE | Senior SRE | Engineering Manager | VP Engineering |
| **P2** | On-call SRE | Platform Team Lead | Engineering Manager | - |
| **P3** | Platform Team | - | - | - |
| **P4** | Any engineer | - | - | - |

**Escalation Timing**:
- P1: Escalate after 15 minutes if no progress
- P2: Escalate after 1 hour if no progress
- P3/P4: Escalate if blocked or needs expertise

---

## Quick Diagnostic Tools

### Universal Health Check Script

```bash
#!/bin/bash
# quick-health-check.sh - Run this first for any incident

echo "======================================"
echo "MLOps Platform Quick Health Check"
echo "======================================"
echo ""

# 1. Cluster connectivity
echo "[1/10] Checking cluster connectivity..."
if kubectl cluster-info &>/dev/null; then
  echo "✅ Cluster is reachable"
else
  echo "❌ Cannot reach cluster"
  echo "   → Run: aws eks update-kubeconfig --name mlops-platform-production --region us-east-1"
  exit 1
fi

# 2. Node status
echo ""
echo "[2/10] Checking node status..."
NOT_READY=$(kubectl get nodes | grep -v Ready | grep -v NAME | wc -l)
if [ "$NOT_READY" -eq 0 ]; then
  echo "✅ All nodes ready ($(kubectl get nodes --no-headers | wc -l) nodes)"
else
  echo "❌ $NOT_READY nodes not ready"
  kubectl get nodes | grep -v Ready
fi

# 3. Pod health
echo ""
echo "[3/10] Checking pod health..."
FAILING_PODS=$(kubectl get pods -A | grep -vE 'Running|Completed' | grep -v NAME | wc -l)
if [ "$FAILING_PODS" -eq 0 ]; then
  echo "✅ All pods healthy"
else
  echo "⚠️  $FAILING_PODS pods not healthy"
  kubectl get pods -A | grep -vE 'Running|Completed' | head -10
fi

# 4. Critical services
echo ""
echo "[4/10] Checking critical services..."
for service in mlflow platform-api feast-feature-server; do
  if kubectl get svc -n mlops-platform $service &>/dev/null; then
    echo "  ✅ $service exists"
  else
    echo "  ❌ $service missing"
  fi
done

# 5. Recent events
echo ""
echo "[5/10] Checking recent warnings/errors..."
kubectl get events -A --sort-by='.lastTimestamp' | grep -E 'Warning|Error' | tail -5

# 6. Resource pressure
echo ""
echo "[6/10] Checking resource pressure..."
HIGH_CPU=$(kubectl top nodes | awk 'NR>1 {gsub(/%/,"",$3); if($3>80) print $1}')
if [ -z "$HIGH_CPU" ]; then
  echo "✅ CPU usage normal"
else
  echo "⚠️  High CPU on: $HIGH_CPU"
fi

HIGH_MEM=$(kubectl top nodes | awk 'NR>1 {gsub(/%/,"",$5); if($5>85) print $1}')
if [ -z "$HIGH_MEM" ]; then
  echo "✅ Memory usage normal"
else
  echo "⚠️  High memory on: $HIGH_MEM"
fi

# 7. Active alerts
echo ""
echo "[7/10] Checking active alerts..."
FIRING_ALERTS=$(curl -s http://prometheus-kube-prometheus-prometheus.monitoring:9090/api/v1/alerts | jq '.data.alerts[] | select(.state=="firing")' | jq -s length)
if [ "$FIRING_ALERTS" -eq 0 ]; then
  echo "✅ No active alerts"
else
  echo "⚠️  $FIRING_ALERTS active alerts"
  curl -s http://prometheus-kube-prometheus-prometheus.monitoring:9090/api/v1/alerts | \
    jq -r '.data.alerts[] | select(.state=="firing") | "  - \(.labels.alertname) (\(.labels.severity))"'
fi

# 8. External connectivity
echo ""
echo "[8/10] Checking external endpoints..."
for endpoint in "https://mlflow.mlops-platform.com/health" "https://api.mlops-platform.com/health"; do
  if curl -s -o /dev/null -w "%{http_code}" "$endpoint" | grep -q "200"; then
    echo "  ✅ $endpoint reachable"
  else
    echo "  ❌ $endpoint unreachable"
  fi
done

# 9. Database connectivity
echo ""
echo "[9/10] Checking database connectivity..."
DB_HOST=$(kubectl get secret mlflow-db-secret -n mlops-platform -o jsonpath='{.data.host}' | base64 -d 2>/dev/null)
if [ -n "$DB_HOST" ]; then
  if nc -z -w5 $DB_HOST 5432 2>/dev/null; then
    echo "✅ Database reachable at $DB_HOST"
  else
    echo "❌ Cannot reach database at $DB_HOST"
  fi
else
  echo "⚠️  Database secret not found"
fi

# 10. Disk space
echo ""
echo "[10/10] Checking disk space..."
for node in $(kubectl get nodes -o name); do
  node_name=$(echo $node | cut -d/ -f2)
  disk_usage=$(kubectl get --raw "/api/v1/nodes/$node_name/proxy/stats/summary" 2>/dev/null | \
    jq -r '.node.fs.usedBytes / .node.fs.capacityBytes * 100' 2>/dev/null)

  if [ -n "$disk_usage" ]; then
    disk_usage_int=$(printf "%.0f" "$disk_usage")
    if [ "$disk_usage_int" -gt 85 ]; then
      echo "  ⚠️  $node_name: ${disk_usage_int}% disk usage"
    else
      echo "  ✅ $node_name: ${disk_usage_int}% disk usage"
    fi
  fi
done

echo ""
echo "======================================"
echo "Health check complete"
echo "======================================"
```

**Usage**:

```bash
chmod +x quick-health-check.sh
./quick-health-check.sh | tee health-check-$(date +%Y%m%d-%H%M%S).log
```

### Log Aggregation Commands

```bash
# Get logs from all pods of a deployment (last 1 hour)
kubectl logs -n mlops-platform -l app=mlflow --since=1h --tail=1000

# Search for specific error across all pods
kubectl logs -n mlops-platform -l app=platform-api --since=1h | grep -i "error\|exception" | tail -50

# Get events for a specific pod
kubectl describe pod <pod-name> -n mlops-platform | grep -A10 Events

# Tail logs from multiple pods
stern -n mlops-platform mlflow
```

### Performance Profiling

```bash
# Check latency metrics
kubectl exec -n mlops-platform mlflow-0 -- \
  curl -s localhost:5000/metrics | grep -E 'request_latency|request_duration'

# Profile API endpoint
time curl -w "@curl-format.txt" -o /dev/null -s "https://api.mlops-platform.com/api/v1/models"

# curl-format.txt contents:
#     time_namelookup:  %{time_namelookup}s
#        time_connect:  %{time_connect}s
#     time_appconnect:  %{time_appconnect}s
#    time_pretransfer:  %{time_pretransfer}s
#       time_redirect:  %{time_redirect}s
#  time_starttransfer:  %{time_starttransfer}s
#          time_total:  %{time_total}s
```

---

## Infrastructure Issues

### Issue: EKS Cluster Unreachable

**Symptoms**:
- `kubectl` commands timeout
- "Unable to connect to the server" errors
- API server health checks failing

**Diagnosis**:

```bash
# 1. Check AWS credentials
aws sts get-caller-identity

# 2. Verify cluster exists
aws eks describe-cluster --name mlops-platform-production --region us-east-1

# 3. Check cluster status
aws eks describe-cluster --name mlops-platform-production \
  --query 'cluster.status' --output text
# Expected: ACTIVE

# 4. Verify kubeconfig
cat ~/.kube/config | grep mlops-platform-production

# 5. Test API server endpoint
ENDPOINT=$(aws eks describe-cluster --name mlops-platform-production \
  --query 'cluster.endpoint' --output text)
curl -k $ENDPOINT/healthz
```

**Resolution**:

```bash
# Solution 1: Update kubeconfig
aws eks update-kubeconfig \
  --name mlops-platform-production \
  --region us-east-1

# Solution 2: Check security groups (if endpoint unreachable)
# API server security group must allow traffic from your IP
CLUSTER_SG=$(aws eks describe-cluster --name mlops-platform-production \
  --query 'cluster.resourcesVpcConfig.clusterSecurityGroupId' --output text)

aws ec2 authorize-security-group-ingress \
  --group-id $CLUSTER_SG \
  --protocol tcp \
  --port 443 \
  --cidr $(curl -s ifconfig.me)/32

# Solution 3: Check VPC endpoint (if using private endpoint)
aws eks describe-cluster --name mlops-platform-production \
  --query 'cluster.resourcesVpcConfig.endpointPrivateAccess'
# If true, ensure you're connecting from within VPC or via VPN
```

**Prevention**:
- Set up VPN or Direct Connect for reliable access
- Use bastion host within VPC for emergency access
- Configure multiple admin users with cluster access

### Issue: Nodes Not Ready

**Symptoms**:
- `kubectl get nodes` shows NotReady status
- Pods stuck in Pending state
- Node conditions show MemoryPressure, DiskPressure, or NetworkUnavailable

**Diagnosis**:

```bash
# 1. Check node conditions
kubectl describe node <node-name> | grep Conditions -A20

# 2. Check node logs (via SSM)
NODE_INSTANCE_ID=$(aws ec2 describe-instances \
  --filters "Name=private-dns-name,Values=<node-name>" \
  --query 'Reservations[0].Instances[0].InstanceId' --output text)

aws ssm start-session --target $NODE_INSTANCE_ID

# On the node:
sudo journalctl -u kubelet -n 100
sudo systemctl status kubelet
df -h
free -m

# 3. Check kubelet logs via kubectl
kubectl get --raw "/api/v1/nodes/<node-name>/proxy/logs/kubelet.log" | tail -100
```

**Common Causes and Resolutions**:

**Cause 1: Disk Pressure**

```bash
# Check disk usage
kubectl get --raw "/api/v1/nodes/<node-name>/proxy/stats/summary" | \
  jq '.node.fs'

# Resolution: Clean up unused images and containers
kubectl drain <node-name> --ignore-daemonsets --delete-emptydir-data
aws ssm start-session --target $NODE_INSTANCE_ID

# On the node:
sudo docker system prune -a -f
sudo systemctl restart kubelet

# Uncordon node
kubectl uncordon <node-name>
```

**Cause 2: Memory Pressure**

```bash
# Check memory usage
kubectl top node <node-name>

# Resolution: Identify memory-hungry pods
kubectl top pods -A --sort-by=memory | head -20

# Restart or reschedule heavy pods
kubectl delete pod <heavy-pod> -n mlops-platform

# If persistent: scale up node group
aws eks update-nodegroup-config \
  --cluster-name mlops-platform-production \
  --nodegroup-name compute-nodes \
  --scaling-config minSize=4,maxSize=12,desiredSize=6
```

**Cause 3: Network Issues**

```bash
# Check CNI plugin
kubectl get pods -n kube-system -l k8s-app=aws-node

# Restart CNI if needed
kubectl rollout restart daemonset aws-node -n kube-system

# Check security groups
aws ec2 describe-security-groups --group-ids <node-sg> \
  --query 'SecurityGroups[0].IpPermissions'
```

### Issue: Cluster Autoscaler Not Scaling

**Symptoms**:
- Pods remain Pending despite autoscaling enabled
- Node group size doesn't change under load
- Cluster Autoscaler logs show errors

**Diagnosis**:

```bash
# 1. Check Cluster Autoscaler status
kubectl logs -n kube-system deployment/cluster-autoscaler | tail -100

# 2. Check pending pods
kubectl get pods -A --field-selector status.phase=Pending

# 3. Check autoscaler configmap
kubectl describe configmap cluster-autoscaler-status -n kube-system

# 4. Verify IAM permissions
kubectl describe sa cluster-autoscaler -n kube-system
aws iam get-role --role-name eks-cluster-autoscaler-role
```

**Resolution**:

```bash
# Solution 1: Check IAM permissions
# Cluster Autoscaler needs autoscaling:DescribeAutoScalingGroups,
# autoscaling:SetDesiredCapacity, etc.

cat > cluster-autoscaler-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "autoscaling:DescribeAutoScalingGroups",
        "autoscaling:DescribeAutoScalingInstances",
        "autoscaling:DescribeLaunchConfigurations",
        "autoscaling:DescribeScalingActivities",
        "autoscaling:DescribeTags",
        "ec2:DescribeImages",
        "ec2:DescribeInstanceTypes",
        "ec2:DescribeLaunchTemplateVersions",
        "ec2:GetInstanceTypesFromInstanceRequirements",
        "eks:DescribeNodegroup",
        "autoscaling:SetDesiredCapacity",
        "autoscaling:TerminateInstanceInAutoScalingGroup"
      ],
      "Resource": "*"
    }
  ]
}
EOF

aws iam put-role-policy \
  --role-name eks-cluster-autoscaler-role \
  --policy-name ClusterAutoscalerPolicy \
  --policy-document file://cluster-autoscaler-policy.json

# Solution 2: Verify ASG tags
# Auto Scaling Groups must be tagged with:
# k8s.io/cluster-autoscaler/<cluster-name>: owned
# k8s.io/cluster-autoscaler/enabled: true

aws autoscaling describe-auto-scaling-groups \
  --query 'AutoScalingGroups[?contains(Tags[?Key==`k8s.io/cluster-autoscaler/mlops-platform-production`].Value, `owned`)]'

# Solution 3: Check max size limits
kubectl edit deployment cluster-autoscaler -n kube-system
# Ensure --max-nodes-total is set appropriately

# Solution 4: Restart Cluster Autoscaler
kubectl rollout restart deployment cluster-autoscaler -n kube-system
```

---

## MLflow Issues

### Issue: MLflow UI Not Loading

**Symptoms**:
- MLflow webpage returns 502/503 errors
- Blank page or timeout
- "Backend not available" errors

**Diagnosis**:

```bash
# 1. Check MLflow pods
kubectl get pods -n mlops-platform -l app=mlflow

# 2. Check pod logs
kubectl logs -n mlops-platform -l app=mlflow --tail=100

# 3. Check service
kubectl get svc -n mlops-platform mlflow
kubectl describe svc -n mlops-platform mlflow

# 4. Check ingress
kubectl get ingress -n mlops-platform mlflow
kubectl describe ingress -n mlops-platform mlflow

# 5. Test pod directly
kubectl port-forward -n mlops-platform svc/mlflow 5000:5000
curl http://localhost:5000/health
```

**Resolution**:

**Cause 1: Pod CrashLoopBackOff**

```bash
# Check why pod is crashing
kubectl logs -n mlops-platform <mlflow-pod> --previous

# Common causes:
# - Database connection failure
# - S3 access issues
# - Configuration errors

# Verify database connectivity
kubectl exec -n mlops-platform <mlflow-pod> -- \
  nc -zv <db-host> 5432

# Verify S3 access
kubectl exec -n mlops-platform <mlflow-pod> -- \
  aws s3 ls s3://mlops-platform-production-artifacts/

# Check environment variables
kubectl exec -n mlops-platform <mlflow-pod> -- env | grep MLFLOW
```

**Cause 2: Database Connection Issues**

```bash
# Verify database secret
kubectl get secret mlflow-db-secret -n mlops-platform -o yaml

# Test database connection from pod
kubectl exec -it -n mlops-platform <mlflow-pod> -- \
  psql -h <db-host> -U mlops_admin -d mlflow -c "SELECT 1;"

# If connection fails, check RDS security group
RDS_SG=$(aws rds describe-db-instances \
  --db-instance-identifier mlops-platform-production-mlflow \
  --query 'DBInstances[0].VpcSecurityGroups[0].VpcSecurityGroupId' \
  --output text)

aws ec2 describe-security-groups --group-ids $RDS_SG

# Ensure security group allows inbound from EKS nodes
NODE_SG=$(kubectl get nodes -o json | \
  jq -r '.items[0].spec.providerID' | \
  awk -F/ '{print $NF}' | \
  xargs -I {} aws ec2 describe-instances --instance-ids {} \
  --query 'Reservations[0].Instances[0].SecurityGroups[0].GroupId' --output text)

aws ec2 authorize-security-group-ingress \
  --group-id $RDS_SG \
  --protocol tcp \
  --port 5432 \
  --source-group $NODE_SG
```

**Cause 3: S3 Access Issues**

```bash
# Check ServiceAccount annotations
kubectl describe sa mlflow-sa -n mlops-platform

# Verify IAM role
IAM_ROLE=$(kubectl get sa mlflow-sa -n mlops-platform \
  -o jsonpath='{.metadata.annotations.eks\.amazonaws\.com/role-arn}')

aws iam get-role --role-name $(echo $IAM_ROLE | awk -F/ '{print $NF}')

# Test S3 access from pod
kubectl exec -it -n mlops-platform <mlflow-pod> -- \
  aws s3 ls s3://mlops-platform-production-artifacts/
```

### Issue: Cannot Log Experiments to MLflow

**Symptoms**:
- `mlflow.log_metric()` fails with connection errors
- Authentication errors
- "Experiment not found" errors

**Diagnosis**:

```bash
# 1. Verify MLflow tracking URI
echo $MLFLOW_TRACKING_URI

# 2. Test connectivity
curl $MLFLOW_TRACKING_URI/health

# 3. Test experiment creation
python3 << EOF
import mlflow
mlflow.set_tracking_uri("$MLFLOW_TRACKING_URI")
try:
    experiment_id = mlflow.create_experiment("test-connectivity")
    print(f"✅ Connection successful! Experiment ID: {experiment_id}")
except Exception as e:
    print(f"❌ Connection failed: {e}")
EOF

# 4. Check MLflow logs during request
kubectl logs -n mlops-platform -l app=mlflow --tail=50 -f
```

**Resolution**:

```bash
# Solution 1: Verify network connectivity
# From client machine/pod
nc -zv mlflow.mlops-platform.com 443

# Solution 2: Check authentication
# MLflow may require authentication
export MLFLOW_TRACKING_USERNAME=<username>
export MLFLOW_TRACKING_PASSWORD=<password>

# Solution 3: Verify experiment exists
mlflow experiments list --tracking-uri $MLFLOW_TRACKING_URI
```

### Issue: MLflow High Latency

**Symptoms**:
- Slow experiment logging (>5 seconds)
- UI takes long to load
- API timeouts

**Diagnosis**:

```bash
# 1. Check MLflow pod resource usage
kubectl top pod -n mlops-platform -l app=mlflow

# 2. Check database performance
# Connect to RDS
psql -h <rds-endpoint> -U mlops_admin -d mlflow

# Run slow query log
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;

# 3. Check S3 performance
kubectl exec -n mlops-platform <mlflow-pod> -- \
  aws s3 cp s3://mlops-platform-production-artifacts/test.txt - --debug 2>&1 | \
  grep -i "time"

# 4. Profile MLflow requests
kubectl exec -n mlops-platform <mlflow-pod> -- \
  curl -w "@curl-format.txt" -o /dev/null -s "http://localhost:5000/api/2.0/mlflow/experiments/list"
```

**Resolution**:

```bash
# Solution 1: Scale MLflow horizontally
kubectl scale deployment mlflow -n mlops-platform --replicas=5

# Solution 2: Scale RDS vertically
aws rds modify-db-instance \
  --db-instance-identifier mlops-platform-production-mlflow \
  --db-instance-class db.r5.xlarge \
  --apply-immediately

# Solution 3: Add RDS read replica for read-heavy operations
aws rds create-db-instance-read-replica \
  --db-instance-identifier mlops-mlflow-read-replica \
  --source-db-instance-identifier mlops-platform-production-mlflow

# Update MLflow to use read replica for queries
kubectl set env deployment/mlflow \
  -n mlops-platform \
  MLFLOW_READ_DB_URI=postgresql://mlops_admin:password@<read-replica-endpoint>:5432/mlflow

# Solution 4: Optimize database
psql -h <rds-endpoint> -U mlops_admin -d mlflow << EOF
-- Analyze tables
ANALYZE experiments;
ANALYZE runs;
ANALYZE metrics;

-- Rebuild indexes
REINDEX TABLE experiments;
REINDEX TABLE runs;

-- Update statistics
VACUUM ANALYZE;
EOF
```

---

## Feast (Feature Store) Issues

### Issue: Feast Feature Retrieval Slow

**Symptoms**:
- `get_online_features()` takes >100ms (P95)
- Redis high latency
- Timeouts during feature retrieval

**Diagnosis**:

```bash
# 1. Check Feast pods
kubectl get pods -n mlops-platform -l app=feast
kubectl top pods -n mlops-platform -l app=feast

# 2. Check Redis performance
kubectl exec -it -n mlops-platform feast-redis-master-0 -- redis-cli INFO stats

# Look for:
# - total_commands_processed
# - instantaneous_ops_per_sec
# - keyspace_hits vs keyspace_misses

# 3. Test feature retrieval latency
python3 << EOF
import time
from feast import FeatureStore

store = FeatureStore(repo_path=".")

start = time.time()
features = store.get_online_features(
    features=["customer_features:total_purchases"],
    entity_rows=[{"customer_id": "123"}]
).to_dict()
latency = (time.time() - start) * 1000

print(f"Feature retrieval latency: {latency:.2f}ms")
if latency > 100:
    print("⚠️  Latency exceeds SLO (100ms)")
EOF

# 4. Check Redis slow log
kubectl exec -it -n mlops-platform feast-redis-master-0 -- \
  redis-cli SLOWLOG GET 10
```

**Resolution**:

```bash
# Solution 1: Scale Redis replicas
kubectl scale statefulset feast-redis-replica -n mlops-platform --replicas=5

# Solution 2: Increase Redis memory
kubectl edit statefulset feast-redis-master -n mlops-platform
# Update resources.requests.memory and resources.limits.memory

# Restart Redis pods (one at a time)
kubectl delete pod feast-redis-master-0 -n mlops-platform

# Solution 3: Enable Redis persistence optimization
kubectl exec -it -n mlops-platform feast-redis-master-0 -- \
  redis-cli CONFIG SET save ""

# Solution 4: Check network latency
# If Feast and Redis are in different availability zones
kubectl get pods -n mlops-platform -o wide | grep feast
kubectl get pods -n mlops-platform -o wide | grep redis

# Use pod anti-affinity to co-locate Feast and Redis
kubectl edit deployment feast-feature-server -n mlops-platform
# Add affinity rules
```

### Issue: Features Not Found

**Symptoms**:
- `FeatureView not found` errors
- Empty feature values returned
- Registry errors

**Diagnosis**:

```bash
# 1. Check Feast registry
feast registry-dump

# 2. List feature views
feast feature-views list

# 3. Check S3 registry file
aws s3 ls s3://mlops-platform-production-features/registry.db
aws s3 cp s3://mlops-platform-production-features/registry.db - | file -

# 4. Verify feature view definition
feast feature-views describe <feature-view-name>
```

**Resolution**:

```bash
# Solution 1: Re-apply feature definitions
cd feature-repo/
feast apply

# Solution 2: Verify registry location
# Check Feast config
cat feature_store.yaml

# Ensure registry path is correct
registry: s3://mlops-platform-production-features/registry.db

# Solution 3: Materialize features to online store
feast materialize-incremental $(date +%Y-%m-%d)

# Verify features in Redis
kubectl exec -it -n mlops-platform feast-redis-master-0 -- \
  redis-cli KEYS "*"

# Solution 4: Check data source connectivity
# If features depend on Redshift/Athena
aws redshift-data execute-statement \
  --cluster-identifier mlops-cluster \
  --database mlops \
  --sql "SELECT COUNT(*) FROM customer_features;"
```

---

## KServe (Model Serving) Issues

### Issue: InferenceService Not Ready

**Symptoms**:
- `kubectl get inferenceservice` shows "IngressNotConfigured" or "Unknown"
- Model deployment stuck
- Prediction endpoint not accessible

**Diagnosis**:

```bash
# 1. Check InferenceService status
kubectl get inferenceservice -n models <model-name>
kubectl describe inferenceservice -n models <model-name>

# 2. Check predictor pods
kubectl get pods -n models -l serving.kserve.io/inferenceservice=<model-name>

# 3. Check KServe controller logs
kubectl logs -n kserve -l control-plane=kserve-controller-manager --tail=100

# 4. Check revision
kubectl get revision -n models
```

**Resolution**:

**Cause 1: Model Not Found in S3**

```bash
# Verify model exists
MODEL_URI=$(kubectl get inferenceservice -n models <model-name> \
  -o jsonpath='{.spec.predictor.model.storageUri}')

aws s3 ls $MODEL_URI/

# If model missing, copy it
mlflow models download --model-uri models:/<model-name>/<version> --dst /tmp/model
aws s3 cp /tmp/model $MODEL_URI --recursive
```

**Cause 2: Insufficient Resources**

```bash
# Check if pods are pending due to resources
kubectl describe pod -n models <predictor-pod>

# Look for:
# - "Insufficient cpu"
# - "Insufficient memory"

# Solution: Adjust resource requests
kubectl edit inferenceservice -n models <model-name>

# Reduce requests or scale cluster:
spec:
  predictor:
    model:
      resources:
        requests:
          cpu: "500m"      # Reduced from 1
          memory: "1Gi"    # Reduced from 2Gi
```

**Cause 3: Image Pull Errors**

```bash
# Check pod events
kubectl describe pod -n models <predictor-pod> | grep -A5 "Events"

# Common errors:
# - "ImagePullBackOff": Image not found or no access
# - "ErrImagePull": Network issues

# Solution: Verify image exists
kubectl get inferenceservice -n models <model-name> \
  -o jsonpath='{.spec.predictor.containers[0].image}'

# Test image pull manually
docker pull <image>

# Check ECR permissions
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin <account>.dkr.ecr.us-east-1.amazonaws.com
```

**Cause 4: Networking Issues**

```bash
# Check if ingress is configured
kubectl get ingress -n models

# Check service
kubectl get svc -n models -l serving.kserve.io/inferenceservice=<model-name>

# Test service directly
kubectl port-forward -n models svc/<model-name>-predictor 8080:80
curl http://localhost:8080/v1/models/<model-name>
```

### Issue: Model Prediction Errors

**Symptoms**:
- HTTP 500 errors from prediction endpoint
- Incorrect predictions
- Timeouts

**Diagnosis**:

```bash
# 1. Check predictor logs
kubectl logs -n models -l serving.kserve.io/inferenceservice=<model-name> --tail=100

# 2. Test prediction locally
kubectl port-forward -n models svc/<model-name>-predictor 8080:80

curl -X POST http://localhost:8080/v1/models/<model-name>:predict \
  -H "Content-Type: application/json" \
  -d '{
    "instances": [
      {"feature1": 1.0, "feature2": 2.0, "feature3": 3.0}
    ]
  }'

# 3. Check model metadata
curl http://localhost:8080/v1/models/<model-name>

# 4. Check predictor metrics
kubectl exec -n models <predictor-pod> -- \
  curl localhost:9090/metrics | grep request
```

**Resolution**:

```bash
# Solution 1: Verify model format
# Download model and test locally
aws s3 cp <model-storage-uri> /tmp/model --recursive
python3 << EOF
import mlflow

model = mlflow.pyfunc.load_model("/tmp/model")
prediction = model.predict([[1.0, 2.0, 3.0]])
print(prediction)
EOF

# Solution 2: Check input schema
# Model may expect different input format
curl http://localhost:8080/v1/models/<model-name>/metadata

# Solution 3: Increase timeout
kubectl edit inferenceservice -n models <model-name>

spec:
  predictor:
    timeout: 120  # Increase from default 60 seconds
```

### Issue: Model Serving High Latency

**Symptoms**:
- P95 latency >200ms (SLO breach)
- Slow predictions
- Autoscaler constantly scaling

**Diagnosis**:

```bash
# 1. Check predictor resource usage
kubectl top pods -n models -l serving.kserve.io/inferenceservice=<model-name>

# 2. Check HPA status
kubectl get hpa -n models <model-name>-predictor

# 3. Measure latency
for i in {1..100}; do
  curl -w "%{time_total}\n" -o /dev/null -s \
    -X POST http://<prediction-endpoint>/v1/models/<model-name>:predict \
    -H "Content-Type: application/json" \
    -d '{"instances": [{"feature1": 1.0}]}'
done | awk '{sum+=$1; sumsq+=$1*$1} END {print "Avg:", sum/NR, "Std:", sqrt(sumsq/NR - (sum/NR)^2)}'

# 4. Profile model inference
kubectl exec -n models <predictor-pod> -- \
  python3 -m cProfile -o /tmp/profile.stats model_server.py

# Download and analyze
kubectl cp models/<predictor-pod>:/tmp/profile.stats ./profile.stats
python3 -c "import pstats; p = pstats.Stats('profile.stats'); p.sort_stats('cumulative'); p.print_stats(20)"
```

**Resolution**:

```bash
# Solution 1: Scale up replicas
kubectl scale inferenceservice <model-name> -n models --replicas=5

# Or adjust autoscaling
kubectl edit inferenceservice -n models <model-name>

spec:
  predictor:
    minReplicas: 5
    maxReplicas: 20
    scaleTarget: 70    # Target 70% concurrency

# Solution 2: Use GPU instances (if model benefits)
kubectl edit inferenceservice -n models <model-name>

spec:
  predictor:
    model:
      resources:
        limits:
          nvidia.com/gpu: 1
    nodeSelector:
      workload: gpu

# Solution 3: Optimize model
# - Quantization (FP16, INT8)
# - ONNX conversion for faster inference
# - Model pruning
# - Batching requests

# Solution 4: Enable batching
kubectl edit inferenceservice -n models <model-name>

spec:
  predictor:
    batcher:
      maxBatchSize: 32
      maxLatency: 100  # ms
```

---

## Platform API Issues

### Issue: Platform API Returning 500 Errors

**Symptoms**:
- HTTP 500 Internal Server Error
- Random failures
- Error rate spike in Grafana

**Diagnosis**:

```bash
# 1. Check API pods
kubectl get pods -n mlops-platform -l app=platform-api
kubectl logs -n mlops-platform -l app=platform-api --tail=200

# 2. Check recent errors
kubectl logs -n mlops-platform -l app=platform-api --since=10m | \
  grep -i "error\|exception\|traceback" | tail -50

# 3. Check API metrics
curl http://prometheus:9090/api/v1/query?query='rate(http_requests_total{app="platform-api",status=~"5.."}[5m])'

# 4. Test specific endpoint
curl -v https://api.mlops-platform.com/api/v1/models
```

**Resolution**:

```bash
# Common causes and solutions:

# Cause 1: Database connection pool exhausted
kubectl logs -n mlops-platform <api-pod> | grep -i "connection pool"

# Solution: Increase connection pool size
kubectl set env deployment/platform-api \
  -n mlops-platform \
  DB_POOL_SIZE=20 \
  DB_MAX_OVERFLOW=40

# Cause 2: Timeout connecting to MLflow
kubectl set env deployment/platform-api \
  -n mlops-platform \
  MLFLOW_TIMEOUT=30

# Cause 3: Memory leak
kubectl top pods -n mlops-platform -l app=platform-api

# Solution: Restart pods with memory leak
kubectl delete pod <api-pod> -n mlops-platform

# Or rolling restart
kubectl rollout restart deployment/platform-api -n mlops-platform

# Cause 4: Unhandled exceptions
# Check logs for stack traces
kubectl logs -n mlops-platform <api-pod> --tail=1000 > api-errors.log
grep -A20 "Traceback" api-errors.log

# Fix code and redeploy
```

### Issue: API Authentication Failures

**Symptoms**:
- HTTP 401 Unauthorized
- "Invalid token" errors
- Authentication working intermittently

**Diagnosis**:

```bash
# 1. Test authentication
curl -X POST https://api.mlops-platform.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "test", "password": "test"}'

# 2. Verify token
TOKEN="<your-token>"
curl -H "Authorization: Bearer $TOKEN" \
  https://api.mlops-platform.com/api/v1/models

# 3. Check API logs for auth errors
kubectl logs -n mlops-platform -l app=platform-api | grep -i "auth\|401\|unauthorized"

# 4. Check secret configuration
kubectl get secret platform-api-secrets -n mlops-platform -o yaml
```

**Resolution**:

```bash
# Solution 1: Regenerate JWT secret
JWT_SECRET=$(openssl rand -base64 32)
kubectl create secret generic platform-api-secrets \
  -n mlops-platform \
  --from-literal=jwt-secret=$JWT_SECRET \
  --dry-run=client -o yaml | kubectl apply -f -

# Restart API pods
kubectl rollout restart deployment/platform-api -n mlops-platform

# Solution 2: Fix token expiration
kubectl set env deployment/platform-api \
  -n mlops-platform \
  JWT_EXPIRATION=86400  # 24 hours

# Solution 3: Verify OIDC provider (if using SSO)
kubectl describe configmap platform-api-config -n mlops-platform
```

---

## Networking Issues

### Issue: Cannot Access Services Externally

**Symptoms**:
- DNS resolution fails
- Connection timeout to service endpoints
- "Could not resolve host" errors

**Diagnosis**:

```bash
# 1. Check DNS
dig mlflow.mlops-platform.com
nslookup mlflow.mlops-platform.com

# 2. Check Route53 records
aws route53 list-resource-record-sets \
  --hosted-zone-id <hosted-zone-id> | \
  jq '.ResourceRecordSets[] | select(.Name | contains("mlops-platform"))'

# 3. Check Load Balancer
kubectl get ingress -A
kubectl describe ingress -n mlops-platform mlflow

# Get LB DNS
LB_DNS=$(kubectl get ingress -n mlops-platform mlflow \
  -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')

echo "Load Balancer: $LB_DNS"

# Test LB directly
curl -H "Host: mlflow.mlops-platform.com" http://$LB_DNS/health

# 4. Check ALB status
aws elbv2 describe-load-balancers | \
  jq '.LoadBalancers[] | select(.DNSName=="'$LB_DNS'")'
```

**Resolution**:

```bash
# Solution 1: Update DNS records
LB_DNS=$(kubectl get ingress -n mlops-platform mlflow \
  -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')

aws route53 change-resource-record-sets \
  --hosted-zone-id <hosted-zone-id> \
  --change-batch '{
    "Changes": [{
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "mlflow.mlops-platform.com",
        "Type": "CNAME",
        "TTL": 300,
        "ResourceRecords": [{"Value": "'$LB_DNS'"}]
      }
    }]
  }'

# Solution 2: Check security groups
# Load Balancer SG must allow inbound 443
aws elbv2 describe-load-balancers --query 'LoadBalancers[?DNSName==`'$LB_DNS'`]'

# Get LB ARN and security groups
LB_ARN=<from-above>
aws elbv2 describe-load-balancers --load-balancer-arns $LB_ARN \
  --query 'LoadBalancers[0].SecurityGroups'

# Verify SG rules
aws ec2 describe-security-groups --group-ids <sg-id>

# Solution 3: Check SSL certificate
kubectl describe ingress -n mlops-platform mlflow | grep -i tls

# Verify ACM certificate
aws acm list-certificates | grep mlops-platform
```

### Issue: Pod-to-Pod Communication Failures

**Symptoms**:
- Services cannot communicate
- "Connection refused" errors between pods
- Network policies blocking traffic

**Diagnosis**:

```bash
# 1. Test pod-to-pod connectivity
# From one pod to another
kubectl exec -n mlops-platform <pod-a> -- \
  curl -v http://<pod-b-ip>:5000

# 2. Check network policies
kubectl get networkpolicies -A
kubectl describe networkpolicy <policy-name> -n mlops-platform

# 3. Check DNS resolution within cluster
kubectl exec -n mlops-platform <pod-a> -- \
  nslookup mlflow.mlops-platform.svc.cluster.local

# 4. Check CoreDNS
kubectl get pods -n kube-system -l k8s-app=kube-dns
kubectl logs -n kube-system -l k8s-app=kube-dns
```

**Resolution**:

```bash
# Solution 1: Update network policy
kubectl edit networkpolicy <policy-name> -n mlops-platform

# Allow traffic from specific namespace
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-mlops-traffic
spec:
  podSelector: {}
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              name: mlops-platform
        - namespaceSelector:
            matchLabels:
              name: models
  policyTypes:
    - Ingress

# Solution 2: Restart CoreDNS
kubectl rollout restart deployment coredns -n kube-system

# Solution 3: Check CNI plugin
kubectl get pods -n kube-system -l k8s-app=aws-node
kubectl logs -n kube-system -l k8s-app=aws-node | grep -i error
```

---

## Database Issues

### Issue: RDS Connection Exhaustion

**Symptoms**:
- "Too many connections" errors
- Applications cannot connect to database
- Connection timeouts

**Diagnosis**:

```bash
# 1. Check current connections
psql -h <rds-endpoint> -U mlops_admin -d mlflow << EOF
SELECT
  count(*),
  state
FROM pg_stat_activity
GROUP BY state;

SELECT
  datname,
  usename,
  application_name,
  state,
  count(*)
FROM pg_stat_activity
GROUP BY datname, usename, application_name, state
ORDER BY count DESC;
EOF

# 2. Check max connections
psql -h <rds-endpoint> -U mlops_admin -d mlflow -c \
  "SHOW max_connections;"

# 3. Check RDS metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/RDS \
  --metric-name DatabaseConnections \
  --dimensions Name=DBInstanceIdentifier,Value=mlops-platform-production-mlflow \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Maximum,Average
```

**Resolution**:

```bash
# Solution 1: Terminate idle connections
psql -h <rds-endpoint> -U mlops_admin -d mlflow << EOF
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE state = 'idle'
  AND state_change < NOW() - INTERVAL '30 minutes';
EOF

# Solution 2: Increase max_connections (requires reboot)
aws rds modify-db-parameter-group \
  --db-parameter-group-name mlops-mlflow-params \
  --parameters "ParameterName=max_connections,ParameterValue=500,ApplyMethod=pending-reboot"

aws rds reboot-db-instance \
  --db-instance-identifier mlops-platform-production-mlflow

# Solution 3: Fix connection leaks in applications
# Check application connection pool settings
kubectl get configmap platform-api-config -n mlops-platform -o yaml

# Update connection pool
kubectl patch configmap platform-api-config -n mlops-platform --type merge -p '{
  "data": {
    "DB_POOL_SIZE": "10",
    "DB_POOL_RECYCLE": "3600",
    "DB_POOL_PRE_PING": "true"
  }
}'

# Restart applications
kubectl rollout restart deployment/platform-api -n mlops-platform
kubectl rollout restart deployment/mlflow -n mlops-platform

# Solution 4: Use connection pooler (PgBouncer)
kubectl apply -f pgbouncer.yaml
# Update applications to connect through PgBouncer
```

### Issue: RDS High CPU Usage

**Symptoms**:
- Database queries slow
- RDS CPU consistently >80%
- Timeout errors

**Diagnosis**:

```bash
# 1. Check CPU metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/RDS \
  --metric-name CPUUtilization \
  --dimensions Name=DBInstanceIdentifier,Value=mlops-platform-production-mlflow \
  --start-time $(date -u -d '24 hours ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 3600 \
  --statistics Maximum,Average

# 2. Identify slow queries
psql -h <rds-endpoint> -U mlops_admin -d mlflow << EOF
SELECT
  query,
  calls,
  total_time,
  mean_time,
  max_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 20;
EOF

# 3. Check for missing indexes
psql -h <rds-endpoint> -U mlops_admin -d mlflow << EOF
SELECT
  schemaname,
  tablename,
  attname,
  n_distinct,
  correlation
FROM pg_stats
WHERE schemaname = 'public'
  AND n_distinct > 100
  AND correlation < 0.1;
EOF

# 4. Check for long-running queries
psql -h <rds-endpoint> -U mlops_admin -d mlflow << EOF
SELECT
  pid,
  now() - query_start AS duration,
  query,
  state
FROM pg_stat_activity
WHERE state != 'idle'
ORDER BY duration DESC;
EOF
```

**Resolution**:

```bash
# Solution 1: Add missing indexes
psql -h <rds-endpoint> -U mlops_admin -d mlflow << EOF
-- Example: Add index on frequently queried columns
CREATE INDEX CONCURRENTLY idx_runs_experiment_id ON runs(experiment_id);
CREATE INDEX CONCURRENTLY idx_metrics_run_id ON metrics(run_id);
EOF

# Solution 2: Optimize queries
# Analyze slow queries and rewrite
psql -h <rds-endpoint> -U mlops_admin -d mlflow << EOF
EXPLAIN ANALYZE <slow-query>;
EOF

# Solution 3: Terminate long-running queries
psql -h <rds-endpoint> -U mlops_admin -d mlflow << EOF
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE state != 'idle'
  AND now() - query_start > interval '5 minutes';
EOF

# Solution 4: Scale up RDS instance
aws rds modify-db-instance \
  --db-instance-identifier mlops-platform-production-mlflow \
  --db-instance-class db.r5.2xlarge \
  --apply-immediately

# Solution 5: Add read replica
aws rds create-db-instance-read-replica \
  --db-instance-identifier mlops-mlflow-read-replica \
  --source-db-instance-identifier mlops-platform-production-mlflow \
  --db-instance-class db.r5.large

# Update applications to use read replica for SELECT queries
```

---

## Performance Issues

### Issue: High API Latency

**Symptoms**:
- API response times >300ms (P95)
- Timeout errors
- Slow page loads

**Diagnosis**:

```bash
# 1. Measure latency distribution
for i in {1..100}; do
  curl -w "%{time_total}\n" -o /dev/null -s \
    https://api.mlops-platform.com/api/v1/models
done | sort -n | awk '{
  all[NR] = $0
}
END {
  print "P50:", all[int(NR*0.5)]
  print "P95:", all[int(NR*0.95)]
  print "P99:", all[int(NR*0.99)]
}'

# 2. Profile specific endpoint
kubectl exec -n mlops-platform <api-pod> -- \
  python3 -m cProfile -s cumulative api_server.py 2>&1 | head -50

# 3. Check resource usage
kubectl top pods -n mlops-platform -l app=platform-api

# 4. Check database query performance
kubectl logs -n mlops-platform <api-pod> | \
  grep -i "query took" | \
  awk '{print $NF}' | \
  sort -n | \
  tail -20
```

**Resolution**:

```bash
# Solution 1: Enable caching
kubectl set env deployment/platform-api \
  -n mlops-platform \
  REDIS_CACHE_ENABLED=true \
  REDIS_CACHE_HOST=platform-redis \
  CACHE_TTL=300

# Deploy Redis for caching
helm install platform-redis bitnami/redis \
  -n mlops-platform \
  --set auth.enabled=false \
  --set master.persistence.enabled=false

# Solution 2: Database connection pooling
kubectl set env deployment/platform-api \
  -n mlops-platform \
  DB_POOL_SIZE=20 \
  DB_POOL_PRE_PING=true

# Solution 3: Scale horizontally
kubectl scale deployment platform-api \
  -n mlops-platform \
  --replicas=10

# Solution 4: Optimize slow queries
# Identify N+1 query patterns
# Add database indexes
# Use eager loading for related objects
```

### Issue: Out of Memory (OOM) Kills

**Symptoms**:
- Pods restarting frequently
- "OOMKilled" status
- Memory pressure on nodes

**Diagnosis**:

```bash
# 1. Check for OOM kills
kubectl get pods -A -o json | \
  jq -r '.items[] | select(.status.containerStatuses[]?.lastState.terminated.reason=="OOMKilled") | .metadata.name'

# 2. Check memory usage
kubectl top pods -A --sort-by=memory | head -20

# 3. Check pod memory limits
kubectl get pods -A -o json | \
  jq -r '.items[] | "\(.metadata.name) \(.spec.containers[0].resources.limits.memory // "no limit")"'

# 4. Analyze memory growth
kubectl exec -n mlops-platform <pod> -- \
  python3 -c "
import psutil
import os
process = psutil.Process(os.getpid())
print(f'Memory: {process.memory_info().rss / 1024 / 1024:.2f} MB')
"
```

**Resolution**:

```bash
# Solution 1: Increase memory limits
kubectl edit deployment <deployment> -n mlops-platform

spec:
  template:
    spec:
      containers:
        - resources:
            requests:
              memory: "2Gi"
            limits:
              memory: "4Gi"

# Solution 2: Fix memory leaks
# Profile application memory usage
kubectl exec -n mlops-platform <pod> -- \
  python3 -m memory_profiler app.py

# Solution 3: Implement memory limits in application
# Add garbage collection tuning
kubectl set env deployment/<deployment> \
  -n mlops-platform \
  PYTHONHASHSEED=0 \
  MALLOC_TRIM_THRESHOLD_=100000

# Solution 4: Use larger nodes
# Scale up node group instance type
aws eks update-nodegroup-config \
  --cluster-name mlops-platform-production \
  --nodegroup-name compute-nodes \
  --update-config launchTemplate={id=lt-xxx,version=2}
```

---

## Security and Access Issues

### Issue: IAM Permission Denied

**Symptoms**:
- "Access Denied" errors accessing S3, RDS, etc.
- Pods cannot assume IAM role
- IRSA not working

**Diagnosis**:

```bash
# 1. Check pod ServiceAccount
kubectl describe pod <pod> -n mlops-platform | grep "Service Account"

# 2. Check ServiceAccount annotations
kubectl describe sa <service-account> -n mlops-platform

# Expected annotation:
# eks.amazonaws.com/role-arn: arn:aws:iam::123456789012:role/mlops-role

# 3. Verify IAM role trust policy
IAM_ROLE=<role-name-from-annotation>
aws iam get-role --role-name $IAM_ROLE

# Trust policy should include:
# {
#   "Effect": "Allow",
#   "Principal": {
#     "Federated": "arn:aws:iam::123456789012:oidc-provider/oidc.eks.us-east-1.amazonaws.com/id/EXAMPLE"
#   },
#   "Action": "sts:AssumeRoleWithWebIdentity",
#   "Condition": {
#     "StringEquals": {
#       "oidc.eks.us-east-1.amazonaws.com/id/EXAMPLE:sub": "system:serviceaccount:mlops-platform:mlflow-sa"
#     }
#   }
# }

# 4. Test from pod
kubectl exec -n mlops-platform <pod> -- \
  aws sts get-caller-identity
```

**Resolution**:

```bash
# Solution 1: Fix ServiceAccount annotation
kubectl annotate serviceaccount <sa-name> -n mlops-platform \
  eks.amazonaws.com/role-arn=arn:aws:iam::123456789012:role/mlops-mlflow-role

# Restart pods
kubectl rollout restart deployment/<deployment> -n mlops-platform

# Solution 2: Update IAM role trust policy
cat > trust-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::123456789012:oidc-provider/$(aws eks describe-cluster --name mlops-platform-production --query 'cluster.identity.oidc.issuer' --output text | sed 's|https://||')"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "$(aws eks describe-cluster --name mlops-platform-production --query 'cluster.identity.oidc.issuer' --output text | sed 's|https://||'):sub": "system:serviceaccount:mlops-platform:mlflow-sa"
        }
      }
    }
  ]
}
EOF

aws iam update-assume-role-policy \
  --role-name mlops-mlflow-role \
  --policy-document file://trust-policy.json

# Solution 3: Attach necessary policies
aws iam attach-role-policy \
  --role-name mlops-mlflow-role \
  --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess
```

### Issue: SSL Certificate Errors

**Symptoms**:
- "Certificate verification failed" errors
- Browser shows "Not Secure"
- SSL/TLS handshake failures

**Diagnosis**:

```bash
# 1. Check certificate validity
echo | openssl s_client -servername mlflow.mlops-platform.com \
  -connect mlflow.mlops-platform.com:443 2>/dev/null | \
  openssl x509 -noout -dates

# 2. Check certificate issuer
echo | openssl s_client -servername mlflow.mlops-platform.com \
  -connect mlflow.mlops-platform.com:443 2>/dev/null | \
  openssl x509 -noout -issuer -subject

# 3. Check ACM certificate status
aws acm list-certificates | grep mlops-platform
aws acm describe-certificate --certificate-arn <cert-arn>

# 4. Check ingress TLS configuration
kubectl describe ingress -n mlops-platform mlflow | grep -A5 TLS
```

**Resolution**:

```bash
# Solution 1: Request new certificate
aws acm request-certificate \
  --domain-name "*.mlops-platform.com" \
  --subject-alternative-names "mlops-platform.com" \
  --validation-method DNS

# Validate certificate via Route53
aws acm describe-certificate --certificate-arn <cert-arn>

# Solution 2: Update ingress with correct certificate
kubectl edit ingress -n mlops-platform mlflow

spec:
  tls:
    - hosts:
        - mlflow.mlops-platform.com
      secretName: mlops-tls-cert

# Solution 3: Import existing certificate
aws acm import-certificate \
  --certificate fileb://certificate.crt \
  --private-key fileb://private-key.pem \
  --certificate-chain fileb://certificate-chain.crt
```

---

## Common Error Messages

### "ImagePullBackOff"

**Cause**: Cannot pull container image

**Resolution**:
```bash
# Verify image exists
docker pull <image>

# Check image pull secrets
kubectl get secrets -n mlops-platform

# Create image pull secret if needed
kubectl create secret docker-registry ecr-registry \
  -n mlops-platform \
  --docker-server=<account>.dkr.ecr.us-east-1.amazonaws.com \
  --docker-username=AWS \
  --docker-password=$(aws ecr get-login-password --region us-east-1)

# Update deployment to use secret
kubectl patch serviceaccount default -n mlops-platform \
  -p '{"imagePullSecrets": [{"name": "ecr-registry"}]}'
```

### "CrashLoopBackOff"

**Cause**: Container crashes immediately after starting

**Resolution**:
```bash
# Check previous logs
kubectl logs -n mlops-platform <pod> --previous

# Check startup probe
kubectl describe pod -n mlops-platform <pod> | grep -A10 "Liveness\|Readiness\|Startup"

# Increase startup time
kubectl edit deployment -n mlops-platform <deployment>

spec:
  template:
    spec:
      containers:
        - startupProbe:
            initialDelaySeconds: 60
```

### "Insufficient cpu/memory"

**Cause**: Not enough resources to schedule pod

**Resolution**:
```bash
# Check available resources
kubectl describe nodes | grep -A5 "Allocated resources"

# Scale cluster
aws eks update-nodegroup-config \
  --cluster-name mlops-platform-production \
  --nodegroup-name compute-nodes \
  --scaling-config minSize=5,maxSize=15,desiredSize=8

# Or reduce pod requests
kubectl edit deployment -n mlops-platform <deployment>
```

---

**End of Troubleshooting Runbook**

For deployment procedures, see `deployment-runbook.md`.
For operational procedures, see `operations-runbook.md`.

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────────────┐
│                     Emergency Contact List                       │
├─────────────────────────────────────────────────────────────────┤
│ P1 Incidents:    PagerDuty → oncall-sre@company.com           │
│ Platform Team:   #mlops-platform on Slack                      │
│ Security Team:   #security on Slack                            │
│ AWS Support:     Enterprise Support via AWS Console            │
├─────────────────────────────────────────────────────────────────┤
│                     Quick Diagnostic Commands                    │
├─────────────────────────────────────────────────────────────────┤
│ Health Check:    ./quick-health-check.sh                       │
│ All Pods:        kubectl get pods -A                           │
│ Node Status:     kubectl get nodes                             │
│ Recent Events:   kubectl get events -A --sort-by=.lastTimestamp│
│ Active Alerts:   curl http://prometheus:9090/api/v1/alerts     │
│ Resource Usage:  kubectl top nodes; kubectl top pods -A        │
└─────────────────────────────────────────────────────────────────┘
```
