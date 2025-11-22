# Car DB → Kafka → Spark → Inventory DB 파이프라인 실행 가이드

## 실행 순서 요약 (Docker → Kubernetes 흐름)

### 1. **MariaDB 준비:** 외부 MariaDB(172.16.11.114:3307)를 기본 사용
**로컬 StatefulSet은 테스트용**
- **Secret 생성** → `kubectl apply -f k8s/mariadb-secret.yaml`
- **StatefulSet 배포** (필요 시) → `kubectl apply -f k8s/mariadb-statefulset.yaml`
- **Pod/서비스 상태 확인** → `kubectl get pods,svc -l app=mariadb`
- **외부 DB 접속 테스트** → `mysql -h 172.16.11.114 -P 3307 -u root -p`

### 2. **Kafka 준비:** Kafka StatefulSet과 Connect가 배포되어 있다는 가정
- **Pod 상태 확인** → `kubectl get pods -l app=kafka`
- **car.uservehicle 토픽 생성/확인** → Kafka CLI 또는 REST API로 확인
- **car.driving_session 토픽 생성/확인** → 동일

### 3. **Spark 이미지 빌드:** spark-stream/Dockerfile 기반으로 spark-stream:local 생성
**Kafka/MariaDB 커넥터 JAR과 stream_processor_car.py 포함**
```bash
# 현재 폴더에서 빌드 (Dockerfile이 이미 있음)
docker build -t spark-stream:local .
docker images | grep spark-stream
```

### 4. **Airflow 이미지 빌드 및 배포:** airflow-k8s/Dockerfile로 airflow-k8s:local 빌드
```bash
# airflow 네임스페이스 생성
kubectl create namespace airflow

# Secret/ConfigMap 생성
kubectl apply -f k8s/mariadb-secret.yaml

# Helm으로 Airflow 설치 (values.local.yaml 사용)
helm repo add apache-airflow https://airflow.apache.org
helm install airflow apache-airflow/airflow \
  --namespace airflow \
  --values k8s/values.local.yaml \
  --set images.airflow.repository=airflow-k8s \
  --set images.airflow.tag=local

# Web UI 확인: http://localhost:30080
```

### 5. **Car DB Source Connector:** k8s/car-db-connector.json을 REST API로 등록
```bash
# Kafka Connect REST API로 등록
curl -X POST -H "Content-Type: application/json" \
  --data @k8s/car-db-connector.json \
  http://kafka-connect-service:8083/connectors

# 로컬 테스트 시 car_db_producer.py로 직접 메시지 전송 가능
docker-compose exec spark-worker python final_pj/car_db_producer.py
```

### 6. **Airflow DAG 활성화:** k8s_spark_stream_dag_car DAG를 활성화
```bash
# Airflow Web UI에서 unpause (http://localhost:30080)
# 또는 CLI로 활성화
kubectl exec -n airflow deployment/airflow-webserver -- airflow dags unpause k8s_spark_stream_dag_car

# 1분마다 Spark 스트리밍 작업 실행 확인
kubectl get pods -n airflow --watch
```

### 7. **모델 예측 서비스 배포:** model-service/Dockerfile로 빌드 (선택사항)
```bash
# 현재 프로젝트에는 모델 서비스가 별도로 분리되어 있음
# 필요시 model-service 폴더에서 빌드
cd model-service
docker build -t model-service:local .
kubectl apply -f ../k8s/model-service-deployment.yaml
```

### 8. **테스트 & 문제 해결:**
- **Kafka 메시지 송수신 확인** → `kubectl logs -l app=kafka-connect`
- **MariaDB 테이블 조회** → `kubectl exec mariadb-pod -- mysql -u root inventory_db -e "SELECT * FROM uservehicle LIMIT 5"`
- **Spark 스트리밍 로그** → `kubectl logs -n airflow -l dag_id=k8s_spark_stream_dag_car`

### 9. **start_car_pipeline.sh:** 위 과정을 일괄 실행하는 스크립트
```bash
# 로컬 Docker Compose 환경에서 실행
./start_car_pipeline.sh
```

### 10. **부록:** 주요 파일 설명
- **DAG**: `dags/k8s_spark_stream_dag_car.py` - Car DB 파이프라인 워크플로우
- **Spark 스크립트**: `final_pj/stream_processor_car.py` - 실시간 데이터 처리
- **프로듀서**: `final_pj/car_db_producer.py` - 수동 데이터 전송
- **초기화**: `final_pj/init_uservehicle.py` - 초기 데이터 복사

---

## Docker → Kubernetes 흐름 설명

### **Docker부터 시작하는 이유:**
모든 서비스(Spark 스트리밍, Airflow, 모델 예측)가 **Docker 이미지로 패키징**되어 있어야 Kubernetes 배포가 가능합니다.

### **Docker 핵심 포인트:**
- `docker build -t spark-stream:local .`처럼 각 서비스별 Dockerfile로 이미지를 만듭니다
- 이미지에는 실행 스크립트와 필요한 라이브러리를 포함해 **환경 차이 제거**
- 빌드 후 `docker images | grep spark-stream` 등으로 생성 상태 확인

### **Kubernetes 단계:**
- 준비된 이미지를 `kubectl apply`나 Helm으로 배포
- MariaDB, Kafka, Airflow, 모델 서비스 등 모든 워크로드가 **YAML/Helm 차트로 정의**
- **Secret·ConfigMap**으로 민감정보와 설정 전달, **스케줄링·오토리커버리는 K8s가 담당**

### **전체 흐름 정리:**
1. **Docker로 컨테이너 이미지를 만든다**
2. **해당 이미지를 참조하는 Kubernetes 매니페스트를 적용한다**
3. **Airflow DAG이 Spark Pod를 띄워 Kafka→MariaDB 처리를 수행**
4. **문제 발생 시 kubectl logs 명령으로 각 레이어를 점검**

---

## 용어 설명 (docker_pipeline 폴더 기준)

- **Pod**: Kubernetes에서 가장 작은 배포 단위. 컨테이너(들)와 저장소, 네트워크 설정을 묶은 실행 단위로, Spark 작업 Pod, 모델 서비스 Pod 등 모든 워크로드가 Pod 형태로 뜹니다.

- **Deployment**: 동일한 Pod를 원하는 수만큼 유지/롤링업데이트하는 K8s 리소스. 모델 서비스처럼 지속 실행이 필요한 앱에 사용합니다.

- **StatefulSet**: 상태를 가진 Pod를 고정 이름/스토리지로 관리하는 리소스. MariaDB 같은 DB에 사용합니다.

- **Service**: Pod에 안정적인 접근 주소를 제공하는 K8s 오브젝트. ClusterIP/NodePort 등을 통해 MariaDB, Airflow Web, Kafka 등을 노출합니다.

- **ConfigMap**: 환경설정, DAG 파일 등 민감하지 않은 데이터를 K8s 리소스로 저장. Airflow DAG/Pod 템플릿을 ConfigMap으로 주입합니다.

- **Secret**: 비밀번호·키 같은 민감 정보 저장. 예) mariadb-secret에 DB 루트 비밀번호, Airflow Fernet 키.

- **Helm**: K8s 패키지 매니저. 여러 리소스를 템플릿화한 차트를 `helm install`로 한 번에 배포. Airflow는 공식 Helm 차트를 values.local.yaml과 함께 사용.

- **KubernetesPodOperator**: Airflow에서 K8s Pod를 직접 생성해 작업을 실행하는 오퍼레이터. DAG가 Spark 스트리밍 Pod를 띄우는 데 사용.

- **Kafka Connect**: Kafka와 외부 시스템(DB 등)을 연결하는 프레임워크. Debezium Connector를 REST API로 등록하면 DB→Kafka 동기화.

- **JDBC URL**: Spark가 MariaDB에 쓰기 위해 사용하는 표준 DB 접속 문자열 (`jdbc:mariadb://172.16.11.114:3307/inventory_db?sessionVariables=sql_mode='ANSI_QUOTES'`).

- **Checkpoint**: Spark Structured Streaming이 진행 상태를 `spark_checkpoints/` 경로에 저장해 재시작 시 이어서 처리할 수 있게 하는 기능. docker_pipeline/spark_checkpoints/car_db_to_inventory_db 에 저장됩니다.

---

## AWS 전환 체크리스트 (선택사항)

### **로컬 → AWS 환경 변경사항:**
- [ ] MariaDB: 외부 RDS 엔드포인트로 변경 (172.16.11.114 → RDS 엔드포인트)
- [ ] Kafka: 로컬 Kafka → Amazon MSK로 변경
- [ ] Spark: 로컬 실행 → Amazon EMR 또는 EKS에서 실행
- [ ] Airflow: 로컬 → Amazon MWAA로 변경
- [ ] Secret: AWS Secrets Manager로 변경
- [ ] Storage: 로컬 볼륨 → Amazon EFS/S3로 변경

이 가이드를 따라 Car DB 파이프라인을 단계별로 구축하고 실행할 수 있습니다! 🚀
