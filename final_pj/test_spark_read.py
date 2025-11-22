#!/usr/bin/env python3
"""
Spark를 사용해서 MariaDB에서 데이터를 읽는 테스트 스크립트
"""

from pyspark.sql import SparkSession

def main():
    # SparkSession 생성
    spark = SparkSession.builder \
        .appName("TestMariaDBRead") \
        .getOrCreate()

    print("Spark 세션 생성 완료")

    # MariaDB 연결 설정
    jdbc_url = "jdbc:mariadb://mariadb_inventory:3306/inventory_db"
    connection_properties = {
        "user": "root",
        "password": "0000",
        "driver": "org.mariadb.jdbc.Driver"
    }

    try:
        # uservehicle 테이블에서 데이터 읽기
        print("uservehicle 테이블에서 데이터 읽는 중...")
        df = spark.read.jdbc(
            url=jdbc_url,
            table="uservehicle",
            properties=connection_properties
        )

        # 데이터 확인
        print(f"읽은 데이터 행 수: {df.count()}")
        print("스키마:")
        df.printSchema()

        print("\n데이터 내용:")
        df.show(truncate=False)

        # 간단한 집계 예시
        print(f"\n차량 브랜드별 개수:")
        df.groupBy("user_car_brand").count().show()

        print("\n테스트 완료!")

    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()

    finally:
        spark.stop()

if __name__ == "__main__":
    main()
