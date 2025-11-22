"""
로컬 쿠버네티스에서 Spark 스트림 잡을 트리거하는 DAG.
- 이미지: spark-stream:local
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

DEFAULT_KAFKA_BOOTSTRAP = "kafka-headless-service.default.svc.cluster.local:9092"
DEFAULT_KAFKA_TOPIC = "mariadb.fulfillment.inventory_db.products"
DEFAULT_JDBC_URL = (
    "jdbc:mariadb://mariadb-internal-service.default.svc.cluster.local:3306/"
    "inventory_db?sessionVariables=sql_mode='ANSI_QUOTES'&useUnicode=true&characterEncoding=UTF-8"
)
DEFAULT_CHECKPOINT = "/opt/checkpoints/kafka_to_db"

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
    dag_id="k8s_spark_stream_processor",
    default_args=default_args,
    # 주기 실행 설정 (1분마다 실행)
    # 다른 주기: "*/5 * * * *" (5분마다), "0 * * * *" (매시간), None (수동 실행)
    schedule="*/1 * * * *",  # 1분마다 실행
    catchup=False,
    tags=["spark", "kafka", "kubernetes"],
    description="Kafka에서 CDC 이벤트를 읽어 MariaDB cdc_products_log에 저장하는 Spark 스트리밍 Job",
) as dag:
    run_stream_processor = KubernetesPodOperator(
        task_id="run_stream_processor",
        name="spark-stream-processor",
        namespace="airflow",
        image="spark-stream:local",
        is_delete_operator_pod=False,
        get_logs=True,
        secrets=[mariadb_password_secret],
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


