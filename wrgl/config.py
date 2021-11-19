# SPDX-License-Identifier: Apache-2.0
# Copyright © 2021 Wrangle Ltd

from wrgl.serialize import Serializable


class User(Serializable):
    fields = {
        'name': str,
        'email': str
    }


class Receive(Serializable):
    fields = {
        'deny_non_fast_forwards': bool,
        'deny_deletes': bool
    }


class Branch(Serializable):
    fields = {
        'remote': str,
        'merge': str,
    }


class Auth(Serializable):
    fields = {
        'token_duration': str
    }


class Pack(Serializable):
    fields = {
        'max_file_size': int
    }


class Remote(Serializable):
    fields = {
        'url': str,
        'fetch': [str],
        'push': [str],
        'mirror': bool
    }


class Config(Serializable):
    fields = {
        "user": User,
        "remote": {Remote},
        "receive": Receive,
        "branch": {Branch},
        "auth": Auth,
        "pack": Pack
    }
