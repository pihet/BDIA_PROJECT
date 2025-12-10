# EKS 배포 가이드

Docker Hub에 푸시한 이미지(`9sujeong10/backend:latest`, `9sujeong10/frontend:latest`)를 AWS EKS에 배포하는 가이드입니다.

## 📋 사전 준비사항

### 1. 필수 도구 설치

#### AWS CLI
```bash
# Windows (Chocolatey)
choco install awscli

# 또는 직접 다운로드
# https://aws.amazon.com/cli/
```

#### kubectl
```bash
# Windows (Chocolatey)
choco install kubernetes-cli

# 또는 직접 다운로드
# https://kubernetes.io/docs/tasks/tools/
```

#### eksctl (EKS 클러스터 생성용)
```bash
# Windows (Chocolatey)
choco install eksctl

# 또는 직접 다운로드
# https://github.com/weaveworks/eksctl/releases
```

### 2. AWS 자격 증명 설정

```bash
aws configure
# AWS Access Key ID 입력
# AWS Secret Access Key 입력
# Default region: ap-northeast-2 (서울)
# Default output format: json
```

## 🚀 단계별 배포 가이드

### Step 1: EKS 클러스터 생성

```bash
# 기본 클러스터 생성 (약 15-20분 소요)
eksctl create cluster \
  --name busan-project \
  --region ap-northeast-2 \
  --nodegroup-name standard-workers \
  --node-type t3.medium \
  --nodes 2 \
  --nodes-min 1 \
  --nodes-max 3 \
  --managed

# 또는 더 간단하게
eksctl create cluster --name busan-project --region ap-northeast-2
```

### Step 2: 클러스터 연결

```bash
# kubeconfig 업데이트
aws eks update-kubeconfig --name busan-project --region ap-northeast-2

# 연결 확인
kubectl get nodes
```

### Step 3: Secrets 생성

**⚠️ 중요: `backend-secrets.yaml` 파일을 수정하여 실제 데이터베이스 정보를 입력하세요!**

```bash
# 파일 수정 후
kubectl apply -f k8s/backend-secrets.yaml

# 확인
kubectl get secrets backend-secrets
```

### Step 4: Backend 배포

```bash
# 배포
kubectl apply -f k8s/backend-deployment.yaml

# 상태 확인
kubectl get pods -l app=backend
kubectl get svc backend-service

# 로그 확인
kubectl logs -l app=backend --tail=50
```

### Step 5: Frontend 배포

```bash
# 배포
kubectl apply -f k8s/frontend-deployment.yaml

# 상태 확인
kubectl get pods -l app=frontend
kubectl get svc frontend-service

# 로그 확인
kubectl logs -l app=frontend --tail=50
```

### Step 6: Ingress 설정 (선택사항)

외부 도메인으로 접근하려면 Ingress를 설정하세요.

```bash
# ALB Ingress Controller 설치 (AWS Load Balancer Controller)
kubectl apply -f https://github.com/kubernetes-sigs/aws-load-balancer-controller/releases/download/v2.7.0/v2_7_0_full.yaml

# Ingress 배포
kubectl apply -f k8s/ingress.yaml

# Ingress 상태 확인
kubectl get ingress
```

## 🔍 유용한 명령어

### Pod 관리
```bash
# 모든 Pod 확인
kubectl get pods

# 특정 Pod 상세 정보
kubectl describe pod <pod-name>

# Pod 로그 확인
kubectl logs <pod-name>
kubectl logs -l app=backend --tail=100 -f  # 실시간 로그

# Pod에 접속 (디버깅)
kubectl exec -it <pod-name> -- /bin/sh
```

### Deployment 관리
```bash
# Deployment 상태 확인
kubectl get deployments

# Deployment 스케일 조정
kubectl scale deployment backend-deployment --replicas=3

# 이미지 업데이트 후 재배포
kubectl set image deployment/backend-deployment backend=9sujeong10/backend:latest
kubectl rollout restart deployment/backend-deployment

# 롤백
kubectl rollout undo deployment/backend-deployment
```

### Service 확인
```bash
# 모든 Service 확인
kubectl get svc

# LoadBalancer External IP 확인
kubectl get svc frontend-service

# Port Forwarding (로컬에서 테스트)
kubectl port-forward svc/backend-service 8000:80
kubectl port-forward svc/frontend-service 3000:80
```

## 🌐 접근 방법

### 1. LoadBalancer를 통한 접근

```bash
# Frontend Service의 External IP 확인
kubectl get svc frontend-service

# 출력 예시:
# NAME               TYPE           CLUSTER-IP      EXTERNAL-IP     PORT(S)
# frontend-service   LoadBalancer    10.100.x.x      x.x.x.x         80:xxxxx/TCP

# 브라우저에서 http://x.x.x.x 접속
```

### 2. Port Forwarding (로컬 테스트)

```bash
# Backend 접근
kubectl port-forward svc/backend-service 8000:80
# http://localhost:8000 접속

# Frontend 접근
kubectl port-forward svc/frontend-service 3000:80
# http://localhost:3000 접속
```

### 3. Ingress를 통한 도메인 접근

도메인을 설정하고 Ingress를 사용하면:
- `http://yourdomain.com` → Frontend
- `http://api.yourdomain.com` → Backend

## 🔒 보안 주의사항

1. **Secrets 관리**
   - 실제 운영 환경에서는 AWS Secrets Manager 사용 권장
   - 또는 External Secrets Operator 사용

2. **데이터베이스**
   - RDS 사용 권장 (Pod 내부 DB는 데이터 손실 위험)
   - VPC 내부에서만 접근 가능하도록 Security Group 설정

3. **네트워크 보안**
   - Backend Service는 ClusterIP로 내부 접근만 허용
   - Frontend만 LoadBalancer로 외부 노출

## 💰 비용 최적화

1. **Auto Scaling**
   ```bash
   # Horizontal Pod Autoscaler 설정
   kubectl autoscale deployment backend-deployment --cpu-percent=70 --min=1 --max=5
   ```

2. **클러스터 관리**
   - 개발 환경: 필요시에만 클러스터 실행
   - 운영 환경: Spot Instances 사용 고려

3. **리소스 제한**
   - 적절한 requests/limits 설정으로 과도한 리소스 사용 방지

## 🧹 정리 (삭제)

```bash
# Deployment 삭제
kubectl delete -f k8s/backend-deployment.yaml
kubectl delete -f k8s/frontend-deployment.yaml

# Secrets 삭제
kubectl delete -f k8s/backend-secrets.yaml

# Ingress 삭제
kubectl delete -f k8s/ingress.yaml

# 클러스터 삭제
eksctl delete cluster --name busan-project --region ap-northeast-2
```

## 📝 체크리스트

배포 전 확인사항:
- [ ] Docker Hub에 이미지 푸시 완료
- [ ] AWS 자격 증명 설정 완료
- [ ] EKS 클러스터 생성 완료
- [ ] kubectl 연결 확인 완료
- [ ] backend-secrets.yaml에 실제 DB 정보 입력
- [ ] Backend 배포 및 정상 동작 확인
- [ ] Frontend 배포 및 정상 동작 확인
- [ ] 외부 접근 테스트 완료

## 🆘 문제 해결

### Pod가 시작되지 않는 경우
```bash
kubectl describe pod <pod-name>
kubectl logs <pod-name>
```

### 이미지를 가져올 수 없는 경우
- Docker Hub 이미지가 public인지 확인
- 또는 ImagePullSecrets 설정 필요

### 데이터베이스 연결 실패
- RDS Security Group에서 EKS 노드 보안 그룹 허용 확인
- 데이터베이스 URL 형식 확인


