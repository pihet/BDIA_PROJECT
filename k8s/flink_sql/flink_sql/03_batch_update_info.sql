-- Job 3: 기준 정보 배치 갱신 (Batch/Airflow)
-- Source: Kafka (update_info_topics)
-- Sink: RDS (arrears_info, missing_person_info)
-- 기준 DDL: 사용자 제공 최종 스키마

SET 'execution.runtime-mode' = 'batch';
SET 'pipeline.name' = 'batch-update-reference-info';

-- ==========================================
-- 1. Kafka Source (Batch Mode)
-- ==========================================

-- 1.1 체납자 정보
CREATE TABLE kafka_update_arrears (
    `car_plate_number` STRING,
    `arrears_user_id` STRING,
    `total_arrears_amount` INT,
    `arrears_period` STRING,
    `notice_sent` TINYINT, -- Boolean
    `updated_at` TIMESTAMP(3)
) WITH (
    'connector' = 'kafka',
    'topic' = 'update_arrears_topic',
    'properties.bootstrap.servers' = 'kafka-cluster-kafka-bootstrap.kafka-kubernetes-operator.svc.cluster.local:9092',
    'properties.group.id' = 'batch-update-group',
    'scan.startup.mode' = 'earliest-offset',
    'format' = 'json'
);

-- 1.2 실종자 정보
-- DDL에서 'missing_feature' 컬럼이 추가됨을 확인하여 반영
CREATE TABLE kafka_update_missing (
    `missing_id` STRING,
    `missing_name` STRING,
    `missing_age` INT,
    `missing_identity` STRING,
    `missing_feature` STRING, -- 추가된 컬럼
    `registered_at` TIMESTAMP(3),
    `updated_at` TIMESTAMP(3),
    `missing_location` STRING
) WITH (
    'connector' = 'kafka',
    'topic' = 'update_missing_topic',
    'properties.bootstrap.servers' = 'kafka-cluster-kafka-bootstrap.kafka-kubernetes-operator.svc.cluster.local:9092',
    'format' = 'json'
);

-- ==========================================
-- 2. RDS Sink Tables
-- ==========================================

-- 2.1 체납자 정보
CREATE TABLE rds_sink_arrears_info (
    `car_plate_number` STRING,
    `arrears_user_id` STRING,
    `total_arrears_amount` INT,
    `arrears_period` STRING,
    `notice_sent` TINYINT, -- Boolean
    `updated_at` TIMESTAMP(3),
    PRIMARY KEY (`car_plate_number`) NOT ENFORCED
) WITH (
    'connector' = 'jdbc',
    'url' = 'jdbc:mysql://busan-maria.cf8s8geeaqc9.ap-northeast-2.rds.amazonaws.com:23306/car_db',
    'table-name' = 'arrears_info',
    'username' = 'root',
    'password' = 'busan!234pw'
);

-- 2.2 실종자 정보
CREATE TABLE rds_sink_missing_info (
    `missing_id` STRING,
    `missing_name` STRING,
    `missing_age` INT,
    `missing_identity` STRING,
    `missing_feature` STRING, -- 추가된 컬럼
    `registered_at` TIMESTAMP(3),
    `updated_at` TIMESTAMP(3),
    `missing_location` STRING,
    PRIMARY KEY (`missing_id`) NOT ENFORCED
) WITH (
    'connector' = 'jdbc',
    'url' = 'jdbc:mysql://busan-maria.cf8s8geeaqc9.ap-northeast-2.rds.amazonaws.com:23306/car_db',
    'table-name' = 'missing_person_info',
    'username' = 'root',
    'password' = 'busan!234pw'
);

-- ==========================================
-- 3. Execution
-- ==========================================

BEGIN STATEMENT SET;

INSERT INTO rds_sink_arrears_info SELECT * FROM kafka_update_arrears;
INSERT INTO rds_sink_missing_info SELECT * FROM kafka_update_missing;

END;
