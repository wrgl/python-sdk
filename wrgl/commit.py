import attr
import typing

from wrgl.serialize import field_transformer


@attr.s(field_transformer=field_transformer)
class CommitResult(object):
    sum = attr.ib(type=str)
    table = attr.ib(type=str)


@attr.s(field_transformer=field_transformer)
class Table(object):
    sum = attr.ib(type=str)
    columns = attr.ib(type=typing.List[str])
    pk = attr.ib(type=typing.List[int])
    rows_count = attr.ib(type=int)


@attr.s(auto_attribs=True, field_transformer=field_transformer)
class Commit(object):
    sum: str
    author_name: str
    author_email: str
    message: str
    table: Table
    time: str
    parents: typing.List[str]
    parent_commits: "Commit"
