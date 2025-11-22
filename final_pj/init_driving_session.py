"""
car 데이터베이스의 driving_session 테이블 데이터를
inventory_db 데이터베이스의 driving_session 테이블로 초기 복사하는 스크립트
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

def copy_uservehicle_data(limit=10):
    """uservehicle 테이블 데이터 복사 (외래 키 제약 해결을 위해 먼저 실행)"""

    # 소스 DB (car) 연결
    source_conn = get_db_connection("car")
    # 대상 DB (inventory_db) 연결
    target_conn = get_db_connection("inventory_db")

    try:
        with source_conn.cursor() as source_cursor, target_conn.cursor() as target_cursor:

            # car DB에서 uservehicle 데이터 조회
            source_cursor.execute(f"""
                SELECT car_id, age, user_location, user_car_class, user_car_brand,
                       user_car_year, user_car_model, user_car_weight, user_car_displace,
                       user_car_efficiency, updated_at
                FROM uservehicle
                LIMIT {limit}
            """)

            rows = source_cursor.fetchall()
            print(f"car DB에서 {len(rows)}건의 uservehicle 데이터를 조회했습니다.")

            if not rows:
                print("복사할 uservehicle 데이터가 없습니다.")
                return

            # inventory_db에 데이터 삽입
            insert_count = 0
            for row in rows:
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
                    print(f"  ✓ {row['car_id']} 복사 완료")

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

def copy_driving_session_data(limit=10):
    """driving_session 테이블 데이터 복사"""

    # 소스 DB (car) 연결
    source_conn = get_db_connection("car")
    # 대상 DB (inventory_db) 연결
    target_conn = get_db_connection("inventory_db")

    try:
        with source_conn.cursor() as source_cursor, target_conn.cursor() as target_cursor:

            # car DB에서 driving_session 데이터 조회 (제한 개수만큼)
            source_cursor.execute(f"""
                SELECT session_id, car_id, app_engine, start_time, end_time, created_at, updated_at
                FROM driving_session
                LIMIT {limit}
            """)

            rows = source_cursor.fetchall()
            print(f"car DB에서 {len(rows)}건의 driving_session 데이터를 조회했습니다.")

            if not rows:
                print("복사할 데이터가 없습니다.")
                return

            # inventory_db에 데이터 삽입
            insert_count = 0
            for row in rows:
                try:
                    # NULL 값 처리
                    app_engine = 1 if row['app_engine'] else 0  # Boolean을 TINYINT로 변환

                    target_cursor.execute("""
                        INSERT INTO driving_session
                        (session_id, car_id, app_engine, start_time, end_time, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                        app_engine=VALUES(app_engine), start_time=VALUES(start_time),
                        end_time=VALUES(end_time), created_at=VALUES(created_at), updated_at=VALUES(updated_at)
                    """, (
                        row['session_id'],
                        row['car_id'],
                        app_engine,
                        row['start_time'],
                        row['end_time'],
                        row['created_at'],
                        row['updated_at']
                    ))

                    insert_count += 1
                    print(f"  ✓ {row['session_id']} 복사 완료")

                except Exception as e:
                    print(f"  ✗ {row['session_id']} 복사 실패: {e}")
                    continue

            # 변경사항 커밋
            target_conn.commit()
            print(f"\n총 {insert_count}건의 데이터를 inventory_db.driving_session으로 복사했습니다.")

    except Exception as e:
        print(f"데이터 복사 중 오류 발생: {e}")
        target_conn.rollback()

    finally:
        source_conn.close()
        target_conn.close()

def copy_driving_session_data_batch(limit=None, batch_size=10000):
    """driving_session 테이블 데이터 배치 복사 (대용량 데이터용)"""

    # 소스 DB (car) 연결
    source_conn = get_db_connection("car")
    # 대상 DB (inventory_db) 연결
    target_conn = get_db_connection("inventory_db")

    try:
        with source_conn.cursor() as source_cursor, target_conn.cursor() as target_cursor:

            # 전체 데이터 수 확인
            source_cursor.execute("SELECT COUNT(*) as total FROM driving_session")
            total_count = source_cursor.fetchone()['total']

            if limit is not None:
                total_count = min(total_count, limit)

            print(f"driving_session 테이블 총 {total_count}건의 데이터를 배치로 복사합니다.")

            # 배치로 데이터 처리
            offset = 0
            total_inserted = 0

            while offset < total_count:
                current_batch = min(batch_size, total_count - offset)

                # 배치 데이터 조회
                source_cursor.execute(f"""
                    SELECT session_id, car_id, app_engine, start_time, end_time, created_at, updated_at
                    FROM driving_session
                    ORDER BY session_id
                    LIMIT {current_batch} OFFSET {offset}
                """)

                rows = source_cursor.fetchall()
                if not rows:
                    break

                # 배치 삽입
                batch_inserted = 0
                for row in rows:
                    try:
                        # NULL 값 처리
                        app_engine = 1 if row['app_engine'] else 0  # Boolean을 TINYINT로 변환

                        target_cursor.execute("""
                            INSERT INTO driving_session
                            (session_id, car_id, app_engine, start_time, end_time, created_at, updated_at)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                            ON DUPLICATE KEY UPDATE
                            app_engine=VALUES(app_engine), start_time=VALUES(start_time),
                            end_time=VALUES(end_time), created_at=VALUES(created_at), updated_at=VALUES(updated_at)
                        """, (
                            row['session_id'],
                            row['car_id'],
                            app_engine,
                            row['start_time'],
                            row['end_time'],
                            row['created_at'],
                            row['updated_at']
                        ))

                        batch_inserted += 1

                    except Exception as e:
                        # 외래 키 제약 오류는 무시하고 계속 진행
                        if "foreign key constraint" in str(e).lower():
                            continue
                        else:
                            print(f"  ✗ {row['session_id']} 복사 실패: {e}")
                        continue

                # 배치 커밋
                target_conn.commit()
                total_inserted += batch_inserted

                print(f"  배치 완료: {offset + current_batch}/{total_count}건 처리됨 (현재 배치: {batch_inserted}건 성공)")
                offset += current_batch

            print(f"\n총 {total_inserted}건의 데이터를 inventory_db.driving_session으로 복사했습니다.")

    except Exception as e:
        print(f"데이터 복사 중 오류 발생: {e}")
        target_conn.rollback()

    finally:
        source_conn.close()
        target_conn.close()

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "full":
        print("car DB → inventory_db driving_session 전체 데이터 복사를 시작합니다...")
        copy_driving_session_data_batch(limit=None, batch_size=10000)  # 전체 데이터 배치 복사
        print("전체 데이터 복사가 완료되었습니다.")
    else:
        print("car DB → inventory_db 초기 데이터 복사를 시작합니다...")
        # 1. 외래 키 제약을 위한 uservehicle 데이터 먼저 복사
        print("\n1. uservehicle 데이터 복사 중...")
        copy_uservehicle_data(limit=20)  # 충분한 수의 uservehicle 데이터 복사

        # 2. driving_session 데이터 복사
        print("\n2. driving_session 데이터 복사 중...")
        copy_driving_session_data(limit=10)  # 10건만 복사

        print("\n샘플 데이터 복사가 완료되었습니다.")
        print("전체 데이터를 복사하려면: python init_driving_session.py full")
