"""
S3 → Kafka → Spark → MariaDB 파이프라인용 스트리밍 프로세서
- S3 Source Connector가 Kafka로 전송한 일반 JSON 데이터를 처리
- Debezium 포맷이 아닌 일반 JSON 포맷 사용
"""
import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, current_timestamp
from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    IntegerType,
    DoubleType,
    LongType,
)

# 환경 변수로 체크포인트 디렉터리를 제어하고, 기본값은 호스트 경로를 사용합니다.
checkpoint_dir = os.getenv(
    "CHECKPOINT_DIR",
    "/home/wjdcks/docker_pipeline/spark_checkpoints/s3_kafka_to_db",
)
kafka_bootstrap_servers = os.getenv(
    "KAFKA_BOOTSTRAP_SERVERS",
    "kafka:9092",
)
kafka_topic = os.getenv(
    "KAFKA_TOPIC",
    "s3.products.data",  # S3 Source Connector가 생성하는 토픽
)

# --- DB에 데이터를 쓰는 함수 ---
def write_to_mariadb(batch_df, batch_id):
    """
    하나의 마이크로 배치를 MariaDB에 저장하는 함수
    """
    print(f"--- Batch {batch_id} 처리 시작 ---")
    
    # 기본적으로 Kubernetes 서비스 DNS를 사용하되, 환경 변수로 오버라이드할 수 있습니다.
    db_url = os.getenv(
        "MARIADB_JDBC_URL",
        "jdbc:mariadb://mariadb-internal-service:3306/inventory_db?sessionVariables=sql_mode='ANSI_QUOTES'&useUnicode=true&characterEncoding=UTF-8",
    )
    db_table_name = "cdc_products_log"
    db_properties = {
        "user": os.getenv("MARIADB_USERNAME", "root"),
        "password": os.getenv("MARIADB_PASSWORD", "0000"),
        "driver": "org.mariadb.jdbc.Driver"
    }

    # batch_df (이 묶음)에 데이터가 1건이라도 있으면 저장
    if batch_df.count() > 0:
        print(f"Batch {batch_id}: {batch_df.count()} 건의 새 데이터 발견. 저장 시도...")
        
        # 이 코드는 우리가 이전에 성공했던 배치 저장(write.jdbc) 코드와 동일합니다.
        batch_df.write.jdbc(
            url=db_url,
            table=db_table_name,
            mode="append",  # 미리 만들어 둔 테이블에 데이터 추가
            properties=db_properties
        )
        print(f"Batch {batch_id}: 저장 완료.")
    else:
        print(f"Batch {batch_id}: 처리할 새 데이터 없음.")


def main():
    # 1. SparkSession 생성
    spark = (
        SparkSession.builder.appName("S3KafkaToMariaDB")
        .getOrCreate()
    )

    print("Spark 스트리밍 소비자가 Kafka를 대기 중입니다... (S3 Source)")

    # 2. [E] Kafka 토픽에서 S3 데이터 읽기
    kafka_df = (
        spark.readStream.format("kafka")
        .option("kafka.bootstrap.servers", kafka_bootstrap_servers)
        .option("subscribe", kafka_topic)
        .option("startingOffsets", "earliest")
        .load()
    )

    # S3 Source Connector가 전송하는 일반 JSON 스키마 정의
    # 예시: {"id": 1, "name": "상품명", "description": "설명", "weight": 1.5}
    schema = StructType([
        StructField("id", IntegerType()),
        StructField("name", StringType()),
        StructField("description", StringType()),
        StructField("weight", DoubleType())
    ])

    # 3. [T] 데이터 변환
    # Kafka의 'value' 컬럼을 JSON으로 파싱 (Debezium 포맷이 아닌 일반 JSON)
    output_df = kafka_df.select(
        from_json(col("value").cast("string"), schema).alias("data"),
        col("timestamp").alias("kafka_timestamp")  # Kafka 메시지 타임스탬프
    ).select(
        col("data.id").alias("product_id"),
        col("data.name").alias("name"),
        col("data.description").alias("description"),
        col("data.weight").alias("weight"),
        # S3 데이터에는 op, ts_ms가 없으므로 기본값 설정
        (col("kafka_timestamp").cast("long") * 1000).alias("ts_ms"),  # 밀리초로 변환
        col("kafka_timestamp").cast("string").alias("op")  # 또는 lit("c")로 "create" 고정 가능
    ).where(col("product_id").isNotNull())

    # 4. [L] MariaDB에 변경 로그 저장
    # 
    # trigger 옵션 설명:
    # - availableNow=True: 현재 Kafka에 있는 모든 메시지를 처리하고 종료 (Airflow 주기 실행에 적합)
    # - processingTime='10 seconds': 10초마다 체크하며 지속 실행 (실시간 스트리밍)
    # - continuous='1 second': 초단위로 지속 실행 (가장 실시간)
    #
    # Airflow로 주기 실행하는 경우: availableNow=True 권장 (각 실행이 독립적, 실패 시 재시도 용이)
    # 지속 실행이 필요한 경우: processingTime 또는 continuous 사용
    query = (
        output_df.writeStream
        .outputMode("append")
        .foreachBatch(write_to_mariadb) # format("console") 대신 이 함수를 호출
        .option("checkpointLocation", checkpoint_dir)
        .trigger(availableNow=True) # Airflow 주기 실행용: 현재 메시지 처리 후 종료
        # .trigger(processingTime='10 seconds')  # 지속 실행용: 10초마다 체크
        # .trigger(continuous='1 second')  # 지속 실행용: 1초마다 체크 (가장 실시간)
        .start()
    )

    query.awaitTermination()

if __name__ == "__main__":
    main()

