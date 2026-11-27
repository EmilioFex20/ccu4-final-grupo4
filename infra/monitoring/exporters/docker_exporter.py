import http.client
import json
import os
import socket
import threading
import time
from urllib.parse import urlparse

from prometheus_client import Counter, Gauge, start_http_server

PORT = int(os.getenv("EXPORTER_PORT", "9102"))
INTERVAL = max(5, int(os.getenv("COLLECT_INTERVAL_SECONDS", "15")))
DOCKER_HOST = os.getenv("DOCKER_HOST", "unix:///var/run/docker.sock")
LAST_CPU = {}

CONTAINER_CPU = Counter(
    "cafeteria_container_cpu_seconds_total",
    "Tiempo acumulado de CPU por contenedor segun Docker Engine",
    ["name", "image"],
)
CONTAINER_MEMORY = Gauge(
    "cafeteria_container_memory_bytes",
    "Memoria en uso por contenedor segun Docker Engine",
    ["name", "image"],
)
CONTAINER_RUNNING = Gauge(
    "cafeteria_container_running",
    "1 si el contenedor esta corriendo, 0 si no",
    ["name", "image"],
)
CONTAINER_RESTARTS = Gauge(
    "cafeteria_container_restart_count",
    "Numero acumulado de reinicios del contenedor",
    ["name", "image"],
)
COLLECT_ERRORS = Counter(
    "cafeteria_docker_exporter_errors_total",
    "Errores al consultar Docker Engine",
)


class UnixSocketHTTPConnection(http.client.HTTPConnection):
    def __init__(self, socket_path, timeout=5):
        super().__init__("docker", timeout=timeout)
        self.socket_path = socket_path

    def connect(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.settimeout(self.timeout)
        self.sock.connect(self.socket_path)


def connection():
    parsed = urlparse(DOCKER_HOST)
    if parsed.scheme != "unix" or not parsed.path:
        raise RuntimeError("DOCKER_HOST debe ser unix:///var/run/docker.sock; TCP no esta permitido")
    return UnixSocketHTTPConnection(parsed.path, timeout=5)


def docker_get(path):
    conn = connection()
    try:
        conn.request("GET", f"/v1.41{path}", headers={"Host": "docker"})
        response = conn.getresponse()
        body = response.read()
        if response.status != 200:
            raise RuntimeError(f"Docker Engine devolvio {response.status} para {path}")
        return json.loads(body)
    finally:
        conn.close()


def container_name(item):
    names = item.get("Names") or []
    return names[0].lstrip("/") if names else item.get("Id", "")[:12]


def collect():
    containers = docker_get("/containers/json?all=0")
    for item in containers:
        name = container_name(item)
        image = item.get("Image", "unknown")
        labels = {"name": name, "image": image}
        CONTAINER_RUNNING.labels(**labels).set(1 if item.get("State") == "running" else 0)

        restarts = int(item.get("RestartCount", 0) or 0)
        CONTAINER_RESTARTS.labels(**labels).set(restarts)

        try:
            stats = docker_get(f"/containers/{item['Id']}/stats?stream=false")
            cpu_total = stats.get("cpu_stats", {}).get("cpu_usage", {}).get("total_usage", 0)
            memory = stats.get("memory_stats", {}).get("usage", 0)
            previous = LAST_CPU.get(name, cpu_total)
            if cpu_total >= previous:
                CONTAINER_CPU.labels(**labels).inc(cpu_total - previous)
            LAST_CPU[name] = cpu_total
            CONTAINER_MEMORY.labels(**labels).set(memory)
        except Exception:
            COLLECT_ERRORS.inc()


def loop():
    while True:
        try:
            collect()
        except Exception:
            COLLECT_ERRORS.inc()
        time.sleep(INTERVAL)


def main():
    start_http_server(PORT)
    print(f"docker-exporter escuchando en :{PORT} usando {DOCKER_HOST}", flush=True)
    threading.Thread(target=loop, daemon=True).start()
    while True:
        time.sleep(3600)


if __name__ == "__main__":
    main()
