#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Package:celery_task
Author: wangqiang <wangqiang1989@xjtu.edu.cn>

Copyright (C) 2017 xjtunic. All Rights Reserved.
"""
import os
import logging
import time
import datetime

import pymysql
from DBUtils.PooledDB import PooledDB
import redis

import config

class DBManager(object):
    logger = logging.getLogger(config.get('LOGGER_NAME'))
    #mysql database pool
    """
    try:
        schedule_mysql_pool = PooledDB(pymysql,host= config.get('SCHEDULE_MYSQL_DB').get("host"),port = config.get('SCHEDULE_MYSQL_DB').get("port"),user=config.get('SCHEDULE_MYSQL_DB').get("user"),passwd=config.get('SCHEDULE_MYSQL_DB').get("password"),db=config.get('SCHEDULE_MYSQL_DB').get("db"),charset='utf8',cursorclass=pymysql.cursors.DictCursor,mincached=5,maxcached=20)
    except Exception as e:
        logger.error("schedule mysql database connect error %s "%(str(e)))
    """
    try:
        iclass_mysql_pool = PooledDB(pymysql,cursorclass=pymysql.cursors.DictCursor,mincached=5,maxcached=20,**config.get('ICLASS_MYSQL_DB'))
    except Exception as e:
        logger.error("iclass mysql database connect error %s "%(str(e)))
    try:
        local_mysql_pool = PooledDB(pymysql,cursorclass=pymysql.cursors.DictCursor,mincached=5,maxcached=20,**config.get('LOCAL_MYSQL_DB'))
    except Exception as e:
        logger.error("local mysql database connect error %s "%(str(e)))
    @classmethod
    def _get_mysql_instance(cls):
        return cls.mysql_pool.connection()
    
    @classmethod
    def _RUN_MYSQL(cls,sql,dbname='local'):
        """执行MYSQL SQL"""
        res=[]
        if not sql:
            return res
        if dbname == 'local':
            conn = cls.local_mysql_pool.connection()
        elif dbname == 'schedule':
            conn = cls.schedule_mysql_pool.connection()
        elif dbname == 'iclass':
            conn = cls.iclass_mysql_pool.connection()
        else:
            return res
        #conn.autocommit(1)
        res = cls.__run_sql(conn,sql)
        return res

    @classmethod
    def _RUN_MYSQL_MANY(cls,sql,args):
        """执行MYSQL SQL"""
        res=[]
        if not sql:
            return res
        conn = cls.local_mysql_pool.connection()
        res = cls.__run_manysql(conn,sql,args)
        return res

    @classmethod
    def __run_sql(cls,conn,sql):
        res = []
        try:
            curs = conn.cursor()
            curs.execute(sql)
            res = curs.fetchall()
            cls.logger.debug("success run sql: %s"%(sql))
        except Exception as e:
            cls.logger.error("执行SQL: %s 失败: %s"%(sql,str(e)))
            return False
        finally:
            conn.commit()
            conn.close()
            return res
    @classmethod
    def __run_manysql(cls,conn,sql,args):
        try:
            cursor = conn.cursor()
            cursor.executemany(sql, args)
            conn.commit()
            cls.logger.debug("success run manysql: %s"%(sql))
        except Exception as e:
            conn.rollback()
            cls.logger.error('sql: %s 处理过程发生错误 %s，事务已回滚，对目标数据库的更改没有发生 '%(sql,str(e)))
            return False
        finally:
            cursor.close()
            conn.close()
            return True
