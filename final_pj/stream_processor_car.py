"""
car 데이터베이스 → Kafka → Spark → inventory_db 파이프라인용 스트리밍 프로세서
- car DB의 UserVehicle, Driving_Session 테이블 변경사항을 Debezium CDC로 Kafka에서 읽기
- inventory_db의 동일한 테이블로 저장
"""
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
    ShortType,
    TimestampType,
    BooleanType,
)

# 환경 변수
checkpoint_dir = os.getenv(
    "CHECKPOINT_DIR",
    "/opt/checkpoints/car_db_to_inventory_db",
)
kafka_bootstrap_servers = os.getenv(
    "KAFKA_BOOTSTRAP_SERVERS",
    "kafka-headless-service.default.svc.cluster.local:9092",
)
kafka_topic = os.getenv(
    "KAFKA_TOPIC",
    "mariadb.car.car.uservehicle",  # 또는 mariadb.car.car.driving_session (Debezium은 소문자로 변환)
)
target_table = os.getenv("TARGET_TABLE", "uservehicle")  # uservehicle 또는 driving_session (소문자)

# --- DB에 데이터를 쓰는 함수 ---
def write_to_mariadb(batch_df, batch_id):
    """
    하나의 마이크로 배치를 inventory_db에 저장하는 함수
    """
    print(f"--- Batch {batch_id} 처리 시작 (테이블: {target_table}) ---")
    
    db_url = os.getenv(
        "MARIADB_JDBC_URL",
        "jdbc:mariadb://172.16.11.114:3307/inventory_db?sessionVariables=sql_mode='ANSI_QUOTES'&useUnicode=true&characterEncoding=UTF-8",
    )
    db_properties = {
        "user": os.getenv("MARIADB_USERNAME", "root"),
        "password": os.getenv("MARIADB_PASSWORD", "0000"),
        "driver": "org.mariadb.jdbc.Driver"
    }

    if batch_df.count() > 0:
        print(f"Batch {batch_id}: {batch_df.count()} 건의 새 데이터 발견. {target_table} 테이블에 저장 시도...")
        
        batch_df.write.jdbc(
            url=db_url,
            table=target_table,
            mode="append",
            properties=db_properties
        )
        print(f"Batch {batch_id}: 저장 완료.")
    else:
        print(f"Batch {batch_id}: 처리할 새 데이터 없음.")


def main():
    spark = (
        SparkSession.builder.appName("CarDBToInventoryDB")
        .getOrCreate()
    )

    print(f"Spark 스트리밍 소비자가 Kafka 토픽 '{kafka_topic}'을 대기 중입니다...")
    print(f"대상 테이블: {target_table}")

    # Kafka에서 CDC 이벤트 읽기
    kafka_df = (
        spark.readStream.format("kafka")
        .option("kafka.bootstrap.servers", kafka_bootstrap_servers)
        .option("subscribe", kafka_topic)
        .option("startingOffsets", "latest")  # 최신 데이터부터
        .load()
    )

    # UserVehicle 테이블 스키마 (소문자: uservehicle)
    if target_table.lower() == "uservehicle":
        after_schema = StructType([
            StructField("car_id", StringType()),
            StructField("age", IntegerType()),
            StructField("user_location", StringType()),
            StructField("user_car_class", StringType()),
            StructField("user_car_brand", StringType()),
            StructField("user_car_year", ShortType()),
            StructField("user_car_model", StringType()),
            StructField("user_car_weight", DoubleType()),
            StructField("user_car_displace", ShortType()),
            StructField("user_car_efficiency", StringType()),
            StructField("updated_at", TimestampType())
        ])
    # Driving_Session 테이블 스키마 (소문자: driving_session)
    elif target_table.lower() == "driving_session":
        after_schema = StructType([
            StructField("session_id", StringType()),
            StructField("car_id", StringType()),
            StructField("app_engine", BooleanType()),
            StructField("start_time", TimestampType()),
            StructField("end_time", TimestampType()),
            StructField("created_at", TimestampType()),
            StructField("updated_at", TimestampType())
        ])
    else:
        raise ValueError(f"지원하지 않는 테이블: {target_table}")

    # Debezium CDC 이벤트 스키마
    schema = StructType([
        StructField("payload", StructType([
            StructField("after", after_schema),
            StructField("before", after_schema),
            StructField("op", StringType()),  # c=create, u=update, d=delete
            StructField("ts_ms", LongType())
        ]))
    ])

    # 데이터 변환: Debezium after 레코드 추출
    output_df = kafka_df.select(
        from_json(col("value").cast("string"), schema).alias("data")
    ).select(
        col("data.payload.after.*"),
        col("data.payload.op").alias("op"),
        col("data.payload.ts_ms").alias("ts_ms")
    ).where(col("data.payload.after").isNotNull())

    # inventory_db에 저장
    query = (
        output_df.writeStream
        .outputMode("append")
        .foreachBatch(write_to_mariadb)
        .option("checkpointLocation", checkpoint_dir)
        .trigger(availableNow=True)  # Airflow 주기 실행용
        .start()
    )

    query.awaitTermination()

if __name__ == "__main__":
    main()

