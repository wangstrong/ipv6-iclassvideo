#!/usr/bin/env python
# -*- encoding: utf-8 -*-


import logging
import logging.config
import datetime
import time
import os
import subprocess
from multiprocessing import Process

import config

from celery_app import app
from ffmpeg import FFmpeg
from camera import Camera 
from sync_data import SyncData
import upload
import download
from celery.contrib.abortable import AbortableTask


hdfs_basedir = config.get("HDFS_BASEDIR")
ceph_basedir = config.get("CEPH_BASEDIR")
buffer_dir =  config.get("BUFFER_DIR")
shm_dir = config.get('SHM_DIR')
logger = logging.getLogger(config.get('LOGGER_NAME'))

"""同步camera信息"""
@app.task(bind=True,base=AbortableTask)
def sync_data_task(self):
    res = SyncData.sync_camera_info()
    return res

"""定期发布upload任务"""
@app.task(bind=True,base=AbortableTask,name='task.issue_upload_file_task')
def issue_upload_file_task(self,dir=None):
    if not dir or not os.path.exists(dir):
        return False
    result=0
    for dirpath,dirnames,filenames in os.walk(top=dir,topdown=True):
        if len(filenames):
            for file in filenames:
                fullpath = os.path.join(dirpath,file)
                try:
                    task.upload_file_task.apply_async((fullpath,),queue='upload_file_tasks',routing_key='upload.s3')
                except Exception as e:
                    logger.error("issue upload task for file %s error %s"%(fullpath,str(e)))
                result=result+1
    return result

"""上传文件任务"""
@app.task(bind=True,base=AbortableTask,name='task.upload_file_task')
def upload_file_task(self,filename):
    res = upload.upload_file_to_s3(filename)
    return res

"""下载文件任务"""
@app.task(bind=True,base=AbortableTask,name='task.download_file_task')
def download_file_task(self,bucket,filename,dest_dir):
    res = download.download_file_from_s3(bucket,filename,dest_dir)
    return res

"""直播work 运行的程序"""
@app.task(bind=True,base=AbortableTask)
def ffmpeg_live_task(self,duration,cmd):
    if self.is_aborted():
        return True
    res = FFmpeg.run_live_task(duration,cmd)
    return res


@app.task(bind=True,base=AbortableTask)
def ffmpeg_format_task(self,video_dir):
    if self.is_aborted():
        return True
    res = FFmpeg.fast_start(video_dir=video_dir)
    return res

"""控制端定时运行的程序进行下发转码任务"""
@app.task
def issue_format_tasks(date=None):
    rooms = Camera.get_room_code()
    if not date:
        date = datetime.datetime.now().strftime("%Y%m%d")
    base_video_dir = os.path.join(config.get("HDFS_BASE_DIR"),date)
    for room in rooms:
        video_dir = os.path.join(base_video_dir,str(room['room_code']))
        ffmpeg_format_task.apply_async((video_dir,))

@app.task
def test_hls_task(duration=60*10,size=50):
    camera_info =Camera.get_camera_info_v2(size=size)
    video_dir = os.path.join(config.get('SHM_DIR'),'ts')
    now = datetime.datetime.now()+datetime.timedelta(seconds=60)
    start_time = now.strftime("%Y%m%d%H%M")
    stop_time = (now+datetime.timedelta(seconds=duration)).strftime("%Y%m%d%H%M")
    for camera in camera_info:
        path = video_dir
        filename = os.path.join(path,"%s-%s-%s-%s"%(camera['type'],camera['room_code'],start_time,stop_time))
        #print(filename)
        ffmpeg_record_task.apply_async((duration,camera['rtsp_addr'],filename,1))

"""控制端定时运行的程序进行视频采集任务"""
@app.task
def issue_record_tasks(duration=60*60,plan='MP4_CEPH_RGW',room_code_list=['11200','11203','11204'],camera_type=7,iclass=False):
    """ MP4_HDFS_FUSE,MP4_CEPH_NFS,MP4_CEPH_RGW,HLS_CEPH_RGW"""
    #plan = 'HLS_CEPH_RGW'
    room_code_list=['11200','11203','11204']
    iclass=False
    camera_info =Camera.get_camera_info(room_code_list=room_code_list,camera_type=camera_type,iclass=iclass)
    if plan =='MP4_HDFS_FUSE':
        base_dir = hdfs_basedir
    elif plan =='MP4_CEPH_NFS':
        base_dir = ceph_basedir
    elif plan =='MP4_CEPH_RGW':
        base_dir = buffer_dir
    elif plan =='HLS_CEPH_RGW':
        base_dir = shm_dir
    else:
        return False

    now = datetime.datetime.now()+datetime.timedelta(seconds=60)
    start_time = now.strftime("%Y%m%d%H%M")
    stop_time = (now+datetime.timedelta(seconds=duration)).strftime("%Y%m%d%H%M")
    
    for camera in camera_info:
        if plan =='HLS_CEPH_RGW' or plan =='MP4_CEPH_RGW':
            video_dir = base_dir
        else:
            video_dir = os.path.join(os.path.join(base_dir,datetime.datetime.now().strftime("%Y%m%d")),str(camera['room_code']))

        if not os.path.exists(video_dir):
            os.makedirs(video_dir)
        filename = os.path.join(video_dir,"%s-%s-%s-%s"%(camera['type'],camera['room_code'],start_time,stop_time))
        #ffmpeg_record_task.apply_async((duration,camera['rtsp_addr'],filename,plan))
        ffmpeg_record_task.apply_async((duration,camera['rtsp_addr'],filename,'MP4_CEPH_RGW'),queue='ffmpeg_record_tasks',routing_key='ffmpeg.record')
        ffmpeg_record_task.apply_async((duration,camera['rtsp_addr'],filename,'HLS_CEPH_RGW'),queue='ffmpeg_record_tasks',routing_key='ffmpeg.record')
        logger.info('%s'%camera['rtsp_addr'])
"""录播worker 需要运行的程序"""
@app.task(bind=True,base=AbortableTask)
def ffmpeg_record_task(self,duration,rtsp_addr,filename,plan='MP4_CEPH_RGW'):
    logger.info(filename)
    #if self.is_aborted():
    #    return True
    res = True
    if plan in ["MP4_HDFS_FUSE","MP4_CEPH_NFS","MP4_CEPH_RGW"]:
        str_cmd = "python /home/git/iclassvideo/mp4.py %s %s %s %s"%(duration,rtsp_addr,filename,plan)
        subprocess.Popen(str_cmd,shell=True)
        #res = FFmpeg.run_record_task(duration,rtsp_addr,filename)
    elif plan == 'HLS_CEPH_RGW':
        # hls.py should be change 使用这个方式的原因是防止celery task并发数的限制,缺点是不能知晓程序返回结果
        str_cmd = "python /home/git/iclassvideo/hls.py  %s %s %s"%(duration,rtsp_addr,filename)
        subprocess.Popen(str_cmd,shell=True)
        #res = FFmpeg.run_hls_task(duration,rtsp_addr,filename,False)
        #res = FFmpeg.run_hls_task(duration,rtsp_addr,filename,True,ts_time)
    else:
        res=False
    return res
if __name__ == "__main__":
    #sync_data_task()
    issue_record_tasks(duration=60*10,plan='MP4_CEPH_RGW',room_code_list=['11200','11203','11204'],camera_type=7)
    #ffmpeg_record_task(60*5,"rtsp://admin:jiaoshi2015@10.37.0.2:554/h264/ch1/main/av_stream","/mnt/iclassvideo/buffer/0-11200-201911291600-201911291700",plan='HLS_CEPH_RGW')    
