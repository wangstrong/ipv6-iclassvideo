# -*- coding: utf-8 -*-

from kombu import Exchange,Queue
from datetime import timedelta
from celery.schedules import crontab
from dbmanager import DBManager
#BROKER_URL = 'amqp://iclassvideo:rabbitmq_media2019@10.32.166.254:5672/iclassvideo_vhost'
BROKER_URL = 'redis://127.0.0.1:6379/7'

CELERY_TASK_SERIALIZER = 'msgpack'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT =['json','msgpack']
#考虑不存储结果
CELERY_RESULT_BACKEND = 'redis://127.0.0.1:6379/10'
#CELERY_RESULT_BACKEND = 'amqp://iclassvideo:rabbitmq_media2019@10.32.166.254:5672/iclassvideo_vhost'
CELERY_TIMEZONE='Asia/Shanghai'
#ENABLE_UTC = False
CELERY_TASK_RESULT_EXPIRES = 60*60*24

#不通类型设置不通的参数

#CELERYD_CONCURRENCY =10 #并发的woker数量
CELERYD_PREFETCH_MULTIPLIER = 30 #celery worker 每次去rabbitmq取任务的数量?,这里不适用预取
CELERYD_TASK_TIME_LIMIT =60*60*2 #每个task执行的最长时间，超过这个时间杀死task
CELERYD_MAX_TASKS_PER_CHILD = 40 #每个worker执行多少个task之后，销毁,释放内存，重建



CELERY_DEFAULT_EXCHANGE = 'default'
CELERY_DEFAULT_EXCHANGE_TYPE = 'default'
CELERY_DEFAULT_ROUTING_KEY = 'default'

CELERY_QUEUES = ( #定义队列
    Queue('default',routing_key='default'),
    Queue('ffmpeg_live_tasks',routing_key='ffmpeg.live#'),
    Queue('ffmpeg_record_tasks',routing_key='ffmpeg.record#'),
    Queue('ffmpeg_format_tasks',routing_key='ffmpeg.format#'),
    Queue('upload_file_tasks',routing_key='upload.s3#'),
    Queue('download_file_tasks',routing_key='download.s3#'),
)

CELERY_ROUTES = {
    'iclassvideo.task.ffmpeg_live_task':{
            'queue': 'ffmpeg_live_tasks',
            'routing_key': 'ffmpeg.live'
    },
    'iclassvideo.task.ffmpeg_record_task':{
            'queue': 'ffmpeg_record_tasks',
            'routing_key': 'ffmpeg.record'
    },
    'iclassvideo.task.ffmpeg_format_task':{
            'queue': 'ffmpeg_format_tasks',
            'routing_key': 'ffmpeg.format'
    },
    'iclassvideo.task.upload_file_task':{
            'queue': 'upload_file_tasks',
            'routing_key': 'upload.s3'
    },
    'iclassvideo.task.download_file_task':{
            'queue': 'download_file_tasks',
            'routing_key': 'download.s3'
    },
}

CELERYBEAT_SCHEDULE = {
    'ffmpeg-video-each-hour-am': {
        'task': 'iclassvideo.task.issue_record_tasks',
        'schedule': crontab(minute=59,hour='23-2'),#7-10
        'args': ([60*60,'MP4_CEPH_RGW',[],7,True]),
        "options":{'queue':'issue_record_tasks'}
    },

    'ffmpeg-video-each-hour-win-pm': {
        'task': 'iclassvideo.task.issue_record_tasks',
        'schedule': crontab(minute=59,hour='5-8,10-11',month_of_year='1-4,10-12'),#13-16,18-19
        'args': ([60*60,'MP4_CEPH_RGW',[],7,True]),
        "options":{'queue':'issue_record_tasks'}
    },

    'ffmpeg-video-each-hour-sum-pm': {
        'task': 'iclassvideo.task.issue_record_tasks',
        'schedule': crontab(minute=59,hour='6-9,11-13',month_of_year='5-9'), #14-17,19-20
        'args': ([60*60,'MP4_CEPH_RGW',[],7,True]),
        "options":{'queue':'issue_record_tasks'}
    }
}
"""
    'sync_data_each_day': {
        'task': 'iclassvideo.task.sync_data_task',
        'schedule': crontab(minute=2,hour='10'), #2:02
        'args': ()
    },
    'upload_data_each_day': {
        'task': 'iclassvideo.task.issue_upload_file_task',
        'schedule': crontab(minute=2,hour='9'), #1:02
        'args': (["/mnt/iclassvideo/"])
    }
}
    'ffmpeg-video-format': {
        'task': 'iclassvideo.task.issue_format_tasks',
        'schedule': crontab(minute=30,hour='14'),
        'args': ([None]),
        "options":{'queue':'issue_format_tasks'}
    }
"""
