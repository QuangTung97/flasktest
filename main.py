from typing import List

import flask
import msgspec
import time
from flask import jsonify
from flask_restplus import Resource
from opentelemetry import trace
from prometheus_client import Counter
from sqlalchemy import Column, Integer, VARCHAR, event

from caching import new_cache_item
from init_app import app, api, db

total_item_counter = Counter(
    name='cache_counter', documentation='',
    labelnames=['content', 'type'],
)

invalidate_keys: List[str] = []
deleted_keys: List[str] = []


@event.listens_for(db.session, 'before_commit')
def my_before_commit(sess):
    print("DO Before COMMIT", sess, invalidate_keys)
    deleted_keys.extend(invalidate_keys)
    invalidate_keys.clear()


@event.listens_for(db.session, 'before_commit')
def my_before_commit_second(_sess):
    print("DO Before COMMIT SECOND=======")


@event.listens_for(db.session, 'after_commit')
def my_after_commit(obj):
    print("DO After COMMIT", obj, deleted_keys)
    # CALL Delete in Redis
    # redis.delete_all(deleted_events)
    deleted_keys.clear()


class User(msgspec.Struct):
    user_id: int
    name: str
    age: int


u1 = User(user_id=11, name='user01', age=80)
u2 = User(user_id=12, name='user02', age=81)


class UserModel(db.Model):  # type: ignore
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(VARCHAR(255), nullable=False)
    age = Column(Integer, nullable=False)


@app.route('/users/<user_id>', methods=['GET'])
def get_user(user_id):
    total_item_counter.labels('user', 'hit').inc()
    if int(user_id) > 1000:
        total_item_counter.labels('user', 'fill').inc()
    return jsonify({'name': 'username'})


def get_users_from_db(id_list: List[int]) -> List[User]:
    tracer = trace.get_tracer('my-tracer')

    with tracer.start_span('get-from-db'):
        query = db.session.query(UserModel).filter(UserModel.id.in_(id_list))
        db_users = query.all()

    users = [User(user_id=u.id, name=u.username, age=u.age) for u in db_users]
    return users


new_user_item = new_cache_item(
    cls=User, fill_func=get_users_from_db,
    get_key=lambda u: u.id,
    default=lambda: User(user_id=0, name='', age=0),
    key_name=lambda user_id: f'u1:{user_id}',
)

NUM_KEYS = 100

json_encoder = msgspec.json.Encoder()


@app.route('/all-users', methods=['GET'])
def get_all_users():
    tracer = trace.get_tracer('my-tracer')
    user_item = new_user_item()

    with tracer.start_span('get-from-cache') as span:
        start = time.perf_counter_ns()

        id_list = list(range(1, NUM_KEYS + 1))
        fn = user_item.get_multi(id_list)

        id_list2 = list(range(1, NUM_KEYS + 1))
        fn2 = user_item.get_multi(id_list2)

        users = fn()
        users2 = fn2()

        d = (time.perf_counter_ns() - start) / 1000
        print(f'GET from Cache: {d}us')

        span.set_attribute('hit_count', user_item.hit_count)
        span.set_attribute('fill_count', user_item.fill_count)
        span.set_attribute('bytes_read', user_item.bytes_read)

    with tracer.start_span('get-cache-2'):
        user_item.get_multi([200])()

    with tracer.start_span('get-cache-3'):
        user_item.get_multi([300])()

    with tracer.start_span('get-cache-4'):
        user_item.get_multi([400])()

    with tracer.start_span('jsonify'):
        data = json_encoder.encode({
            'users': users,
            'users2': users2,
        })
    return flask.Response(response=data, content_type='application/json')


@app.route('/db-users', methods=['GET'])
def get_db_users():
    users = get_users_from_db(list(range(1, NUM_KEYS + 1)))
    users2 = get_users_from_db(list(range(1, NUM_KEYS + 1)))

    get_users_from_db([200])
    get_users_from_db([300])
    get_users_from_db([400])

    tracer = trace.get_tracer('my-tracer')
    with tracer.start_span('jsonify'):
        obj = jsonify({
            'users': users,
            'users2': users2,
        })

    return obj


@api.route('/customers')
class Customers(Resource):
    def get(self):
        tracer = trace.get_tracer('my-tracer')
        with tracer.start_as_current_span('get-users'):
            time.sleep(0.01)

        data = json_encoder.encode({
            'users': [u1, u2],
        })
        return flask.Response(response=data, content_type='application/json')


@app.route('/create-users', methods=['POST'])
def create_users():
    u = db.session.query(UserModel).filter(UserModel.id == 1001).first()
    if not u:
        u = UserModel(id=1001, username='username01', age=31)
        db.session.add(u)
        db.session.flush()

    invalidate_keys.append("EVENT1")

    tracer = trace.get_tracer('my-tracer')
    with tracer.start_span('COMMIT'):
        db.session.commit()

    db.session.commit()

    return jsonify({'code': 'success'})


if __name__ == "__main__":
    app.run(threaded=True)
