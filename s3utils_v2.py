#!/bin/python
# -*- coding: utf-8 -*-
"""
S3 Object API use boto3

"""
import os
import random
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
import logging


import config

class S3Utils_v2():
    logger = logging.getLogger(config.get('LOGGER_NAME'))
    object_storage = config.get("OBJECT_STORAGE_INFOS")
    access_key = object_storage.get('access_key')
    secret_key = object_storage.get('secret_key')
    endpoint_url_list = object_storage.get('endpoint_url_list')
    boto_config = Config(connect_timeout=120,read_timeout=120)
    s3_list=[]
    for endpoint_url in endpoint_url_list:
        s3 = boto3.client("s3", endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,config=boto_config)
        s3_list.append(s3)
        

    @classmethod
    def list_buckets(cls):
        #list buckets
        try:
            s3 = random.choice(cls.s3_list)
            response = s3.list_buckets()
        except Exception as e:
            cls.logger.error("list buckets exception %s"%str(e))
            return str(e)

        if response and response['ResponseMetadata']['HTTPStatusCode'] == 200:
            buckets = [bucket['Name'] for bucket in response['Buckets']]
            return buckets
        else:
            return False

    @classmethod
    def create_bucket(cls,bucket=None,acl='public-read'):
        #create bucket
        if not bucket:
            return False
        try:
            s3 = random.choice(cls.s3_list)
            response = s3.create_bucket(Bucket=bucket,ACL=acl,CreateBucketConfiguration={'LocationConstraint':'default'})
        except Exception as e:
            cls.logger.error("create bucket exception %s"%str(e))
            return  str(e)
        if response and response['ResponseMetadata']['HTTPStatusCode'] == 200:
            return True
        else:
            return False
    
    @classmethod
    def get_bucket_metadata(cls,bucket=None):
        #get meta info of bucket
        if not bucket:
            return False
        try:
            s3 = random.choice(cls.s3_list)
            response = s3.head_bucket(Bucket=bucket)
        except Exception as e:
            cls.logger.error("get meta info of bucket exception %s"%str(e))
            return False
        return True
    @classmethod
    def put_object(cls,bucket=None,file=None,acl='public-read'):
        #put object
        if not bucket or not file or not os.path.isfile(file):
            return False
        file_name = os.path.basename(file)
        file_handle = open(file, 'r')
        try:
            s3 = random.choice(cls.s3_list)
            response = s3.put_object(ACL=acl,Bucket=bucket, Key=file_name, Body=file_handle)
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
            s3 = random.choice(cls.s3_list)
            response = s3.get_object(Bucket=bucket, Key=file_key)
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
            s3 = random.choice(cls.s3_list)
            # Maxkeys: returned object nums at most one time, default 1000
            response = s3.list_objects(Bucket=bucket, Marker=marker, Delimiter='/', Prefix=prefix_dir, MaxKeys=100)
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
            s3 = random.choice(cls.s3_list)
            response = s3.delete_object(Bucket=bucket, Key=file_key)
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
        s3 = random.choice(cls.s3_list)
        response = s3.list_objects(Bucket=bucket, MaxKeys=1000)
        if response.has_key('Contents'):
            for i in response['Contents']:
                objects_key.append({'Key':i['Key']})
        Delete_dict={}
        Delete_dict['Objects']=objects_key
        res = s3.delete_objects(Bucket=bucket,Delete=Delete_dict)
    
    @classmethod
    def delete_bucket(cls,bucket=None):
        if not bucket:
            return False
        cls.delete_bucket_objects(bucket=bucket)
        #delete bucket
        try:
            s3 = random.choice(cls.s3_list)
            response = s3.delete_bucket(Bucket=bucket)
        except Exception as e:
            cls.logger.error("delete bucket exception %s"%str(e))
            return  str(e)
        if response and response['ResponseMetadata']['HTTPStatusCode'] == 200:
            return True
        else:
            return False
    @classmethod
    def get_object_metadata(cls,bucket,object):
        try:
            s3 = random.choice(cls.s3_list)
            response = s3.head_object(Bucket=bucket,Key=object)
        except ClientError as e:
            cls.logger.error("get object metadata  exception %s"%str(e))
            return None
        return response
    
    @classmethod
    def create_presigned_url(cls,bucket, object, expiration=3600):
        try:
            s3 = random.choice(cls.s3_list)
            response = s3.generate_presigned_url('get_object',
                                            Params={'Bucket': bucket,
                                                    'Key': object},
                                            ExpiresIn=expiration)
        except ClientError as e:
            cls.logger.error(e)
            return None
        # The response contains the presigned URL
        return response
    #设置bucket的策略，policy字典例子如下:
    @classmethod
    def put_bucket_policy(cls,bucket,policy):
        try:
            bucket_policy = json.dumps(policy)
            s3 = random.choice(cls.s3_list)
            s3.put_bucket_policy(Bucket=bucket,Policy=bucket_policy)
        except ClientError as e:
            cls.logger.error(e)
            return False
        # The response contains the presigned URL
        return True
if __name__ == "__main__":
    policy_temp= {
                "Version": "2012-10-17",
                "Statement": [{
                    "Effect": "Allow",
                    "Principal": {},
                    "Action": ['s3:ListBucket','s3:GetBucketAcl','s3:GetObject','s3:GetObjectAcl'],
                    "Resource": []
                }]
        }
    res= S3Utils_v2.list_buckets()
    for bucket in res:
        policy = policy_temp
        temp_list=["arn:aws:s3:::"+bucket,"arn:aws:s3:::"+bucket+'/*']
        policy['Statement'][0]['Resource']=temp_list
        print(policy)
        res= S3Utils_v2.put_bucket_policy(bucket=bucket,policy=policy)
        print(res)
        res= S3Utils_v2.get_bucket_policy(bucket=bucket)
        print(res)
    """
    res = S3Utils_v2.get_object_metadata(bucket='82002',object='0-822002-201909051930-201909052030.mp4')
    print(res)
    res = S3Utils_v2.create_bucket(bucket='00123')
    print(res)
    res = S3Utils_v2.put_object(bucket='00123',file='./s3utils.py')
    print(res)
    res = S3Utils_v2.create_presigned_url('00123','s3utils.py')
    print(res)
    res= S3Utils_v2.list_buckets()
    
    res = S3Utils_v2.put_object(bucket='00123',file='/home/git/iclassvideo/s3utils.py')
    print res
    """
