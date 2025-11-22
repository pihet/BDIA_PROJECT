import os
from datetime import datetime
from airflow.decorators import dag
from airflow.operators.bash import BashOperator
from airflow.providers.apache.kafka.operators.produce import ProduceToTopicOperator
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator

# SPARK_HOME 환경 변수 가져오기 (Dockerfile에서 설정함)
SPARK_HOME = os.environ.get("SPARK_HOME", "/opt/spark")
# JAVA_HOME 환경 변수 가져오기 (Dockerfile에서 설정함)
JAVA_HOME = os.environ.get("JAVA_HOME", "/usr/lib/jvm/java-17-openjdk-amd64")

# --- Kafka 프로듀서 함수 정의 (이전과 동일) ---
def kafka_producer_function(**context):
    """
    ProduceToTopicOperator를 위한 producer_function.
    메시지 리스트(key, value)를 반환합니다.
    """
    # [최종 수정] 'ts'가 없는 KeyError를 방지하기 위해 .get()과 기본값을 사용합니다.
    # 수동 실행('ts'가 없음) 시에는 현재 시간을 대신 사용합니다.
    ts = context.get("ts", datetime.now().isoformat())
    
    # (key, value) 튜플의 리스트를 반환
    messages = [
        (None, f"Timestamp: {ts}"),
        (None, "Kafka 연결 테스트 성공")
    ]
    print(f"Producing messages: {messages}")
    return messages
# --- [수정 완료] ---


@dag(
    dag_id="system_integration_test",
    start_date=datetime(2025, 1, 1),
    schedule=None,
    catchup=False,
    tags=["test", "system_check"],
)
def system_integration_test_dag():
    """
    Airflow, Kafka, Spark 통합 테스트용 DAG
    """

    # 1. BashOperator: 간단한 echo 명령어로 Airflow 기본 기능 테스트
    task_check_bash = BashOperator(
        task_id="check_bash_operator",
        bash_command="echo 'Airflow BashOperator가 성공적으로 실행되었습니다.'",
    )

    # 2. KafkaProducer: (이전과 동일)
    task_check_kafka = ProduceToTopicOperator(
        task_id="check_kafka_producer",
        kafka_config_id="kafka_default",
        topic="airflow_test_topic",
        producer_function=kafka_producer_function,
    )

    # 3. SparkSubmit: [최종 수정] 'master'를 다시 'conf'로 되돌립니다.
    task_check_spark = SparkSubmitOperator(
        task_id="check_spark_submit",
        conn_id="spark_default", # 1단계에서 이 연결의 Host를 'local[*]'로 수정했습니다.
        application=f"{SPARK_HOME}/examples/src/main/python/pi.py",
        application_args=["10"],
        conf={"spark.master": "local[*]"}, # 'master=' 인자 대신 'conf'가 올바른 인자입니다.
        # master="local[*]",  <- [삭제] 유효하지 않은 인자
        env_vars={"JAVA_HOME": JAVA_HOME},
    )

    # 작업 순서 정의
    task_check_bash >> [task_check_kafka, task_check_spark]

# DAG 정의
system_integration_test_dag()