#!/bin/env python
# -*- coding: utf-8 -*-

"""
Camera Info
Author: wangqiang <wangqiang1989@xjtu.edu.cn>
Copyright (C) 2017 xjtu. All Rights Reserved.
"""
import os
import csv
import json
import logging
from copy import deepcopy
import config
from dbmanager import DBManager

class SyncData():
    logger = logging.getLogger(config.get('LOGGER_NAME'))
    camera_table = config.get('CAMERA_TABLE')
    data_dir = config.get('DATA_DIR')
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
                writer = csv.writer(f, dialect='excel')
                for row in data:
                    writer.writerow(row)
                f.close()
                cls.logger.info("Success create file %s"%(filename))
                return True
        except Exception as e:
            cls.logger.error("error create file %s error reson is %s"%(filename,str
(e)))
            return False

    @classmethod
    def sync_camera_info(cls):
        sql = "select room_code,addr,port,channel,type,rtsp_addr,username,password,vendor,stor_id from %s"%(cls.camera_table)
        cls.logger.info(sql)
        res = DBManager._RUN_MYSQL(sql,dbname='iclass')
        if not res:
            cls.logger.error('sync data %s error'%(cls.camera_table))
            return False
        decode_data=[]
        for row in res:
            decode_data.append((row['room_code'],row['addr'],row['port'],row['channel'],row['type'],row['rtsp_addr'],row['username'],row['password'],row['vendor'],row['stor_id']))
        #写入数据到存储
        filename = "%s.csv"%(cls.camera_table)
        if not cls.data2file(decode_data,os.path.join(cls.data_dir,filename)):
            cls.logger.error("%s数据暂存文件失败，同步数据中断，MySQL数据库未更改"%(cls.camera_table))
            return False
        #判断表是否存在，如果不存在则创建表
        create_sql = """CREATE TABLE IF NOT EXISTS `%s`  (
            `camera_id` int(11) PRIMARY KEY NOT NULL  AUTO_INCREMENT COMMENT '设备编号',
            `room_code` varchar(64) NOT NULL COMMENT '教室编号',
            `addr` varchar(64) NOT NULL COMMENT '设备IP地址，兼容IPv6',
            `port` int(8) NOT NULL COMMENT '设备端口',
            `channel` int(8) NOT NULL COMMENT '设备通道',
            `type` tinyint NOT NULL COMMENT '设备类型，教师机:0，学生机:1，VGA:2',
            `rtsp_addr` varchar(256) NOT NULL COMMENT '设备RTSP地址',
            `username` varchar(64) NOT NULL COMMENT '访问设备的用户名',
            `password` varchar(64) NOT NULL COMMENT '设备密码，明文存储',
            `vendor` varchar(64) NOT NULL COMMENT '厂商，海康：HIK，大华：dahua，VGA: HIK',
            `stor_id` tinyint NOT NULL COMMENT '监控存储设备ID',
            INDEX `index_room_code` (`room_code`) USING BTREE
            )ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='camera数据表';
             """%(cls.camera_table)
        DBManager._RUN_MYSQL(create_sql,'local')
        #清空mysql表,危险，不可恢复数据
        del_sql = "truncate table %s"%(cls.camera_table)
        DBManager._RUN_MYSQL(del_sql,'local')
        #写入数据库
        mysql_sql = "insert into "+cls.camera_table+" (room_code,addr,port,channel,type,rtsp_addr,username,password,vendor,stor_id) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        result = DBManager._RUN_MYSQL_MANY(mysql_sql,decode_data)
        if result:
            cls.logger.info("成功同步数据 %s"%(cls.camera_table))
        return result
if __name__ == "__main__":
    res = SyncData.sync_camera_info()
    print(res)
