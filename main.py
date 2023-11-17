import os

from flask import Flask, jsonify
from prometheus_client import multiprocess
from prometheus_client.core import CollectorRegistry
from prometheus_flask_exporter import PrometheusMetrics


def setup_app():
    registry = CollectorRegistry()

    p = os.environ.get('prometheus_multiproc_dir')
    if not p:
        raise ValueError('missing "prometheus_multiproc_dir" env variable')

    multiprocess.MultiProcessCollector(registry, path=p)

    flask_app = Flask(__name__)
    PrometheusMetrics(app=flask_app, registry=registry, group_by='url_rule', defaults_prefix='teko')
    return flask_app


app = setup_app()


@app.route('/', methods=['GET'])
def home():
    return jsonify({'data': 'ABCD'})


@app.route('/users/<user_id>', methods=['GET'])
def get_user(user_id: int):
    return jsonify({'data': f'User: {user_id}'})


if __name__ == "__main__":
    app.run()
