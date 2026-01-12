
import queue
import time
from threading import Lock

# Singleton Queue
_msg_queue = queue.Queue()
_last_sent_times = {}
_lock = Lock()

def send(message: str, min_interval: float = 0.0):
    """
    Queues a message to be sent via the WebSocket, adhering to the specified interval.
    
    Args:
        message (str): The text to send.
        min_interval (float): Minimum time (in seconds) between sends of THIS specific message string.
                              If 0, sends immediately (queued).
    """
    global _last_sent_times

    current_time = time.time()
    
    with _lock:
        last_time = _last_sent_times.get(message, 0.0)
        
        if (current_time - last_time) >= min_interval:
            _msg_queue.put(message)
            _last_sent_times[message] = current_time

def get_queue():
    """Returns the underlying queue object (for consumer use)."""
    return _msg_queue
