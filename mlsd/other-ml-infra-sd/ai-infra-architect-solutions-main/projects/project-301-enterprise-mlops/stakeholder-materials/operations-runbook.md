# Enterprise MLOps Platform - Operations Runbook

**Version**: 1.0
**Last Updated**: 2024-01-15
**Owner**: Platform Engineering Team
**Audience**: SREs, DevOps Engineers, Platform Operators

---

## Table of Contents

1. [Overview](#overview)
2. [Daily Operations](#daily-operations)
3. [Weekly Operations](#weekly-operations)
4. [Monthly Operations](#monthly-operations)
5. [Backup and Recovery](#backup-and-recovery)
6. [Scaling Operations](#scaling-operations)
7. [Upgrade Procedures](#upgrade-procedures)
8. [Monitoring and Alerting](#monitoring-and-alerting)
9. [Incident Response](#incident-response)
10. [Cost Management](#cost-management)
11. [Security Operations](#security-operations)
12. [Maintenance Windows](#maintenance-windows)

---

## Overview

This runbook documents day-to-day operational procedures for the Enterprise MLOps Platform. It covers routine tasks, maintenance activities, monitoring, and operational best practices.

### Operational Model

```
┌────────────────────────────────────────────────────────────────┐
│                     24/7 Operations Coverage                    │
├────────────────────────────────────────────────────────────────┤
│ Business Hours (9am-5pm EST)                                   │
│   • Platform Team: Full coverage (5 engineers)                 │
│   • Response Time: <15 minutes for P1, <1 hour for P2         │
├────────────────────────────────────────────────────────────────┤
│ After Hours (5pm-9am EST, weekends)                           │
│   • On-Call Engineer: Rotating schedule                        │
│   • Response Time: <30 minutes for P1, <4 hours for P2        │
│   • Escalation: Senior SRE → Engineering Manager              │
└────────────────────────────────────────────────────────────────┘
```

### Service Level Objectives (SLOs)

| Service | Availability SLO | Latency SLO (P95) | Error Budget |
|---------|------------------|-------------------|--------------|
| **MLflow** | 99.9% | 500ms | 43 minutes/month |
| **Feast Online** | 99.9% | 100ms | 43 minutes/month |
| **KServe** | 99.5% | 200ms | 3.6 hours/month |
| **Platform API** | 99.9% | 300ms | 43 minutes/month |
| **Training Jobs** | 99.0% | N/A | 7.2 hours/month |

### Operational Responsibilities

| Team | Responsibilities |
|------|-----------------|
| **Platform Team** | Platform infrastructure, upgrades, capacity planning |
| **Data Team** | Feature engineering, data quality, Feast management |
| **ML Engineers** | Model training, deployment, monitoring |
| **Security Team** | Access control, compliance, vulnerability management |
| **FinOps Team** | Cost optimization, budget tracking, reporting |

---

## Daily Operations

### Morning Health Check (Every Day at 9am EST)

**Duration**: 15 minutes
**Owner**: On-call engineer or platform team member

#### Step 1: Check Service Health

```bash
#!/bin/bash
# daily-health-check.sh

echo "================================"
echo "Daily Health Check - $(date)"
echo "================================"

# Check Kubernetes cluster
echo "1. Kubernetes Cluster Status"
kubectl get nodes
kubectl get componentstatuses

# Check critical namespaces
echo ""
echo "2. Critical Pods Status"
for ns in mlops-platform monitoring models kube-system; do
  echo "Namespace: $ns"
  kubectl get pods -n $ns | grep -v Running || echo "  All pods running"
done

# Check resource usage
echo ""
echo "3. Resource Usage"
kubectl top nodes
echo ""
kubectl top pods -n mlops-platform --sort-by=memory | head -10

# Check MLflow
echo ""
echo "4. MLflow Health"
curl -s https://mlflow.mlops-platform.com/health || echo "MLflow UNHEALTHY"

# Check Platform API
echo ""
echo "5. Platform API Health"
curl -s https://api.mlops-platform.com/health || echo "Platform API UNHEALTHY"

# Check recent errors
echo ""
echo "6. Recent Error Count (last 1 hour)"
kubectl logs -n mlops-platform -l app=platform-api --since=1h | grep -i error | wc -l

# Check pending model deployments
echo ""
echo "7. Pending Model Deployments"
kubectl get inferenceservice -n models | grep -v Ready || echo "  No pending deployments"

# Check alerts
echo ""
echo "8. Active Alerts"
curl -s http://prometheus-kube-prometheus-prometheus.monitoring:9090/api/v1/alerts | \
  jq '.data.alerts[] | select(.state=="firing") | {alert: .labels.alertname, severity: .labels.severity}'

echo ""
echo "================================"
echo "Health Check Complete"
echo "================================"
```

**Run the health check**:

```bash
./scripts/daily-health-check.sh | tee logs/health-check-$(date +%Y%m%d).log

# Upload to S3 for record-keeping
aws s3 cp logs/health-check-$(date +%Y%m%d).log \
  s3://mlops-platform-production-logs/health-checks/
```

**Alert Conditions**:

- **Red Alert** (Page on-call immediately):
  - Any service down
  - Cluster nodes NotReady
  - >10 active P1 alerts
  - API error rate >5%

- **Yellow Alert** (Investigate within 1 hour):
  - High memory/CPU usage (>85%)
  - 1-5 active P2 alerts
  - Slow response times (>2x SLO)
  - Failed model deployments

#### Step 2: Review Overnight Activity

```bash
# Check overnight model deployments
kubectl get events -n models --sort-by='.lastTimestamp' | grep -A5 "InferenceService"

# Check overnight errors
aws logs tail /aws/eks/mlops-platform-production/cluster \
  --since 12h --filter-pattern "ERROR"

# Check cost anomalies
aws ce get-anomalies --max-results 10 --total-impact-threshold 100
```

#### Step 3: Capacity Check

```bash
# Check EKS node utilization
kubectl describe nodes | grep -A5 "Allocated resources"

# Check if autoscaling is needed
kubectl get hpa -A

# Check pending pods (may indicate capacity issues)
kubectl get pods -A --field-selector=status.phase=Pending
```

**Action Items**:

- If node CPU >80% consistently: Scale up node group
- If node memory >85%: Investigate memory leaks or scale up
- If pending pods exist >5 minutes: Check cluster autoscaler logs

#### Step 4: Update Status Page

```bash
# Update internal status page
curl -X POST https://status.mlops-platform.com/api/v1/status \
  -H "Authorization: Bearer ${STATUS_PAGE_TOKEN}" \
  -d '{
    "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",
    "services": {
      "mlflow": "operational",
      "feast": "operational",
      "kserve": "operational",
      "platform_api": "operational"
    },
    "message": "All systems operational"
  }'
```

### End of Day Summary (Every Day at 5pm EST)

**Duration**: 10 minutes

```bash
# Generate daily summary
cat > daily-summary-$(date +%Y%m%d).md << EOF
# Daily Operations Summary - $(date +%Y-%m-%d)

## Metrics
- **Model Deployments**: $(kubectl get inferenceservice -n models | wc -l)
- **Training Jobs**: $(kubectl get jobs -n mlops-platform | grep Completed | wc -l)
- **API Requests**: $(curl -s http://prometheus:9090/api/v1/query?query='sum(rate(http_requests_total[24h]))' | jq '.data.result[0].value[1]')
- **Average Latency**: $(curl -s http://prometheus:9090/api/v1/query?query='avg(http_request_duration_seconds{quantile="0.95"}[24h])' | jq '.data.result[0].value[1]')

## Incidents
$(kubectl get events -n mlops-platform --field-selector type=Warning --sort-by='.lastTimestamp' | tail -10)

## Cost
- **Today's Cost**: \$$(aws ce get-cost-and-usage --time-period Start=$(date +%Y-%m-%d),End=$(date -d tomorrow +%Y-%m-%d) --granularity DAILY --metrics UnblendedCost | jq '.ResultsByTime[0].Total.UnblendedCost.Amount')

## Action Items
- [ ] Follow up on warning events
- [ ] Review cost anomalies
- [ ] Update on-call notes

EOF

# Send summary to Slack
slack-cli -d daily-summary-$(date +%Y%m%d).md -c mlops-operations
```

---

## Weekly Operations

### Monday: Capacity Planning Review

**Duration**: 30 minutes
**Owner**: Platform Team Lead

#### Review Resource Utilization

```bash
# Generate 7-day resource report
kubectl top nodes --use-protocol-buffers | awk '{print $1,$2,$4,$5}' > weekly-resources.txt

# Check EKS node group scaling history
aws autoscaling describe-scaling-activities \
  --auto-scaling-group-name eksctl-mlops-platform-production-nodegroup-compute-nodes \
  --max-records 50

# Review storage usage
kubectl get pvc -A
df -h | grep /var/lib/kubelet

# Check S3 bucket sizes
aws s3 ls | while read -r line; do
  bucket=$(echo $line | awk '{print $3}')
  size=$(aws s3 ls s3://$bucket --recursive --summarize | grep "Total Size" | awk '{print $3}')
  echo "$bucket: $size bytes"
done
```

#### Capacity Planning Actions

```python
# capacity-planning.py
import boto3
from datetime import datetime, timedelta

def analyze_capacity():
    """Analyze resource usage trends and recommend scaling"""

    # Get CloudWatch metrics for past 7 days
    cloudwatch = boto3.client('cloudwatch')

    metrics = [
        'CPUUtilization',
        'MemoryUtilization',
        'NetworkIn',
        'NetworkOut'
    ]

    for metric in metrics:
        response = cloudwatch.get_metric_statistics(
            Namespace='AWS/EKS',
            MetricName=metric,
            Dimensions=[
                {'Name': 'ClusterName', 'Value': 'mlops-platform-production'}
            ],
            StartTime=datetime.now() - timedelta(days=7),
            EndTime=datetime.now(),
            Period=3600,
            Statistics=['Average', 'Maximum']
        )

        # Analyze trends
        datapoints = sorted(response['Datapoints'], key=lambda x: x['Timestamp'])
        avg_values = [dp['Average'] for dp in datapoints]
        max_values = [dp['Maximum'] for dp in datapoints]

        avg_utilization = sum(avg_values) / len(avg_values)
        max_utilization = max(max_values)

        print(f"{metric}:")
        print(f"  Average: {avg_utilization:.2f}%")
        print(f"  Maximum: {max_utilization:.2f}%")

        # Recommendations
        if avg_utilization > 70:
            print(f"  ⚠️  RECOMMENDATION: Scale up (avg utilization {avg_utilization:.1f}%)")
        elif avg_utilization < 30:
            print(f"  💡 RECOMMENDATION: Consider scaling down (avg utilization {avg_utilization:.1f}%)")
        else:
            print(f"  ✅ Capacity is appropriate")
        print()

if __name__ == '__main__':
    analyze_capacity()
```

### Wednesday: Security Review

**Duration**: 45 minutes
**Owner**: Security Team + Platform Team

#### Security Checks

```bash
# Check for outdated container images
kubectl get pods -A -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.containers[*].image}{"\n"}' | \
  while read pod image; do
    # Check image age (implement using Docker registry API)
    echo "Checking $pod: $image"
  done

# Review IAM roles and policies
aws iam list-roles | jq '.Roles[] | select(.RoleName | contains("mlops"))'

# Check for open security groups
aws ec2 describe-security-groups --query 'SecurityGroups[?IpPermissions[?IpRanges[?CidrIp==`0.0.0.0/0`]]]'

# Review access logs
aws s3 cp s3://mlops-platform-production-access-logs/$(date +%Y/%m/%d)/ . --recursive
grep -i "403\|401\|500" access-*.log | tail -50

# Check SSL certificate expiration
echo | openssl s_client -servername mlflow.mlops-platform.com -connect mlflow.mlops-platform.com:443 2>/dev/null | \
  openssl x509 -noout -dates
```

#### Vulnerability Scanning

```bash
# Scan running containers with Trivy
trivy image --severity HIGH,CRITICAL $(kubectl get pods -n mlops-platform -o jsonpath='{.items[0].spec.containers[0].image}')

# Check for Kubernetes CVEs
kubectl version
curl -s https://kubernetes.io/docs/reference/issues-security/official-cve-feed/ | grep -A5 "1.27"

# Review GuardDuty findings
aws guardduty list-findings --detector-id $(aws guardduty list-detectors --query 'DetectorIds[0]' --output text) \
  --finding-criteria '{"Criterion":{"severity":{"Gte":7}}}'
```

### Friday: Cost Review and Optimization

**Duration**: 1 hour
**Owner**: FinOps Team + Platform Team

#### Cost Analysis

```bash
# Get week's cost breakdown
aws ce get-cost-and-usage \
  --time-period Start=$(date -d '7 days ago' +%Y-%m-%d),End=$(date +%Y-%m-%d) \
  --granularity DAILY \
  --metrics UnblendedCost \
  --group-by Type=DIMENSION,Key=SERVICE \
  --output json > weekly-costs.json

# Analyze costs by service
jq '.ResultsByTime[] | {date: .TimePeriod.Start, costs: .Groups}' weekly-costs.json

# Top 10 cost drivers
jq '[.ResultsByTime[].Groups[] | {service: .Keys[0], cost: .Metrics.UnblendedCost.Amount | tonumber}] | group_by(.service) | map({service: .[0].service, total: map(.cost) | add}) | sort_by(.total) | reverse | .[0:10]' weekly-costs.json
```

**Cost Optimization Script**:

```python
# cost-optimizer.py
import boto3
from datetime import datetime, timedelta

def identify_cost_savings():
    """Identify cost optimization opportunities"""

    # 1. Idle EBS volumes
    ec2 = boto3.client('ec2')
    volumes = ec2.describe_volumes(Filters=[{'Name': 'status', 'Values': ['available']}])

    print("=== Idle EBS Volumes ===")
    idle_cost = 0
    for vol in volumes['Volumes']:
        size = vol['Size']
        cost_per_gb = 0.10  # gp3 pricing
        monthly_cost = size * cost_per_gb
        idle_cost += monthly_cost
        print(f"Volume {vol['VolumeId']}: {size}GB - ${monthly_cost:.2f}/month")
    print(f"Total potential savings: ${idle_cost:.2f}/month\n")

    # 2. Old snapshots (>90 days)
    snapshots = ec2.describe_snapshots(OwnerIds=['self'])

    print("=== Old Snapshots (>90 days) ===")
    snapshot_cost = 0
    cutoff_date = datetime.now() - timedelta(days=90)
    for snap in snapshots['Snapshots']:
        if snap['StartTime'].replace(tzinfo=None) < cutoff_date:
            size = snap['VolumeSize']
            cost = size * 0.05  # Snapshot pricing
            snapshot_cost += cost
            print(f"Snapshot {snap['SnapshotId']}: {size}GB - ${cost:.2f}/month")
    print(f"Total potential savings: ${snapshot_cost:.2f}/month\n")

    # 3. Oversized RDS instances
    rds = boto3.client('rds')
    instances = rds.describe_db_instances()

    print("=== RDS Instance Utilization ===")
    cloudwatch = boto3.client('cloudwatch')
    for instance in instances['DBInstances']:
        instance_id = instance['DBInstanceIdentifier']

        # Get CPU utilization
        cpu_metrics = cloudwatch.get_metric_statistics(
            Namespace='AWS/RDS',
            MetricName='CPUUtilization',
            Dimensions=[{'Name': 'DBInstanceIdentifier', 'Value': instance_id}],
            StartTime=datetime.now() - timedelta(days=7),
            EndTime=datetime.now(),
            Period=3600,
            Statistics=['Average']
        )

        if cpu_metrics['Datapoints']:
            avg_cpu = sum(dp['Average'] for dp in cpu_metrics['Datapoints']) / len(cpu_metrics['Datapoints'])

            if avg_cpu < 20:
                print(f"{instance_id}: {avg_cpu:.1f}% CPU - Consider downsizing")
            else:
                print(f"{instance_id}: {avg_cpu:.1f}% CPU - Appropriate size")
    print()

    # 4. Spot instance opportunities
    asg = boto3.client('autoscaling')
    groups = asg.describe_auto_scaling_groups()

    print("=== Spot Instance Opportunities ===")
    for group in groups['AutoScalingGroups']:
        if 'compute' in group['AutoScalingGroupName']:
            on_demand_count = len([i for i in group['Instances'] if not i.get('LifecycleState', '').startswith('Spot')])
            if on_demand_count > 0:
                potential_savings = on_demand_count * 0.30 * 24 * 30  # Assume 70% savings
                print(f"{group['AutoScalingGroupName']}: {on_demand_count} on-demand instances")
                print(f"  Potential savings with Spot: ${potential_savings:.2f}/month")

    print("\n=== Total Monthly Savings Potential ===")
    total_savings = idle_cost + snapshot_cost
    print(f"${total_savings:.2f}/month")

if __name__ == '__main__':
    identify_cost_savings()
```

---

## Monthly Operations

### First Monday of Month: Platform Review

**Duration**: 2 hours
**Attendees**: Platform Team, Engineering Managers, Security Team

#### Agenda

1. **SLO Review** (30 minutes)
   - Review SLO compliance for previous month
   - Analyze incidents and root causes
   - Identify improvement areas

2. **Capacity Planning** (30 minutes)
   - Review growth trends
   - Plan for next quarter's capacity
   - Budget allocation

3. **Security Posture** (30 minutes)
   - Review security incidents
   - Compliance audit results
   - Security roadmap updates

4. **Cost Optimization** (30 minutes)
   - Month-over-month cost analysis
   - ROI on optimization initiatives
   - Budget forecast

#### Monthly Reporting

```bash
# Generate monthly report
./scripts/generate-monthly-report.sh $(date +%Y-%m)

# Report includes:
# - Service availability metrics
# - Model deployment statistics
# - Cost breakdown
# - Security summary
# - Capacity utilization
# - Incident summary
```

### Patch Management (Second Wednesday)

**Duration**: 2-4 hours (depending on scope)
**Owner**: Platform Team

#### Kubernetes Version Upgrade

```bash
# Check current EKS version
aws eks describe-cluster --name mlops-platform-production \
  --query 'cluster.version' --output text

# Check available upgrades
aws eks describe-addon-versions --kubernetes-version 1.27

# Upgrade EKS control plane (example: 1.27 -> 1.28)
aws eks update-cluster-version \
  --name mlops-platform-production \
  --kubernetes-version 1.28

# Monitor upgrade progress
aws eks describe-update \
  --name mlops-platform-production \
  --update-id <update-id>

# Upgrade node groups (one by one)
eksctl upgrade nodegroup \
  --name system-nodes \
  --cluster mlops-platform-production \
  --kubernetes-version 1.28
```

#### Application Updates

```bash
# Update MLflow
helm upgrade mlflow mlflow/mlflow \
  -n mlops-platform \
  --version 2.9.0 \
  --reuse-values

# Update KServe
kubectl apply -f https://github.com/kserve/kserve/releases/download/v0.12.0/kserve.yaml

# Update monitoring stack
helm upgrade prometheus prometheus-community/kube-prometheus-stack \
  -n monitoring \
  --version 45.0.0 \
  --reuse-values
```

### Database Maintenance (Third Tuesday, 2am EST)

**Duration**: 1-2 hours
**Maintenance Window**: 2am-4am EST

```bash
# Pre-maintenance checks
aws rds describe-db-instances --db-instance-identifier mlops-platform-production-mlflow

# Enable maintenance mode (redirect traffic)
kubectl scale deployment platform-api -n mlops-platform --replicas=0
kubectl apply -f maintenance-page.yaml

# Perform maintenance
# 1. Create snapshot
SNAPSHOT_ID="mlops-mlflow-$(date +%Y%m%d-%H%M)"
aws rds create-db-snapshot \
  --db-instance-identifier mlops-platform-production-mlflow \
  --db-snapshot-identifier $SNAPSHOT_ID

# 2. Apply patches (if needed)
aws rds modify-db-instance \
  --db-instance-identifier mlops-platform-production-mlflow \
  --apply-immediately \
  --preferred-maintenance-window "tue:02:00-tue:04:00"

# 3. Vacuum database
kubectl exec -it mlops-postgres-client -n mlops-platform -- \
  psql -h <RDS-ENDPOINT> -U mlops_admin -d mlflow -c "VACUUM ANALYZE;"

# 4. Reindex
kubectl exec -it mlops-postgres-client -n mlops-platform -- \
  psql -h <RDS-ENDPOINT> -U mlops_admin -d mlflow -c "REINDEX DATABASE mlflow;"

# Post-maintenance
kubectl scale deployment platform-api -n mlops-platform --replicas=3
kubectl delete -f maintenance-page.yaml

# Verify
curl https://api.mlops-platform.com/health
```

---

## Backup and Recovery

### Automated Backups

#### RDS Backups

```bash
# RDS automated backups (configured in Terraform)
# - Daily snapshots at 3am EST
# - 7-day retention
# - Cross-region replication to us-west-2

# Verify backup status
aws rds describe-db-snapshots \
  --db-instance-identifier mlops-platform-production-mlflow \
  --snapshot-type automated

# Manual backup
aws rds create-db-snapshot \
  --db-instance-identifier mlops-platform-production-mlflow \
  --db-snapshot-identifier manual-$(date +%Y%m%d-%H%M)
```

#### S3 Versioning and Lifecycle

```bash
# Enable versioning (already configured)
aws s3api get-bucket-versioning --bucket mlops-platform-production-models

# Lifecycle policy for cost optimization
cat > lifecycle-policy.json << EOF
{
  "Rules": [
    {
      "Id": "Archive old model versions",
      "Status": "Enabled",
      "Transitions": [
        {
          "Days": 90,
          "StorageClass": "STANDARD_IA"
        },
        {
          "Days": 180,
          "StorageClass": "GLACIER"
        }
      ],
      "NoncurrentVersionTransitions": [
        {
          "NoncurrentDays": 30,
          "StorageClass": "STANDARD_IA"
        }
      ]
    }
  ]
}
EOF

aws s3api put-bucket-lifecycle-configuration \
  --bucket mlops-platform-production-models \
  --lifecycle-configuration file://lifecycle-policy.json
```

#### Application State Backup

```bash
# Backup Kubernetes resources
kubectl get all -A -o yaml > k8s-backup-$(date +%Y%m%d).yaml
aws s3 cp k8s-backup-$(date +%Y%m%d).yaml s3://mlops-platform-production-backups/k8s/

# Backup ConfigMaps and Secrets (encrypted)
kubectl get configmaps -A -o yaml > configmaps-backup-$(date +%Y%m%d).yaml
kubectl get secrets -A -o yaml > secrets-backup-$(date +%Y%m%d).yaml

# Encrypt before upload
gpg --symmetric --cipher-algo AES256 secrets-backup-$(date +%Y%m%d).yaml
aws s3 cp secrets-backup-$(date +%Y%m%d).yaml.gpg s3://mlops-platform-production-backups/secrets/
rm secrets-backup-$(date +%Y%m%d).yaml*
```

### Recovery Procedures

#### Scenario 1: Restore Deleted Model

```bash
# List S3 versions
aws s3api list-object-versions \
  --bucket mlops-platform-production-models \
  --prefix my-model/

# Restore specific version
aws s3api copy-object \
  --copy-source mlops-platform-production-models/my-model/model.pkl?versionId=<version-id> \
  --bucket mlops-platform-production-models \
  --key my-model/model.pkl
```

#### Scenario 2: Restore Database

```bash
# List available snapshots
aws rds describe-db-snapshots \
  --db-instance-identifier mlops-platform-production-mlflow

# Restore from snapshot
RESTORE_ID="mlops-mlflow-restored-$(date +%Y%m%d)"
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier $RESTORE_ID \
  --db-snapshot-identifier <snapshot-id> \
  --db-instance-class db.r5.large

# Wait for restore to complete
aws rds wait db-instance-available --db-instance-identifier $RESTORE_ID

# Update application to point to restored database
kubectl set env deployment/mlflow \
  -n mlops-platform \
  DB_HOST=$(aws rds describe-db-instances --db-instance-identifier $RESTORE_ID --query 'DBInstances[0].Endpoint.Address' --output text)

# Verify
kubectl exec -it mlflow-0 -n mlops-platform -- \
  psql -h <NEW-ENDPOINT> -U mlops_admin -d mlflow -c "SELECT COUNT(*) FROM experiments;"
```

#### Scenario 3: Disaster Recovery (Full Region Failure)

```bash
# DR runbook for full region failover
cd disaster-recovery/

# 1. Activate DR region (us-west-2)
export AWS_REGION=us-west-2

# 2. Restore infrastructure from backups
terraform init -backend-config=backend-dr.conf
terraform apply -var-file=dr.tfvars

# 3. Restore RDS from latest snapshot
# (Cross-region snapshot replication already configured)
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier mlops-platform-production-mlflow-dr \
  --db-snapshot-identifier <latest-snapshot-in-dr-region>

# 4. Sync S3 data
aws s3 sync s3://mlops-platform-production-models s3://mlops-platform-dr-models

# 5. Deploy applications
kubectl apply -k kubernetes/overlays/dr/

# 6. Update DNS to point to DR region
aws route53 change-resource-record-sets \
  --hosted-zone-id $HOSTED_ZONE_ID \
  --change-batch file://dns-failover.json

# 7. Verify DR environment
./scripts/verify-dr-environment.sh
```

---

## Scaling Operations

### Horizontal Pod Autoscaling (HPA)

```bash
# View HPA status
kubectl get hpa -A

# MLflow autoscaling
kubectl autoscale deployment mlflow \
  -n mlops-platform \
  --cpu-percent=70 \
  --min=3 \
  --max=10

# Platform API autoscaling
kubectl autoscale deployment platform-api \
  -n mlops-platform \
  --cpu-percent=70 \
  --memory-percent=80 \
  --min=3 \
  --max=15
```

### Cluster Autoscaling

```bash
# Check Cluster Autoscaler status
kubectl logs -n kube-system deployment/cluster-autoscaler

# View autoscaler decisions
kubectl describe cm cluster-autoscaler-status -n kube-system

# Manually adjust node group size (temporary)
aws autoscaling set-desired-capacity \
  --auto-scaling-group-name eksctl-mlops-platform-production-nodegroup-compute-nodes \
  --desired-capacity 5
```

### Database Scaling

```bash
# Vertical scaling (instance type change)
aws rds modify-db-instance \
  --db-instance-identifier mlops-platform-production-mlflow \
  --db-instance-class db.r5.xlarge \
  --apply-immediately

# Read replica for read-heavy workloads
aws rds create-db-instance-read-replica \
  --db-instance-identifier mlops-mlflow-read-replica \
  --source-db-instance-identifier mlops-platform-production-mlflow \
  --db-instance-class db.r5.large

# Update application to use read replica
kubectl set env deployment/mlflow \
  -n mlops-platform \
  DB_READ_HOST=<read-replica-endpoint>
```

---

## Upgrade Procedures

See `deployment-runbook.md` Phase 2, Step 2.6 for detailed upgrade procedures.

### Zero-Downtime Deployment Strategy

```bash
# Rolling update with readiness checks
kubectl set image deployment/platform-api \
  -n mlops-platform \
  platform-api=<new-image>:v2.0.0 \
  --record

# Monitor rollout
kubectl rollout status deployment/platform-api -n mlops-platform

# Rollback if issues
kubectl rollout undo deployment/platform-api -n mlops-platform
```

---

## Monitoring and Alerting

### Key Dashboards

1. **Platform Overview** - `http://grafana.mlops-platform.com/d/platform-overview`
2. **Model Serving** - `http://grafana.mlops-platform.com/d/model-serving`
3. **Cost Dashboard** - `http://grafana.mlops-platform.com/d/cost-tracking`
4. **Security Dashboard** - `http://grafana.mlops-platform.com/d/security-events`

### Alert Routing

```yaml
# alertmanager-config.yaml
route:
  receiver: 'slack-general'
  group_by: ['alertname', 'cluster', 'service']
  group_wait: 10s
  group_interval: 5m
  repeat_interval: 4h
  routes:
    - match:
        severity: critical
      receiver: 'pagerduty'
      continue: true

    - match:
        severity: warning
      receiver: 'slack-warnings'

    - match:
        alert_type: cost
      receiver: 'slack-finops'

receivers:
  - name: 'pagerduty'
    pagerduty_configs:
      - service_key: '<pagerduty-key>'

  - name: 'slack-general'
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/...'
        channel: '#mlops-alerts'

  - name: 'slack-warnings'
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/...'
        channel: '#mlops-warnings'
```

---

## Incident Response

### Severity Definitions

| Severity | Description | Response Time | Examples |
|----------|-------------|---------------|----------|
| **P1 - Critical** | Service down, data loss | <15 min | API unavailable, database corruption |
| **P2 - High** | Degraded service, SLO breach | <1 hour | High latency, partial outage |
| **P3 - Medium** | Minor issues, no user impact | <4 hours | Single pod failure, slow query |
| **P4 - Low** | Cosmetic issues, future concerns | <24 hours | Documentation updates, monitoring gaps |

### Incident Response Workflow

```bash
# 1. Acknowledge incident
pagerduty-cli acknowledge --incident-key <key>

# 2. Create incident channel
slack-cli create-channel mlops-incident-$(date +%Y%m%d-%H%M)

# 3. Start incident log
cat > incident-$(date +%Y%m%d-%H%M).md << EOF
# Incident Response Log

**Incident ID**: INC-$(date +%Y%m%d-%H%M)
**Severity**: P1
**Start Time**: $(date -u +%Y-%m-%dT%H:%M:%SZ)
**On-Call Engineer**: $USER

## Timeline

$(date +%H:%M) - Incident detected
$(date +%H:%M) - Investigation started

## Actions Taken

- [ ] Identified root cause
- [ ] Applied mitigation
- [ ] Verified resolution
- [ ] Updated stakeholders

## Root Cause

TBD

## Resolution

TBD
EOF
```

---

## Cost Management

### Daily Cost Tracking

```bash
# Get yesterday's cost
aws ce get-cost-and-usage \
  --time-period Start=$(date -d yesterday +%Y-%m-%d),End=$(date +%Y-%m-%d) \
  --granularity DAILY \
  --metrics UnblendedCost

# Set up budget alert
aws budgets create-budget \
  --account-id $AWS_ACCOUNT_ID \
  --budget file://budget-alert.json
```

### Cost Allocation Tags

```bash
# Tag all resources
for resource in $(aws resourcegroupstaggingapi get-resources --resource-type-filters ec2:instance eks:cluster rds:db | jq -r '.ResourceTagMappingList[].ResourceARN'); do
  aws resourcegroupstaggingapi tag-resources \
    --resource-arn-list $resource \
    --tags CostCenter=Engineering,Project=MLOps,Environment=Production
done
```

---

## Security Operations

### Access Reviews (Monthly)

```bash
# Review IAM users with access
aws iam list-users

# Check for unused access keys
aws iam list-access-keys --user-name <username>

# Review Kubernetes RBAC
kubectl get rolebindings,clusterrolebindings -A -o wide
```

### Compliance Audits

```bash
# Generate compliance report
aws securityhub get-compliance-summary

# Check AWS Config compliance
aws configservice describe-compliance-by-config-rule
```

---

## Maintenance Windows

### Scheduled Maintenance

| Activity | Frequency | Window | Duration |
|----------|-----------|--------|----------|
| **Database maintenance** | Monthly | 3rd Tuesday, 2am-4am EST | 2 hours |
| **EKS upgrades** | Quarterly | Saturday, 2am-6am EST | 4 hours |
| **Security patching** | Monthly | 2nd Wednesday, 2am-4am EST | 2 hours |

### Emergency Maintenance

For emergency maintenance outside scheduled windows:

1. Create emergency change request
2. Notify stakeholders (email + Slack) with 2-hour notice minimum
3. Update status page
4. Execute maintenance with rollback plan ready
5. Post-maintenance validation
6. Post-mortem within 48 hours

---

**End of Operations Runbook**

For deployment procedures, see `deployment-runbook.md`.
For troubleshooting, see `troubleshooting-runbook.md`.
