"""
S3 → Kafka → Spark → MariaDB 파이프라인용 DAG
- S3 Source Connector가 Kafka로 전송한 데이터를 Spark가 처리
- 이미지: spark-stream:local (stream_processor_s3.py 포함)
- AWS EKS 배포 시
  * image 를 `<ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com/spark-stream:prod` 로 변경
  * namespace / serviceAccount 가 EKS의 Airflow 네임스페이스와 일치하도록 values.eks.yaml 에서 정의
  * Kafka/MariaDB/S3 엔드포인트는 환경변수 override 로 주입
"""
import os
from datetime import datetime, timedelta

from airflow import DAG
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import KubernetesPodOperator
from airflow.providers.cncf.kubernetes.secret import Secret

# 환경변수로 설정 가능 (로컬/AWS 모두 적용)
# 로컬: 환경변수 미설정 시 기본값 사용
# AWS: 환경변수로 RDS 엔드포인트 또는 외부 DB 주소 설정
DEFAULT_KAFKA_BOOTSTRAP = os.getenv(
    "KAFKA_BOOTSTRAP_SERVERS",
    "kafka-headless-service.default.svc.cluster.local:9092"
)
DEFAULT_KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "s3.products.data")  # S3 Source Connector 토픽

# MariaDB 연결 URL
# 로컬: 외부 MariaDB 사용 시 (예: 172.16.11.114:3307)
# AWS RDS: jdbc:mariadb://<RDS_ENDPOINT>:3306/inventory_db?...
# AWS 외부 MariaDB: jdbc:mariadb://<EXTERNAL_DB_HOST>:<PORT>/inventory_db?...
# 환경변수 MARIADB_JDBC_URL로 오버라이드 가능
DEFAULT_MARIADB_HOST = os.getenv("MARIADB_HOST", "172.16.11.114")
DEFAULT_MARIADB_PORT = os.getenv("MARIADB_PORT", "3307")
DEFAULT_JDBC_URL = os.getenv(
    "MARIADB_JDBC_URL",
    f"jdbc:mariadb://{DEFAULT_MARIADB_HOST}:{DEFAULT_MARIADB_PORT}/"
    "inventory_db?sessionVariables=sql_mode='ANSI_QUOTES'&useUnicode=true&characterEncoding=UTF-8"
)
DEFAULT_CHECKPOINT = os.getenv("CHECKPOINT_DIR", "/opt/checkpoints/s3_kafka_to_db")

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
    "start_date": datetime(2025, 11, 15),
}

mariadb_password_secret = Secret(
    deploy_type="env",
    deploy_target="MARIADB_PASSWORD",
    secret="mariadb-secret",
    key="MYSQL_ROOT_PASSWORD",
)

with DAG(
    dag_id="k8s_spark_stream_processor_s3",
    default_args=default_args,
    # 주기 실행 설정 (1분마다 실행)
    # 다른 주기: "*/5 * * * *" (5분마다), "0 * * * *" (매시간), None (수동 실행)
    schedule="*/1 * * * *",  # 1분마다 실행
    catchup=False,
    tags=["spark", "kafka", "kubernetes", "s3"],
    description="S3에서 Kafka로 전송된 데이터를 읽어 MariaDB cdc_products_log에 저장하는 Spark 스트리밍 Job",
) as dag:
    run_stream_processor = KubernetesPodOperator(
        task_id="run_stream_processor",
        name="spark-stream-processor-s3",
        namespace="airflow",
        image="spark-stream:local",
        is_delete_operator_pod=False,
        get_logs=True,
        secrets=[mariadb_password_secret],
        # stream_processor_s3.py 실행
        cmds=["/opt/spark/bin/spark-submit"],
        arguments=[
            "--jars", "/opt/app/jars/spark-sql-kafka-0-10_2.12-3.5.1.jar,/opt/app/jars/spark-token-provider-kafka-0-10_2.12-3.5.1.jar,/opt/app/jars/kafka-clients-3.4.1.jar,/opt/app/jars/commons-pool2-2.12.0.jar,/opt/app/jars/mariadb-java-client-3.4.1.jar",
            "/opt/app/stream_processor_s3.py"
        ],
        env_vars={
            "CHECKPOINT_DIR": os.getenv("CHECKPOINT_DIR", DEFAULT_CHECKPOINT),
            "KAFKA_BOOTSTRAP_SERVERS": os.getenv(
                "KAFKA_BOOTSTRAP_SERVERS", DEFAULT_KAFKA_BOOTSTRAP
            ),
            "KAFKA_TOPIC": os.getenv("KAFKA_TOPIC", DEFAULT_KAFKA_TOPIC),
            "MARIADB_JDBC_URL": os.getenv("MARIADB_JDBC_URL", DEFAULT_JDBC_URL),
            "MARIADB_USERNAME": os.getenv("MARIADB_USERNAME", "root"),
        },
    )


