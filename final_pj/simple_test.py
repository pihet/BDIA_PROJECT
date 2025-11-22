#!/usr/bin/env python3
"""
간단한 Spark 테스트
"""

try:
    from pyspark.sql import SparkSession
    print("✓ PySpark 임포트 성공")

    # 간단한 Spark 세션 생성 시도
    spark = SparkSession.builder.appName("SimpleTest").getOrCreate()
    print("✓ Spark 세션 생성 성공")

    # 간단한 데이터프레임 생성
    data = [("Alice", 25), ("Bob", 30), ("Charlie", 35)]
    df = spark.createDataFrame(data, ["name", "age"])
    print("✓ 데이터프레임 생성 성공")
    print(f"데이터 행 수: {df.count()}")

    spark.stop()
    print("✓ 모든 테스트 통과!")

except Exception as e:
    print(f"✗ 오류 발생: {e}")
    import traceback
    traceback.print_exc()
