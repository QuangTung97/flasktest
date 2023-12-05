import json
import unittest
from dataclasses import dataclass, field
from typing import List

from marshmallow import Schema, fields


@dataclass
class Role:
    code: str


@dataclass
class Person:
    name: str
    age: int
    roles: List[Role] = field(default_factory=lambda: [])


def _serialize_roles(p: Person) -> List[dict]:
    return [r.__dict__ for r in p.roles]


class PersonSchema(Schema):
    name = fields.String()
    age = fields.Integer()
    roles = fields.Function(_serialize_roles)


class TestMarshal(unittest.TestCase):
    def test_normal(self) -> None:
        p = Person(name='user 01', age=71, roles=[
            Role(code='ROLE01'),
            Role(code='ROLE02'),
        ])
        schema = PersonSchema()
        self.assertDictEqual({
            'name': 'user 01', 'age': 71,
            'roles': [
                {'code': 'ROLE01'},
                {'code': 'ROLE02'},
            ]
        }, schema.dump(p))
