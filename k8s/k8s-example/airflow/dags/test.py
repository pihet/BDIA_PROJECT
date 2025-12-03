from airflow import DAG
from airflow.operators.empty import EmptyOperator
from datetime import datetime, timedelta

# 1. 기본 설정
default_args = {
    'owner': 'airflow',
    'start_date': datetime(2025, 12, 1),
    'retries': 1,
}

# 2. DAG 정의 (schedule='* * * * *' -> 1분마다 실행)
with DAG(
    dag_id='minutely_dag',
    default_args=default_args,
    description='Runs every 1 minute',
    schedule='* * * * *', 
    catchup=False, 
    tags=['example'],
) as dag:

    start = EmptyOperator(task_id='start')
    end = EmptyOperator(task_id='end')

    start >> end