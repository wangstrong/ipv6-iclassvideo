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
def download_file_from_s3(bucket=None,file_key=None,dest_dir=None):
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)
    #1.测试对象是否存在
    res = S3Utils_v2.get_object_metadata(bucket=bucket,object=file_key)
    if not res:
        logger.error(" object %s not in bucket %s"%(file_key,bucket))
        return False
    dest_file = os.path.join(dest_dir,file_key)
    res = S3Utils_v2.get_object(bucket=bucket,file_key=file_key,dest_file=dest_file)
    if res:
        logger.info("Success get file %s from bucket %s to %s"%(file_key,bucket,dest_file))
        return True
    else:
        logger.error("Failed get file %s from bucket %s to %s"%(file_key,bucket,dest_file))
        return False
if __name__ == "__main__":
    download_file_from_s3(sys.argv[1],sys.argv[2],sys.argv[3])
