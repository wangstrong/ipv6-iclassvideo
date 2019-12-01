#!/usr/bin/env python
# -*- coding:utf-8 -*-

from celery import Celery

app = Celery('iclassvideo.task', include=['iclassvideo.task'])

app.config_from_object('iclassvideo.celery_config')
if __name__ == '__main__':
    app.start()
