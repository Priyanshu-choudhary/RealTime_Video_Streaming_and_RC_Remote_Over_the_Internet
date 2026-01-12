# --- health_monitor.py ---
import asyncio
import aiohttp
import time

class HealthMonitor:
    def __init__(self, endpoint_url, interval=1.0):
        self.url = endpoint_url
        self.interval = interval
        self.last_report_time = 0
        self.container_status = "RUNNING"
        self._session = None

    
    async def _get_session(self):
        """Internal helper to ensure a session exists."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def _send_post(self, latency,lastMessageTime):
        """The actual background POST request."""
        payload = {
            "latency": int(latency),
            "last_message_time": lastMessageTime,
            "container_status": self.container_status,
            "connected": True,
            "up_time": int(time.time()), 
        }
        try:
            session = await self._get_session()
            async with session.post(self.url, json=payload, timeout=1.0) as response:
                if response.status != 200:
                    print(f"⚠️ Health Monitor Error: {response.status}")
        except Exception as e:
            print(f"⚠️ Health Monitor failed to reach endpoint: {e}")

    def update(self, latency,lastMessageTime):
        """
        Call this every loop iteration. 
        It handles its own timing so it won't flood the server.
        """
        current_time = time.time()
        if current_time - self.last_report_time > self.interval:
            # Trigger the background task
            asyncio.ensure_future(self._send_post(latency,lastMessageTime))
            self.last_report_time = current_time

    async def close(self):
        """Closes the underlying aiohttp session."""
        if self._session:
            await self._session.close()
