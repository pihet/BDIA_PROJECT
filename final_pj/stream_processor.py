import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
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
    "/home/wjdcks/docker_pipeline/spark_checkpoints/kafka_to_db",
)
kafka_bootstrap_servers = os.getenv(
    "KAFKA_BOOTSTRAP_SERVERS",
    "kafka:9092",
)
kafka_topic = os.getenv(
    "KAFKA_TOPIC",
    "mariadb.fulfillment.inventory_db.products",
)

# --- [수정 1] : DB에 데이터를 쓰는 함수를 새로 정의 ---
# 이 함수는 Spark가 실시간 데이터를 작은 묶음(batch_df)으로 전달해줄 때마다 호출됩니다.
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
    # 1. SparkSession 생성 (이전과 동일)
    # (주의: jars.packages는 spark-submit에서 --packages로 주는 것이 더 안정적입니다)
    spark = (
        SparkSession.builder.appName("KafkaToMariaDB")
        .getOrCreate()
    )

    print("Spark 스트리밍 소비자가 Kafka를 대기 중입니다...")

    # 2. [E] Kafka 토픽에서 CDC 이벤트 읽기
    kafka_df = (
        spark.readStream.format("kafka")
        .option("kafka.bootstrap.servers", kafka_bootstrap_servers)
        .option("subscribe", kafka_topic)
        .option("startingOffsets", "earliest")
        .load()
    )

    # Debezium CDC 이벤트(JSON)의 payload.after 값을 파싱하기 위한 스키마 정의
    schema = StructType([
        StructField("payload", StructType([
            StructField("after", StructType([
                StructField("id", IntegerType()),
                StructField("name", StringType()),
                StructField("description", StringType()),
                StructField("weight", DoubleType())
            ])),
            StructField("before", StructType([
                StructField("id", IntegerType()),
                StructField("name", StringType()),
                StructField("description", StringType()),
                StructField("weight", DoubleType())
            ])),
            StructField("op", StringType()),
            StructField("ts_ms", LongType())
        ]))
    ])

    # 3. [T] 데이터 변환 (수정됨)
    # Kafka의 'value' 컬럼을 JSON으로 파싱하고 Debezium after 레코드를 추출합니다.
    output_df = kafka_df.select(
        from_json(col("value").cast("string"), schema).alias("data")
    ).select(
        col("data.payload.after.id").alias("product_id"),
        col("data.payload.after.name").alias("name"),
        col("data.payload.after.description").alias("description"),
        col("data.payload.after.weight").alias("weight"),
        col("data.payload.op").alias("op"),
        col("data.payload.ts_ms").alias("ts_ms")
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