from flask import Flask, jsonify
from prometheus_client import Counter
from prometheus_flask_exporter import PrometheusMetrics


def setup_app():
    flask_app = Flask(__name__)
    PrometheusMetrics(app=flask_app, group_by='url_rule', defaults_prefix='teko')
    return flask_app


total_item_counter = Counter(
    name='cache_counter', documentation='',
    labelnames=['content', 'type'],
)

app = setup_app()

pipe = 0


def before_req_func():
    global pipe
    pipe += 1
    print("NEXT PIPE:", pipe)


app.before_request(before_req_func)


@app.route('/', methods=['GET'])
def home():
    return jsonify({'data': 'ABCD'})


@app.route('/users/<user_id>', methods=['GET'])
def get_user(user_id):
    total_item_counter.labels('user', 'hit').inc()
    if int(user_id) > 1000:
        total_item_counter.labels('user', 'fill').inc()
    return jsonify({'data': f'User: {user_id}'})


if __name__ == "__main__":
    app.run()
