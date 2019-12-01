#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import time
import datetime
from copy import deepcopy

import config
import task
from camera import Camera
from ffmpeg import FFmpeg
def test_mp4_task(duration=60*10,size=50):
    camera_info =Camera.get_camera_info_v2(size=size)
    res_camera_info=[]
    for i in range(0,size/len(camera_info)):
        print i
        camera_info_tmp = []
        for row in camera_info:
            tmp_row= deepcopy(row)
            tmp_row['room_code'] = "%s%s"%(row['room_code'],str(i))
            camera_info_tmp.append(tmp_row)
        res_camera_info.extend(camera_info_tmp)
    print len(res_camera_info)
    camera_info.extend(res_camera_info)
    camera_info = camera_info[:size]
    #for row in camera_info:
    #    print row['room_code']
    print(len(camera_info))
    video_dir = os.path.join(config.get('SHM_DIR'),'ts')
    now = datetime.datetime.now()+datetime.timedelta(seconds=60)
    start_time = now.strftime("%Y%m%d%H%M")
    stop_time = (now+datetime.timedelta(seconds=duration)).strftime("%Y%m%d%H%M")
    for camera in camera_info:
        path = video_dir
        filename = os.path.join(path,"%s-%s-%s-%s"%(camera['type'],camera['room_code'],start_time,stop_time))
        print(filename)
        task.ffmpeg_record_task.apply_async((duration,camera['rtsp_addr'],filename,0,0))
    print(len(camera_info))
def test_hls_task(duration=60*10,size=50,ts_time=60):
    camera_info =Camera.get_camera_info_v2(size=size)
    res_camera_info=[]
    for i in range(0,size/len(camera_info)):
        print i
        camera_info_tmp = []
        for row in camera_info:
            tmp_row= deepcopy(row)
            tmp_row['room_code'] = "%s%s"%(row['room_code'],str(i))
            camera_info_tmp.append(tmp_row)
        res_camera_info.extend(camera_info_tmp)
    print len(res_camera_info)
    camera_info.extend(res_camera_info)
    camera_info = camera_info[:size]
    #for row in camera_info:
    #    print row['room_code']
    print(len(camera_info))

    video_dir = os.path.join(config.get('SHM_DIR'),'ts')
    now = datetime.datetime.now()+datetime.timedelta(seconds=60)
    start_time = now.strftime("%Y%m%d%H%M")
    stop_time = (now+datetime.timedelta(seconds=duration)).strftime("%Y%m%d%H%M")
    for camera in camera_info:
        path = video_dir
        filename = os.path.join(path,"%s-%s-%s-%s"%(camera['type'],camera['room_code'],start_time,stop_time))
        print(filename)
        task.ffmpeg_record_task.apply_async((duration,camera['rtsp_addr'],filename,1,ts_time))
    print(len(camera_info))
if __name__ == "__main__":
    #test_hls_task(duration=60*20,size=50)
    res = task.issue_format_tasks.apply_async(date='20181008')
    print res
