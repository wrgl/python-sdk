import attr
import typing

from wrgl.serialize import field_transformer


@attr.s(field_transformer=field_transformer(globals()))
class RowDiff(object):
    off1 = attr.ib(type=int)
    off2 = attr.ib(type=int)


@attr.s(field_transformer=field_transformer(globals()))
class DiffResponse(object):
    table_sum = attr.ib(type=str)
    old_table_sum = attr.ib(type=str)
    old_pk = attr.ib(type=typing.List[int])
    pk = attr.ib(type=typing.List[int])
    old_columns = attr.ib(type=typing.List[str])
    columns = attr.ib(type=typing.List[str])
    row_diff = attr.ib(type=typing.List[RowDiff])
