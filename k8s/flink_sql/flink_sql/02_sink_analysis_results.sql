-- Job 2: 분석 결과 RDS 저장 (Streaming)
-- Source: Kafka (analysis_result_topics)
-- Sink: RDS (arrears_detection, missing_person_detection)
-- 변경사항: drowsy_drive 제거 (외부 모델이 직접 DB에 넣거나, 단방향 수집 대상이므로 Sink Job에서 제외)

SET 'execution.runtime-mode' = 'streaming';
SET 'pipeline.name' = 'sink-analysis-results';

-- ==========================================
-- 1. Kafka Source (분석 결과)
-- ==========================================

-- 1.1 체납 탐지 결과
CREATE TABLE kafka_result_arrears (
    `detection_id` STRING,
    `image_id` STRING,
    `car_plate_number` STRING,
    `detection_success` TINYINT,
    `detected_lat` DOUBLE,
    `detected_lon` DOUBLE,
    `detected_time` TIMESTAMP(3)
) WITH (
    'connector' = 'kafka',
    'topic' = 'result_arrears_detection',
    'properties.bootstrap.servers' = 'kafka-cluster-kafka-bootstrap.kafka-kubernetes-operator.svc.cluster.local:9092',
    'properties.group.id' = 'sink-arrears-group',
    'format' = 'json'
);

-- 1.2 실종자 탐지 결과
CREATE TABLE kafka_result_missing (
    `detection_id` STRING,
    `image_id` STRING,
    `missing_id` STRING,
    `detection_success` TINYINT,
    `detected_lat` DOUBLE,
    `detected_lon` DOUBLE,
    `detected_time` TIMESTAMP(3)
) WITH (
    'connector' = 'kafka',
    'topic' = 'result_missing_person_detection',
    'properties.bootstrap.servers' = 'kafka-cluster-kafka-bootstrap.kafka-kubernetes-operator.svc.cluster.local:9092',
    'properties.group.id' = 'sink-missing-group',
    'format' = 'json'
);

-- ==========================================
-- 2. RDS Sink Tables
-- ==========================================

-- 2.1 체납 탐지 결과
CREATE TABLE rds_sink_arrears (
    `detection_id` STRING,
    `image_id` STRING,
    `car_plate_number` STRING,
    `detection_success` TINYINT,
    `detected_lat` DOUBLE,
    `detected_lon` DOUBLE,
    `detected_time` TIMESTAMP(3),
    PRIMARY KEY (`detection_id`) NOT ENFORCED
) WITH (
    'connector' = 'jdbc',
    'url' = 'jdbc:mysql://busan-maria.cf8s8geeaqc9.ap-northeast-2.rds.amazonaws.com:23306/car_db',
    'table-name' = 'arrears_detection',
    'username' = 'root',
    'password' = 'busan!234pw'
);

-- 2.2 실종자 탐지 결과
CREATE TABLE rds_sink_missing (
    `detection_id` STRING,
    `image_id` STRING,
    `missing_id` STRING,
    `detection_success` TINYINT,
    `detected_lat` DOUBLE,
    `detected_lon` DOUBLE,
    `detected_time` TIMESTAMP(3),
    PRIMARY KEY (`detection_id`) NOT ENFORCED
) WITH (
    'connector' = 'jdbc',
    'url' = 'jdbc:mysql://busan-maria.cf8s8geeaqc9.ap-northeast-2.rds.amazonaws.com:23306/car_db',
    'table-name' = 'missing_person_detection',
    'username' = 'root',
    'password' = 'busan!234pw'
);

-- ==========================================
-- 3. Execution
-- ==========================================

BEGIN STATEMENT SET;

INSERT INTO rds_sink_arrears SELECT * FROM kafka_result_arrears;
INSERT INTO rds_sink_missing SELECT * FROM kafka_result_missing;

END;
