FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY *.py ./

ARG EXPORTER_SCRIPT=app_exporter.py
ENV EXPORTER_SCRIPT=${EXPORTER_SCRIPT}
CMD python /app/${EXPORTER_SCRIPT}
