"""
Streamora Platform Telemetry
All observability dependencies are optional — the server starts cleanly
even when pythonjsonlogger / opentelemetry / prometheus are not installed.
"""
import logging
from fastapi import FastAPI

# ── Optional: JSON structured logging ─────────────────────────────────────────
try:
    from pythonjsonlogger import jsonlogger
    _JSON_LOGGER_AVAILABLE = True
except ImportError:
    jsonlogger = None  # type: ignore
    _JSON_LOGGER_AVAILABLE = False

# ── Optional: OpenTelemetry tracing ───────────────────────────────────────────
try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    _OTEL_AVAILABLE = True
except ImportError:
    _OTEL_AVAILABLE = False

# ── Config ────────────────────────────────────────────────────────────────────
try:
    from core.config import get_settings
    settings = get_settings()
    _env = getattr(settings, "environment", "development")
    _telemetry_enabled = getattr(settings, "enable_telemetry", False)
except Exception:
    _env = "development"
    _telemetry_enabled = False


def setup_telemetry(app: FastAPI) -> None:
    """Configure structured logging and distributed tracing.
    All integrations degrade gracefully when their packages are absent.
    """
    # 1. JSON Logging (production only)
    if _env == "production" and _JSON_LOGGER_AVAILABLE:
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        log_handler = logging.StreamHandler()
        formatter = jsonlogger.JsonFormatter(  # type: ignore[union-attr]
            "%(timestamp)s %(level)s %(name)s %(message)s",
            timestamp=True,
        )
        log_handler.setFormatter(formatter)
        logger.addHandler(log_handler)
        logging.info("[telemetry] JSON structured logging enabled")
    else:
        logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    # 2. OpenTelemetry tracing
    if _telemetry_enabled and _OTEL_AVAILABLE:
        provider = TracerProvider()  # type: ignore[name-defined]
        # Uncomment to export to an OTLP collector:
        # processor = BatchSpanProcessor(ConsoleSpanExporter())
        # provider.add_span_processor(processor)
        trace.set_tracer_provider(provider)  # type: ignore[name-defined]
        FastAPIInstrumentor.instrument_app(app)  # type: ignore[name-defined]
        logging.info("[telemetry] OpenTelemetry tracing enabled")
    else:
        logging.info("[telemetry] OpenTelemetry disabled (set ENABLE_TELEMETRY=true to activate)")
