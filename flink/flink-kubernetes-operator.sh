#!/bin/bash

# Flink Kubernetes Operator 설치 스크립트
# Helm을 사용하여 Flink Kubernetes Operator를 설치합니다.
# Operator는 FlinkDeployment 리소스를 관리하여 Flink 클러스터를 자동으로 생성/관리합니다.

set -euo pipefail

HELM_REPO_NAME="${HELM_REPO_NAME:-flink-operator-repo}"
HELM_REPO_URL="${HELM_REPO_URL:-https://archive.apache.org/dist/flink/flink-kubernetes-operator-1.12.1/}"
RELEASE_NAME="${RELEASE_NAME:-flink-kubernetes-operator}"
NAMESPACE="${NAMESPACE:-flink-kubernetes-operator}"

if ! helm repo list | awk 'NR>1 {print $1}' | grep -qx "$HELM_REPO_NAME"; then
  helm repo add "$HELM_REPO_NAME" "$HELM_REPO_URL"
fi
helm repo update

helm upgrade --install "$RELEASE_NAME" "${HELM_REPO_NAME}/flink-kubernetes-operator" \
  -n "$NAMESPACE" \
  --create-namespace \
  --wait \
  --timeout=5m