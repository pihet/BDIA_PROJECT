"""
car 데이터베이스에서 데이터를 읽어서 Kafka로 보내는 프로듀서
- uservehicle과 driving_session 테이블의 데이터를 Kafka 토픽으로 전송
"""

import time
import json
import sys
from decimal import Decimal
from kafka import KafkaProducer
import pymysql

# Decimal 타입을 JSON으로 직렬화하기 위한 헬퍼 함수
def decimal_serializer(obj):
    """Decimal 객체를 문자열(str)로 변환하는 JSON 직렬화 함수"""
    if isinstance(obj, Decimal):
        return str(obj)
    # datetime 객체 처리
    if hasattr(obj, 'isoformat'):  # datetime, date, time 객체
        return obj.isoformat()
    # 다른 타입은 기본 핸들러에게 맡김
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")

def create_producer():
    """Kafka Producer 생성"""
    return KafkaProducer(
        bootstrap_servers=["kafka:9092"],
        value_serializer=lambda v: json.dumps(v, default=decimal_serializer).encode("utf-8"),
    )

def send_uservehicle_data(producer, limit=None):
    """uservehicle 테이블 데이터 전송"""
    batch_size = 100  # batch_size를 100으로 설정
    try:
        # car DB 연결
        conn = pymysql.connect(
            user="root",
            password="0000",
            host="mariadb_data",  # 또는 실제 car DB 호스트
            port=3306,
            database="car"
        )
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        print("car DB 연결 성공. uservehicle 데이터를 Kafka로 전송합니다...")

        # uservehicle 데이터 조회
        query = """
            SELECT car_id, age, user_location, user_car_class, user_car_brand,
                   user_car_year, user_car_model, user_car_weight, user_car_displace,
                   user_car_efficiency, updated_at
            FROM uservehicle
        """
        # limit=None이면 LIMIT 절 없이 전체 조회
        if limit is not None:
            query += f" LIMIT {limit}"
        cursor.execute(query)

        rows = cursor.fetchall()
        total_count = len(rows)
        print(f"uservehicle 테이블에서 {total_count}건의 데이터를 읽어왔습니다.")

        count = 0
        for i, row in enumerate(rows):
            # Kafka 메시지 구성
            message = {
                "table": "uservehicle",
                "data": row,
                "timestamp": time.time()
            }

            print(f"[Producer] uservehicle 전송: car_id={row['car_id']}")
            producer.send("car.uservehicle", value=message)
            count += 1

            # batch_size마다 flush
            if (i + 1) % batch_size == 0 or (i + 1) == total_count:
                producer.flush()
                print(f"  진행중: {i + 1}/{total_count}건 전송됨")

        print(f"uservehicle: 총 {count}건 전송 완료.")

    except Exception as e:
        print(f"uservehicle 데이터 전송 오류: {e}")
        sys.exit(1)
    finally:
        if "conn" in locals() and conn:
            conn.close()

def send_driving_session_data(producer, limit=10):
    """driving_session 테이블 데이터 전송"""
    try:
        # car DB 연결
        conn = pymysql.connect(
            user="root",
            password="0000",
            host="mariadb_data",  # 또는 실제 car DB 호스트
            port=3306,
            database="car"
        )
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        print("car DB 연결 성공. driving_session 데이터를 Kafka로 전송합니다...")

        # driving_session 데이터 조회
        cursor.execute(f"""
            SELECT session_id, car_id, app_engine, start_time, end_time, created_at, updated_at
            FROM driving_session
            LIMIT {limit}
        """)

        count = 0
        for row in cursor:
            # Kafka 메시지 구성
            message = {
                "table": "driving_session",
                "data": row,
                "timestamp": time.time()
            }

            print(f"[Producer] driving_session 전송: session_id={row['session_id']}")
            producer.send("car.driving_session", value=message)
            count += 1

        producer.flush()
        print(f"driving_session: 총 {count}건 전송 완료.")

    except Exception as e:
        print(f"driving_session 데이터 전송 오류: {e}")
        sys.exit(1)
    finally:
        if "conn" in locals() and conn:
            conn.close()

def main():
    """메인 함수"""
    producer = None
    try:
        producer = create_producer()

        print("=== car DB → Kafka 데이터 전송 시작 ===")

        # 1. uservehicle 데이터 전송
        send_uservehicle_data(producer, limit=10)

        # 2. driving_session 데이터 전송
        send_driving_session_data(producer, limit=10)

        print("=== 모든 데이터 전송 완료 ===")

    except Exception as e:
        print(f"프로그램 실행 오류: {e}")
        sys.exit(1)
    finally:
        if producer:
            producer.close()

if __name__ == "__main__":
    main()
