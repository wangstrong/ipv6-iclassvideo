#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Package: config
Author: 

Copyright (C) 2017 wangstrong. All Rights Reserved.
"""
import logging
import logging.config

class Config:
    VERSION = "0.4"
    # Log
    LOGGER_NAME = "iclassvideo"
    LOGGER_FILE = "/home/git/iclassvideo/logging.conf"
    DATA_DIR = "/home/git/iclassvideo/"
    PLAN = "MP4_CEPH_RGW"
    #PLAN = "MP4_HDFS_FUSE"
    SHM_DIR = "/dev/shm" #内存暂存盘，用hls文件存储以及转码时暂存MP4
    ERROR_BUFFER_DIR = "/mnt/iclassvideo/errorbuffer" #如果视频上传失败，则暂存此处   
    BUFFER_DIR = "/mnt/iclassvideo/buffer" #此容量需要规划一下
    CEPH_BASEDIR = "/ceph-rgw-nfs/"
    HDFS_BASEDIR = "/hdfs/data/coursevideos/"
    LOCAL_MYSQL_DB = {
        'host': '10.32.166.254',
        'port': 3306,
        'user': 'iclassvideo',
        'password': '',
        'db': 'iclassvideo',
        'charset': "utf8"
    }
    ICLASS_MYSQL_DB = {
        'host': '10.32.129.25',
        'port': 3306,
        'user': 'iclassvideo',
        'password': '',
        'db': 'iclassdata',
        'charset': "utf8"
    }
    OBJECT_STORAGE_INFO = {
        'access_key': '',
        'secret_key': '',
        'endpoint_url': 'http://10.49.3.104:8080',
    }

    CAMERA_TABLE = "camera_info"
    TECSCHEDULE = "tecschedule"
    YJSY_TECSCHEDULE = "yjsy_tecschedule"
__instanse = None


def __init_instanse():
    ''' 初始化配置实例 '''
    global __instanse
    if __instanse:
        return
    try:
        from config_custom import CustomConfig
        if not issubclass(CustomConfig, Config):
            raise TypeError('自定义配置类必须是config.Config的子类')
        __instanse = CustomConfig()
    except ImportError:
        __instanse = Config()


def get(name, default=None):
    ''' 获取配置 '''
    __instanse or __init_instanse()
    return getattr(__instanse, name, default)


def set(name, value):
    ''' 运行时动态修改配置 '''
    __instanse or __init_instanse()
    return setattr(__instanse, name, value)


__init_instanse()
logging.config.fileConfig(Config.LOGGER_FILE)
