#!/bin/bash

#!/bin/bash

# 로컬 Kubernetes 클러스터에서 Flink를 설치하기 위한 스크립트
# 사용 전에 다음이 설치되어 있어야 합니다:
# - kubectl
# - Helm
# - Kubernetes 클러스터 (minikube, kind, k3d 등)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
FLINK_DIR="${SCRIPT_DIR}/flink"

echo "=========================================="
echo "Flink Kubernetes 설치 스크립트"
echo "=========================================="

# 1. 네임스페이스 생성
echo "[1/5] 네임스페이스 생성 중..."
kubectl create namespace flink-busan --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace flink-kubernetes-operator --dry-run=client -o yaml | kubectl apply -f -

# 2. cert-manager 설치
echo "[2/5] cert-manager 설치 중..."
bash "${FLINK_DIR}/cert-manager.sh"
echo "cert-manager 설치 완료. Pod가 준비될 때까지 대기 중..."
kubectl wait --for=condition=ready pod -l app.kubernetes.io/instance=cert-manager -n cert-manager --timeout=300s || echo "cert-manager 대기 시간 초과 (계속 진행)"

# 3. Flink Kubernetes Operator 설치
echo "[3/5] Flink Kubernetes Operator 설치 중..."
bash "${FLINK_DIR}/flink-kubernetes-operator.sh"

# 4. Flink RBAC 및 ServiceAccount 설정
echo "[4/5] Flink RBAC 및 ServiceAccount 설정 중..."
kubectl apply -f "${FLINK_DIR}/flink-seviceaccount.yaml"
kubectl apply -f "${FLINK_DIR}/flink-rbac.yaml"

# 5. Flink 클러스터 배포
echo "[5/5] Flink 클러스터 배포 중..."
kubectl apply -f "${FLINK_DIR}/flink-session-cluster.yaml"

echo ""
echo "=========================================="
echo "설치 완료!"
echo "=========================================="
echo ""
echo "다음 명령어로 상태를 확인하세요:"
echo "  kubectl get pods -n flink-busan"
echo "  kubectl get flinkdeployments -n flink-busan"
echo ""
echo "Flink Web UI에 접근하려면:"
echo "  kubectl port-forward -n flink-busan svc/flink-busan-cluster-20-rest 8081:8081"
echo "  브라우저에서 http://localhost:8081 접속"
echo ""
