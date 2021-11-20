# SPDX-License-Identifier: Apache-2.0
# Copyright © 2021 Wrangle Ltd

import typing
import attr

from wrgl.serialize import field_transformer


@attr.s(auto_attribs=True, field_transformer=field_transformer(globals()))
class User(object):
    name: str
    email: str


@attr.s(auto_attribs=True, field_transformer=field_transformer(globals()))
class Receive(object):
    deny_non_fast_forwards: bool
    deny_deletes: bool


@attr.s(auto_attribs=True, field_transformer=field_transformer(globals()))
class Branch(object):
    remote: str
    merge: str


@attr.s(auto_attribs=True, field_transformer=field_transformer(globals()))
class Auth(object):
    token_duration: str


@attr.s(auto_attribs=True, field_transformer=field_transformer(globals()))
class Pack(object):
    max_file_size: int


@attr.s(auto_attribs=True, field_transformer=field_transformer(globals()))
class Remote(object):
    url: str
    fetch: typing.List[str]
    push: typing.List[str]
    mirror: bool


@attr.s(auto_attribs=True, field_transformer=field_transformer(globals()))
class Config(object):
    user: User
    remote: typing.Dict[str, Remote]
    receive: Receive
    branch: typing.Dict[str, Branch]
    auth: Auth
    pack: Pack
