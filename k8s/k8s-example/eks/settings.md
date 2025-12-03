# IAM 정책 생성 및 서비스 어카운트 생성
eksctl create iamserviceaccount \
  --cluster=busan \
  --namespace=kube-system \
  --name=cluster-autoscaler \
  --attach-policy-arn=arn:aws:iam::aws:policy/AutoScalingFullAccess \
  --override-existing-serviceaccounts \
  --approve \
  --region=ap-northeast-2

# Cluster Autoscaler 설치
kubectl apply -f https://raw.githubusercontent.com/kubernetes/autoscaler/master/cluster-autoscaler/cloudprovider/aws/examples/cluster-autoscaler-autodiscover.yaml

# 클러스터 생성
eksctl create cluster -f k8s.yaml

# 노드 확인
eksctl get nodegroup --cluster busan --region ap-northeast-2 --name spot-workers

# kubeconfig 조회 (OpenLens 등록)
eksctl utils write-kubeconfig --cluster=busan --region=ap-northeast-2

# 노드 추가
eksctl scale nodegroup \
  --cluster=busan \
  --name=spot-workers \
  --nodes=5 \
  --nodes-min=1 \
  --nodes-max=5 \
  --region=ap-northeast-2


# gp2 삭제 또는 기본 해제
kubectl patch storageclass gp2 -p '{"metadata": {"annotations":{"storageclass.kubernetes.io/is-default-class":"false"}}}'
kubectl delete storageclass gp2

# gp3 StorageClass 생성
kubectl apply -f gp3_storageclass.yaml


# 노드 그룹 회수 및 스케일 업

# 1. 더 큰 인스턴스 타입으로 새 Node Group 생성
eksctl create nodegroup \
  --cluster=busan \
  --name=spot-workers-large \
  --instance-types=t3.large,t3a.large,m5.xlarge \
  --spot \
  --nodes=2 \
  --nodes-min=1 \
  --nodes-max=5 \
  --region=ap-northeast-2

# 2. 기존 Node Group의 Pod를 drain
kubectl drain <old-node-name> --ignore-daemonsets --delete-emptydir-data

# 3. 기존 Node Group 삭제
eksctl delete nodegroup \
  --cluster=busan \
  --name=spot-workers \
  --region=ap-northeast-2


# 클러스터 삭제
eksctl delete cluster -f k8s.yaml
