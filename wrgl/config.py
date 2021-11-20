# SPDX-License-Identifier: Apache-2.0
# Copyright © 2021 Wrangle Ltd

import typing
import attr

from wrgl.serialize import field_transformer


@attr.s(field_transformer=field_transformer(globals()))
class User(object):
    name = attr.ib(type=str)
    email = attr.ib(type=str)


@attr.s(field_transformer=field_transformer(globals()))
class Receive(object):
    deny_non_fast_forwards = attr.ib(type=bool)
    deny_deletes = attr.ib(type=bool)


@attr.s(field_transformer=field_transformer(globals()))
class Branch(object):
    remote = attr.ib(type=str)
    merge = attr.ib(type=str)


@attr.s(field_transformer=field_transformer(globals()))
class Auth(object):
    token_duration = attr.ib(type=str)


@attr.s(field_transformer=field_transformer(globals()))
class Pack(object):
    max_file_size = attr.ib(type=int)


@attr.s(field_transformer=field_transformer(globals()))
class Remote(object):
    url = attr.ib(type=str)
    fetch = attr.ib(type=typing.List[str])
    push = attr.ib(type=typing.List[str])
    mirror = attr.ib(type=bool)


@attr.s(field_transformer=field_transformer(globals()))
class Config(object):
    user = attr.ib(type=User)
    remote = attr.ib(type=typing.Dict[str, Remote])
    receive = attr.ib(type=Receive)
    branch = attr.ib(type=typing.Dict[str, Branch])
    auth = attr.ib(type=Auth)
    pack = attr.ib(type=Pack)
