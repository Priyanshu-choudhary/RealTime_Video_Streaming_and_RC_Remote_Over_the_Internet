import cv2
import numpy as np
import time
import math

# -------- constants (safe at import) --------
WIDTH, HEIGHT = 1280, 720
FPS = 30

ENGINE_FILE_PATH = "unet_mobilenetv2_Marbel.engine"
MODEL_INPUT_H = 384
MODEL_INPUT_W = 384
CAM = 0
USE_OVERLAY = True 

AWS_RTSP_URL = "rtsp://yadiec2.freedynamicdns.net:8554/cam2"

PIPELINE_STR = (
    "appsrc name=mysource is-live=true format=3 "
    "caps=video/x-raw,format=BGR,width=1280,height=720,framerate=30/1 ! "
    "videoconvert ! video/x-raw,format=I420 ! "
    "nvvidconv ! video/x-raw(memory:NVMM),format=NV12 ! "
    "nvv4l2h264enc bitrate=800000 control-rate=1 preset-level=1 "
    "insert-sps-pps=true maxperf-enable=1 ! "
    "h264parse ! "
    "rtspclientsink location=rtsp://yadiec2.freedynamicdns.net:8554/cam2 "
    "protocols=tcp do-rtsp-keep-alive=true"
)

FRAME_DURATION = int(1e9 / FPS)




def calculate_steering_error(center_bottom, target_point):
    """
    Calculates the angle between the car's center-forward axis 
    and the detected path point.
    """
    # Vector from car bottom-center to a point on the path
    dx = target_point[0] - center_bottom[0]
    dy = target_point[1] - center_bottom[1] # dy will be negative because y decreases upward
    
    # Calculate angle in radians. 
    # We use -dy because in image coordinates, 'up' is negative Y.
    # This aligns 0 degrees with "straight up"
    angle_rad = math.atan2(dx, -dy) 
    
    return math.degrees(angle_rad)




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

    cap = cv2.VideoCapture(f"/dev/video{CAM}", cv2.CAP_V4L2)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)

    time.sleep(0.3)

    pts = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # ---------- 1. Inference (ALWAYS runs) ----------
        mask = segmentor.infer(frame)

        # ---------- 2. Path computation ----------
        center_points = []
        for y in range(0, mask.shape[0], 50):
            idx = np.where(mask[y] == 255)[0]
            if len(idx):
                center_points.append(((idx[0] + idx[-1]) // 2, y))

        if len(center_points) < 2:
            continue

        
        
        # Define the car's bottom center
        car_center_x = WIDTH // 2
        car_bottom_y = HEIGHT - 1
        center = (car_center_x, car_bottom_y )
        vp_y = int(HEIGHT * 0.6)
        
        # Pick a target point from the detected line (e.g., the second point found)
        # Choosing a point higher up (e.g., center_points[2]) gives the PID 
        # a "look-ahead" distance which makes the car more stable at speed.
        target_p = center_points[1] 

        # Calculate error: Positive = Right, Negative = Left
        angle = calculate_steering_error((car_center_x, car_bottom_y), target_p)

        # Publish the signed angle
        shared_angle.value = float(angle)
        shared_seq.value += 1


        # ---------- 4. Choose frame to stream ----------
        if USE_OVERLAY:
            # ---- overlay mask ----
            color_mask = np.zeros_like(frame, dtype=np.uint8)
            color_mask[mask > 0] = (255, 255, 255)
            output = cv2.addWeighted(frame, 1.0, color_mask, 0.5, 0)

            # ---- draw guide lines ----
            vp_x = WIDTH // 2
            left_bottom  = (int(WIDTH * 0.2), HEIGHT - 10)
            right_bottom = (int(WIDTH * 0.8), HEIGHT - 10)

            cv2.line(output, left_bottom, (vp_x, vp_y), (0, 255, 0), 2)
            cv2.line(output, right_bottom, (vp_x, vp_y), (0, 255, 0), 2)
            cv2.line(output, (vp_x, vp_y + 50), (vp_x, HEIGHT - 10), (0, 255, 255), 1)

            # ---- draw center points ----
            for p in center_points:
                cv2.circle(output, p, 4, (255, 0, 0), -1)

            # ---- draw predicted path ----
            cv2.line(output, center, center_points[1], (0, 0, 0), 2)

            # ---- draw angle text ----
            cv2.putText(
                output,
                f"{angle:.1f} deg",
                (100, 100),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.9,
                (0, 0, 255),
                2
            )

            frame_to_push = output

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
    cap.release()
