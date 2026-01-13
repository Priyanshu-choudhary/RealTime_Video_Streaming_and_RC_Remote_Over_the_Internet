import multiprocessing as mp
import ctypes
from multiprocessing import Value, Process
import config

from python_GStreamer_transmitter import process_camera_stream
# from control_process import PIDController
from main_client import run_main

if __name__ == "__main__":
    mp.set_start_method("spawn", force=True)

    shared_angle = Value(ctypes.c_double, 0.0, lock=False)
    shared_seq   = Value(ctypes.c_ulong, 0, lock=False)

    if config.RUN_VISION_PROCESS:
        vision = Process(
            target=process_camera_stream,
            args=(shared_angle, shared_seq),
            daemon=True
        )

   
    control = Process(
        target=run_main,
        args=(shared_angle, shared_seq),
        daemon=True
    )

    if config.RUN_VISION_PROCESS:
        vision.start()
        

    control.start()
    if config.RUN_VISION_PROCESS:
        vision.join()

    control.join()
