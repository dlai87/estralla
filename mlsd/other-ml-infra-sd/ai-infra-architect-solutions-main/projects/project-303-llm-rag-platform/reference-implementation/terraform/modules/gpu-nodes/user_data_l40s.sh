#!/bin/bash
# User data script for L40S GPU nodes
# Installs CUDA drivers, container runtime, and optimizes for LLM inference

set -e

# Variables (rendered by terraform templatefile)
CLUSTER_NAME="${cluster_name}"
CUDA_VERSION="${cuda_version}"
REGION=$(curl -s http://169.254.169.254/latest/meta-data/placement/region)

echo "Setting up L40S GPU node for cluster: $CLUSTER_NAME"

# Update system
yum update -y

# Install CUDA drivers
echo "Installing CUDA $CUDA_VERSION drivers..."
distribution=$(. /etc/os-release;echo $ID$VERSION_ID | sed -e 's/\.//g')
wget https://developer.download.nvidia.com/compute/cuda/repos/$distribution/x86_64/cuda-keyring-1.1-1.noarch.rpm
rpm -i cuda-keyring-1.1-1.noarch.rpm
yum install -y cuda-$CUDA_VERSION

# Install NVIDIA container toolkit
echo "Installing NVIDIA container toolkit..."
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.repo | \
  tee /etc/yum.repos.d/nvidia-container-toolkit.repo
yum install -y nvidia-container-toolkit
nvidia-ctk runtime configure --runtime=containerd

# Configure containerd for GPU
cat > /etc/containerd/config.toml <<EOF
version = 2
[plugins."io.containerd.grpc.v1.cri".containerd]
  default_runtime_name = "nvidia"
  [plugins."io.containerd.grpc.v1.cri".containerd.runtimes.nvidia]
    runtime_type = "io.containerd.runc.v2"
    [plugins."io.containerd.grpc.v1.cri".containerd.runtimes.nvidia.options]
      BinaryName = "/usr/bin/nvidia-container-runtime"
EOF

systemctl restart containerd

# Optimize GPU settings for LLM inference
echo "Optimizing GPU settings..."
nvidia-smi -pm 1  # Enable persistence mode

# Set GPU power limit (L40S is a 350W card)
nvidia-smi -pl 350

# Configure huge pages for better memory performance
echo "vm.nr_hugepages = 2048" >> /etc/sysctl.conf
sysctl -p

# Set CPU governor to performance
for cpu in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do
  echo performance > $cpu
done

# Install CloudWatch agent for monitoring
wget https://s3.amazonaws.com/amazoncloudwatch-agent/amazon_linux/amd64/latest/amazon-cloudwatch-agent.rpm
rpm -U ./amazon-cloudwatch-agent.rpm

# Configure CloudWatch agent for GPU metrics
cat > /opt/aws/amazon-cloudwatch-agent/etc/config.json <<EOF
{
  "metrics": {
    "namespace": "EKS/LLM",
    "metrics_collected": {
      "nvidia_gpu": {
        "measurement": [
          "utilization_gpu",
          "utilization_memory",
          "temperature_gpu",
          "power_draw",
          "memory_total",
          "memory_used",
          "memory_free"
        ],
        "metrics_collection_interval": 10
      }
    }
  }
}
EOF

/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
  -a fetch-config \
  -m ec2 \
  -s \
  -c file:/opt/aws/amazon-cloudwatch-agent/etc/config.json

# Join EKS cluster
/etc/eks/bootstrap.sh $CLUSTER_NAME \
  --b64-cluster-ca $(aws eks describe-cluster --name $CLUSTER_NAME --region $REGION --query 'cluster.certificateAuthority.data' --output text) \
  --apiserver-endpoint $(aws eks describe-cluster --name $CLUSTER_NAME --region $REGION --query 'cluster.endpoint' --output text) \
  --kubelet-extra-args '--node-labels=nvidia.com/gpu=true,gpu-type=l40s,workload-type=llm-inference'

echo "L40S GPU node setup complete"
