# SPDX-License-Identifier: Apache-2.0
# Copyright © 2021 Wrangle Ltd

import attr
import typing

from wrgl.serialize import field_transformer


@attr.s(auto_attribs=True, field_transformer=field_transformer(globals()))
class RowDiff(object):
    """Row offsets from both tables.

    :ivar int off1: row offset from the first commit. If it is not defined, this row doesn't exist in the first commit (was removed).
    :ivar int off2: row offset from the second commit. If it is not defined, this row doesn't exist in the second commit (new addition).
    """
    off1: int
    off2: int


@attr.s(auto_attribs=True, field_transformer=field_transformer(globals()))
class DiffResult(object):
    """Diff result. Learn more at `diff endpoint`_

    :ivar str table_sum: 16-bit checksum of the first table presented as hex string
    :ivar str old_table_sum: 16-bit checksum of the second table presented as hex string
    :ivar list[int] pk: list of indices of primary key columns of the first table
    :ivar list[int] old_pk: list of indices of primary key columns of the second table
    :ivar list[str] columns: list of column names of the first table
    :ivar list[str] old_columns: list of column names of the second table
    :ivar list[RowDiff] row_diff: list of rows that changed
    """
    table_sum: str
    old_table_sum: str
    old_pk: typing.List[int]
    pk: typing.List[int]
    old_columns: typing.List[str]
    columns: typing.List[str]
    row_diff: typing.List[RowDiff]

    @property
    def primary_key(self) -> typing.List[str]:
        """Returns primary-key columns of the first commit

        :rtype: list[str]
        """
        return [self.columns[idx] for idx in self.pk]

    @property
    def old_primary_key(self) -> typing.List[str]:
        """Returns primary-key columns of the second commit

        :rtype: list[str]
        """
        return [self.old_columns[idx] for idx in self.old_pk]
