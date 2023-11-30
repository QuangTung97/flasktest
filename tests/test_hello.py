import unittest
from typing import Dict

import pytest


class DBTestCase(unittest.TestCase):
    @pytest.fixture(autouse=True)
    def _prepare(self, db_class):
        print("\nDB TEST CASE AUTOUSE")
        self.db = db_class


class SessTestCase:
    @pytest.fixture(autouse=True)
    def _prepare_sess(self, session):
        self.sess = session


class TestHello(DBTestCase, SessTestCase):
    db: Dict

    def test_hello(self) -> None:
        self.assertEqual({'name': 'quangtung97'}, self.db)
        self.assertEqual(2, 2)
        self.assertEqual({'sess': 'new session quangtung97'}, self.sess)

    def test_hello_2(self) -> None:
        self.assertEqual({'name': 'quangtung97'}, self.db)
        self.assertEqual(2, 2)

    def test_hello_3(self) -> None:
        self.assertEqual({'name': 'quangtung97'}, self.db)
        self.assertEqual(2, 2)
        self.assertEqual({'sess': 'new session quangtung97'}, self.sess)


class TestSetup(unittest.TestCase):
    def test_setup(self) -> None:
        self.assertEqual(1, 1)
