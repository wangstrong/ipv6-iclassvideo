#!/bin/env python
# -*- coding: utf-8 -*-

"""
Author: wangqiang <wangqiang1989@xjtu.edu.cn>
Copyright (C) 2017 xjtu. All Rights Reserved.
"""
import sys
import os
import shutil
import datetime
import re
import csv

import logging
import logging.config
import config
from dbmanager import DBManager
from schedule import Schedule
from s3utils_v2 import S3Utils_v2

class Video():
    logger = logging.getLogger(config.get('LOGGER_NAME'))
    roomname_code={}
    plan = config.get("PLAN","MP4_CEPH_RGW")
    classvideo_template = config.get('CLASSVIDEO_TEMPLATE','/tmp/iclassvideo_template')
    if plan is 'MP4_HDFS_FUSE':
        base_dir = config.get("HDFS_BASEDIR")
    elif plan is 'MP4_CEPH_NFS':
        base_dir = config.get("CEPH_BASEDIR")
    elif plan is "MP4_CEPH_RGW":
        base_dir = config.get("CEPH_BASEDIR")

    def __init__(self):
        pass
    @classmethod
    def data2file(cls,data=None,filename=None):
        if not data or not filename:
            return False
        filepath = os.path.dirname(filename)
        if not os.path.exists(filepath):
            os.makedirs(filepath)
        try:
            with open(filename,mode='w') as f:
                for row in data:
                    f.write(row+"\n")
                f.close()
                cls.logger.info("Success create file %s"%(filename))
                return True
        except Exception as e:
            cls.logger.error("error create file %s error reson is %s"%(filename,str(e)))
            return False
    @classmethod
    def getDateList(cls,startDateStr,endDateStr):
        date_list = []
        start_date = datetime.datetime.strptime(startDateStr, "%Y%m%d")
        end_date = datetime.datetime.strptime(endDateStr, "%Y%m%d")
        while start_date <= end_date:
            date_str = start_date.strftime("%Y%m%d")
            date_list.append(date_str)
            start_date += datetime.timedelta(days=1)
        return date_list

    @classmethod
    def get_roomname_code_dict(cls,school_code=None):
        """返回字典结构，key为教室名称，value为教室编号"""
        if cls.roomname_code:
            return cls.roomname_code
        roomname_code={}
        if not school_code:
            sql = "select school_code,building_name,room_name,room_code from room_info"
        else:
            sql = "select school_code,building_name,room_name,room_code from room_info where school_code=%s"%(school_code)
        res = DBManager._RUN_MYSQL(sql,dbname='iclass')
        for row in res:
            room_name= "%s-%s"%(row['building_name'],row['room_name'])
            room_code= row['room_code']
            roomname_code[room_name]=room_code
        cls.roomname_code = roomname_code
        return roomname_code
    @classmethod
    def get_videolist(cls,date=None,section=None,building_name=None,room_name=None,type=7):
        video_list={}
        bitlist= Schedule._bitmap_to_bitlist(type)
        roomname_code = cls.get_roomname_code_dict()
        roomname = "%s-%s"%(building_name,room_name)
        room_code= str(roomname_code[roomname])
        video_list=[]
        for video_date in Schedule.get_section(date,section):
            for i in bitlist:
                video_list.append('%s-%s-%s.mp4'%(i,room_code,video_date))
        return video_list
    @classmethod
    def get_course_video_byfile(cls,course_file=None):
        """学期，时间，节次，课程名称，教师姓名，教学楼名称，教室名称，type
           只返回文件名列表
        """
        video_dict={}
        try:
            with open(course_file,"r") as f:
                lines = f.readlines()
                lines="".join(lines).strip("\n").splitlines()
                for line in lines:
                    regex = re.compile('\s+')
                    term = regex.split(line)[0]
                    date = regex.split(line)[1]
                    print(date)
                    section = regex.split(line)[2]
                    course_name = regex.split(line)[3]
                    teacher_name = regex.split(line)[4]
                    building_name = regex.split(line)[5]
                    room_name = regex.split(line)[6]
                    type = regex.split(line)[7]
                    video_list = cls.get_videolist(date=date,section=section,building_name=building_name,room_name=room_name)
                    video_key="%s:%s:%s"%(term,course_name,teacher_name)
                    if video_dict.has_key(video_key):
                        video_dict[video_key].extend(video_list)
                    else:
                        video_dict[video_key] = video_list
        except Exception as e:
            cls.logger.error( "%s %s "%(course_file,str(e)))
        return video_dict
    @classmethod
    def get_course_video_bydatabase(cls,term=None,course_name=None,teacher_name=None,teaching_class_code=None,start_week=None,stop_week=None,building_name=None,room_name=None,unit_code=None,type=7,flag=0):
        """只返回文件名列表"""
        video_dict={}
        bitlist= Schedule._bitmap_to_bitlist(type)
        roomname_code = cls.get_roomname_code_dict()
        res = Schedule.get_courseinfo_database(term=term,course_name=course_name,teacher_name=teacher_name,teaching_class_code=teaching_class_code,start_week=start_week,stop_week=stop_week,building_name=building_name,room_name=room_name,unit_code=unit_code,flag=flag)
        for row in res:
            date = row['date'].replace('-','')
            section= row['section']
            room_name= row['building_name']+"-"+row['room_name']
            if room_name not in roomname_code.keys():
                cls.logger.error("schedule room_name %s not in iclass room"%(room_name))
                continue
            room_code= str(roomname_code[room_name])
            video_list=[]
            for video_date in Schedule.get_section(date,section):
                for i in bitlist:
                    video_list.append('%s-%s-%s.mp4'%(i,room_code,video_date))
            video_key="%s:%s"%(term,row['course_name'])
            if video_dict.has_key(video_key):
                video_dict[video_key].extend(video_list)
            else:
                video_dict[video_key] = video_list
        return video_dict

    @classmethod
    def get_room_video(cls,room_file=None):
        """文件内容: 教室名称 开始时间-结束时间 例如：中2-1200 201906061000-201906061300
        返回的是全路径"""
        if not os.path.exists(room_file):
            return False
        video_list = []
        roomname_code = cls.get_roomname_code_dict()
        try:
            with open(room_file,"r") as f:
                lines = f.readlines()
                lines="".join(lines).strip("\n").splitlines()
                for line in lines:
                    regex = re.compile('\s+')
                    room_name = regex.split(line)[0]
                    if room_name not in roomname_code.keys():
                        cls.logger.error("schedule room_name %s not in iclass room"%(room_name))
                        continue
                    room_code = str(roomname_code[room_name])
                    start_time = regex.split(line)[1]
                    stop_time = regex.split(line)[2]
                    camera_type = regex.split(line)[3]
                    bitlist= Schedule._bitmap_to_bitlist(int(camera_type))
                    #这里需要检测时间范围内的文件是否存在
                    date_list = cls.getDateList(start_time[:8],stop_time[:8])
                    for date in date_list:
                        if cls.plan is "MP4_CEPH_RGW":
                            video_dir = os.path.join(cls.base_dir,str(room_code))
                        else:
                            video_dir = os.path.join(os.path.join(cls.base_dir,date),str(room_code))
                        for dirpath,dirnames,filenames in os.walk(top=video_dir,topdown=True):
                            for file in filenames:
                                if "_" in file:
                                    continue
                                type = file.split("-")[0]
                                if type not in bitlist:
                                    continue
                                video_start_time = file.split("-")[2]
                                video_stop_time = file.split("-")[3].split('.')[0]
                                if video_stop_time > start_time and video_start_time <stop_time:
                                    fullpath = os.path.join(dirpath,file)
                                    video_list.append(fullpath)
        except Exception as e:
            cls.logger.error( "%s %s "%(room_file,str(e)))
        return video_list
    @classmethod
    def video_exists(cls,video_name):
        """测试视频是否存在"""
        if not video_name:
            return False
        if cls.plan is "MP4_CEPH_RGW":
            bucket = video_name.split('-')[1]
            res = S3Utils_v2.get_object_metadata(bucket=bucket,object=video_name)
            if res:
                return True
            else:
                return False
        else:
            return os.path.exists(video_name)
    @classmethod
    def check_video(cls,date=None,type_list=['0','1','2'],school_code=2):
        """检查视频是否正常录制"""
        if not date:
            return []
        video_list=[]#生成应该有的视频列表，然后逐个检测是否存在
        roomname_code = cls.get_roomname_code_dict(school_code=school_code)
        date_list = Schedule.get_section(date=date,section='1-11')
        for room_name,room_code in roomname_code.items():
            for i in type_list:
                for date_info in date_list:        
                    file_name = '%s-%s-%s.mp4'%(i,room_code,date_info)
                    video_list.append(file_name)
        error_video_list = []
        for video_file in video_list:
            if not cls.plan is "MP4_CEPH_RGW":
                video_dir = os.path.join(os.path.join(cls.base_dir,date),str(room_code))
                video_file = os.path.join(video_dir,video_file)
            res = cls.video_exists(video_file)
            if not res:
                cls.logger.error("file %s is not exists"%video_file)
                error_video_list.append(video_file)
        #写入到文件中
        cls.data2file(error_video_list,"/tmp/error_video-%s"%date)
        return error_video_list
        
    @classmethod
    def download_video_single(cls,src_video,dest_video,isabsolute=False):
        """src_video源文件，目标文件，源文件是否绝对路径"""
        if not cls.video_exists(src_video):
            return False
        dest_dir = os.path.dirname(dest_video)
        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir)
        if isabsolute:
            try:
                shutil.copy(src_video,dest_video)
                return True
            except Exception as e:
                cls.logger.error("copy file %s to  %s error %s"%(src_video,dest_video,str(e)))
                return False 
        else:
            try:
                if cls.plan is "MP4_CEPH_RGW":
                    bucket = src_video.split('-')[1]
                    #修改为下发任务模式,但是如何获取执行结果是个问题
                    task.download_file_task.apply_async((bucket,src_video,dest_video,),queue='download_file_tasks',routing_key='download.s3')
                    return True
                    """
                    res = S3Utils_v2.get_object(bucket=bucket,file_key=src_video,dest_file=dest_video)
                    if res:
                        return True
                    else:
                        return False
                    """
                else:
                    date = src_video.split('-')[2][:9]
                    room_code = src_video.split('-')[1]
                    video_dir = os.path.join(os.path.join(cls.base_dir,date),str(room_code))
                    shutil.copy(os.path.join(video_dir,src_video),dest_video)
                    return True
            except Exception as e:
                cls.logger.error("copy file %s to  %s error %s"%(src_video,dest_video,str(e)))
                return False
    @classmethod
    def download_video(cls,video_list,dest_dir,keep_dir_flag=1):
        """下载视频到指定目录中,video_list是全路径"""
        error_video={}
        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir)
        for i in video_list:
            if os.path.exists(i):
                try:
                    size = os.path.getsize(i)/1024/1024
                    if size<200:
                        cls.logger.error(" file %s  too small"%i)
                        error_video[i]="too small"
                        continue
                    if keep_dir_flag==1:
                        #need remove base hdfs dir
                        tmp_dest_dir = os.path.split(i)[0].replace(cls.base_dir, '')
                        tmp_dest_dir = os.path.join(dest_dir,tmp_dest_dir)
                        if not os.path.exists(tmp_dest_dir):
                            os.makedirs(tmp_dest_dir)
                    else:
                        tmp_dest_dir=dest_dir
                    dest_file = os.path.join(tmp_dest_dir,os.path.split(i)[1])
                    if os.path.exists(dest_file):
                        continue
                    shutil.copy(i,dest_file)
                except Exception as e:
                    cls.logger.error("%s %s"%(i,str(e)))
            else:
                cls.logger.error("no file error %s"%i)
                error_video[i] = "not exists"
        error_file = os.path.join(dest_dir,"error_file.txt")
        if error_video:
            try:
                with open(error_file,"w") as f:
                    for key,value in error_video.items():
                        f.writelines("%s\t%s\n"%(key,value))
            except Exception as e:
                cls.logger.error("Failed to Write file %s %s "%(error_file,str(e)))
        return True
    @classmethod
    def make_classvideo(src_dir,dest_dir):
        """src_dir 包含三路视频，dest_dir包含所有最终可播放数据"""
        #需要复制程序内容过去
        try:
            shutil.copytree(cls.classvideo_template,dest_dir)
            files = os.listdir(src_dir)
            for file in files:
                if file.endswith(".mp4"):
                    src_file = os.path.join(src_dir,file)
                    if file.startswith("0-"):
                        dest_file = os.path.join(dest_dir,"video/0.mp4")
                    elif file.startswith("1-"):
                        dest_file = os.path.join(dest_dir,"video/1.mp4")
                    elif file.startswith("2-"):
                        dest_file = os.path.join(dest_dir,"video/2.mp4")
                #copy file to dest
                shutil.copy(src_file,dest_file)
                cls.logger.info("copy file %s to %s"%(src_file,dest_file))
                return True
        except Exception as e:
            cls.logger.error("Failed copy %s to %s error %s"%(src_file,dest_file,str(e)))
            return False
if __name__ == "__main__":
    res = Video.get_course_video_byfile(course_file="/tmp/longjiangang")
    for key,value in res.items():
        print(value)
    """
    res = Video.check_video(date='20190924')
    print(res)
    res = Video.get_course_video(term='2019-2020-1',start_week=2,stop_week=2,flag=1)
    for key,value in res.items():
        print(value)
        break
    video_list = Video.get_room_video(room_file="/tmp/20190601_xiquyingyukaoshi.txt")
    print(video_list)
    Video.download_video(video_list,"/mnt/nas1_lun2/2018-2019-2/20190601西区成人英语考试")
    """
