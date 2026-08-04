from fastapi import APIRouter, Response
from services.observability.metrics_exporter import PrometheusMetricsExporter

observability_router = APIRouter(tags=["Observability & Health"])
exporter = PrometheusMetricsExporter()

@observability_router.get("/health")
def health_check():
    return exporter.get_health_status()

@observability_router.get("/metrics")
def get_prometheus_metrics():
    metrics_text = exporter.export_prometheus_metrics()
    return Response(content=metrics_text, media_type="text/plain")
