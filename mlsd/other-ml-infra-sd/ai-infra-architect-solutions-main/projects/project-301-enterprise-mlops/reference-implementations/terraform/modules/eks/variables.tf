# Variables for EKS Module

variable "cluster_name" {
  description = "Name of the EKS cluster"
  type        = string
}

variable "kubernetes_version" {
  description = "Kubernetes version"
  type        = string
  default     = "1.27"
  validation {
    condition     = can(regex("^1\\.(2[7-9]|[3-9][0-9])$", var.kubernetes_version))
    error_message = "Kubernetes version must be 1.27 or higher."
  }
}

variable "region" {
  description = "AWS region"
  type        = string
}

variable "vpc_id" {
  description = "ID of the VPC"
  type        = string
}

variable "private_subnet_ids" {
  description = "IDs of private subnets for EKS nodes"
  type        = list(string)
}

variable "public_subnet_ids" {
  description = "IDs of public subnets for EKS load balancers"
  type        = list(string)
}

variable "enable_public_access" {
  description = "Enable public access to EKS API server"
  type        = bool
  default     = false
}

variable "public_access_cidrs" {
  description = "CIDR blocks allowed to access EKS API server publicly"
  type        = list(string)
  default     = []
}

variable "enabled_cluster_log_types" {
  description = "List of control plane logging types to enable"
  type        = list(string)
  default     = ["api", "audit", "authenticator", "controllerManager", "scheduler"]
  validation {
    condition = alltrue([
      for log_type in var.enabled_cluster_log_types :
      contains(["api", "audit", "authenticator", "controllerManager", "scheduler"], log_type)
    ])
    error_message = "Invalid cluster log type. Must be one of: api, audit, authenticator, controllerManager, scheduler."
  }
}

variable "log_retention_days" {
  description = "Number of days to retain cluster logs"
  type        = number
  default     = 90
}

variable "log_kms_key_arn" {
  description = "KMS key ARN for encrypting CloudWatch Logs"
  type        = string
  default     = null
}

variable "node_groups" {
  description = "Configuration for EKS managed node groups"
  type = map(object({
    desired_size         = number
    max_size             = number
    min_size             = number
    instance_types       = list(string)
    capacity_type        = string # ON_DEMAND or SPOT
    disk_size            = number
    labels               = map(string)
    taints               = list(object({
      key    = string
      value  = string
      effect = string
    }))
    bootstrap_arguments  = string
  }))
  default = {
    system = {
      desired_size        = 3
      max_size            = 5
      min_size            = 3
      instance_types      = ["m5.large"]
      capacity_type       = "ON_DEMAND"
      disk_size           = 100
      labels              = { "workload-type" = "system" }
      taints              = []
      bootstrap_arguments = ""
    }
    compute = {
      desired_size        = 2
      max_size            = 20
      min_size            = 0
      instance_types      = ["m5.2xlarge", "m5.4xlarge"]
      capacity_type       = "SPOT"
      disk_size           = 200
      labels              = { "workload-type" = "compute" }
      taints              = []
      bootstrap_arguments = ""
    }
    gpu = {
      desired_size        = 0
      max_size            = 10
      min_size            = 0
      instance_types      = ["g4dn.xlarge", "g4dn.2xlarge"]
      capacity_type       = "SPOT"
      disk_size           = 300
      labels              = { "workload-type" = "gpu" }
      taints = [{
        key    = "nvidia.com/gpu"
        value  = "true"
        effect = "NoSchedule"
      }]
      bootstrap_arguments = "--kubelet-extra-args '--register-with-taints=nvidia.com/gpu=true:NoSchedule'"
    }
  }
}

variable "addon_versions" {
  description = "Versions of EKS addons"
  type = object({
    vpc_cni        = string
    coredns        = string
    kube_proxy     = string
    ebs_csi_driver = string
  })
  default = {
    vpc_cni        = "v1.14.1-eksbuild.1"
    coredns        = "v1.10.1-eksbuild.2"
    kube_proxy     = "v1.27.6-eksbuild.2"
    ebs_csi_driver = "v1.24.0-eksbuild.1"
  }
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}
