import asyncio
import multiprocessing
import uvicorn
from mitmproxy.tools.dump import DumpMaster
from mitmproxy import options
from apm_tool.agents import http_agent
from apm_tool.agents.resource_agent import ResourceAgent
from apm_tool.dashboard import app

def run_http_agent():
    opts = options.Options(
        listen_host='0.0.0.0',
        listen_port=8080,
    )
    opts.add_option("mode", str, "regular", "Proxy mode")

    m = DumpMaster(opts)
    m.addons.add(http_agent.addons)

    print("HTTP Agent (Proxy) started on http://0.0.0.0:8080")
    m.run()

def run_dashboard():
    config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="info")
    server = uvicorn.Server(config)
    server.run()

class Orchestrator:
    def __init__(self):
        self.agents = []
        self.http_process = None
        self.dashboard_process = None

    async def run(self):
        print("Orchestrator is running")

        self.http_process = multiprocessing.Process(target=run_http_agent)
        self.dashboard_process = multiprocessing.Process(target=run_dashboard)

        self.http_process.start()
        self.dashboard_process.start()

        resource_agent = ResourceAgent()

        await resource_agent.start()

    def shutdown(self):
        print("Shutting down...")
        if self.http_process:
            self.http_process.terminate()
            self.http_process.join()
        if self.dashboard_process:
            self.dashboard_process.terminate()
            self.dashboard_process.join()
