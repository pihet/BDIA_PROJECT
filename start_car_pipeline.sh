#!/bin/bash

# Car DB → Kafka → Spark → Inventory DB 파이프라인 시작 스크립트

echo "=== Car DB Pipeline 시작 ==="

# 1. 기존 컨테이너 정리
echo "1. 기존 컨테이너 정리 중..."
docker-compose down -v

# 2. 서비스 시작
echo "2. 서비스 시작 중..."
docker-compose --env-file docker_env up -d

# 3. 서비스 상태 확인
echo "3. 서비스 상태 확인 중..."
echo "   - MariaDB Car DB 상태 확인..."
docker-compose exec -T mariadb_car mysqladmin ping -u root -p0000

echo "   - MariaDB Inventory DB 상태 확인..."
docker-compose exec -T mariadb_inventory mysqladmin ping -u root -p0000

echo "   - Kafka 상태 확인..."
docker-compose exec -T kafka kafka-broker-api-versions --bootstrap-server localhost:9092

echo "   - Debezium Connect 상태 확인..."
curl -f http://localhost:8083/connectors/ || echo "Debezium Connect 준비 중..."

# 4. Debezium Connector 등록 (서비스가 완전히 시작될 때까지 대기)
echo "4. Debezium Connector 등록 중..."
sleep 30

curl -X POST -H "Content-Type: application/json" \
     -d @debezium-connector.json \
     http://localhost:8083/connectors

echo "5. 파이프라인 준비 완료!"
echo ""
echo "=== 사용 가능한 명령어 ==="
echo "• Spark 스트리밍 시작: docker-compose exec spark-worker python stream_processor_car.py"
echo "• 수동 데이터 전송: docker-compose exec spark-worker python car_db_producer.py"
echo "• Airflow 웹 UI: http://localhost:8080"
echo "• Debezium Connect: http://localhost:8083"
echo "• Kafka 토픽 확인: docker-compose exec kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic car.car.uservehicle --from-beginning"
echo ""
echo "=== 파이프라인 흐름 ==="
echo "Car DB 변경사항 → Debezium → Kafka → Spark Streaming → Inventory DB"
