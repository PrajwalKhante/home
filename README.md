# APM Tool

This is a simple Application Performance Monitoring (APM) tool built with Python. It can monitor system resources (CPU and memory) and intercept HTTP traffic to measure latency and other metrics.

## Features

- **Resource Monitoring:** Monitors CPU and memory usage.
- **HTTP Monitoring:** Acts as a proxy to intercept and analyze HTTP traffic.
- **Web Dashboard:** Provides a simple web-based dashboard to view the collected metrics.

## How to Run

1.  Install the dependencies:
    ```bash
    pip install -r requirements.txt
    ```

2.  Run the application:
    ```bash
    python3 -m apm_tool.main
    ```

## How to Use the HTTP Proxy

To monitor the HTTP traffic of an application, you need to configure the application to use the APM tool's proxy. The proxy runs on `http://localhost:8080`.

How you configure the proxy depends on the application you want to monitor. Here are a few examples:

- **For command-line tools like `curl`:**
  ```bash
  curl -x http://localhost:8080 http://example.com
  ```

- **For Python applications using the `requests` library:**
  ```python
  import requests

  proxies = {
      "http": "http://localhost:8080",
      "https": "http://localhost:8080",
  }

  requests.get("http://example.com", proxies=proxies)
  ```

- **For web browsers:** You can configure the proxy settings in your browser to point to `http://localhost:8080`.

## Dashboard

The dashboard is available at `http://localhost:8000`. It provides a JSON API to view the collected metrics at the `/metrics` endpoint.
