-- Job 1: 전체 Raw 데이터 실시간 수집 (Streaming)
-- Source: RDS (uservehicle, driving_session, driving_session_info, vehicle_exterior_image, drowsy_drive, missing_person_detection, arrears_detection)
-- Sink: Kafka (각 테이블별 1:1 토픽)
-- 설명: 주요 테이블 7개를 Kafka로 1:1 미러링합니다. (최종 DDL 반영)

SET 'execution.runtime-mode' = 'streaming';
SET 'sql-client.execution.result-mode' = 'tableau';
SET 'pipeline.name' = 'ingest-all-raw-data';

-- ==========================================
-- 1. Source Tables (RDS)
-- ==========================================

-- 1.1 차량 정보
CREATE TABLE rds_uservehicle (
    `car_id` STRING,
    `age` INT,
    `user_sex` STRING,
    `user_location` STRING,
    `user_car_class` STRING,
    `user_car_brand` STRING,
    `user_car_year` INT,
    `user_car_model` STRING,
    `user_car_weight` INT,
    `user_car_displace` INT,
    `user_car_efficiency` STRING,
    `updated_at` TIMESTAMP(3)
) WITH (
    'connector' = 'jdbc',
    'url' = 'jdbc:mysql://busan-maria.cf8s8geeaqc9.ap-northeast-2.rds.amazonaws.com:23306/car_db',
    'table-name' = 'uservehicle',
    'username' = 'root',
    'password' = 'busan!234pw'
);

-- 1.2 운행 세션
CREATE TABLE rds_driving_session (
    `session_id` STRING,
    `car_id` STRING,
    `start_time` TIMESTAMP(3),
    `end_time` TIMESTAMP(3),
    `created_at` TIMESTAMP(3),
    `updated_at` TIMESTAMP(3)
) WITH (
    'connector' = 'jdbc',
    'url' = 'jdbc:mysql://busan-maria.cf8s8geeaqc9.ap-northeast-2.rds.amazonaws.com:23306/car_db',
    'table-name' = 'driving_session',
    'username' = 'root',
    'password' = 'busan!234pw'
);

-- 1.3 운행 상세 정보
CREATE TABLE rds_driving_session_info (
    `info_id` STRING,
    `session_id` STRING,
    `app_lat` DOUBLE,
    `app_lon` DOUBLE,
    `app_prev_lat` DOUBLE,
    `app_prev_lon` DOUBLE,
    `voltage` TINYINT,
    `d_door` TINYINT,
    `p_door` TINYINT,
    `rd_door` TINYINT,
    `rp_door` TINYINT,
    `t_door` TINYINT,
    `engine_status` TINYINT,
    `r_engine_status` TINYINT,
    `stt_alert` TINYINT,
    `el_status` TINYINT,
    `detect_shock` TINYINT,
    `remain_remote` TINYINT,
    `autodoor_use` TINYINT,
    `silence_mode` TINYINT,
    `low_voltage_alert` TINYINT,
    `low_voltage_engine` TINYINT,
    `temperature` TINYINT,
    `app_travel` TINYINT, -- Boolean
    `app_avg_speed` FLOAT,
    `app_accel` FLOAT,
    `app_gradient` FLOAT,
    `app_rapid_acc` INT,
    `app_rapid_deacc` INT,
    `speed` FLOAT,
    `createdDate` TIMESTAMP(3),
    `app_weather_status` STRING,
    `app_precipitation` FLOAT,
    `dt` TIMESTAMP(3),
    `roadname` STRING,
    `treveltime` DOUBLE,
    `Hour` INT
) WITH (
    'connector' = 'jdbc',
    'url' = 'jdbc:mysql://busan-maria.cf8s8geeaqc9.ap-northeast-2.rds.amazonaws.com:23306/car_db',
    'table-name' = 'driving_session_info',
    'username' = 'root',
    'password' = 'busan!234pw'
);

-- 1.4 차량 외부 이미지 (image_base64 LONGTEXT -> STRING)
CREATE TABLE rds_vehicle_exterior_image (
    `image_id` STRING,
    `session_id` STRING,
    `captured_lat` DOUBLE,
    `captured_lon` DOUBLE,
    `captured_at` TIMESTAMP(3),
    `created_at` TIMESTAMP(3),
    `updated_at` TIMESTAMP(3),
    `image_base64` STRING
) WITH (
    'connector' = 'jdbc',
    'url' = 'jdbc:mysql://busan-maria.cf8s8geeaqc9.ap-northeast-2.rds.amazonaws.com:23306/car_db',
    'table-name' = 'vehicle_exterior_image',
    'username' = 'root',
    'password' = 'busan!234pw'
);

-- 1.5 졸음 운전
CREATE TABLE rds_drowsy_drive (
    `drowsy_id` STRING,
    `session_id` STRING,
    `detected_lat` DOUBLE,
    `detected_lon` DOUBLE,
    `detected_at` TIMESTAMP(3),
    `duration_sec` INT,
    `gaze_closure` INT,
    `head_drop` INT,
    `yawn_flag` INT,
    `abnormal_flag` INT,
    `created_at` TIMESTAMP(3),
    `updated_at` TIMESTAMP(3)
) WITH (
    'connector' = 'jdbc',
    'url' = 'jdbc:mysql://busan-maria.cf8s8geeaqc9.ap-northeast-2.rds.amazonaws.com:23306/car_db',
    'table-name' = 'drowsy_drive',
    'username' = 'root',
    'password' = 'busan!234pw'
);

-- 1.6 체납 탐지 결과
CREATE TABLE rds_arrears_detection (
    `detection_id` STRING,
    `image_id` STRING,
    `car_plate_number` STRING,
    `detection_success` TINYINT, -- Boolean
    `detected_lat` DOUBLE,
    `detected_lon` DOUBLE,
    `detected_time` TIMESTAMP(3)
) WITH (
    'connector' = 'jdbc',
    'url' = 'jdbc:mysql://busan-maria.cf8s8geeaqc9.ap-northeast-2.rds.amazonaws.com:23306/car_db',
    'table-name' = 'arrears_detection',
    'username' = 'root',
    'password' = 'busan!234pw'
);

-- 1.7 실종자 탐지 결과
CREATE TABLE rds_missing_person_detection (
    `detection_id` STRING,
    `image_id` STRING,
    `missing_id` STRING,
    `detection_success` TINYINT, -- Boolean
    `detected_lat` DOUBLE,
    `detected_lon` DOUBLE,
    `detected_time` TIMESTAMP(3)
) WITH (
    'connector' = 'jdbc',
    'url' = 'jdbc:mysql://busan-maria.cf8s8geeaqc9.ap-northeast-2.rds.amazonaws.com:23306/car_db',
    'table-name' = 'missing_person_detection',
    'username' = 'root',
    'password' = 'busan!234pw'
);

-- ==========================================
-- 2. Sink Tables (Kafka)
-- ==========================================

CREATE TABLE kafka_uservehicle (
    `car_id` STRING,
    `age` INT,
    `user_sex` STRING,
    `user_location` STRING,
    `user_car_class` STRING,
    `user_car_brand` STRING,
    `user_car_year` INT,
    `user_car_model` STRING,
    `user_car_weight` INT,
    `user_car_displace` INT,
    `user_car_efficiency` STRING,
    `updated_at` TIMESTAMP(3)
) WITH (
    'connector' = 'kafka',
    'topic' = 'raw_uservehicle',
    'properties.bootstrap.servers' = 'kafka-cluster-kafka-bootstrap.kafka-kubernetes-operator.svc.cluster.local:9092',
    'format' = 'json'
);

CREATE TABLE kafka_driving_session (
    `session_id` STRING,
    `car_id` STRING,
    `start_time` TIMESTAMP(3),
    `end_time` TIMESTAMP(3),
    `created_at` TIMESTAMP(3),
    `updated_at` TIMESTAMP(3)
) WITH (
    'connector' = 'kafka',
    'topic' = 'raw_driving_session',
    'properties.bootstrap.servers' = 'kafka-cluster-kafka-bootstrap.kafka-kubernetes-operator.svc.cluster.local:9092',
    'format' = 'json'
);

CREATE TABLE kafka_driving_session_info (
    `info_id` STRING,
    `session_id` STRING,
    `app_lat` DOUBLE,
    `app_lon` DOUBLE,
    `app_prev_lat` DOUBLE,
    `app_prev_lon` DOUBLE,
    `voltage` TINYINT,
    `d_door` TINYINT,
    `p_door` TINYINT,
    `rd_door` TINYINT,
    `rp_door` TINYINT,
    `t_door` TINYINT,
    `engine_status` TINYINT,
    `r_engine_status` TINYINT,
    `stt_alert` TINYINT,
    `el_status` TINYINT,
    `detect_shock` TINYINT,
    `remain_remote` TINYINT,
    `autodoor_use` TINYINT,
    `silence_mode` TINYINT,
    `low_voltage_alert` TINYINT,
    `low_voltage_engine` TINYINT,
    `temperature` TINYINT,
    `app_travel` TINYINT,
    `app_avg_speed` FLOAT,
    `app_accel` FLOAT,
    `app_gradient` FLOAT,
    `app_rapid_acc` INT,
    `app_rapid_deacc` INT,
    `speed` FLOAT,
    `createdDate` TIMESTAMP(3),
    `app_weather_status` STRING,
    `app_precipitation` FLOAT,
    `dt` TIMESTAMP(3),
    `roadname` STRING,
    `treveltime` DOUBLE,
    `Hour` INT
) WITH (
    'connector' = 'kafka',
    'topic' = 'raw_driving_session_info',
    'properties.bootstrap.servers' = 'kafka-cluster-kafka-bootstrap.kafka-kubernetes-operator.svc.cluster.local:9092',
    'format' = 'json'
);

CREATE TABLE kafka_vehicle_exterior_image (
    `image_id` STRING,
    `session_id` STRING,
    `captured_lat` DOUBLE,
    `captured_lon` DOUBLE,
    `captured_at` TIMESTAMP(3),
    `created_at` TIMESTAMP(3),
    `updated_at` TIMESTAMP(3),
    `image_base64` STRING
) WITH (
    'connector' = 'kafka',
    'topic' = 'raw_vehicle_exterior_image',
    'properties.bootstrap.servers' = 'kafka-cluster-kafka-bootstrap.kafka-kubernetes-operator.svc.cluster.local:9092',
    'format' = 'json'
);

CREATE TABLE kafka_drowsy_drive (
    `drowsy_id` STRING,
    `session_id` STRING,
    `detected_lat` DOUBLE,
    `detected_lon` DOUBLE,
    `detected_at` TIMESTAMP(3),
    `duration_sec` INT,
    `gaze_closure` INT,
    `head_drop` INT,
    `yawn_flag` INT,
    `abnormal_flag` INT,
    `created_at` TIMESTAMP(3),
    `updated_at` TIMESTAMP(3)
) WITH (
    'connector' = 'kafka',
    'topic' = 'raw_drowsy_drive',
    'properties.bootstrap.servers' = 'kafka-cluster-kafka-bootstrap.kafka-kubernetes-operator.svc.cluster.local:9092',
    'format' = 'json'
);

CREATE TABLE kafka_arrears_detection (
    `detection_id` STRING,
    `image_id` STRING,
    `car_plate_number` STRING,
    `detection_success` TINYINT,
    `detected_lat` DOUBLE,
    `detected_lon` DOUBLE,
    `detected_time` TIMESTAMP(3)
) WITH (
    'connector' = 'kafka',
    'topic' = 'raw_arrears_detection',
    'properties.bootstrap.servers' = 'kafka-cluster-kafka-bootstrap.kafka-kubernetes-operator.svc.cluster.local:9092',
    'format' = 'json'
);

CREATE TABLE kafka_missing_person_detection (
    `detection_id` STRING,
    `image_id` STRING,
    `missing_id` STRING,
    `detection_success` TINYINT,
    `detected_lat` DOUBLE,
    `detected_lon` DOUBLE,
    `detected_time` TIMESTAMP(3)
) WITH (
    'connector' = 'kafka',
    'topic' = 'raw_missing_person_detection',
    'properties.bootstrap.servers' = 'kafka-cluster-kafka-bootstrap.kafka-kubernetes-operator.svc.cluster.local:9092',
    'format' = 'json'
);

-- ==========================================
-- 3. Execution (Statement Set)
-- ==========================================

BEGIN STATEMENT SET;

INSERT INTO kafka_uservehicle SELECT * FROM rds_uservehicle;
INSERT INTO kafka_driving_session SELECT * FROM rds_driving_session;
INSERT INTO kafka_driving_session_info SELECT * FROM rds_driving_session_info;
INSERT INTO kafka_vehicle_exterior_image SELECT * FROM rds_vehicle_exterior_image;
INSERT INTO kafka_drowsy_drive SELECT * FROM rds_drowsy_drive;
INSERT INTO kafka_arrears_detection SELECT * FROM rds_arrears_detection;
INSERT INTO kafka_missing_person_detection SELECT * FROM rds_missing_person_detection;

END;
