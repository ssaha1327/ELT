from airflow import DAG
import pendulum
from datetime import timedelta, datetime
from api.video_stats import get_playlist_id, get_video_ids, extract_video_data, save_to_json

from airflow.operators.trigger_dagrun import TriggerDagRunOperator

from datawarehouse.dwh import staging_table, core_table
from dataquality.soda import yt_elt_data_quality_check



#define the local timezone
local_tz=pendulum.timezone('America/New_York')

# Default Args
default_args={
    'owner':'data_engineers',
    'depends_on_past':False,
    'email_on_failure':False,
    'email_on_retry':False,
    'email': 'data@engineers.com',
    'max_active_runs':1,
    'dagrun_timeout':timedelta(hours=1),
    'start_date':datetime(2026,5,13, tzinfo=local_tz),
    #'retries':1,
    #'retry_delay':timedelta(minutes=5)
    # end_date=datetime(2030,5,14, tzinfo=local_tz)
}

#variables
staging_schema='staging'
core_schema='core'

with DAG(
    dag_id='produce_json',
    default_args=default_args,
    description='A DAG to extract video stats from YouTube API and save it as JSON',
    schedule_interval= '0 14 * * *',
     catchup=False # every day at 2 PM
) as dag_produce:
    # Define tasks
    playlist_id = get_playlist_id()
    video_ids=get_video_ids(playlist_id)
    exctract_data=extract_video_data(video_ids)
    save_to_josn_task=save_to_json(exctract_data)
    
    trigger_update_db = TriggerDagRunOperator(
        task_id='trigger_update_db',
        trigger_dag_id='update_db',
    )

     # Define task dependencies
    playlist_id >> video_ids >> exctract_data >> save_to_josn_task >> trigger_update_db

with DAG(
    dag_id='update_db',
    default_args=default_args,
     catchup=False,
     schedule= None,
       # This DAG will be triggered by the produce_json DAG
) as dag_update:
    # Define tasks
    
    update_staging = staging_table()
    update_core= core_table()

    trigger_data_quality = TriggerDagRunOperator(
        task_id='trigger_data_quality',
        trigger_dag_id='data_quality',
    )

    # Define task dependencies
    update_staging >> update_core >> trigger_data_quality

with DAG(
    dag_id='data_quality',
    default_args=default_args,
        catchup=False,
        schedule= None,
) as dag_quality:
    # Define tasks
    
    soda_validate_staging = yt_elt_data_quality_check(staging_schema)
    soda_validate_core = yt_elt_data_quality_check(core_schema)

    # Define task dependencies
    soda_validate_staging >> soda_validate_core
   