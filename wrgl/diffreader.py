import typing
import itertools

from wrgl import repository
from wrgl.commit import Table
from wrgl.diff import DiffResult
from wrgl.coldiff import ColDiff


RowArranger = typing.Callable[
    [typing.List[str]], typing.List[str]
]


class RowReader(object):
    _repo: repository.Repository
    _tbl_sum: str
    _offsets: typing.List
    _off: int
    _rearrange_row: RowArranger
    _fetch_size: int

    columns: typing.List[str]

    def __init__(
            self,
            repo: repository.Repository,
            tbl_sum: str,
            columns: typing.List[str],
            rearrange_row: RowArranger,
            fetch_size: int = 100
    ) -> None:
        self._repo = repo
        self._tbl_sum = tbl_sum
        self._offsets = []
        self._off = 0
        self.columns = columns
        self._rearrange_row = rearrange_row
        self._fetch_size = fetch_size

    def add_offset(self, offset: int) -> None:
        self._offsets.append(offset)

    def __len__(self):
        return len(self._offsets)

    def data(self) -> typing.Iterator[typing.List[str]]:
        while self._off < len(self._offsets):
            for row in self._repo.get_rows(
                    self._tbl_sum,
                    self._offsets[self._off:self._off + self._fetch_size]
            ):
                yield self._rearrange_row(row)
            self._off += self._fetch_size


class ModifiedRowReader(object):
    _repo: repository.Repository
    _tbl_sum1: str
    _tbl_sum2: str
    _cd: ColDiff
    _fetch_size: int
    _offsets: typing.List[typing.Tuple[int, int]]
    _off: int

    columns: typing.List[str]

    def __init__(
            self,
            repo: repository.Repository,
            tbl_sum1: str,
            tbl_sum2: str,
            columns: typing.List[str],
            cd: ColDiff,
            fetch_size: int = 100
    ) -> None:
        self._repo = repo
        self._tbl_sum1 = tbl_sum1
        self._tbl_sum2 = tbl_sum2
        self._cd = cd
        self._fetch_size = fetch_size
        self._offsets = []
        self._off = 0
        self.columns = columns

    def add_offset(self, offset1: int, offset2: int) -> None:
        self._offsets.append((offset1, offset2))

    def __len__(self):
        return len(self._offsets)

    def data(self) -> typing.Iterator[typing.List[str]]:
        while self._off < len(self._offsets):
            offsets = self._offsets[self._off:self._off + self._fetch_size]
            rows1 = self._repo.get_rows(
                self._tbl_sum1, [i for i, _ in offsets]
            )
            rows2 = self._repo.get_rows(
                self._tbl_sum2, [i for _, i in offsets]
            )
            for row1, row2 in itertools.zip_longest(rows1, rows2):
                yield self._cd.combine_rows(0, row1, row2)
            self._off += self._fetch_size


class ColumnChanges(object):
    new_values: typing.List[str]
    old_values: typing.List[str]
    unchanged: typing.List[str]
    added: typing.List[str]
    removed: typing.List[str]

    def __init__(self, new_cols: typing.List[str], old_cols: typing.List[str]) -> None:
        self.new_values = new_cols
        self.old_values = old_cols
        old_set = set(new_cols)
        new_set = set(old_cols)
        self.unchanged = list(old_set & new_set)
        self.added = list(new_set - old_set)
        self.removed = list(old_set - new_set)


class DiffReader(object):
    _repo: repository.Repository
    _com_sum1: str
    _com_sum2: str
    _dr: DiffResult
    _cd: ColDiff

    column_changes: ColumnChanges
    pk_changes: ColumnChanges
    columns: typing.List[str]
    added_rows: RowReader or None = None
    removed_rows: RowReader or None = None
    modified_rows: ModifiedRowReader or None = None

    def __init__(self, repo: repository.Repository, com_sum1: str, com_sum2: str) -> None:
        self._repo = repo
        self._com_sum1 = com_sum1
        self._com_sum2 = com_sum2
        self._dr = self._repo.diff(com_sum1, com_sum2)
        old_tbl = Table(columns=self._dr.old_columns, pk=self._dr.old_pk)
        new_tbl = Table(columns=self._dr.columns, pk=self._dr.pk)
        self._cd = ColDiff(old_tbl, new_tbl)
        self.column_changes = ColumnChanges(
            self._dr.columns, self._dr.old_columns)
        self.pk_changes = ColumnChanges(
            new_tbl.primary_key, old_tbl.primary_key)
        self.columns = [
            col.name for col in self._cd.columns
        ]
        if old_tbl.primary_key == new_tbl.primary_key:
            self.added_rows = RowReader(
                repo=self._repo,
                tbl_sum=self._dr.table_sum,
                columns=self.columns,
                rearrange_row=lambda row: self._cd.rearrange_row(0, row)
            )
            self.removed_rows = RowReader(
                repo=self._repo,
                tbl_sum=self._dr.old_table_sum,
                columns=self.columns,
                rearrange_row=lambda row: self._cd.rearrange_base_row(row)
            )
            self.modified_rows = ModifiedRowReader(
                repo=self._repo,
                tbl_sum1=self._dr.table_sum,
                tbl_sum2=self._dr.old_table_sum,
                columns=self.columns,
                cd=self._cd,
            )
            for rd in self._dr.row_diff:
                if rd.off1 is None:
                    self.removed_rows.add_offset(rd.off2)
                elif rd.off2 is None:
                    self.added_rows.add_offset(rd.off1)
                else:
                    self.modified_rows.add_offset(rd.off1, rd.off2)
