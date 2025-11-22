"""
로컬 Docker/Airflow 환경에서만 사용하는 DB -> Kafka -> Spark 파이프라인 DAG.
- KubernetesExecutor/PodOperator 기반이 아니며, AWS EKS 이전 시에는 사용하지 않음.
- AWS 로 전환하면 `k8s_spark_stream_processor` DAG 을 확장하거나
  MWAA/Managed Workflows 로 마이그레이션.
"""
import os
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator

# Dockerfile에서 설정한 환경 변수를 가져옵니다.
JAVA_HOME = os.environ.get("JAVA_HOME", "/usr/lib/jvm/java-17-openjdk-amd64")

# Airflow DAG의 기본 설정
default_args = {
    'owner': 'wjdcks',
    'start_date': datetime(2025, 11, 11),
    'retries': 1,
    'retry_delay': timedelta(minutes=1),
}

with DAG(
    dag_id='spark_kafka_pipeline_v1',
    default_args=default_args,
    schedule='@daily',
    catchup=False
) as dag:

    # Task 1: Python Producer (DB -> Kafka)
    # [수정] 'conda run' 제거
    # [수정] 파일 경로를 호스트(/home/wjdcks/...)가 아닌 컨테이너 내부(/opt/final_pj/...)로 변경
    task_produce_to_kafka = BashOperator(
        task_id='run_db_producer',
        bash_command='python /opt/final_pj/db_producer.py'
    )

    # Task 2: Spark Consumer (Kafka -> Spark -> MariaDB)
    # [수정] BashOperator 대신 SparkSubmitOperator 사용 (인프라 테스트에서 검증됨)
    task_consume_with_spark = SparkSubmitOperator(
        task_id='run_spark_processor',
        conn_id='spark_default', # UI에서 'local[*]'로 설정한 연결 사용
        
        # [수정] Spark 작업 파일 경로를 컨테이너 내부 경로로 변경
        application='/opt/final_pj/stream_processor.py',
        
        # [수정] Spark 및 Scala 버전(3.4.1, 2.12)을 Dockerfile과 일치시킴
        packages='org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.1',
        
        # [수정] Jar 파일 경로를 컨테이너 내부 경로로 변경
        jars='/opt/drivers/mariadb-java-client-3.4.1.jar',
        
        # Spark가 Java를 찾도록 환경 변수 전달
        env_vars={"JAVA_HOME": JAVA_HOME},
        
        # 로컬 모드로 실행 (UI의 conn_id 설정이 덮어쓸 수 있으나 명시적으로 지정)
        conf={"spark.master": "local[*]"},
    )

    # 작업 순서 정의: 
    # 1번(Producer) Task가 성공해야(>>) 2번(Consumer) Task가 실행됩니다.
    task_produce_to_kafka >> task_consume_with_spark