import logging
from pythonjsonlogger import jsonlogger
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from fastapi import FastAPI
from core.config import get_settings

settings = get_settings()

def setup_telemetry(app: FastAPI):
    # 1. Setup JSON Logging
    logger = logging.getLogger()
    
    # We want to keep standard logging in development for readability,
    # but use JSON logs in production.
    if settings.environment == "production":
        logger.setLevel(logging.INFO)
        # Clear existing handlers
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
            
        logHandler = logging.StreamHandler()
        formatter = jsonlogger.JsonFormatter(
            '%(timestamp)s %(level)s %(name)s %(message)s',
            timestamp=True
        )
        logHandler.setFormatter(formatter)
        logger.addHandler(logHandler)

    # 2. Setup OpenTelemetry
    if settings.enable_telemetry:
        provider = TracerProvider()
        
        # In a real production setting, you'd use OTLPSpanExporter here
        # to send data to Jaeger or an OpenTelemetry Collector.
        # For now, we'll just log traces to console (or drop them if no exporter is configured).
        # We'll use ConsoleSpanExporter just for demonstration, but in real prod we'd configure OTLP.
        # processor = BatchSpanProcessor(ConsoleSpanExporter())
        # provider.add_span_processor(processor)
        
        trace.set_tracer_provider(provider)
        FastAPIInstrumentor.instrument_app(app)
