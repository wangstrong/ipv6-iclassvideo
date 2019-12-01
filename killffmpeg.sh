#!/bin/sh
ps aux | grep "ffmpeg -y" |grep -v grep| cut -c 9-15 | xargs kill -9
kill -HUP `ps -A -ostat,ppid | grep -e '^[Zz]' | awk '{print $2}'`
