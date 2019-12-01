#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import os
import shutil
import sys
import subprocess

import pyinotify

from s3utils import S3Utils

DIRMASK = pyinotify.IN_CLOSE_WRITE

from celery_app import app
import config
import logging
import task

plan = config.get("PLAN","MP4_CEPH_RGW")
count=0
logger = logging.getLogger(config.get('LOGGER_NAME'))

class EventHandler(pyinotify.ProcessEvent):
    """事件处理,调用外部程序不等待,需要测试并发上传大文件是否有问题"""
    def process_IN_CLOSE_WRITE(self, event):
        """
        global count
        if count == 10:
            random_int = random.uniform(0,10)
            time.sleep(random_int)
            print(random_int)
            count =0
        count=count+1
        """
        event_path = event.path
        event_name = event.name
        file_name = os.path.join(event_path,event_name)
        #if file_name.endswith("tmp"):
        #    logger.error("m3u8 file name %s"%file_name)
        #    os.remove(file_name)
        #    return
        logger.info("file %s closed"%file_name)
        """ 
        str_cmd = "python upload.py %s"%(file_name)
        subprocess.Popen(str_cmd,shell=True)
        """ 
        """替换为服务任务的方式"""
        try:
            task.upload_file_task.apply_async((file_name,),queue='upload_file_tasks',routing_key='upload.s3')
        except Exception as e:
            logger.error(str(e))
class FSMon(object):
    def __init__(self,path):
        self._mon_path = path
        self._notifier = None

        self._init()

    def __del__(self):
        self._notifier.stop()

    def _init(self):
        wm = pyinotify.WatchManager()
        wm.add_watch(self._mon_path, DIRMASK)
        self._notifier = pyinotify.Notifier(wm, EventHandler())

    def run(self):
        while True:
            try:
                self._notifier.process_events()
                if self._notifier.check_events():
                    self._notifier.read_events()
            except Exception as e:
                print(str(e))
                self.__del__()
                break

if __name__ == "__main__":
    if plan in ["MP4_CEPH_RGW","HLS_CEPH_RGW"]:
        mon_dir = config.get('BUFFER_DIR','/dev/shm/')
    elif plan in ['HLS_CEPH_RGW']:
        mon_dir = config.get('SHM_DIR','/dev/shm/')
    else:
        logger.info("plan is %s no need to monitor dir"%plan)
    fsmon = FSMon(mon_dir)
    fsmon.run()
