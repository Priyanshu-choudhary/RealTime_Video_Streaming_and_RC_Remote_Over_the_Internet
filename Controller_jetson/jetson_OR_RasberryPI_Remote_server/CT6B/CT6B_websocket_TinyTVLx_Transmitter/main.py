
import asyncio
from Ct6b_serial_read import CT6BReceiver
from WebSocketSender import WebSocketSender


# --- Configuration ---
PORT = 'COM9'             
BAUD = 115200             
WS_URI = "wss://unmelodramatically-nonoxidating-mana.ngrok-free.dev/ws"
async def main_async():
    """Initializes components and runs the reader/sender tasks."""
    
    # 1. Initialize Serial Receiver
    receiver = CT6BReceiver(port=PORT, baud=BAUD)
    if not receiver.connect():
        return # Exit if serial connection fails

    # 2. Initialize WebSocket Sender
    sender = WebSocketSender(ws_uri=WS_URI, receiver_queue=receiver.queue)
    
    # 3. Create and run concurrent tasks
    reader_task = asyncio.create_task(receiver.run_reader())
    sender_task = asyncio.create_task(sender.run_sender())

    try:
        # Wait for both tasks to complete
        await asyncio.gather(reader_task, sender_task)
    except KeyboardInterrupt:
        print("\n[INFO] Program stopped by user (Ctrl+C).")
    finally:
        receiver.close() # Ensure serial port is closed

def run_main():
    """Entry point for the application."""
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        pass 

if __name__ == "__main__":
    run_main()