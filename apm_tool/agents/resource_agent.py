import asyncio
import psutil
from apm_tool.datastore import datastore
from apm_tool.config import MONITORING_INTERVAL_SECONDS

class ResourceAgent:
    def __init__(self, interval=MONITORING_INTERVAL_SECONDS):
        self.interval = interval
        self.is_running = False

    async def start(self):
        self.is_running = True
        while self.is_running:
            cpu_percent = psutil.cpu_percent()
            memory_percent = psutil.virtual_memory().percent
            metric = {
                "cpu_percent": cpu_percent,
                "memory_percent": memory_percent,
            }
            datastore.add_resource_metric(metric)
            print(f"Resource Usage: {metric}")
            await asyncio.sleep(self.interval)

    def stop(self):
        self.is_running = False
