import pytest


@pytest.fixture(scope='session')
def session_object():
    print("\n=============BEGIN SESISON OBJECT")
    return {'value': 123}


@pytest.fixture
def username_test(session_object) -> str:
    return "quangtung97"


@pytest.fixture
def db_class(username_test):
    return {
        'name': username_test,
    }


@pytest.fixture
def session(username_test):
    return {
        'sess': 'new session ' + username_test,
    }
