"""
모델 예측 서비스 - MariaDB에서 데이터를 읽어 예측 수행
- Airflow와 독립적으로 지속 실행
- MariaDB를 주기적으로 폴링하여 새 데이터 처리
- 또는 Kafka를 구독하여 실시간 처리 가능
"""
import os
import time
import mysql.connector
from datetime import datetime
import json

# 환경 변수 설정
MARIADB_HOST = os.getenv("MARIADB_HOST", "mariadb-internal-service.default.svc.cluster.local")
MARIADB_PORT = int(os.getenv("MARIADB_PORT", "3306"))
MARIADB_USER = os.getenv("MARIADB_USER", "root")
MARIADB_PASSWORD = os.getenv("MARIADB_PASSWORD", "0000")
MARIADB_DATABASE = os.getenv("MARIADB_DATABASE", "inventory_db")

# 폴링 설정
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "300"))  # 초 단위 (기본 5분)
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "100"))  # 한 번에 처리할 레코드 수

# 테이블 설정
SOURCE_TABLE = os.getenv("SOURCE_TABLE", "cdc_products_log")
PREDICTION_TABLE = os.getenv("PREDICTION_TABLE", "product_predictions")

# 마지막 처리 시간 저장 (재시작 시 중복 방지)
LAST_PROCESSED_ID_FILE = os.getenv("LAST_PROCESSED_ID_FILE", "/tmp/last_processed_id.txt")


def get_last_processed_id():
    """마지막으로 처리한 ID를 파일에서 읽기"""
    try:
        if os.path.exists(LAST_PROCESSED_ID_FILE):
            with open(LAST_PROCESSED_ID_FILE, 'r') as f:
                return int(f.read().strip())
    except Exception as e:
        print(f"마지막 처리 ID 읽기 실패: {e}")
    return 0


def save_last_processed_id(last_id):
    """마지막으로 처리한 ID를 파일에 저장"""
    try:
        with open(LAST_PROCESSED_ID_FILE, 'w') as f:
            f.write(str(last_id))
    except Exception as e:
        print(f"마지막 처리 ID 저장 실패: {e}")


def connect_mariadb():
    """MariaDB 연결"""
    return mysql.connector.connect(
        host=MARIADB_HOST,
        port=MARIADB_PORT,
        user=MARIADB_USER,
        password=MARIADB_PASSWORD,
        database=MARIADB_DATABASE,
        charset='utf8mb4',
        collation='utf8mb4_unicode_ci'
    )


def load_model():
    """
    모델 로드 함수
    - 실제 모델 파일 경로나 모델 로딩 로직을 여기에 구현
    - 예: pickle, joblib, tensorflow, pytorch 등
    """
    # 예시: 모델 파일 경로
    model_path = os.getenv("MODEL_PATH", "/opt/models/product_model.pkl")
    
    # TODO: 실제 모델 로딩 로직 구현
    # import pickle
    # with open(model_path, 'rb') as f:
    #     model = pickle.load(f)
    # return model
    
    print(f"[모델 로드] 모델 경로: {model_path}")
    return None  # 임시로 None 반환


def predict(model, data_row):
    """
    예측 함수
    - 모델을 사용하여 예측 수행
    - data_row: (product_id, name, description, weight, op, ts_ms)
    """
    # TODO: 실제 예측 로직 구현
    # 예시:
    # features = [data_row['weight'], len(data_row['name']), ...]
    # prediction = model.predict([features])[0]
    # return prediction
    
    # 임시 예측값 (실제로는 모델 사용)
    import random
    prediction = {
        'predicted_value': random.uniform(0, 100),
        'confidence': random.uniform(0.7, 0.99),
        'prediction_time': datetime.now().isoformat()
    }
    return prediction


def process_new_data(model):
    """새 데이터를 읽어서 예측 수행"""
    conn = None
    cursor = None
    
    try:
        # MariaDB 연결
        conn = connect_mariadb()
        cursor = conn.cursor(dictionary=True)
        
        # 마지막 처리 ID 가져오기
        last_id = get_last_processed_id()
        
        # 새 데이터 조회 (마지막 처리 ID 이후의 데이터)
        query = f"""
            SELECT product_id, name, description, weight, op, ts_ms
            FROM {SOURCE_TABLE}
            WHERE product_id > %s
            ORDER BY product_id ASC
            LIMIT %s
        """
        cursor.execute(query, (last_id, BATCH_SIZE))
        new_records = cursor.fetchall()
        
        if not new_records:
            print(f"[{datetime.now()}] 처리할 새 데이터 없음 (마지막 ID: {last_id})")
            return last_id
        
        print(f"[{datetime.now()}] {len(new_records)}건의 새 데이터 발견. 예측 시작...")
        
        # 예측 결과 저장용 리스트
        predictions = []
        max_id = last_id
        
        # 각 레코드에 대해 예측 수행
        for record in new_records:
            product_id = record['product_id']
            max_id = max(max_id, product_id)
            
            # 예측 수행
            prediction_result = predict(model, record)
            
            # 예측 결과 저장
            predictions.append({
                'product_id': product_id,
                'predicted_value': prediction_result['predicted_value'],
                'confidence': prediction_result['confidence'],
                'prediction_time': prediction_result['prediction_time'],
                'created_at': datetime.now()
            })
            
            print(f"  - Product ID {product_id}: 예측값={prediction_result['predicted_value']:.2f}, 신뢰도={prediction_result['confidence']:.2f}")
        
        # 예측 결과를 DB에 저장
        if predictions:
            insert_query = f"""
                INSERT INTO {PREDICTION_TABLE}
                (product_id, predicted_value, confidence, prediction_time, created_at)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    predicted_value = VALUES(predicted_value),
                    confidence = VALUES(confidence),
                    prediction_time = VALUES(prediction_time),
                    created_at = VALUES(created_at)
            """
            
            for pred in predictions:
                cursor.execute(insert_query, (
                    pred['product_id'],
                    pred['predicted_value'],
                    pred['confidence'],
                    pred['prediction_time'],
                    pred['created_at']
                ))
            
            conn.commit()
            print(f"[{datetime.now()}] {len(predictions)}건의 예측 결과 저장 완료")
        
        # 마지막 처리 ID 저장
        save_last_processed_id(max_id)
        
        return max_id
        
    except Exception as e:
        print(f"[에러] 데이터 처리 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return last_id
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def create_prediction_table_if_not_exists():
    """예측 결과 테이블이 없으면 생성"""
    conn = None
    cursor = None
    
    try:
        conn = connect_mariadb()
        cursor = conn.cursor()
        
        create_table_query = f"""
            CREATE TABLE IF NOT EXISTS {PREDICTION_TABLE} (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                product_id INT NOT NULL UNIQUE,
                predicted_value DECIMAL(10, 2),
                confidence DECIMAL(5, 4),
                prediction_time DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_product_id (product_id),
                INDEX idx_created_at (created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        
        cursor.execute(create_table_query)
        conn.commit()
        print(f"[초기화] 예측 결과 테이블 생성 완료: {PREDICTION_TABLE}")
        
    except Exception as e:
        print(f"[에러] 테이블 생성 실패: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def main():
    """메인 루프 - 지속적으로 실행"""
    print("=" * 60)
    print("모델 예측 서비스 시작")
    print(f"  - MariaDB: {MARIADB_HOST}:{MARIADB_PORT}/{MARIADB_DATABASE}")
    print(f"  - 소스 테이블: {SOURCE_TABLE}")
    print(f"  - 예측 테이블: {PREDICTION_TABLE}")
    print(f"  - 폴링 간격: {POLL_INTERVAL}초 ({POLL_INTERVAL//60}분)")
    print(f"  - 배치 크기: {BATCH_SIZE}건")
    print("=" * 60)
    
    # 예측 결과 테이블 생성
    create_prediction_table_if_not_exists()
    
    # 모델 로드 (한 번만 로드)
    print("\n[모델 로드] 모델 로딩 중...")
    model = load_model()
    print("[모델 로드] 완료\n")
    
    # 메인 루프
    print(f"[시작] {POLL_INTERVAL}초마다 새 데이터를 확인합니다...\n")
    
    while True:
        try:
            # 새 데이터 처리
            last_id = process_new_data(model)
            
            # 대기
            print(f"[대기] {POLL_INTERVAL}초 후 다시 확인합니다...\n")
            time.sleep(POLL_INTERVAL)
            
        except KeyboardInterrupt:
            print("\n[종료] 사용자에 의해 중단됨")
            break
        except Exception as e:
            print(f"[에러] 메인 루프 오류: {e}")
            import traceback
            traceback.print_exc()
            print(f"[재시도] {POLL_INTERVAL}초 후 재시도합니다...\n")
            time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()

