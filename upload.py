#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import os
import time
import shutil
import sys
from s3utils import S3Utils
from s3utils_v2 import S3Utils_v2

import config
import logging

logger = logging.getLogger(config.get('LOGGER_NAME'))
error_buffer = config.get('ERROR_BUFFER_DIR','')
def upload_file_to_s3(file_name):
    if file_name.endswith('.tmp'):
        file_name = file_name[:-4]
    if not os.path.exists(file_name):
        logger.error("file %s not exists"%file_name)
        return False
    size = os.path.getsize(file_name)
    """
    size = os.path.getsize(file_name)/1024/1024
    if size <10 or "_" in file_name: #小于10M的不上传，直接删除
        logger.error("file name  %s size %s is too small  remove file"%(file_name,size))
        os.remove(file_name)
        return False
    """
    if file_name.endswith('.tmp'):
        file_name = file_name[:-4]
    tmp_split =os.path.basename(file_name).split('-')
    if len(tmp_split)<2:
        logger.error("error file name %s"%file_name)
        return False
    ##注意过滤掉无用的数据,检测数据的大小
    bucket = tmp_split[1]
    #暂时采取的方案，后面要找到原因
    if not S3Utils_v2.get_bucket_metadata(bucket=bucket):
        S3Utils_v2.create_bucket(bucket=bucket)
    res = S3Utils_v2.put_object(bucket=bucket,file=file_name)
    #如果检测到上传失败的原因是bucket不存在的话，创建bucket
    if type(res)==str and '(NoSuchBucket)' in res:
        res = S3Utils_v2.create_bucket(bucket=bucket)
        if res == True:
            res = S3Utils_v2.put_object(bucket=bucket,file=file_name)
        else:
            logger.info("create bucket %s error %s"%(bucket,res))
    if res != True:
        logger.error("error put file %s to s3 storage "%(file_name))
        try:
            shutil.move(file_name,error_buffer)#should mv file to disk storage
            logger.info("  mov file %s to %s "%(file_name,error_buffer))
        except Exception as e:
            logger.error(" can not mov file %s to %s err %s "%(file_name,error_buffer,str(e)))
            #os.remove(file_name)
            #logger.info("delete %s"%(file_name))
        return False
    else:
        logger.info("Success put file %s to bucket %s  size is %s"%(file_name,bucket,size))
        if not file_name.endswith("m3u8"):
            os.remove(file_name)
            logger.info("delete %s"%(file_name))
        return
if __name__ == "__main__":
    upload_file_to_s3(sys.argv[1])
