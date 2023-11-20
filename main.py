import dataclasses
import os
from dataclasses import dataclass
from typing import List

import flask.json
import flask_restplus
import msgspec
from flask import Flask, jsonify
from flask_restplus import Resource
from prometheus_client import Counter
from prometheus_flask_exporter import PrometheusMetrics


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
    return flask_app


total_item_counter = Counter(
    name='cache_counter', documentation='',
    labelnames=['content', 'type'],
)

app = setup_app()

api = flask_restplus.Api(app)

next_counter = 0


def before_req_func():
    global next_counter
    next_counter += 1
    print("BEFORE REQ NEXT PIPE:", next_counter, os.getpid())


app.before_request(before_req_func)


@app.route('/', methods=['GET'])
def home():
    print("PRINT HOME")
    return jsonify({'data': 'ABCD'})


@dataclass
class Role:
    role_id: int


@dataclass
class User(msgspec.Struct):
    user_id: int
    name: str
    age: int
    roles: List[Role]


u1 = User(user_id=11, name='user01', age=80, roles=[Role(role_id=51)])
u2 = User(user_id=12, name='user02', age=81, roles=[Role(role_id=52)])


@app.route('/users/<user_id>', methods=['GET'])
def get_user(user_id):
    total_item_counter.labels('user', 'hit').inc()
    if int(user_id) > 1000:
        total_item_counter.labels('user', 'fill').inc()
    return jsonify({'name': 'username'})


@api.route('/customers')
class Customers(Resource):
    def get(self):
        return {
            'users': [u1, u2]
        }


if __name__ == "__main__":
    app.run()
