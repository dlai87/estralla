#!/bin/bash
# EKS node bootstrap user-data, rendered by terraform templatefile().
# The braced placeholders below are terraform variables: cluster_name,
# cluster_ca, cluster_endpoint, and bootstrap_arguments. Everything else
# is plain shell.
set -o xtrace

/etc/eks/bootstrap.sh ${cluster_name} \
  --b64-cluster-ca ${cluster_ca} \
  --apiserver-endpoint ${cluster_endpoint} \
  ${bootstrap_arguments}
