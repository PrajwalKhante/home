import time
from apm_tool.datastore import datastore

class HttpAgent:
    def request(self, flow):
        flow.request.start_time = time.time()

    def response(self, flow):
        duration = time.time() - flow.request.start_time
        metric = {
            "url": flow.request.pretty_url,
            "status_code": flow.response.status_code,
            "latency": duration,
        }
        datastore.add_http_metric(metric)
        print(f"HTTP Request: {metric}")

addons = [
    HttpAgent()
]
