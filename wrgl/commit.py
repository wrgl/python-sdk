import attr
import typing

from wrgl.serialize import field_transformer


@attr.s(auto_attribs=True, field_transformer=field_transformer(globals()))
class CommitResult(object):
    sum: str
    table: str


@attr.s(auto_attribs=True, field_transformer=field_transformer(globals()))
class Table(object):
    sum: str
    columns: typing.List[str]
    pk: typing.List[int]
    rows_count: int


@attr.s(auto_attribs=True, field_transformer=field_transformer(globals()))
class Commit(object):
    sum: str
    author_name: str
    author_email: str
    message: str
    table: Table
    time: str
    parents: typing.List[str]
    parent_commits: "typing.Dict[str, Commit]"


@attr.s(auto_attribs=True, field_transformer=field_transformer(globals()))
class CommitTree(object):
    sum: str
    root: Commit
