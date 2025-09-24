from fastapi import FastAPI
from apm_tool.datastore import datastore

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "APM Tool Dashboard"}

@app.get("/metrics")
def get_metrics():
    return {
        "http_metrics": datastore.get_http_metrics(),
        "resource_metrics": datastore.get_resource_metrics(),
    }
