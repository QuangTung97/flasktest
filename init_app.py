import dataclasses
from typing import Optional

import flask
import flask_restplus
from flask import Flask
from memproxy import Pipeline
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource as OtelResource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from prometheus_flask_exporter import PrometheusMetrics  # type: ignore

from init_cache import init_cache_client


def init_jaeger():
    provider = TracerProvider(
        resource=OtelResource.create({SERVICE_NAME: "tung-api"})
    )
    trace.set_tracer_provider(provider)

    # create a JaegerExporter
    exporter = JaegerExporter(
        agent_host_name='localhost',
        agent_port=6831,
    )

    # Create a BatchSpanProcessor and add the exporter to it
    span_processor = BatchSpanProcessor(exporter)

    # add to the tracer
    provider.add_span_processor(span_processor)


class CustomEncoder(flask.json.JSONEncoder):
    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        return super().default(o)


class Config:
    RESTPLUS_JSON = {'cls': CustomEncoder}


def setup_app():
    flask_app = Flask(__name__)
    flask_app.config.from_object(Config)
    PrometheusMetrics(app=flask_app, group_by='url_rule', defaults_prefix='teko')
    flask_app.json_encoder = CustomEncoder

    FlaskInstrumentor().instrument_app(flask_app, excluded_urls='metrics')

    return flask_app


init_jaeger()

app = setup_app()

api = flask_restplus.Api(app)

_cache_client = init_cache_client()

_pipeline: Optional[Pipeline] = None


# Setup Before Request
def before_req_func():
    # reset pipeline
    global _pipeline
    _pipeline = None


def get_pipeline() -> Pipeline:
    global _pipeline

    if _pipeline:
        return _pipeline

    _pipeline = _cache_client.pipeline()
    return _pipeline


app.before_request(before_req_func)
