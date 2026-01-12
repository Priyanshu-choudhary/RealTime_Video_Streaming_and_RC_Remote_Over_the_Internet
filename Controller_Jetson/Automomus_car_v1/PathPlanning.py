import math
import numpy as np
import cv2
import config

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


def path_planning_thread(frame_queue, shared_angle, shared_seq, stop_event, state_lock, shared_state):
    while not stop_event.is_set():
        try:
            frame, mask = frame_queue.get(timeout=0.1)
        except:
            continue

        center_points = []
        for y in range(0, mask.shape[0], 50):
            idx = np.where(mask[y] == 255)[0]
            if len(idx):
                center_points.append(((idx[0] + idx[-1]) // 2, y))

        if len(center_points) <= config.LOOK_AHEAD:
            continue

        car_center_x = config.CAMERA_WIDTH // 2
        car_bottom_y = config.CAMERA_HEIGHT - 1
        vp_y = int(config.CAMERA_HEIGHT * 0.6)

        target_p = center_points[config.LOOK_AHEAD]
        angle = calculate_steering_error(
            (car_center_x, car_bottom_y),
            target_p
        )

        shared_angle.value = float(angle)
        shared_seq.value += 1
        with state_lock:
            shared_state["angle"] = angle
            shared_state["center_points"] = center_points
            shared_state["vp_y"] = vp_y


def overlay(frame, mask, state_lock, shared_state):
    with state_lock:
        angle = shared_state["angle"]
        center_points = shared_state["center_points"]
        vp_y = shared_state["vp_y"]

    # ---- overlay mask ----
    color_mask = np.zeros_like(frame, dtype=np.uint8)
    color_mask[mask > 0] = (255, 255, 255)
    output = cv2.addWeighted(frame, 1.0, color_mask, 0.5, 0)

    vp_x = config.CAMERA_WIDTH // 2
    left_bottom  = (int(config.CAMERA_WIDTH * 0.2), config.CAMERA_HEIGHT - 10)
    right_bottom = (int(config.CAMERA_WIDTH * 0.8), config.CAMERA_HEIGHT - 10)

    cv2.line(output, left_bottom, (vp_x, vp_y), (0, 255, 0), 2)
    cv2.line(output, right_bottom, (vp_x, vp_y), (0, 255, 0), 2)

    for p in center_points:
        cv2.circle(output, p, 4, (255, 0, 0), -1)

    if len(center_points) > config.LOOK_AHEAD:
        cv2.line(output, center_points[0],
                 center_points[config.LOOK_AHEAD], (0, 0, 0), 2)

    cv2.putText(
        output,
        f"{angle:.1f} deg",
        (100, 100),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.9,
        (0, 0, 255),
        2
    )

    return output