# 기동 순서

```bash
kubectl apply -f https://github.com/jetstack/cert-manager/releases/download/v1.18.2/cert-manager.yaml --insecure-skip-tls-verify
/c/Users/user/Desktop/git/bin/windows-amd64/helm repo add flink-operator-repo https://downloads.apache.org/flink/flink-kubernetes-operator-1.13.0/ 
/c/Users/user/Desktop/git/bin/windows-amd64/helm install flink-kubernetes-operator flink-operator-repo/flink-kubernetes-operator -n flink-kubernetes-operator --create-namespace --insecure-skip-tls-verify  # 실행 (helm 설치 필요)
kubectl create namespace flink
kubectl apply -f flink-rbac.yaml -n flink
kubectl apply -f flink-serviceaccount.yaml -n flink
kubectl apply -f flink-session-cluster.yaml -n flink
kubectl apply -f flink-sql-gateway.yaml -n flink
```


# 삭제

```bash
kubectl delete -f flink-sql-gateway.yaml -n flink
kubectl delete -f flink-session-cluster.yaml -n flink
kubectl delete -f flink-serviceaccount.yaml -n flink
kubectl delete -f flink-rbac.yaml -n flink
kubectl delete namespace flink
/c/Users/user/Desktop/git/bin/windows-amd64/helm delete flink-kubernetes-operator flink-operator-repo/flink-kubernetes-operator -n flink-kubernetes-operator
kubectl delete -f https://github.com/jetstack/cert-manager/releases/download/v1.18.2/cert-manager.yaml
```

## flink 종료 되지 않을 때 

```bash
kubectl patch flinkdeployment -n flink -p '{"metadata": {"finalizers": null}}'--type merge
```


# kubectl delete po flink-kubernetes-operator-5c8c4d7c48-k9sx5 -n flink-kubernetes-operator  --grace-period 0 --force