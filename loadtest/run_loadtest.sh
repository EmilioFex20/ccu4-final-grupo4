#!/usr/bin/env bash
set -euo pipefail

TARGET_HOST="${TARGET_HOST:-http://localhost:8000}"
NORMAL_USERS="${NORMAL_USERS:-10}"
PEAK_USERS="${PEAK_USERS:-100}"
SPIKE_USERS="${SPIKE_USERS:-150}"
RAMP_RATE="${RAMP_RATE:-10}"
DURATION_NORMAL="${DURATION_NORMAL:-30}"
DURATION_RAMP="${DURATION_RAMP:-60}"
DURATION_SPIKE="${DURATION_SPIKE:-30}"
DURATION_SUSTAINED="${DURATION_SUSTAINED:-60}"
DURATION_RAMPDOWN="${DURATION_RAMPDOWN:-60}"
DURATION_RECOVERY="${DURATION_RECOVERY:-30}"

root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
venv="$root/.venv"
results="$root/results"

if [ ! -x "$venv/bin/locust" ]; then
  python3 -m venv "$venv"
  "$venv/bin/pip" install --disable-pip-version-check -r "$root/requirements.txt"
fi

export TARGET_HOST NORMAL_USERS PEAK_USERS SPIKE_USERS RAMP_RATE
export DURATION_NORMAL DURATION_RAMP DURATION_SPIKE DURATION_SUSTAINED
export DURATION_RAMPDOWN DURATION_RECOVERY

mkdir -p "$results"
stamp="$(date +%Y%m%d-%H%M%S)"
prefix="$results/locust-$stamp"

echo "Objetivo: $TARGET_HOST | inicio: $(date -Iseconds)"
"$venv/bin/locust" -f "$root/locustfile.py" --host "$TARGET_HOST" \
  --headless --csv "$prefix" --html "$prefix-report.html" --loglevel INFO
echo "Fin: $(date -Iseconds)"
echo "Resultados: $prefix*.csv y $prefix-report.html | fases: $results/fases.log"
