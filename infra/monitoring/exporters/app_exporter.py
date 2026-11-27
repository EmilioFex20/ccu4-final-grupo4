import os
import threading
import time
import urllib.error
import urllib.request

from prometheus_client import Counter, Gauge, Histogram, start_http_server

DEFAULT_TARGETS = "health=http://api:8000/health,menu=http://api:8000/menu"


def parse_targets(raw):
    targets = []
    for item in raw.split(","):
        item = item.strip()
        if not item:
            continue
        if "=" in item:
            name, url = item.split("=", 1)
        else:
            url = item
            name = url.rstrip("/").rsplit("/", 1)[-1] or "root"
        targets.append((name.strip(), url.strip()))
    return targets


TARGETS = parse_targets(os.getenv("PROBE_TARGETS", DEFAULT_TARGETS))
INTERVAL = max(5, int(os.getenv("PROBE_INTERVAL_SECONDS", "15")))
TIMEOUT = float(os.getenv("PROBE_TIMEOUT_SECONDS", "3"))
PORT = int(os.getenv("EXPORTER_PORT", "9101"))

PROBE_UP = Gauge(
    "cafeteria_probe_up",
    "Resultado de la ultima sonda HTTP (1=exito, 0=fallo)",
    ["endpoint", "target"],
)
PROBE_REQUESTS = Counter(
    "cafeteria_probe_requests_total",
    "Numero de sondas HTTP realizadas por este exportador",
    ["endpoint", "target"],
)
PROBE_ERRORS = Counter(
    "cafeteria_probe_errors_total",
    "Numero de sondas fallidas por red o codigo HTTP >= 400",
    ["endpoint", "target"],
)
PROBE_RESPONSES = Counter(
    "cafeteria_probe_http_responses_total",
    "Respuestas HTTP observadas por las sondas, por codigo",
    ["endpoint", "target", "status"],
)
PROBE_DURATION = Histogram(
    "cafeteria_probe_duration_seconds",
    "Duracion de las sondas HTTP en segundos",
    ["endpoint", "target"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5),
)
PROBE_LAST_SUCCESS = Gauge(
    "cafeteria_probe_last_success_timestamp_seconds",
    "Timestamp Unix de la ultima sonda exitosa",
    ["endpoint", "target"],
)


def probe(endpoint, url):
    labels = {"endpoint": endpoint, "target": url}
    started = time.monotonic()
    status = "network_error"
    success = False
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "ccu4-app-exporter/1.0"})
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            response.read()
            status = str(response.status)
            success = 200 <= response.status < 400
    except urllib.error.HTTPError as error:
        status = str(error.code)
        error.read()
    except (urllib.error.URLError, TimeoutError, OSError):
        pass
    except Exception:
        pass

    elapsed = time.monotonic() - started
    PROBE_REQUESTS.labels(**labels).inc()
    PROBE_RESPONSES.labels(**{**labels, "status": status}).inc()
    PROBE_DURATION.labels(**labels).observe(elapsed)
    PROBE_UP.labels(**labels).set(1 if success else 0)
    if success:
        PROBE_LAST_SUCCESS.labels(**labels).set(time.time())
    else:
        PROBE_ERRORS.labels(**labels).inc()
    print(f"sonda endpoint={endpoint} status={status} duracion={elapsed:.3f}s", flush=True)


def loop():
    while True:
        for endpoint, url in TARGETS:
            probe(endpoint, url)
        time.sleep(INTERVAL)


def main():
    start_http_server(PORT)
    print(f"app-exporter escuchando en :{PORT} con {len(TARGETS)} sondas", flush=True)
    threading.Thread(target=loop, daemon=True).start()
    while True:
        time.sleep(3600)


if __name__ == "__main__":
    main()
