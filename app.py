from __future__ import annotations

import threading

from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse

app = FastAPI(title="SRE Trainee App", version="1.0.0")

_lock = threading.Lock()
http_requests_total = 0
http_errors_total = 0


@app.middleware("http")
async def count_requests(request: Request, call_next):
    global http_requests_total, http_errors_total

    response = await call_next(request)
    with _lock:
        http_requests_total += 1
        if response.status_code >= 500:
            http_errors_total += 1
    return response


@app.get("/", response_class=PlainTextResponse)
async def root() -> str:
    return "OK"


@app.get("/metrics", response_class=PlainTextResponse)
async def metrics() -> str:
    with _lock:
        requests_total = http_requests_total
        errors_total = http_errors_total

    return (
        "# HELP http_requests_total Total requests\n"
        "# TYPE http_requests_total counter\n"
        f"http_requests_total {requests_total}\n"
        "# HELP http_errors_total Total errors\n"
        "# TYPE http_errors_total counter\n"
        f"http_errors_total {errors_total}\n"
    )
