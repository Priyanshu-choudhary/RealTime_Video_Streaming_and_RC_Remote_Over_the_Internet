#!/bin/bash

# Configuration for DJI Action 2 -> RTSP Server
DEVICE="/dev/video0"
RTSP_URL="rtsp://yadiec2.freedynamicdns.net:8554/cam2"
BITRATE="800000" # Increased to 800kbps for 720p quality

gst-launch-1.0 v4l2src device=$DEVICE ! \
    image/jpeg, width=1280, height=720, framerate=30/1 ! \
    jpegdec ! \
    videorate ! video/x-raw, framerate=15/1 ! \
    nvvidconv ! 'video/x-raw(memory:NVMM), format=NV12' ! \
    nvv4l2h264enc bitrate=$BITRATE insert-sps-pps=1 maxperf-enable=1 \
    preset-level=1 control-rate=1 iframeinterval=30 ! \
    h264parse ! \
    queue max-size-buffers=1 leaky=downstream ! \
    rtspclientsink location=$RTSP_URL protocols=tcp do-rtsp-keep-alive=true
