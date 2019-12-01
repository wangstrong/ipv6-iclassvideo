#!/bin/env python
# -*- coding: utf-8 -*-

"""
Camera Info
Author: wangqiang <wangqiang1989@xjtu.edu.cn>
Copyright (C) 2017 xjtu. All Rights Reserved.
"""
import datetime
import logging
import config
from dbmanager import DBManager

class Schedule():
    logger = logging.getLogger(config.get('LOGGER_NAME'))
    schedule_table = config.get('SCHEDULE_TABLE')
    sum_section_dict = {'1':['0800','0900'],'2':['0900','1000'],'3':['1000','1100'],'4':['1100','1200'],'5':['1430','1530'],'6':['1530','1630'],'7':['1630','1730'],'8':['1730','1830'],'9':['1930','2030'],'10':['2030','2130'],'11':['2130','2230']}
    winter_section_dict = {'1':['0800','0900'],'2':['0900','1000'],'3':['1000','1100'],'4':['1100','1200'],'5':['1400','1500'],'6':['1500','1600'],'7':['1600','1700'],'8':['1700','1800'],'9':['1900','2000'],'10':['2000','2100'],'11':['2100','2200']}
    def __init__(self):
        pass
    
    """摄像头类型转为bit"""
    @classmethod
    def _bitmap_to_bitlist(cls,bitmap):
        bit_str = bin(bitmap).replace('0b','')
        i = 0
        bit_list=[]
        for b in bit_str[::-1]:
            if b == '1':
                bit_list.append(str(i))
            i=i+1
        return bit_list
    
    """返回指定时间和节次的时间列表,用于拼接视频文件"""
    @classmethod
    def get_section(cls,date=None,section=None):
        """返回指定时间，指定节次的视频时间信息
            date is 20171105,section is 3-4
            返回[],内容为["1000-1100","1100-1200"]"""
        section_list=[]
        if not date or not section:
            return section_list
        date_time = datetime.datetime.strptime(date, "%Y%m%d")
        date_51 = datetime.datetime(year=date_time.year, month=5, day=1)
        date_101 = datetime.datetime(year=date_time.year,month=10,day=1)
        if date_time >= date_51 and date_time <= date_101:
            section_dict = cls.sum_section_dict
        else:
            section_dict = cls.winter_section_dict
        if '-' not in section and int(section)<12 and int(section)>=1:
            begin_section = int(section)
            end_section = int(section)
        else:
            begin_section = int(section.split('-')[0])
            end_section = int(section.split('-')[1])
        for i in range(begin_section,end_section+1):
            section_list.append("%s%s-%s%s"%(date,section_dict[str(i)][0],date,section_dict[str(i)][1]))
        return section_list
  
    """查询数据库，返回课程信息"""
    @classmethod
    def get_courseinfo_database(cls,term=None,course_name=None,teacher_name=None,teaching_class_code=None,start_week=None,stop_week=None,building_name=None,room_name=None,unit_code=None,flag=0):
        """获取课程信息,flag=0 本科，flag=1 研究生,后期可以直接使用API，不用数据库查表形式"""
        if not term:
            return False
        if flag==0:
            schedule_tablename = config.get("TECSCHEDULE")+'_'+term
        elif flag ==1:
            schedule_tablename=  config.get("YJSY_TECSCHEDULE")+'_'+term
        else:
            return False
        _base_sql = "select distinct date,section,course_name,building_name,room_name,week from `%s` where "%(schedule_tablename)
        _coursename_str = "course_name ='%s'"
        _teachername_str = "teacher_name='%s'"
        _classcode_str = "teaching_class_code='%s'"
        _building_str = "building_name='%s'"
        _room_str = "room_name='%s'"
        _unit_code_str = " unit_code='%s'"
        _start_week_str = "week>=%s"
        _stop_week_str = "week<=%s"

        _sql_where = []
        _args = []

        if course_name:
            _sql_where.append(_coursename_str)
            _args.append(course_name)
        if teacher_name:
           _sql_where.append(_teachername_str)
           _args.append(teacher_name)
        if teaching_class_code:
            _sql_where.append(_classcode_str)
            _args.append(teaching_class_code)
        if building_name:
            _sql_where.append(_building_str)
            _args.append(building_name)
        if room_name:
            _sql_where.append(_room_str)
            _args.append(room_name)
        if unit_code:
            _sql_where.append(_unit_code_str)
            _args.append(unit_code)
        if start_week:
            _sql_where.append(_start_week_str)
            _args.append(start_week)
        if stop_week:
            _sql_where.append(_stop_week_str)
            _args.append(stop_week)

        if not _sql_where or not _args:
            return []
        _sql_where = " and ".join(_sql_where)
        _sql = _base_sql + _sql_where % tuple(_args)
        #print _sql
        res = DBManager._RUN_MYSQL(_sql,dbname='iclass')
        return res
if __name__ == "__main__":
    res = Schedule.get_section('20190606','1-3')
    print(res)
    res = Schedule.get_courseinfo_database(term='2019-2020-1',start_week=2,stop_week=2,flag=1)
    print(res)
