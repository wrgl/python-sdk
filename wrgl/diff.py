import attr
import typing

from wrgl.serialize import field_transformer


@attr.s(auto_attribs=True, field_transformer=field_transformer(globals()))
class RowDiff(object):
    off1: int
    off2: int


@attr.s(auto_attribs=True, field_transformer=field_transformer(globals()))
class DiffResponse(object):
    table_sum: str
    old_table_sum: str
    old_pk: typing.List[int]
    pk: typing.List[int]
    old_columns: typing.List[str]
    columns: typing.List[str]
    row_diff: typing.List[RowDiff]
