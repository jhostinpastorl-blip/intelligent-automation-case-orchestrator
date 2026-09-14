import os
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

_configured=False
def configure_telemetry(app=None):
    global _configured
    if _configured: return
    provider=TracerProvider(resource=Resource.create({"service.name":os.getenv("OTEL_SERVICE_NAME","intelligent-automation-case-orchestrator")}))
    endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if endpoint:
        provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=f"{endpoint.rstrip('/')}/v1/traces")))
    trace.set_tracer_provider(provider)
    HTTPXClientInstrumentor().instrument()
    if app is not None: FastAPIInstrumentor.instrument_app(app)
    _configured=True

def get_tracer(): return trace.get_tracer("intelligent_automation")
