import cv2
import numpy as np
import time
import math
import threading
from queue import Queue
from threading import Event, Lock
import os
import config
from PathPlanning import path_planning_thread, overlay

# -------- constants (imported from config) --------
WIDTH, HEIGHT = config.CAMERA_WIDTH, config.CAMERA_HEIGHT
FPS = config.CAMERA_FPS

ENGINE_FILE_PATH = config.ENGINE_FILE_PATH
MODEL_INPUT_H = config.MODEL_INPUT_H
MODEL_INPUT_W = config.MODEL_INPUT_W
CAM = config.CAMERA_INDEX
USE_OVERLAY = config.USE_OVERLAY

AWS_RTSP_URL = config.AWS_RTSP_URL

PIPELINE_STR = config.PIPELINE_STR

FRAME_DURATION = config.FRAME_DURATION

LOOK_AHEAD = config.LOOK_AHEAD

# Define shared structures
frame_queue = Queue(maxsize=1)   # latest frame only
stop_event = Event()

shared_state = {
    "angle": 0.0,
    "center_points": [],
    "vp_y": 0
}

state_lock = Lock()


def find_camera(max_devices=5):
    for i in range(max_devices):
        cap = cv2.VideoCapture(f"/dev/video{i}", cv2.CAP_V4L2)
        if cap.isOpened():
            cap.release()
            return i
    raise RuntimeError("No camera devices found")


def open_camera(cam_index: int, width: int, height: int, timeout: float = 2.0):
    device_path = f"/dev/video{cam_index}"

    # 1. Check device exists
    if not os.path.exists(device_path):
        raise RuntimeError(f"Camera device not found: {device_path}")

    cap = cv2.VideoCapture(device_path, cv2.CAP_V4L2)

    # 2. Wait briefly for camera to initialize
    start = time.time()
    while not cap.isOpened():
        if time.time() - start > timeout:
            cap.release()
            raise RuntimeError(f"Failed to open camera: {device_path}")
        time.sleep(0.1)

    # 3. Apply properties
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    # 4. Verify properties (V4L2 may ignore requests)
    actual_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    if actual_w != width or actual_h != height:
        print(
            f"[WARN] Camera resolution mismatch: "
            f"requested={width}x{height}, got={actual_w}x{actual_h}"
        )

    # 5. Final sanity read
    ret, frame = cap.read()
    if not ret or frame is None:
        cap.release()
        raise RuntimeError("Camera opened but failed to read initial frame")

    return cap




def process_camera_stream(shared_angle, shared_seq):
    # -------- IMPORT GPU + GST HERE (child-only) --------
    import gi
    gi.require_version('Gst', '1.0')
    from gi.repository import Gst

    import pycuda.driver as cuda
    cuda.init()

    from Model_unet import TensorRTUnetSegmentor

    Gst.init(None)

    pipeline = Gst.parse_launch(PIPELINE_STR)
    appsrc = pipeline.get_by_name("mysource")
    pipeline.set_state(Gst.State.PLAYING)

    segmentor = TensorRTUnetSegmentor(
        ENGINE_FILE_PATH,
        MODEL_INPUT_H,
        MODEL_INPUT_W,
        WIDTH,
        HEIGHT
    )

    CAM = find_camera()
    cap = open_camera(CAM, WIDTH, HEIGHT)
    time.sleep(0.2)

    pts = 0

    planner_thread = threading.Thread(
        target=path_planning_thread,
        args=(frame_queue, shared_angle, shared_seq, stop_event, state_lock, shared_state),
        name="PathPlanner",
        daemon=True
    )
    planner_thread.start()

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # ---------- 1. Inference (ALWAYS runs) ----------
        mask = segmentor.infer(frame)
        if frame_queue.empty():
            frame_queue.put((frame.copy(), mask))
        # path_planning(shared_angle, shared_seq)
        
        # ---------- 4. Choose frame to stream ----------
        if USE_OVERLAY:
           
            frame_to_push = overlay(frame, mask, state_lock, shared_state)

        else:
            # ---- raw camera feed ----
            frame_to_push = frame

        # ---------- 5. Push to GStreamer ----------
        frame_to_push = np.ascontiguousarray(frame_to_push)
        buf = Gst.Buffer.new_wrapped(frame_to_push.tobytes())
        buf.pts = pts
        buf.duration = FRAME_DURATION
        pts += FRAME_DURATION
        appsrc.emit("push-buffer", buf)

    appsrc.emit("end-of-stream")
    pipeline.set_state(Gst.State.NULL)
    stop_event.set()
    planner_thread.join(timeout=1.0)
    cap.release()
