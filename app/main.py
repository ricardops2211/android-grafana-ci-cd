import os, random, time, json
from fastapi import FastAPI, Response
from fastapi.responses import PlainTextResponse
from datetime import datetime

app = FastAPI()
APP = os.getenv("APP_NAME", "api-demo")
FAIL_RATE = float(os.getenv("FAIL_RATE", "0.0"))

def log(level="INFO", msg="", status=200, latency_ms=1):
    print(json.dumps({
        "ts": datetime.utcnow().isoformat() + "Z",
        "app": APP, "level": level, "msg": msg,
        "status": status, "latency_ms": latency_ms, "path": "/healthz"
    }), flush=True)

@app.get("/healthz", response_class=PlainTextResponse)
def healthz():
    t0 = time.time()
    time.sleep(random.uniform(0.001, 0.020))
    if random.random() < FAIL_RATE:
        latency_ms = int((time.time() - t0) * 1000)
        log("ERROR", "request failed", 500, latency_ms)
        return Response("error", status_code=500)
    latency_ms = int((time.time() - t0) * 1000)
    log("INFO", "ok", 200, latency_ms)
    return PlainTextResponse("ok", status_code=200)
