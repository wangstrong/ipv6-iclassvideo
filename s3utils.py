#!/bin/python
# -*- coding: utf-8 -*-
"""
S3 Object API use boto3

"""
import os
import boto3
from botocore.client import Config
import logging


import config

class S3Utils():
    logger = logging.getLogger(config.get('LOGGER_NAME'))
    object_storage = config.get("OBJECT_STORAGE_INFO")
    endpoint_url = object_storage.get('endpoint_url')
    access_key = object_storage.get('access_key')
    secret_key = object_storage.get('secret_key')
    #boto_config = Config(connect_timeout=120,read_timeout=120)
    s3 = boto3.client("s3", endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            #aws_secret_access_key=secret_key,config=boto_config)
            aws_secret_access_key=secret_key)

    @classmethod
    def list_buckets(cls):
        #list buckets
        try:
            response = cls.s3.list_buckets()
        except Exception as e:
            cls.logger.error("list buckets exception %s"%str(e))
            return str(e)

        if response and response['ResponseMetadata']['HTTPStatusCode'] == 200:
            buckets = [bucket['Name'] for bucket in response['Buckets']]
            return buckets
        else:
            return False

    @classmethod
    def create_bucket(cls,bucket=None):
        #create bucket
        if not bucket:
            return False
        try:
            response = cls.s3.create_bucket(Bucket=bucket)
        except Exception as e:
            cls.logger.error("create bucket exception %s"%str(e))
            return  str(e)
        if response and response['ResponseMetadata']['HTTPStatusCode'] == 200:
            return True
        else:
            return False
    
    @classmethod
    def put_object(cls,bucket=None,file=None,acl='authenticated-read'):
        #put object
        if not bucket or not file or not os.path.isfile(file):
            return False
        file_name = os.path.basename(file)
        file_handle = open(file, 'r')
        try:
            response = cls.s3.put_object(ACL=acl,Bucket=bucket, Key=file_name, Body=file_handle)
        except Exception as e:
            cls.logger.error("put object exception %s"%str(e))
            file_handle.close()
            return  str(e)
        file_handle.close()
        if response and response['ResponseMetadata']['HTTPStatusCode'] == 200:
            return True
        else:
            return False
    
    @classmethod
    def get_object(cls,bucket=None,file_key=None,dest_file=None):
        #get object
        download_file = dest_file 
        download_file_handle = open(download_file, "w")
        try:
            response = cls.s3.get_object(Bucket=bucket, Key=file_key)
        except Exception as e:
            cls.logger.error("get object exception %s"%str(e))
            download_file_handle.close()
            return str(e)
        
        if response and response['ResponseMetadata']['HTTPStatusCode'] == 200:
            read_stream = response['Body'].read()  # Body Type: botocore.response.StreamingBody
            download_file_handle.write(read_stream)
            download_file_handle.close()
            return True
        else:
            download_file_handle.close()
            return False
    @classmethod
    def list_object(cls,bucket=None,marker=None,Delimiter=None,prefix=None,maxkeys=None):
        #list objects
        prefix_dir = ''
        marker = ''
        file_num = 0
        total_file_size = 0
        while True:
            # Maxkeys: returned object nums at most one time, default 1000
            response = cls.s3.list_objects(Bucket=bucket, Marker=marker, Delimiter='/', Prefix=prefix_dir, MaxKeys=100)
            #print response
            if response.has_key('Contents'):
                file_num += len(response['Contents'])
                for contents in response['Contents']:
                    total_file_size += contents['Size']
            else:
                break;
            if not response['IsTruncated']:
                break
            else:
                marker = response['NextMarker']
                cls.logger.info("dir: %s, total file num: %d, total file size: %d"%(prefix_dir, file_num, total_file_size))
    
    @classmethod
    def delete_object(cls,bucket=None,file_key=None):
        if not bucket or not file_key:
            return False
        #delete object
        try:
            response = cls.s3.delete_object(Bucket=bucket, Key=file_key)
        except Exception as e:
            cls.logger.error("delete object exception %s"%str(e))
            return  str(e)
        if response and response['ResponseMetadata']['HTTPStatusCode'] == 200:
            return True
        else:
            return False
        
    @classmethod
    def delete_bucket_objects(cls,bucket=None):
        objects_key=[]
        response = cls.s3.list_objects(Bucket=bucket, MaxKeys=1000)
        if response.has_key('Contents'):
            for i in response['Contents']:
                objects_key.append({'Key':i['Key']})
        Delete_dict={}
        Delete_dict['Objects']=objects_key
        res = cls.s3.delete_objects(Bucket=bucket,Delete=Delete_dict)
    
    @classmethod
    def delete_bucket(cls,bucket=None):
        if not bucket:
            return False
        cls.delete_bucket_objects(bucket=bucket)
        #delete bucket
        try:
            response = cls.s3.delete_bucket(Bucket=bucket)
        except Exception as e:
            cls.logger.error("delete bucket exception %s"%str(e))
            return  str(e)
        if response and response['ResponseMetadata']['HTTPStatusCode'] == 200:
            return True
        else:
            return False
if __name__ == "__main__":
    res = S3Utils.put_object(bucket='00123',file='./s3utils.py')
    print(res)
    res = S3Utils.create_bucket(bucket='00123')
    print(res)
    res= S3Utils.list_buckets()
    
    res = S3Utils.put_object(bucket='00123',file='/home/git/iclassvideo/s3utils.py')
    print res
    #res = S3Utils.get_object(bucket='11200',file_key='0-11200-201801062215-201801062315.m3u8',dest_file='/tmp/tt.m3u8')
    #print res
