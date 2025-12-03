-- busan_car 데이터베이스 스키마 정의
-- 이 파일은 실제 MariaDB에 접속하여 테이블을 생성할 때 사용합니다.

-- 1. 차량/운행 관련
CREATE TABLE `uservehicle` (
  `car_id` varchar(255) NOT NULL COMMENT '차량 고유 ID',
  `age` int(11) DEFAULT NULL COMMENT '운전자 나이',
  `user_sex` enum('남','여') DEFAULT NULL COMMENT '운전자 성별',
  `user_location` varchar(255) DEFAULT NULL COMMENT '운전자 주소',
  `user_car_class` varchar(255) DEFAULT NULL COMMENT '차량 용도',
  `user_car_brand` varchar(255) DEFAULT NULL COMMENT '차량 브랜드',
  `user_car_year` int(11) DEFAULT NULL COMMENT '차량 연식',
  `user_car_model` varchar(255) DEFAULT NULL COMMENT '차량 차종',
  `user_car_weight` int(11) DEFAULT NULL COMMENT '차량 중량',
  `user_car_displace` int(11) DEFAULT NULL COMMENT '차량 배기량',
  `user_car_efficiency` varchar(255) DEFAULT NULL COMMENT '차량 연비',
  `updated_at` datetime DEFAULT NULL COMMENT '차량 정보 변경일',
  PRIMARY KEY (`car_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

CREATE TABLE `driving_session` (
  `session_id` varchar(255) NOT NULL COMMENT '운행 세션 고유 ID',
  `car_id` varchar(255) DEFAULT NULL COMMENT '차량 고유 ID (FK)',
  `start_time` datetime DEFAULT NULL COMMENT '주행 시작 시간',
  `end_time` datetime DEFAULT NULL COMMENT '주행 종료 시간',
  `created_at` datetime DEFAULT NULL COMMENT '데이터 생성일',
  `updated_at` datetime DEFAULT NULL COMMENT '데이터 변경일',
  PRIMARY KEY (`session_id`),
  KEY `car_id` (`car_id`),
  CONSTRAINT `driving_session_ibfk_1` FOREIGN KEY (`car_id`) REFERENCES `uservehicle` (`car_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

CREATE TABLE `driving_session_info` (
  `info_id` char(36) NOT NULL DEFAULT uuid() COMMENT '운행기록 상세 정보ID(PK)',
  `session_id` varchar(255) DEFAULT NULL COMMENT '운행 세션 ID (FK)',
  `app_lat` double DEFAULT NULL COMMENT '현재 위도',
  `app_lon` double DEFAULT NULL COMMENT '현재 경도',
  -- ... 나머지 컬럼 생략 가능하나 원본 보존 ...
  `app_prev_lat` double DEFAULT NULL,
  `app_prev_lon` double DEFAULT NULL,
  `voltage` tinyint(4) DEFAULT NULL,
  `d_door` tinyint(4) DEFAULT NULL,
  `p_door` tinyint(4) DEFAULT NULL,
  `rd_door` tinyint(4) DEFAULT NULL,
  `rp_door` tinyint(4) DEFAULT NULL,
  `t_door` tinyint(4) DEFAULT NULL,
  `engine_status` tinyint(4) DEFAULT NULL,
  `r_engine_status` tinyint(4) DEFAULT NULL,
  `stt_alert` tinyint(4) DEFAULT NULL,
  `el_status` tinyint(4) DEFAULT NULL,
  `detect_shock` tinyint(4) DEFAULT NULL,
  `remain_remote` tinyint(4) DEFAULT NULL,
  `autodoor_use` tinyint(4) DEFAULT NULL,
  `silence_mode` tinyint(4) DEFAULT NULL,
  `low_voltage_alert` tinyint(4) DEFAULT NULL,
  `low_voltage_engine` tinyint(4) DEFAULT NULL,
  `temperature` tinyint(4) DEFAULT NULL,
  `app_travel` tinyint(1) DEFAULT NULL,
  `app_avg_speed` float DEFAULT NULL,
  `app_accel` float DEFAULT NULL,
  `app_gradient` float DEFAULT NULL,
  `app_rapid_acc` int(11) DEFAULT NULL,
  `app_rapid_deacc` int(11) DEFAULT NULL,
  `speed` float DEFAULT NULL,
  `createdDate` datetime DEFAULT NULL,
  `app_weather_status` varchar(255) DEFAULT NULL,
  `app_precipitation` float DEFAULT NULL,
  `dt` datetime DEFAULT NULL,
  `roadname` varchar(50) DEFAULT NULL,
  `treveltime` double DEFAULT NULL,
  `Hour` int(11) DEFAULT NULL,
  PRIMARY KEY (`info_id`),
  KEY `session_id` (`session_id`),
  CONSTRAINT `driving_session_info_ibfk_1` FOREIGN KEY (`session_id`) REFERENCES `driving_session` (`session_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

CREATE TABLE `vehicle_exterior_image` (
  `image_id` varchar(64) NOT NULL,
  `session_id` varchar(64) NOT NULL,
  `captured_lat` double DEFAULT NULL,
  `captured_lon` double DEFAULT NULL,
  `captured_at` datetime DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `image_base64` longtext DEFAULT NULL,
  PRIMARY KEY (`image_id`),
  KEY `idx_vei_session` (`session_id`,`captured_at`),
  CONSTRAINT `fk_vei_session` FOREIGN KEY (`session_id`) REFERENCES `driving_session` (`session_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

-- 2. 체납/실종/졸음 관련
CREATE TABLE `arrears_info` (
  `car_plate_number` varchar(20) NOT NULL,
  `arrears_user_id` varchar(64) DEFAULT NULL,
  `total_arrears_amount` int(11) DEFAULT NULL,
  `arrears_period` varchar(50) DEFAULT NULL,
  `notice_sent` tinyint(1) DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`car_plate_number`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

CREATE TABLE `arrears_detection` (
  `detection_id` varchar(64) NOT NULL,
  `image_id` varchar(64) NOT NULL,
  `car_plate_number` varchar(20) NOT NULL,
  `detection_success` tinyint(1) DEFAULT NULL,
  `detected_lat` double DEFAULT NULL,
  `detected_lon` double DEFAULT NULL,
  `detected_time` datetime DEFAULT NULL,
  PRIMARY KEY (`detection_id`),
  KEY `idx_arrears_image` (`image_id`,`detected_time`),
  KEY `idx_arrears_plate` (`car_plate_number`),
  CONSTRAINT `fk_arrears_image` FOREIGN KEY (`image_id`) REFERENCES `vehicle_exterior_image` (`image_id`),
  CONSTRAINT `fk_arrears_plate` FOREIGN KEY (`car_plate_number`) REFERENCES `arrears_info` (`car_plate_number`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

CREATE TABLE `missing_person_info` (
  `missing_id` varchar(64) NOT NULL,
  `missing_name` varchar(100) DEFAULT NULL,
  `missing_age` int(11) DEFAULT NULL,
  `missing_identity` varchar(255) DEFAULT NULL,
  `registered_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `missing_location` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`missing_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

CREATE TABLE `missing_person_detection` (
  `detection_id` varchar(64) NOT NULL,
  `image_id` varchar(64) NOT NULL,
  `missing_id` varchar(64) NOT NULL,
  `detection_success` tinyint(1) DEFAULT NULL,
  `detected_lat` double DEFAULT NULL,
  `detected_lon` double DEFAULT NULL,
  `detected_time` datetime DEFAULT NULL,
  PRIMARY KEY (`detection_id`),
  KEY `idx_mpd_image` (`image_id`,`detected_time`),
  KEY `idx_mpd_missing` (`missing_id`),
  CONSTRAINT `fk_mpd_image` FOREIGN KEY (`image_id`) REFERENCES `vehicle_exterior_image` (`image_id`),
  CONSTRAINT `fk_mpd_missing` FOREIGN KEY (`missing_id`) REFERENCES `missing_person_info` (`missing_id`)
) ENGINE=InnoDB DEFAULT CHARSET=armscii8 COLLATE=armscii8_general_ci;

CREATE TABLE `drowsy_drive` (
  `drowsy_id` varchar(64) NOT NULL,
  `session_id` varchar(64) NOT NULL,
  `detected_lat` double DEFAULT NULL,
  `detected_lon` double DEFAULT NULL,
  `detected_at` datetime DEFAULT NULL,
  `duration_sec` int(11) DEFAULT NULL,
  `gaze_closure` int(11) DEFAULT NULL,
  `head_drop` int(11) DEFAULT NULL,
  `yawn_flag` int(11) DEFAULT NULL,
  `abnormal_flag` int(11) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`drowsy_id`),
  KEY `idx_drowsy_session` (`session_id`,`detected_at`),
  CONSTRAINT `fk_drowsy_session` FOREIGN KEY (`session_id`) REFERENCES `driving_session` (`session_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

