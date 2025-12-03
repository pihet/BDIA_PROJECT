# helm repo 추가

```bash
/c/Users/user/Desktop/git/bin/windows-amd64/helm repo add apache-airflow https://airflow.apache.org
/c/Users/user/Desktop/git/bin/windows-amd64/helm update
```

# 네임스페이스 추가

```bash
kubectl create namespace airflow
```

# airflow chart 다운

```bash
/c/Users/user/Desktop/git/bin/windows-amd64/helm  pull apache-airflow/airflow 
```

# airflow chart UP

```bash
/c/Users/user/Desktop/git/bin/windows-amd64/helm install airflow -n airflow ./ --create-namespace
```

# airflow chart remove

```bash
/c/Users/user/Desktop/git/bin/windows-amd64/helm delete airflow -n airflow
```