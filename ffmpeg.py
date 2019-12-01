#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Package:celery_task
Author: wangqiang <wangqiang1989@xjtu.edu.cn>

Copyright (C) 2017 xjtunic. All Rights Reserved.
"""
import time
import datetime
import os
import shutil
import subprocess
import re
import logging

import config
class FFmpeg():
    logger = logging.getLogger(config.get('LOGGER_NAME'))
    shm_dir = config.get("SHM_DIR",'/dev/shm')
    FileCount=5
    RetryCount=20
    Sleep_time=30
    endpoint_url='test'    
    def __init__():
        pass
    
    @classmethod
    def run_live_task(cls,duration,cmd):
        local_cmd = cmd
        re_str = re.compile("-t[\s]+[^\s]*")
        while True:
            start_time=datetime.datetime.now()
            subprocess.call(cmd,shell=True)
            delta = (datetime.datetime.now()-start_time).seconds
            if delta < duration:
                duration = duration - delta
                local_cmd = re_str.sub("-t %s"%(duration),local_cmd)
                cls.logger.error("task %s halt restart task %s "%(cmd,local_cmd))
                continue
            else:
                cls.logger.info("task %s success "%cmd)
                break
        return True
    @classmethod
    def fast_start(cls,video_dir):
        """用ffmpeg读取文件并将结果放置在内存映射盘中,覆盖源文件"""
        for dirpath,dirnames,filenames in os.walk(video_dir):
            for file in filenames:
                if file.split('.')[0].endswith('_*'):
                    continue
                src_file = os.path.join(dirpath,file)
                dest_file = os.path.join(cls.shm_dir,os.path.basename(src_file))
                #处理断流问题
                for i in range(0,cls.FileCount):
                    tmpfile = '%s_%s.mp4'%(file.split('.')[0],i)
                    if tmpfile in filenames:
                        src_file+="|"+tmpfile                      
                    else:
                        break
                ffmpeg_cmd = """ffmpeg -v quiet -y -i concat:"%s" -vcodec copy -acodec copy -f mp4 -movflags faststart %s"""%(src_file,dest_file)
                result = os.system(ffmpeg_cmd)
                if result != 0 :
                    cls.logger.error('ffmpeg process file %s error ret %s'%(src_file,result))
                    #此处记日志，continue
                    continue
                try:
                   shutil.copy(dest_file,src_file)
                   os.remove(dest_file)
                except Exception as e:
                    cls.logger.error('move file %s %s  %s failed'%(dest_file,src_file,str(e)))
                    os.remove(dest_file)
                    #此处记日志，continue
                continue
                cls.logger.info("success process file %s "%(src_file))
        return 0
    @classmethod
    def run_mp4_task(cls,duration,rtsp_addr,filename,plan):
        """解决视频断流的问题,同时利用celery task的配置文件设置task最长运行时间"""
        duration = int(duration)
        new_filename = filename
        count=0
        retrycount=0
        result=True
        if not os.path.exists(os.path.dirname(filename)):
            cls.logger.info("create dir %s "%(os.path.dirname(filename)))
            os.makedirs(os.path.dirname(filename))
        
        if plan == 'MP4_CEPH_RGW':
            movflag = 'faststart'
        else:
            movflag = frag_keyframe+empty_moov
        while True:
            cmd ='ffmpeg -y -v quiet -stimeout 10000000  -t %s -i %s -movflags %s -timelimit %s -vcodec copy -acodec copy -f mp4  %s.mp4'%(duration,rtsp_addr,movflag,int(duration)+60,new_filename)
            cls.logger.info(cmd)
            start_time=datetime.datetime.now()
            r = subprocess.call(cmd,shell=True)
            #需要判断异常退出情况，正常退出的就不要处理了
            if r == 0:
                cls.logger.info("task %s success "%cmd)
                break
            delta = (datetime.datetime.now()-start_time).seconds
            if count > cls.FileCount or retrycount > cls.RetryCount:
                result = False
                break
            if delta < duration:
                duration = int(duration) - delta
                if os.path.exists(new_filename):
                    new_filename = '%s_%s'%(filename,count)
                    count=count+1
                else:
                    time.sleep(cls.Sleep_time)
                    retrycount=retrycount+1
                    duration=duration-cls.Sleep_time
                cls.logger.error("task %s halt restart task "%(cmd))
                continue
            else:
                cls.logger.info("task %s success "%cmd)
                break
        return result

    @classmethod
    def run_hls_task(cls,duration,rtsp_addr,filename,multi_flag=False,ts_time=60):
        """解决视频断流的问题,同时利用celery task的配置文件设置task最长运行时间"""
        #this filename should be ts name or m3u8 name?
        new_filename = filename
        count=0
        retrycount=0
        result=True
        if not os.path.exists(os.path.dirname(filename)):
            cls.logger.info("create dir %s "%(os.path.dirname(filename)))
            os.makedirs(os.path.dirname(filename))
        duration = int(duration)
        ts_time=int(ts_time)
        while True:
            #one in multi out
            #first of all should create top m3u8 index file
            bucket = new_filename.split('-')[1]
            top_filename = "%s.m3u8"%(new_filename)
            high_filename = os.path.join(cls.endpoint_url,"%s/%s_high.m3u8"%(bucket,os.path.basename(new_filename)))
            low_filename = os.path.join(cls.endpoint_url,"%s/%s_low.m3u8"%(bucket,os.path.basename(new_filename)))
            if multi_flag:
                cls.create_top_index(top_filename,high_filename,low_filename)
                cmd ="/usr/bin/ffmpeg -y -v quiet -stimeout 100000000 -t %s -i %s  -timelimit %s -vcodec h264 -acodec aac  -filter_complex '[0:v]yadif,split=2[out1][out2]'  -map '[out1]' -hls_segment_filename %s.ts -f hls -hls_time %d %s.m3u8 -map '[out2]' -s 640x480 -hls_segment_filename %s.ts -f hls -hls_time 60 %s.m3u8"%(duration,rtsp_addr,duration+
60,ts_time,new_filename+'_high_%d',new_filename+'_high',new_filename+'_low_%d',new_filename+'_low')
            else:
                cmd ='/usr/bin/ffmpeg -y -v quiet -stimeout 100000000  -t %s -i %s  -timelimit %s -vcodec copy -acodec copy -f hls -hls_time %d -hls_list_size 0 -hls_segment_filename %s.ts %s.m3u8'%(duration,rtsp_addr,int(duration)+60,int(ts_time),new_filename+'_%d',new_filename)
            start_time=datetime.datetime.now()
            r = subprocess.call(cmd,shell=True)
            #需要判断异常退出情况，正常退出的就不要处理了
            if r == 0:
                cls.logger.info("task %s success "%cmd)
                break
            delta = (datetime.datetime.now()-start_time).seconds
            if count > cls.FileCount or retrycount > cls.RetryCount:
                result = False
                break
            if delta < duration:
                duration = duration - delta
                if os.path.exists(new_filename+'.m3u8'):
                    new_filename = '%s_%s'%(filename,count)
                    count=count+1
                else:
                    time.sleep(cls.Sleep_time)
                    retrycount=retrycount+1
                    duration=duration-cls.Sleep_time
                cls.logger.error("task %s halt restart task "%(cmd))
                continue
            else:
                cls.logger.info("task %s success "%cmd)
                break
        return result

    @classmethod
    def create_top_index(cls,top_filename,high_filename,low_filename):
        """生成顶级索引文件"""
        top_index_content = """#EXTM3U
#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=1280000
%s
#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=2560000
%s
"""%(low_filename,high_filename)
        result = True
        fp = open(top_filename,'w')
        try:
            fp.write(top_index_content)
        except Exception as e:
            cls.logger.error('write top file %s failed'%(top_filename))
            result = False
        finally:
            fp.close()
        return result
