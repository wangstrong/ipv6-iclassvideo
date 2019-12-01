#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import sys
from ffmpeg import FFmpeg

if __name__ == "__main__":
    FFmpeg.run_hls_task(duration=sys.argv[1],rtsp_addr=sys.argv[2],filename=sys.argv[3])
