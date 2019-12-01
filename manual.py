#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import shutil
from celery_app import app
import logging
import task
from video import Video
def test(check_dir):
    for dirpath,dirnames,filenames in os.walk(top=check_dir,topdown=True):
        if len(filenames):
            for file in filenames:
                fullpath = os.path.join(dirpath,file)
                print(fullpath)
                try:
                    task.upload_file_task.apply_async((fullpath,),queue='upload_file_tasks',routing_key='upload.s3')
                except Exception as e:
                    print(str(e))
                    #shutil.move(fullpath,"/mnt/iclassvideo/20190913/")
def get_cxg_first(file=None,dest_dir=None):
    video_dict = Video.get_course_video_byfile(file)
    for video_key,video_list in video_dict.items():
        tmp_dest_dir = os.path.join(dest_dir,video_key)
        for src_video in video_list:
            dest_video = os.path.join(tmp_dest_dir,src_video)
            print(dest_video)
            Video.download_video_single(src_video,dest_video,isabsolute=False)
def get_video(course_file=None,dest_dir=None):
    video_dict = Video.get_course_video_byfile(course_file="/tmp/longjiangang")
    for video_key,video_list in video_dict.items():
        print(video_list)
        print(video_key)
        tmp_dest_dir = os.path.join(dest_dir,video_key)
        for src_video in video_list:
            dest_video = os.path.join(tmp_dest_dir,src_video)
            print(dest_video)
            Video.download_video_single(src_video,dest_video,isabsolute=False)
    
if __name__ == "__main__":
    #test("/mnt/iclassvideo/errorbuffer")
    #get_cxg_first(file="/tmp/first",dest_dir="/tmp/cxg")
    get_video(course_file="/tmp/longjiangang",dest_dir="/mnt/dump")
