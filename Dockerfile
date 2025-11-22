# 1. Airflow 공식 이미지를 [수정]: 'latest' 대신 안정적인 버전을 고정합니다.
# [수정] 'apache-airflow' -> 'apache/airflow' (슬래시 추가)
FROM apache/airflow:2.8.4

# 2. 루트 권한으로 전환 (시스템 라이브러리 설치용)
USER root

# 3. Spark에 필요한 Java(openjdk-17) 설치
# [수정] 'pip install mariadb'에 필요한 C컴파일러와 C라이브러리를 추가합니다.
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        openjdk-17-jre-headless \
        libmariadb-dev \
        build-essential \
    && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 4. [수정] Spark 3.4.1 버전으로 환경 변수 변경
# docker-compose.yml과 동일하게 JAVA_HOME 경로 설정 (Spark가 Java를 찾도록 명시)
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV SPARK_VERSION=3.4.1
ENV HADOOP_VERSION=3
ENV SPARK_HOME=/opt/spark
ENV PATH=$PATH:$SPARK_HOME/bin

# 5. [수정] Spark 3.4.1 설치 (로컬 파일 복사 및 압축 해제)
# 전제: 로컬 디렉토리에 1단계에서 다운로드한 spark-3.4.1-bin-hadoop3.tgz 파일이 존재해야 합니다.
COPY spark-3.4.1-bin-hadoop3.tgz /tmp/spark.tgz

# [수정] 보이지 않는 특수 공백 문자를 모두 일반 공백으로 수정했습니다.
RUN tar -xzf /tmp/spark.tgz -C /opt && \
    # [수정] mv 경로를 새 버전에 맞게 변경
    mv /opt/spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION} ${SPARK_HOME} && \
    rm /tmp/spark.tgz

# 6. Airflow 권한 설정을 위해 airflow 사용자로 전환
USER airflow

# 7. Airflow 사용자 권한으로 필요한 Python 라이브러리 설치
# (이 부분은 이전과 동일하며, 이제 C컴파일러가 있으므로 'mariadb' 설치가 성공할 것입니다)
RUN pip install --no-cache-dir \
    apache-airflow-providers-apache-spark \
    apache-airflow-providers-apache-kafka \
    mysql-connector-python \
    kafka-python \
    mariadb