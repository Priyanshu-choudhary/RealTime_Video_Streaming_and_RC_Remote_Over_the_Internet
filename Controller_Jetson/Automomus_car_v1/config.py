# Config.py
# Central Configuration for Autonomous Car System

# ===========================
# COMMUNICATION CONFIGURATION
# ===========================
WS_URI = "ws://yadiec2.freedynamicdns.net:8080/ws"
HEALTH_URL = "http://yadiec2.freedynamicdns.net:8080/health"
SERIAL_PORT = "/dev/ttyUSB0"
BAUD_RATE = 115200

# ===========================
# SYSTEM MODES & HEALTH
# ===========================
MODE = "MANUAL"
HEALTH_CHECK_INTERVAL = 2.0
AUTO_MODE_TRIGGER = 1700    # If Aux1 > 1700, switch to AUTO

# ===========================
# PID CONTROLLER CONFIGURATION
# ===========================
PID_KP = 1.0
PID_KI = 0.01
PID_KD = 0.01
PID_SETPOINT = 0
PID_OUTPUT_LIMITS = (-100, 100)

# ===========================
# CAMERA & MODEL CONFIGURATION
# ===========================
CAMERA_WIDTH = 1280
CAMERA_HEIGHT = 720
CAMERA_FPS = 15
CAMERA_INDEX = 0
USE_OVERLAY = True

ENGINE_FILE_PATH = "unet_mobilenetv2_Marbel.engine"
MODEL_INPUT_H = 384
MODEL_INPUT_W = 384

# ===========================
# AV STREAMING (GSTREAMER)
# ===========================
AWS_RTSP_URL = "rtsp://yadiec2.freedynamicdns.net:8554/cam2"

# GST Pipeline Configuration
# Using f-string to inject width, height, fps, and url dynamically
PIPELINE_STR = (
    "appsrc name=mysource is-live=true format=3 "
    f"caps=video/x-raw,format=BGR,width={CAMERA_WIDTH},height={CAMERA_HEIGHT},framerate={CAMERA_FPS}/1 ! "
    "videoconvert ! video/x-raw,format=I420 ! "
    "nvvidconv ! video/x-raw(memory:NVMM),format=NV12 ! "
    "nvv4l2h264enc bitrate=800000 control-rate=1 preset-level=1 "
    "insert-sps-pps=true maxperf-enable=1 ! "
    "h264parse ! "
    f"rtspclientsink location={AWS_RTSP_URL} "
    "protocols=tcp do-rtsp-keep-alive=true"
)

FRAME_DURATION = int(1e9 / CAMERA_FPS)

# ===========================
# AUTONOMOUS NAVIGATION
# ===========================
LOOK_AHEAD = 2  # Number of points to look ahead for steering

# ===========================
# RC MIXER & MOTOR CONTROL
# ===========================
RC_MIN = 1000
RC_MAX = 2000
RC_CENTER = 1500
RC_DEADBAND = 10

MAX_PWM_OUTPUT = 175
MAX_CORRECTION_PWM = 30
