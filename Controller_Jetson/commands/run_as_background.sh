# For the video transmitter
cd RealTime_Video_Streaming_and_RC_Remote_Over_the_Internet/Controller_Jetson/Automomus_car_v1
nohup python3 python_GStreamer_transmitter.py > video_log.txt 2>&1 &

cd 
# For the RC receiver
cd ~/RealTime_Video_Streaming_and_RC_Remote_Over_the_Internet/Controller_Jetson/CT6B/CT6B_websocket_TinyTVLx_Recevier
nohup python3 main_client.py > rc_log.txt 2>&1 &
