# 🚗 부산 스마트 차량 관제 시스템
## Biz/Tech Flow Chart

> **작성일**: 2025-12-09  
> **프로젝트**: BDIA_PROJECT  
> **목적**: 실시간 차량 데이터 수집/분석 및 공공안전 서비스 제공

---

## 📌 목차
1. [비즈니스 개요](#1-비즈니스-개요)
2. [전체 아키텍처](#2-전체-아키텍처)
3. [데이터 흐름도](#3-데이터-흐름도)
4. [기술 스택](#4-기술-스택)
5. [주요 프로세스](#5-주요-프로세스)
6. [배포 구성](#6-배포-구성)

---

## 1. 비즈니스 개요

### 1.1 서비스 목표
- 🚨 **안전 운전 지원**: 졸음 운전 실시간 감지 및 경고
- 🏛️ **공공 안전**: 체납 차량 자동 감지 및 추적
- 🔍 **실종자 수색**: 차량 기반 실종자 추적 시스템
- 📊 **데이터 분석**: 운행 패턴 분석 및 교통 정보 제공

### 1.2 주요 비즈니스 프로세스

```
┌─────────────────────────────────────────────────────────────────┐
│                      차량 데이터 수집                            │
│  (차량 IoT 센서 → 운행 정보 → 내/외부 카메라 영상)              │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────────────────┐
│                   실시간 데이터 처리                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ 졸음 운전    │  │ 체납 차량    │  │ 실종자 차량  │         │
│  │ AI 감지      │  │ OCR 감지     │  │ 추적         │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└────────────────┬───────────────────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────────────────┐
│                  알림 및 대응 조치                              │
│  - 운전자 경고 알림                                             │
│  - 관계기관 통보 (경찰청, 지자체)                               │
│  - 대시보드 실시간 모니터링                                      │
└────────────────────────────────────────────────────────────────┘
```

---

## 2. 전체 아키텍처

### 2.1 시스템 아키텍처 다이어그램

```
┌──────────────────────────────────────────────────────────────────────┐
│                         AWS EKS Cluster                               │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │                    Apache Airflow                               │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │  │
│  │  │ ingest_raw   │  │ daily_info   │  │ kafka_to_rds │         │  │
│  │  │ _data        │  │ _update      │  │ _streaming   │         │  │
│  │  │ (매 1분)     │  │ (매일 00:00) │  │ (24/7)       │         │  │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘         │  │
│  │         │                  │                  │                  │  │
│  └─────────┼──────────────────┼──────────────────┼──────────────────┘  │
│            │                  │                  │                     │
│  ┌─────────▼──────────────────▼──────────────────▼──────────────────┐  │
│  │                    Apache Flink (SQL)                            │  │
│  │  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐    │  │
│  │  │  Batch Jobs    │  │  Batch Jobs    │  │ Streaming Job  │    │  │
│  │  │  RDS → Kafka   │  │  RDS → Kafka   │  │  Kafka → RDS   │    │  │
│  │  └────────┬───────┘  └────────┬───────┘  └────────┬───────┘    │  │
│  └───────────┼──────────────────┬─┼──────────────────▲──────────────┘  │
│              │                  │ │                  │                 │
│  ┌───────────▼──────────────────▼─▼──────────────────┴──────────────┐  │
│  │                      Apache Kafka                                 │  │
│  │  ┌─────────┐ ┌─────────────┐ ┌──────────┐ ┌─────────────┐       │  │
│  │  │uservehicle│driving_session│drowsy_drive│arrears_      │       │  │
│  │  │         │ │_info         │            │detection     │       │  │
│  │  └─────────┘ └─────────────┘ └──────────┘ └─────────────┘       │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                OCR Processing (HTTP API)                          │  │
│  │  ┌──────────────┐            ┌─────────────────────┐             │  │
│  │  │ ocr_http     │───Ngrok───▶│ External OCR Server │             │  │
│  │  │ _processing  │            │ (번호판 인식 AI)     │             │  │
│  │  │ (매 5분)     │            └─────────────────────┘             │  │
│  │  └──────┬───────┘                                                 │  │
│  └─────────┼─────────────────────────────────────────────────────────┘  │
│            │                                                             │
└────────────┼─────────────────────────────────────────────────────────────┘
             │
             ▼
┌────────────────────────────────────────────────────────────────────┐
│                    Amazon RDS (MariaDB)                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │ uservehicle  │  │ driving_     │  │ vehicle_     │             │
│  │              │  │ session_info │  │ exterior_img │             │
│  └──────────────┘  └──────────────┘  └──────────────┘             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │ drowsy_drive │  │ arrears_     │  │ missing_     │             │
│  │              │  │ detection    │  │ person_info  │             │
│  └──────────────┘  └──────────────┘  └──────────────┘             │
└────────────────────────────────────────────────────────────────────┘
```

---

## 3. 데이터 흐름도

### 3.1 실시간 스트리밍 파이프라인

```
[차량 IoT/센서] 
    │
    ├─▶ [운행 데이터] ──┐
    │                  │
    ├─▶ [내부 카메라]  ├──▶ [RDS 저장]
    │   (졸음 감지)    │        │
    │                  │        │
    └─▶ [외부 카메라]  ┘        │
        (번호판)                │
                                │
                    ┌───────────┴─────────────┐
                    │                         │
                    ▼                         ▼
            [Airflow Scheduler]       [직접 RDS 저장]
                    │
        ┌───────────┼───────────┐
        │           │           │
        ▼           ▼           ▼
    [1분 배치]  [일일 배치]  [5분 배치]
    RDS→Kafka   RDS→Kafka   OCR 처리
        │           │           │
        └───────────┼───────────┘
                    ▼
            [Kafka Topics]
                    │
                    ▼
        [Flink Streaming Job]
            (24/7 실행)
                    │
                    ▼
            [RDS에 재저장]
                    │
                    ▼
        [대시보드/분석/알림]
```

### 3.2 데이터 레이어별 흐름

| 레이어 | 설명 | 데이터 소스 | 처리 방식 |
|--------|------|-------------|----------|
| **수집 (Collection)** | 차량 센서/카메라 데이터 수집 | IoT 디바이스 | 실시간 |
| **적재 (Ingestion)** | RDS 초기 저장 | 차량 앱 → RDS | Push 방식 |
| **변환 (Transform)** | Kafka 스트림 변환 | RDS → Kafka | Flink Batch (1분) |
| **처리 (Processing)** | 실시간 이벤트 처리 | Kafka Topics | Flink Streaming |
| **저장 (Storage)** | 최종 데이터 저장 | Kafka → RDS | Flink Streaming |
| **분석 (Analytics)** | 대시보드/알림 | RDS | BI 도구 |

---

## 4. 기술 스택

### 4.1 인프라 레이어

| 구분 | 기술 | 용도 |
|------|------|------|
| **클라우드** | AWS EKS | Kubernetes 클러스터 호스팅 |
| **컨테이너** | Kubernetes | 마이크로서비스 오케스트레이션 |
| **스토리지** | EBS (gp3) | 영구 볼륨 저장소 |
| **네트워크** | VPC, Load Balancer | 네트워크 격리 및 라우팅 |

### 4.2 데이터 처리 레이어

| 구분 | 기술 | 버전 | 용도 |
|------|------|------|------|
| **메시지 큐** | Apache Kafka | 3.x | 실시간 이벤트 스트리밍 |
| **스트림 처리** | Apache Flink | 1.18+ | SQL 기반 배치/스트리밍 |
| **워크플로우** | Apache Airflow | 2.x | DAG 스케줄링 |
| **데이터베이스** | MariaDB (RDS) | 10.x | 메인 관계형 DB |

### 4.3 애플리케이션 레이어

| 구분 | 기술 | 용도 |
|------|------|------|
| **OCR API** | Ngrok + AI Model | 번호판 인식 |
| **모니터링** | Kafka UI | Kafka 토픽 모니터링 |
| **스케줄러** | Airflow | 배치 작업 관리 |

---

## 5. 주요 프로세스

### 5.1 운행 데이터 수집 프로세스

#### 📝 Workflow: `ingest_raw_data`
- **실행 주기**: 매 1분
- **모드**: Batch
- **처리 내용**:

```python
# Flink SQL: 01_ingest_raw_data.sql
RDS (updated_at 기준) → Kafka Topics

처리 테이블:
├─ uservehicle         (차량/사용자 정보)
├─ driving_session     (운행 세션)
├─ driving_session_info (운행 상세 - GPS, 센서)
├─ drowsy_drive        (졸음 감지 이력)
├─ arrears_detection   (체납 차량 감지)
└─ missing_person_detection (실종자 감지)
```

**플로우**:
```
1. Airflow: 현재 시간 - 1분 계산
2. Flink SQL: WHERE updated_at BETWEEN :start_time AND :end_time
3. Batch Insert: RDS → Kafka (JSON 포맷)
4. Kafka: 각 토픽에 메시지 저장
```

---

### 5.2 일일 정보 갱신 프로세스

#### 📝 Workflow: `daily_info_update`
- **실행 주기**: 매일 00:00 (KST)
- **모드**: Batch
- **처리 내용**:

```python
# Flink SQL: 02_daily_info_update.sql
RDS → Kafka (전체 스냅샷)

처리 테이블:
├─ arrears_info        (체납 차량 마스터 데이터)
└─ missing_person_info (실종자 마스터 데이터)
```

**플로우**:
```
1. 매일 00:00 Airflow 트리거
2. RDS에서 전체 데이터 읽기 (시간 필터 없음)
3. Kafka에 최신 스냅샷 전송
4. 실시간 스트리밍 Job에서 최신 정보로 조인 가능
```

---

### 5.3 실시간 스트리밍 프로세스

#### 📝 Workflow: `kafka_to_rds_streaming`
- **실행 주기**: 수동 실행 (24/7 실행)
- **모드**: Streaming
- **처리 내용**:

```python
# Flink SQL: 03_kafka_to_rds_streaming.sql
Kafka Topics → RDS (실시간)

스트리밍 설정:
- execution.runtime-mode: streaming
- checkpoint interval: 60s
- state backend: rocksdb
- scan.startup.mode: latest-offset
```

**플로우**:
```
1. Kafka Consumer: 각 토픽 구독
2. Flink Streaming: 실시간 데이터 변환
3. JDBC Sink: RDS에 실시간 저장
   - buffer-flush.max-rows: 100
   - buffer-flush.interval: 1s
4. Checkpoint: 60초마다 상태 저장
```

**처리 테이블** (8개):
- uservehicle, driving_session, driving_session_info
- drowsy_drive, arrears_detection, missing_person_detection
- arrears_info, missing_person_info

---

### 5.4 OCR 번호판 인식 프로세스

#### 📝 Workflow: `ocr_http_processing`
- **실행 주기**: 매 5분
- **모드**: HTTP API 호출
- **처리 내용**:

```python
# DAG: ocr_http_processing.py
RDS (vehicle_exterior_image) → OCR API → RDS

처리 로직:
1. RDS에서 processed=0 이미지 조회 (최대 10개)
2. Ngrok HTTP API 호출 (Base64 이미지 전송)
3. OCR 결과 수신 (번호판, 신뢰도)
4. RDS 업데이트 (processed=1)
```

**API Endpoint**:
```
POST https://sherilyn-acerb-wantonly.ngrok-free.dev/ocr/batch

Request:
[
  {
    "image_id": "uuid",
    "session_id": "session_uuid",
    "image_base64": "data:image/jpeg;base64,..."
  }
]

Response:
[
  {
    "image_id": "uuid",
    "status": "success",
    "plate_number": "12가3456",
    "confidence": 0.95
  }
]
```

---

## 6. 배포 구성

### 6.1 Kubernetes Namespace 구조

```
┌─ airflow                 (Apache Airflow)
│  ├─ airflow-scheduler
│  ├─ airflow-webserver
│  ├─ airflow-worker
│  └─ postgresql
│
┌─ flink                   (Apache Flink)
│  ├─ flink-jobmanager
│  ├─ flink-taskmanager
│  └─ sql-gateway-service
│
┌─ kafka-kubernetes-operator (Apache Kafka)
│  ├─ kafka-controller-0
│  ├─ kafka-controller-1
│  ├─ kafka-controller-2
│  └─ kafka-ui
│
└─ mariadb                 (MariaDB)
   ├─ mariadb-0
   └─ pv/pvc (gp3 스토리지)
```

### 6.2 Helm Charts

| 서비스 | Chart | Values 파일 |
|--------|-------|------------|
| Airflow | `apache-airflow/airflow` | `k8s/k8s-example/airflow/airflow-1.18.0/airflow/values.yaml` |
| Flink | Custom YAML | `k8s/k8s-example/flink/flink-session-cluster.yaml` |
| Kafka | Strimzi Operator | `k8s/k8s-example/kafka/kafka_cluster.yaml` |
| MariaDB | Bitnami Chart | `k8s/k8s-example/mariadb/mariadb.yaml` |

### 6.3 배포 순서

```bash
# 1. EKS 클러스터 생성
eksctl create cluster -f k8s/k8s-example/eks/k8s.yaml

# 2. StorageClass 설정 (gp3)
kubectl apply -f k8s/k8s-example/eks/gp3_storageclass.yaml

# 3. MariaDB 배포
kubectl apply -f k8s/k8s-example/mariadb/mariadb.yaml

# 4. Kafka 배포
kubectl apply -f k8s/k8s-example/kafka/kafka_cluster.yaml

# 5. Flink 배포
kubectl apply -f k8s/k8s-example/flink/flink-session-cluster.yaml
kubectl apply -f k8s/k8s-example/flink/flink-sql-gateway.yaml

# 6. Airflow 배포
helm install airflow k8s/k8s-example/airflow/airflow-1.18.0/airflow/

# 7. Kafka UI 배포 (모니터링)
kubectl apply -f k8s/k8s-example/kafka-ui/kafka-ui.yaml
```

---

## 7. 데이터 스키마

### 7.1 주요 테이블

#### 📋 uservehicle (차량/사용자 정보)
| 컬럼 | 타입 | 설명 |
|------|------|------|
| car_id | VARCHAR(255) | PK, 차량 고유 ID |
| age | INT | 운전자 나이 |
| user_sex | ENUM('남','여') | 성별 |
| user_car_brand | VARCHAR(255) | 차량 브랜드 |
| updated_at | TIMESTAMP | 갱신 시간 |

#### 📋 driving_session (운행 세션)
| 컬럼 | 타입 | 설명 |
|------|------|------|
| session_id | VARCHAR(255) | PK, 세션 ID |
| car_id | VARCHAR(255) | FK → uservehicle |
| start_time | TIMESTAMP | 주행 시작 |
| end_time | TIMESTAMP | 주행 종료 |

#### 📋 driving_session_info (운행 상세)
| 컬럼 | 타입 | 설명 |
|------|------|------|
| info_id | UUID | PK |
| session_id | VARCHAR(255) | FK → driving_session |
| app_lat / app_lon | DOUBLE | GPS 좌표 |
| speed | FLOAT | 속도 |
| app_rapid_acc | INT | 급가속 횟수 |
| dt | TIMESTAMP | 기록 시간 |

#### 📋 drowsy_drive (졸음 운전 감지)
| 컬럼 | 타입 | 설명 |
|------|------|------|
| drowsy_id | VARCHAR(64) | PK |
| session_id | VARCHAR(255) | FK → driving_session |
| detected_at | TIMESTAMP | 감지 시간 |
| gaze_closure | INT | 눈 감김 횟수 |
| head_drop | INT | 고개 숙임 횟수 |

#### 📋 vehicle_exterior_image (외부 카메라 이미지)
| 컬럼 | 타입 | 설명 |
|------|------|------|
| image_id | VARCHAR(64) | PK |
| session_id | VARCHAR(255) | FK → driving_session |
| image_base64 | LONGTEXT | Base64 이미지 |
| processed | TINYINT | OCR 처리 여부 (0/1) |
| plate_number | VARCHAR(20) | 인식된 번호판 |

#### 📋 arrears_info (체납 차량 정보)
| 컬럼 | 타입 | 설명 |
|------|------|------|
| car_plate_number | VARCHAR(20) | PK |
| arrears_user_id | VARCHAR(64) | 체납자 ID |
| total_arrears_amount | INT | 체납 금액 |
| notice_count | TINYINT | 고지 횟수 |

#### 📋 arrears_detection (체납 차량 감지)
| 컬럼 | 타입 | 설명 |
|------|------|------|
| detection_id | VARCHAR(64) | PK |
| image_id | VARCHAR(64) | FK → vehicle_exterior_image |
| car_plate_number | VARCHAR(20) | FK → arrears_info |
| detection_success | TINYINT | 감지 성공 여부 |
| detected_lat/lon | DOUBLE | 감지 위치 |

---

## 8. 주요 Kafka 토픽

### 8.1 토픽 목록

| 토픽명 | 파티션 | 설명 | 데이터 주기 |
|--------|--------|------|------------|
| **uservehicle** | 3 | 차량/사용자 정보 | 변경 시 |
| **driving_session** | 3 | 운행 세션 | 시작/종료 시 |
| **driving_session_info** | 6 | 운행 상세 (GPS, 센서) | 실시간 (초 단위) |
| **drowsy_drive** | 3 | 졸음 운전 감지 이벤트 | 감지 시 |
| **arrears_detection** | 3 | 체납 차량 감지 이벤트 | 감지 시 |
| **arrears_info** | 1 | 체납 차량 마스터 | 일일 갱신 |
| **missing_person_detection** | 3 | 실종자 차량 감지 | 감지 시 |
| **missing_person_info** | 1 | 실종자 마스터 | 일일 갱신 |

### 8.2 메시지 포맷 (JSON)

```json
// driving_session_info 예시
{
  "info_id": "550e8400-e29b-41d4-a716-446655440000",
  "session_id": "session_20251209_001",
  "app_lat": 35.1796,
  "app_lon": 129.0756,
  "speed": 45.5,
  "app_rapid_acc": 2,
  "app_weather_status": "맑음",
  "dt": "2025-12-09T14:30:00"
}

// arrears_detection 예시
{
  "detection_id": "det_20251209_001",
  "image_id": "img_20251209_001",
  "car_plate_number": "12가3456",
  "detection_success": 1,
  "detected_lat": 35.1796,
  "detected_lon": 129.0756,
  "detected_time": "2025-12-09T14:30:00"
}
```

---

## 9. 모니터링 및 운영

### 9.1 모니터링 포인트

| 항목 | 도구 | 메트릭 |
|------|------|--------|
| **Kafka 토픽** | Kafka UI | Consumer Lag, 메시지 처리량 |
| **Flink Job** | Flink Dashboard | Checkpoint 성공률, 처리 지연 |
| **Airflow DAG** | Airflow UI | Task 성공률, 실행 시간 |
| **RDS** | CloudWatch | Connection, CPU, IOPS |

### 9.2 알람 설정

```yaml
알람 조건:
  - Kafka Consumer Lag > 10000 메시지
  - Flink Checkpoint 실패 > 3회 연속
  - Airflow DAG 실패
  - RDS CPU > 80% (5분 이상)
  - OCR API 타임아웃 > 10회/시간
```

---

## 10. 비즈니스 KPI

### 10.1 측정 지표

| KPI | 목표 | 측정 방법 |
|-----|------|----------|
| **데이터 처리 지연** | < 5초 | Kafka → RDS 평균 레이턴시 |
| **OCR 정확도** | > 95% | confidence 평균값 |
| **졸음 운전 감지율** | > 90% | 실제 졸음 대비 감지 비율 |
| **체납 차량 적발** | 월 100건+ | arrears_detection 카운트 |
| **시스템 가용성** | 99.9% | Uptime 모니터링 |

---

## 11. 향후 개선 계획

### 11.1 단기 (1-3개월)
- [ ] 실시간 대시보드 구축 (Grafana)
- [ ] 알림 시스템 구축 (Slack, Email)
- [ ] Flink Job 자동 재시작 (Kubernetes CronJob)
- [ ] RDS 읽기 전용 복제본 추가

### 11.2 중기 (3-6개월)
- [ ] ML 모델 정확도 개선 (졸음 감지, OCR)
- [ ] 교통 패턴 분석 대시보드
- [ ] 모바일 앱 연동 (운전자 알림)
- [ ] 데이터 레이크 구축 (S3 + Athena)

### 11.3 장기 (6-12개월)
- [ ] 실시간 교통 예측 모델
- [ ] 다중 지역 확장 (부산 외 지역)
- [ ] Edge Computing 도입 (차량 내 처리)
- [ ] 블록체인 기반 데이터 무결성

---

## 📚 참고 문서

### 설정 파일 위치
- **Flink SQL**: `k8s/flink_sql/flink_sql/*.sql`
- **Airflow DAGs**: `k8s/flink_sql/tests/dags/*.py`
- **MariaDB Schema**: `k8s/flink_sql/mariadb_sql/init_schema.sql`
- **K8s Manifests**: `k8s/k8s-example/*/*.yaml`

### 접속 정보
```bash
# Airflow UI
kubectl port-forward svc/airflow-webserver 8080:8080 -n airflow
# http://localhost:8080

# Flink Dashboard
kubectl port-forward svc/flink-jobmanager 8081:8081 -n flink
# http://localhost:8081

# Kafka UI
kubectl port-forward svc/kafka-ui 8082:8080 -n kafka-kubernetes-operator
# http://localhost:8082
```

---

## 📞 Contact

| 역할 | 담당자 | 연락처 |
|------|--------|--------|
| 프로젝트 관리 | - | - |
| 인프라 | - | - |
| 데이터 엔지니어링 | - | - |
| OCR 모델 개발 | - | - |

---

> **문서 버전**: v1.0  
> **최종 업데이트**: 2025-12-09  
> **작성자**: AI Assistant (Cursor)

