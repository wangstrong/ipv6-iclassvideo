#!/bin/env python
# -*- coding: utf-8 -*-

"""
Camera Info
Author: wangqiang <wangqiang1989@xjtu.edu.cn>
Copyright (C) 2017 xjtu. All Rights Reserved.
"""
import logging
from copy import deepcopy
import config
from dbmanager import DBManager

class Camera():
    logger = logging.getLogger(config.get('LOGGER_NAME'))
    camera_table = config.get('CAMERA_TABLE')
    def __init__(self):
        pass
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
    @classmethod
    def get_camera_info(cls,room_code_list=[],camera_type=7,db='iclass',iclass=True):
        """读取数据库获取摄像头信息,返回数据类型为字典列表"""
        if iclass:
            sql = "select room_code,addr,rtsp_addr,type from %s where room_code regexp '^8' order by room_code limit 439"%(cls.camera_table)
        else:
            bitlist= cls._bitmap_to_bitlist(camera_type)
            type_list='('+','.join(bitlist)+')'
            if room_code_list:
		print(room_code_list)
                code_list = '('+','.join(room_code_list)+')'
                sql = "select room_code,addr,rtsp_addr,type from %s where  room_code in %s and type in %s"%(cls.camera_table,code_list,type_list)
            else:
                sql = "select room_code,addr,rtsp_addr,type from %s where room_code regexp '^8'  and type in %s"%(cls.camera_table,type_list)
        cls.logger.info(sql)
        res = DBManager._RUN_MYSQL(sql,dbname=db)
        return res
    @classmethod
    def get_room_code(cls,db='iclass'):
       """读取数据库教室编号表""" 
       sql = "select distinct room_code from %s "%cls.camera_table
       cls.logger.info(sql)
       res = DBManager._RUN_MYSQL(sql,dbname=db) 
       return res
if __name__ == "__main__":
    res = Camera().get_camera_info(room_code_list=['53204','53205','53206'],iclass=False)
    print(res)
