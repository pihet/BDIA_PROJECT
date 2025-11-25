# 로컬 Kubernetes에서 Flink 실행 가이드

## 🚀 빠른 시작

### 0. 한번에 끝내기 (권장)

```bash
chmod +x quick-setup.sh
./quick-setup.sh
```

위 스크립트는 다음을 자동으로 처리합니다:
- Docker 실행 여부 확인
- kind 및 Helm 자동 설치 (필요 시)
- kind 클러스터 생성 (`flink-cluster`)
- `setup.sh` 실행으로 Flink 리소스 설치

### 1. 단계별 진행 (원한다면)

```bash
# 1. Docker 설치 및 실행 확인
docker --version && docker ps

# 2. Kubernetes 클러스터 생성 (kind 사용 예시)
kind create cluster --name flink-cluster

# 3. Helm 설치
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# 4. Flink 설치 스크립트 실행
chmod +x setup.sh
./setup.sh
```

⚠️ **중요**: 모든 단계에서 Docker가 실행 중이어야 합니다!

## 사전 요구사항

### 0. Docker 설치 및 실행 (필수! ⚠️)

로컬 Kubernetes 클러스터는 모두 Docker를 기반으로 동작합니다. 먼저 Docker를 설치하고 실행해야 합니다.

#### WSL2 환경에서 Docker 설치

**방법 1: Docker Desktop for Windows 사용 (권장)**
1. [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/) 다운로드 및 설치
2. Docker Desktop 설정에서 **"Use WSL 2 based engine"** 활성화
3. **Settings > Resources > WSL Integration**에서 현재 WSL 배포판 활성화
4. Docker Desktop 실행 후 확인:
   ```bash
   docker --version
   docker ps
   ```

**방법 2: WSL2 내부에서 Docker 직접 설치**
```bash
# Docker 설치
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 현재 사용자를 docker 그룹에 추가
sudo usermod -aG docker $USER

# Docker 서비스 시작
sudo service docker start

# 설치 확인
docker --version
docker ps
```

⚠️ **중요**: Docker Desktop이 실행 중이거나 Docker 서비스가 시작되어 있어야 합니다.

### 1. 필수 도구 설치

- **kubectl**: Kubernetes 클라이언트 (이미 설치됨 ✓)
- **Helm**: Kubernetes 패키지 매니저
- **Kubernetes 클러스터**: 다음 중 하나
  - **minikube** (권장)
  - **kind** (Kubernetes in Docker) - WSL2에서 간단함
  - **k3d** (경량 Kubernetes)
  - **Docker Desktop** (Kubernetes 활성화)

#### Kubernetes 클러스터 도구 설치

**kind 설치 (권장 - 가장 간단)**
```bash
# Linux/WSL2
curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64
chmod +x ./kind
sudo mv ./kind /usr/local/bin/kind

# 클러스터 생성
kind create cluster --name flink-cluster

# 확인
kubectl cluster-info --context kind-flink-cluster
```

**minikube 설치 (대안)**
```bash
# Linux/WSL2
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube

# 클러스터 시작 (Docker 드라이버 사용)
minikube start --driver=docker

# 확인
kubectl cluster-info
```

#### Helm 설치
```bash
# Linux/WSL2
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# 확인
helm version
```

### 2. 리소스 요구사항
⚠️ **주의**: Flink 설정이 매우 높은 리소스를 요구합니다:
- **JobManager**: 8GB 메모리, 4 CPU
- **TaskManager**: 16GB 메모리 × 2개 = 32GB, 8 CPU × 2개 = 16 CPU
- **총 필요 리소스**: 최소 40GB 메모리, 20 CPU

로컬 테스트를 위해서는 리소스를 줄이는 것을 권장합니다.

## 시작 전 확인

다음 명령어로 필수 도구들이 모두 준비되었는지 확인하세요:

```bash
# Docker 확인
docker --version
docker ps  # Docker가 실행 중이어야 함

# kubectl 확인
kubectl version --client

# Kubernetes 클러스터 확인
kubectl cluster-info

# Helm 확인
helm version
```

⚠️ **중요**: Docker가 실행 중이 아니면 Kubernetes 클러스터가 동작하지 않습니다!

## 설치 방법

### 방법 1: 자동 설치 스크립트 사용 (권장)

#### Windows (PowerShell)
```powershell
.\setup.ps1
```

#### Linux/Mac (Bash)
```bash
chmod +x setup.sh
./setup.sh
```

### 방법 2: 수동 설치

#### 1. 네임스페이스 생성
```bash
kubectl create namespace flink-busan
kubectl create namespace flink-kubernetes-operator
```

#### 2. cert-manager 설치
```bash
kubectl apply -f https://github.com/jetstack/cert-manager/releases/download/v1.18.2/cert-manager.yaml
kubectl wait --for=condition=ready pod -l app.kubernetes.io/instance=cert-manager -n cert-manager --timeout=300s
```

#### 3. Helm repository 추가
```bash
helm repo add flink-operator-repo https://archive.apache.org/dist/flink/flink-kubernetes-operator-1.0.1/
helm repo update
```

#### 4. Flink Kubernetes Operator 설치
```bash
helm install flink-kubernetes-operator flink-operator-repo/flink-kubernetes-operator \
  -n flink-kubernetes-operator \
  --create-namespace \
  --wait \
  --timeout=5m
```

#### 5. Flink RBAC 및 ServiceAccount 설정
```bash
kubectl apply -f flink/flink-seviceaccount.yaml
kubectl apply -f flink/flink-rbac.yaml
```

#### 6. Flink 클러스터 배포
```bash
kubectl apply -f flink/flink-session-cluster.yaml
```

## 로컬 테스트를 위한 리소스 조정

현재 설정은 프로덕션 환경을 위한 것입니다. 로컬 테스트를 위해 리소스를 줄이려면 `flink-session-cluster.yaml`을 수정하세요:

```yaml
jobManager:
  replicas: 1
  resource:
    memory: 2G    # 8G → 2G
    cpu: 1        # 4 → 1
taskManager:
  replicas: 1    # 2 → 1
  resource:
    memory: 4G   # 16G → 4G
    cpu: 2       # 8 → 2
```

## 상태 확인

### Pod 상태 확인
```bash
kubectl get pods -n flink-busan
```

### FlinkDeployment 상태 확인
```bash
kubectl get flinkdeployments -n flink-busan
```

### 상세 정보 확인
```bash
kubectl describe flinkdeployment flink-busan-cluster-20 -n flink-busan
```

## Flink Web UI 접근

### Port Forward 설정
```bash
kubectl port-forward -n flink-busan svc/flink-busan-cluster-20-rest 8081:8081
```

브라우저에서 `http://localhost:8081` 접속

## SQL Gateway 배포 (선택사항)

```bash
kubectl apply -f flink/flink-sql-gateway.yaml
```

SQL Gateway 접근:
```bash
kubectl port-forward -n flink-busan svc/sql-gateway-service-20 8083:8083
```

## 문제 해결

### Docker가 실행되지 않는 경우
```bash
# Docker Desktop이 실행 중인지 확인 (Windows)
# 또는 WSL2에서 Docker 서비스 시작
sudo service docker start

# Docker 상태 확인
docker ps

# 권한 문제인 경우
sudo usermod -aG docker $USER
# 그리고 새 터미널에서 다시 시도
```

### kubectl이 클러스터에 연결되지 않는 경우
```bash
# 클러스터 상태 확인
kubectl cluster-info

# kind를 사용한 경우
kubectl cluster-info --context kind-flink-cluster

# minikube를 사용한 경우
minikube status
```

### Pod가 Pending 상태인 경우
리소스 부족일 수 있습니다. 리소스를 줄이거나 클러스터 리소스를 늘리세요.

```bash
kubectl describe pod <pod-name> -n flink-busan
```

### 이미지 Pull 실패
로컬 클러스터에서 외부 이미지를 pull할 수 있는지 확인:
```bash
kubectl run test-pod --image=flink:2.0.1-java17 --rm -it --restart=Never -- /bin/sh
```

### Operator가 설치되지 않는 경우
Helm repository가 올바르게 추가되었는지 확인:
```bash
helm repo list
helm search repo flink-kubernetes-operator
```

## 정리 (Cleanup)

### Flink 리소스 삭제
```bash
kubectl delete -f flink/flink-session-cluster.yaml
kubectl delete -f flink/flink-sql-gateway.yaml
kubectl delete -f flink/flink-rbac.yaml
kubectl delete -f flink/flink-seviceaccount.yaml
helm uninstall flink-kubernetes-operator -n flink-kubernetes-operator
kubectl delete namespace flink-busan
kubectl delete namespace flink-kubernetes-operator
```

### Kubernetes 클러스터 정리

**kind 사용한 경우:**
```bash
kind delete cluster --name flink-cluster
```

**minikube 사용한 경우:**
```bash
minikube stop
minikube delete
```

### Docker 정리 (선택사항)
```bash
# 사용하지 않는 이미지/컨테이너 정리
docker system prune -a
```

