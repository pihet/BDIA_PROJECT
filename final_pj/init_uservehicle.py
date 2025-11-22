"""
car 데이터베이스의 uservehicle 테이블 데이터를
inventory_db 데이터베이스의 uservehicle 테이블로 초기 복사하는 스크립트
"""

import pymysql
import os
from datetime import datetime

def get_db_connection(db_name, host="172.16.11.114", port=3307, user="root", password="0000"):
    """데이터베이스 연결 생성"""
    return pymysql.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=db_name,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

def copy_uservehicle_data(limit=None):
    """uservehicle 테이블 데이터 복사"""

    # 소스 DB (car) 연결
    source_conn = get_db_connection("car")
    # 대상 DB (inventory_db) 연결
    target_conn = get_db_connection("inventory_db")

    try:
        with source_conn.cursor() as source_cursor, target_conn.cursor() as target_cursor:

            # car DB에서 uservehicle 데이터 조회
            query = """
                SELECT car_id, age, user_location, user_car_class, user_car_brand,
                       user_car_year, user_car_model, user_car_weight, user_car_displace,
                       user_car_efficiency, updated_at
                FROM uservehicle
            """
            if limit is not None:
                query += f" LIMIT {limit}"

            source_cursor.execute(query)

            rows = source_cursor.fetchall()
            total_count = len(rows)
            print(f"car DB에서 {total_count}건의 uservehicle 데이터를 조회했습니다.")

            if not rows:
                print("복사할 uservehicle 데이터가 없습니다.")
                return

            # inventory_db에 데이터 삽입
            insert_count = 0
            batch_size = 100  # 100개씩 배치 처리

            for i, row in enumerate(rows):
                try:
                    target_cursor.execute("""
                        INSERT INTO uservehicle
                        (car_id, age, user_location, user_car_class, user_car_brand,
                         user_car_year, user_car_model, user_car_weight, user_car_displace,
                         user_car_efficiency, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                        age=VALUES(age), user_location=VALUES(user_location),
                        user_car_class=VALUES(user_car_class), user_car_brand=VALUES(user_car_brand),
                        user_car_year=VALUES(user_car_year), user_car_model=VALUES(user_car_model),
                        user_car_weight=VALUES(user_car_weight), user_car_displace=VALUES(user_car_displace),
                        user_car_efficiency=VALUES(user_car_efficiency), updated_at=VALUES(updated_at)
                    """, (
                        row['car_id'], row['age'], row['user_location'], row['user_car_class'],
                        row['user_car_brand'], row['user_car_year'], row['user_car_model'],
                        row['user_car_weight'], row['user_car_displace'], row['user_car_efficiency'],
                        row['updated_at']
                    ))

                    insert_count += 1

                    # 진행 상황 표시 (100개마다)
                    if (i + 1) % batch_size == 0 or (i + 1) == total_count:
                        print(f"  진행중: {i + 1}/{total_count}건 처리됨")

                except Exception as e:
                    print(f"  ✗ {row['car_id']} 복사 실패: {e}")
                    continue

            # 변경사항 커밋
            target_conn.commit()
            print(f"\n총 {insert_count}건의 데이터를 inventory_db.uservehicle으로 복사했습니다.")

    except Exception as e:
        print(f"uservehicle 데이터 복사 중 오류 발생: {e}")
        target_conn.rollback()

    finally:
        source_conn.close()
        target_conn.close()

if __name__ == "__main__":
    print("car DB → inventory_db uservehicle 전체 데이터 복사를 시작합니다...")
    copy_uservehicle_data(limit=None)  # 전체 데이터 복사 (limit=None)
    print("전체 데이터 복사가 완료되었습니다.")
