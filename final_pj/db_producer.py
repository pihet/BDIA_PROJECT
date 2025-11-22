import time
import json
import sys # sys 모듈 임포트
from decimal import Decimal # [추가] Decimal 타입을 확인하기 위해 임포트
from kafka import KafkaProducer
import mariadb  # 또는 pymysql 등 DB 연결 라이브러리

# [추가] Decimal 타입을 JSON으로 직렬화하기 위한 헬퍼 함수
def decimal_serializer(obj):
    """Decimal 객체를 문자열(str)로 변환하는 JSON 직렬화 함수"""
    if isinstance(obj, Decimal):
        return str(obj)
    # 다른 타입은 기본 핸들러에게 맡김
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")

# 1. Kafka Producer 설정
producer = KafkaProducer(
    bootstrap_servers=["kafka:9092"],
    
    # [수정] 기본 json.dumps 대신, 'decimal_serializer'를 사용하도록 수정
    value_serializer=lambda v: json.dumps(v, default=decimal_serializer).encode("utf-8"),
)

# 2. MariaDB 연결 (본인 정보로 수정)
try:
    conn = mariadb.connect(
        user="root",
        password="0000",
        host="mariadb_data",
        port=3306,
        database="ex_spark" # [주의] 이 DB가 mariadb_data 컨테이너에 존재해야 합니다.
    )
    cursor = conn.cursor(dictionary=True) # 결과를 딕셔너리로 받기

    print("DB 연결 성공. Kafka로 데이터 전송을 시작합니다...")

    cursor.execute("SELECT * FROM high_paid_engineers")

    count = 0
    for row in cursor:
        print(f"[Producer] 전송 데이터: {row}")
        # [주의] 'test-events' 토픽이 Kafka에 존재해야 합니다.
        producer.send("test-events", value=row)
        count += 1

    producer.flush() # 모든 메시지가 전송되도록 보장
    print(f"총 {count}건 전송 완료.")

except mariadb.Error as e:
    print(f"DB 연결 오류: {e}")
    # [수정] 오류를 Airflow(BashOperator)가 알 수 있도록
    #       스크립트를 비정상 종료(exit code 1)시킵니다.
    sys.exit(1)
finally:
    if "conn" in locals() and conn:
        conn.close()
    if "producer" in locals():
        producer.close()