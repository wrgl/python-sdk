import typing
from unittest import TestCase

import attr

from wrgl.serialize import json_loads, json_dumps, field_transformer


@attr.s(field_transformer=field_transformer)
class Person(object):
    name = attr.ib(type=str)
    birth_date = attr.ib(type=str)
    height = attr.ib(type=int)


@attr.s(field_transformer=field_transformer)
class Remote(object):
    url = attr.ib(type=str)


@attr.s(field_transformer=field_transformer)
class Branch(object):
    fetch = attr.ib(type=str)


@attr.s(field_transformer=field_transformer)
class Config(object):
    user = attr.ib(type=Person)
    remotes = attr.ib(type=typing.List[Remote])
    branch = attr.ib(type=typing.Dict[str, Branch])


@attr.s(field_transformer=field_transformer)
class Receive(object):
    deny_non_fast_forwards = attr.ib(type=bool)
    deny_deletes = attr.ib(type=bool)


class JSONTestCase(TestCase):
    def test_loads_simple(self):
        obj1 = Person(name='John Doe', birth_date='10/02/2000', height=170)
        json_str = json_dumps(obj1)
        self.assertEqual(
            json_str, '{"name": "John Doe", "birthDate": "10/02/2000", "height": 170}'
        )
        obj2 = json_loads(json_str, Person)
        self.assertEqual(obj1, obj2)

    def test_loads_nested(self):
        self.maxDiff = None
        obj1 = Config(
            user=Person(name='John Doe', birth_date='10/02/2000', height=170),
            remotes=[
                Remote(url='https://url1'),
                Remote(url='https://url2'),
            ],
            branch={
                'main': Branch(fetch='refs/heads/main'),
                'test': Branch(fetch='refs/heads/test')
            }
        )
        json_str = json_dumps(obj1, indent=4)
        self.assertEqual(
            json_str, '\n'.join([
                '{',
                '    "user": {',
                '        "name": "John Doe",',
                '        "birthDate": "10/02/2000",',
                '        "height": 170',
                '    },',
                '    "remotes": [',
                '        {',
                '            "url": "https://url1"',
                '        },',
                '        {',
                '            "url": "https://url2"',
                '        }',
                '    ],',
                '    "branch": {',
                '        "main": {',
                '            "fetch": "refs/heads/main"',
                '        },',
                '        "test": {',
                '            "fetch": "refs/heads/test"',
                '        }',
                '    }',
                '}',
            ])
        )
        obj2 = json_loads(json_str, Config)
        self.assertEqual(obj1, obj2)

    def test_loads_ignore_empty(self):
        obj = json_loads('{"denyNonFastForwards": true}', Receive)
        self.assertEqual(obj, Receive(deny_non_fast_forwards=True))
