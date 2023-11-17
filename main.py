from flask import Flask, jsonify


def setup_app():
    from prometheus_client import multiprocess
    from prometheus_client.core import CollectorRegistry
    from prometheus_flask_exporter import PrometheusMetrics

    registry = CollectorRegistry()
    multiprocess.MultiProcessCollector(registry)

    flask_app = Flask(__name__)
    PrometheusMetrics(app=flask_app, registry=registry, group_by='url_rule', defaults_prefix='teko')
    return flask_app


app = setup_app()


@app.route('/', methods=['GET'])
def home():
    return jsonify({'data': 'ABCD'})

# @app.route('/users/<user_id>', methods=['GET'])
# def get_user(user_id: int):
#     return jsonify({'data': f'User: {user_id}'})
