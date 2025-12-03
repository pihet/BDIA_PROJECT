#!/bin/bash

# Flink SQL Gateway 주소
GATEWAY_HOST="sql-gateway-service-20.flink.svc.cluster.local:8083"

echo "Using Gateway: $GATEWAY_HOST"

# 1. 전체 Raw 데이터 수집 (Streaming)
echo "Submitting Job 1: Ingest All Raw Data..."
sql-client.sh gateway -e $GATEWAY_HOST -f 01_ingest_raw_data.sql

# 2. 분석 결과 저장 (Streaming) - drowsy_drive 제외, detection 2종만 처리
echo "Submitting Job 2: Sink Analysis Results..."
sql-client.sh gateway -e $GATEWAY_HOST -f 02_sink_analysis_results.sql

# 3. 기준 정보 업데이트 (Batch) - 필요시 주석 해제 또는 Airflow 사용
# echo "Submitting Job 3: Batch Update Info..."
# sql-client.sh gateway -e $GATEWAY_HOST -f 03_batch_update_info.sql

echo "Jobs submitted."


