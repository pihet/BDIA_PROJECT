# 설치 순서

```bash
kubectl create namespace mariadb
kubectl create secret generic mariadb-secret --from-env-file=env.db -n mariadb
kubectl apply -f maria_pv.yaml
kubectl apply -f mariadb.yaml
```

# 삭제 순서

```bash
kubectl delete -f mariadb.yaml
kubectl delete -f maria_pv.yaml
kubectl delete secret mariadb-secret -n mariadb
```