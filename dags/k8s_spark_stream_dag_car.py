"""
car 데이터베이스 → Kafka → Spark → inventory_db 파이프라인용 DAG
- car DB의 UserVehicle, Driving_Session 테이블 변경사항을 실시간으로 inventory_db로 전송
- Debezium CDC를 통해 Kafka로 전송된 데이터를 Spark가 처리
"""
import os
from datetime import datetime, timedelta

from airflow import DAG
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import KubernetesPodOperator
from airflow.providers.cncf.kubernetes.secret import Secret

# 환경변수로 설정 가능
DEFAULT_KAFKA_BOOTSTRAP = os.getenv(
    "KAFKA_BOOTSTRAP_SERVERS",
    "kafka-internal-service.default.svc.cluster.local:9092"  # ClusterIP 서비스 사용
)

# UserVehicle 테이블용 설정 (Debezium은 테이블명을 소문자로 변환)
DEFAULT_USERVEHICLE_TOPIC = "mariadb.car.car.uservehicle"
DEFAULT_USERVEHICLE_CHECKPOINT = "/opt/checkpoints/car_db_uservehicle"

# Driving_Session 테이블용 설정 (Debezium은 테이블명을 소문자로 변환)
DEFAULT_DRIVING_SESSION_TOPIC = "mariadb.car.car.driving_session"
DEFAULT_DRIVING_SESSION_CHECKPOINT = "/opt/checkpoints/car_db_driving_session"

# MariaDB 연결 URL (inventory_db)
DEFAULT_MARIADB_HOST = os.getenv("MARIADB_HOST", "172.16.11.114")
DEFAULT_MARIADB_PORT = os.getenv("MARIADB_PORT", "3307")
DEFAULT_JDBC_URL = os.getenv(
    "MARIADB_JDBC_URL",
    f"jdbc:mariadb://{DEFAULT_MARIADB_HOST}:{DEFAULT_MARIADB_PORT}/"
    "inventory_db?sessionVariables=sql_mode='ANSI_QUOTES'&useUnicode=true&characterEncoding=UTF-8"
)

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
    dag_id="k8s_spark_stream_processor_car",
    default_args=default_args,
    schedule="*/1 * * * *",  # 1분마다 실행 
    catchup=False,
    tags=["spark", "kafka", "kubernetes", "car-db"],
    description="car DB의 UserVehicle, Driving_Session 테이블 변경사항을 inventory_db로 전송하는 Spark 스트리밍 Job",
) as dag:
    # UserVehicle 테이블 처리
    run_uservehicle_processor = KubernetesPodOperator(
        task_id="run_uservehicle_processor",
        name="spark-stream-processor-uservehicle",
        namespace="default",
        image="spark-stream:local",
        is_delete_operator_pod=False,
        get_logs=True,
        secrets=[mariadb_password_secret],
        cmds=["/opt/spark/bin/spark-submit"],
        arguments=[
            "--jars", "/opt/app/jars/spark-sql-kafka-0-10_2.12-3.5.1.jar,/opt/app/jars/spark-token-provider-kafka-0-10_2.12-3.5.1.jar,/opt/app/jars/kafka-clients-3.4.1.jar,/opt/app/jars/commons-pool2-2.12.0.jar,/opt/app/jars/mariadb-java-client-3.4.1.jar",
            "/opt/app/stream_processor_car.py"
        ],
        env_vars={
            "CHECKPOINT_DIR": os.getenv("CHECKPOINT_DIR", DEFAULT_USERVEHICLE_CHECKPOINT),
            "KAFKA_BOOTSTRAP_SERVERS": os.getenv(
                "KAFKA_BOOTSTRAP_SERVERS", DEFAULT_KAFKA_BOOTSTRAP
            ),
            "KAFKA_TOPIC": os.getenv("KAFKA_TOPIC", DEFAULT_USERVEHICLE_TOPIC),
            "TARGET_TABLE": "uservehicle",  # 소문자 테이블명
            "MARIADB_JDBC_URL": os.getenv("MARIADB_JDBC_URL", DEFAULT_JDBC_URL),
            "MARIADB_USERNAME": os.getenv("MARIADB_USERNAME", "root"),
        },
    )

    # Driving_Session 테이블 처리
    run_driving_session_processor = KubernetesPodOperator(
        task_id="run_driving_session_processor",
        name="spark-stream-processor-driving-session",
        namespace="default",
        image="spark-stream:local",
        is_delete_operator_pod=False,
        get_logs=True,
        secrets=[mariadb_password_secret],
        cmds=["/opt/spark/bin/spark-submit"],
        arguments=[
            "--jars", "/opt/app/jars/spark-sql-kafka-0-10_2.12-3.5.1.jar,/opt/app/jars/spark-token-provider-kafka-0-10_2.12-3.5.1.jar,/opt/app/jars/kafka-clients-3.4.1.jar,/opt/app/jars/commons-pool2-2.12.0.jar,/opt/app/jars/mariadb-java-client-3.4.1.jar",
            "/opt/app/stream_processor_car.py"
        ],
        env_vars={
            "CHECKPOINT_DIR": os.getenv("CHECKPOINT_DIR", DEFAULT_DRIVING_SESSION_CHECKPOINT),
            "KAFKA_BOOTSTRAP_SERVERS": os.getenv(
                "KAFKA_BOOTSTRAP_SERVERS", DEFAULT_KAFKA_BOOTSTRAP
            ),
            "KAFKA_TOPIC": os.getenv("KAFKA_TOPIC", DEFAULT_DRIVING_SESSION_TOPIC),
            "TARGET_TABLE": "driving_session",  # 소문자 테이블명
            "MARIADB_JDBC_URL": os.getenv("MARIADB_JDBC_URL", DEFAULT_JDBC_URL),
            "MARIADB_USERNAME": os.getenv("MARIADB_USERNAME", "root"),
        },
    )

    # 두 작업을 병렬로 실행
    [run_uservehicle_processor, run_driving_session_processor]

