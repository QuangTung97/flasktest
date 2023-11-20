import time
from dataclasses import dataclass
from typing import List

import msgspec
from flask import jsonify
from flask_restplus import Resource
from opentelemetry import trace
from prometheus_client import Counter

from caching import new_cache_item
from init_app import app, api

total_item_counter = Counter(
    name='cache_counter', documentation='',
    labelnames=['content', 'type'],
)


@dataclass
class User(msgspec.Struct):
    user_id: int
    name: str
    age: int

    def get_id(self) -> int:
        return self.user_id


u1 = User(user_id=11, name='user01', age=80)
u2 = User(user_id=12, name='user02', age=81)


@app.route('/users/<user_id>', methods=['GET'])
def get_user(user_id):
    total_item_counter.labels('user', 'hit').inc()
    if int(user_id) > 1000:
        total_item_counter.labels('user', 'fill').inc()
    return jsonify({'name': 'username'})


def get_users_from_db(id_list: List[int]) -> List[User]:
    return [User(user_id=i, name=f'users:{i}', age=51) for i in id_list]


new_user_item = new_cache_item(
    cls=User, fill_func=get_users_from_db,
    get_key=User.get_id,
    default=User(user_id=0, name='', age=0),
    key_name=lambda user_id: f'u2:{user_id}',
)


@app.route('/all-users', methods=['GET'])
def get_all_users():
    tracer = trace.get_tracer('my-tracer')

    user_item = new_user_item()

    with tracer.start_span('get-from-cache') as span:
        id_list = list(range(10))
        fn = user_item.get_multi(id_list)

        id_list = list(range(300, 310))
        fn2 = user_item.get_multi(id_list)

        users = fn()
        users2 = fn2()

        span.set_attribute('hit_count', user_item.hit_count)
        span.set_attribute('fill_count', user_item.fill_count)
        span.set_attribute('bytes_read', user_item.bytes_read)

    return jsonify({
        'users': users,
        'users2': users2,
    })


@api.route('/customers')
class Customers(Resource):
    def get(self):
        tracer = trace.get_tracer('my-tracer')
        with tracer.start_as_current_span('get-users'):
            time.sleep(0.01)

        return {
            'users': [u1, u2]
        }


if __name__ == "__main__":
    app.run()
