# 설치

### CRD

```bash
kubectl apply -f https://github.com/strimzi/strimzi-kafka-operator/releases/download/0.47.0/strimzi-crds-0.47.0.yaml
```

### Kafka Kubernetes Operator 설치

```bash
/c/Users/user/Desktop/git/bin/windows-amd64/helm install my-strimzi-kafka-operator oci://quay.io/strimzi-helm/strimzi-kafka-operator -n kafka-kubernetes-operator --create-namespace --version 0.47.0
```

### Kafka 배포

```bash
kubectl apply -f kafka_cluster.yaml -n kafka-kubernetes-operator
kubectl apply -f broker.yaml -n kafka-kubernetes-operator
kubectl apply -f controller.yaml -n kafka-kubernetes-operator
```


# 삭제

```bash
kubectl delete -f kafka_cluster.yaml -n kafka-kubernetes-operator
kubectl delete -f broker.yaml -n kafka-kubernetes-operator
kubectl delete -f controller.yaml -n kafka-kubernetes-operator
helm delete my-strimzi-kafka-operator -n kafka-kubernetes-operator
kubectl delete -f https://github.com/strimzi/strimzi-kafka-operator/releases/download/0.47.0/strimzi-crds-0.47.0.yaml
kubectl delete -f https://github.com/strimzi/strimzi-kafka-operator/releases/download/0.47.0/strimzi-crds-0.47.0.yaml
```