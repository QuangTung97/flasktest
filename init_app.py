import flask
import flask_restplus
import msgspec
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource as OtelResource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.sampling import TraceIdRatioBased
from prometheus_flask_exporter import PrometheusMetrics  # type: ignore
from sqlalchemy.ext.declarative import declarative_base


def init_jaeger():
    sampler = TraceIdRatioBased(1 / 100)
    provider = TracerProvider(
        resource=OtelResource.create({SERVICE_NAME: "tung-api"}),
        sampler=sampler,
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
        if isinstance(o, msgspec.Struct):
            return msgspec.to_builtins(o)
        return super().default(o)


class Config:
    RESTPLUS_JSON = {'cls': CustomEncoder}
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:1@localhost:3306/bench?charset=utf8mb4'
    SQLALCHEMY_TRACK_MODIFICATIONS = False


Base = declarative_base()
db = SQLAlchemy(model_class=Base)


def create_app():
    flask_app = Flask(__name__)
    flask_app.config.from_object(Config)
    PrometheusMetrics(app=flask_app, group_by='url_rule', defaults_prefix='teko')
    flask_app.json_encoder = CustomEncoder

    FlaskInstrumentor().instrument_app(flask_app, excluded_urls='metrics')

    db.init_app(flask_app)

    return flask_app


init_jaeger()
app = create_app()

SQLAlchemyInstrumentor().instrument()

api = flask_restplus.Api(app)
