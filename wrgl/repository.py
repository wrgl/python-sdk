# SPDX-License-Identifier: Apache-2.0
# Copyright © 2022 Wrangle Ltd

from typing import Iterator, List
import tempfile
import gzip
import shutil
import typing
import csv
import io
from requests_toolbelt.multipart.encoder import MultipartEncoder

from wrgl import diffreader
from wrgl.commit import Commit, CommitResult, Table, CommitTree
from wrgl.diff import DiffResult
from wrgl.serialize import json_loads
from wrgl.uma import UMAClient


class Repository(object):
    """Represents the HTTP API that wraps a hosted Wrgl repository"""

    def __init__(
        self, repo_uri: str, client_id: str, client_secret: str = None
    ) -> None:
        """
        :param str repo_uri: the URI of the repository
        :param str client_id: Keycloak client id
        :param str client_secret: Keycloak client secret
        """
        self._client = UMAClient(repo_uri, client_id, client_secret)

    @property
    def rpt(self) -> str:
        return self._client.rpt

    def get_refs(self) -> dict:
        """Get references as a mapping of reference name and commit checksum

        :rtype: dict
        """
        r = self._client.get("/refs/")
        obj = r.json()
        return obj["refs"]

    def get_branch(self, branch: str) -> Commit:
        """Get the head commit of a branch

        :param str branch: the name of the branch

        :rtype: Commit
        """
        r = self._client.get("/refs/heads/%s/" % branch)
        return json_loads(r.content, Commit)

    def commit(
        self,
        branch: str,
        message: str,
        file: typing.BinaryIO,
        primary_key: typing.List[str],
    ) -> CommitResult:
        """Creates a new commit

        :param str branch: name of the branch to commit under
        :param str message: commit message
        :param typing.BinaryIO file: the CSV file to commit
        :param list[str] primary_key: list of column names that make up the primary key

        :rtype: CommitResult
        """
        with tempfile.TemporaryFile() as fp:
            with gzip.open(fp, "w") as gzf:
                shutil.copyfileobj(file, gzf)

            def create_request_args():
                fp.seek(0)
                m = MultipartEncoder(
                    fields={
                        "branch": branch,
                        "message": message,
                        "primaryKey": ",".join(primary_key),
                        "file": ("data.csv.gz", fp, "text/csv"),
                    }
                )
                return {
                    "data": m,
                    "headers": {"Content-Type": m.content_type},
                }

            r = self._client.post(
                "/commits/",
                create_request_args=create_request_args,
            )
        return json_loads(r.content, CommitResult)

    def get_commit_tree(self, head: str, max_depth: int) -> CommitTree:
        """Gets commit tree

        :param str head: name of the root commit, could either be reference name or commit checksum.
        :param int max_depth: maximum depth of commit tree to fetch

        :rtype: CommitTree
        """
        r = self._client.get("/commits/", params={"head": head, "maxDepth": max_depth})
        return json_loads(r.content, CommitTree)

    def get_commit(self, commit_sum: str) -> Commit:
        """Get commit with the given checksum

        :param str commit_sum: commit checksum

        :rtype: Commit
        """
        r = self._client.get("/commits/%s/" % commit_sum)
        return json_loads(r.content, Commit)

    def get_table(self, table_sum: str) -> Table:
        """Get table with the given checksum

        :param str table_sum: table checksum

        :rtype: Table
        """
        r = self._client.get("/tables/%s/" % table_sum)
        return json_loads(r.content, Table)

    def get_blocks(
        self,
        commit: str,
        start: int = None,
        end: int = None,
        with_column_names: bool = True,
    ) -> Iterator[List[str]]:
        """Fetchs blocks as concatenated rows. Each row as a list of strings.

        Calling this with default `start`, `end`, and `with_column_names` will return the entire table.

        :param str commit: either commit checksum or reference e.g. "heads/main"
        :param int start: index of the first block to fetch. Defaults to 0.
        :param int end: index of the last block to fetch. If not set, fetch til the end.
        :param bool with_column_names: prepend column names to the resulting CSV, which in effect producing a CSV with header.

        :rtype: typing.Iterator[list[str]]
        """
        r = self._client.get(
            "/blocks/",
            params={
                "head": commit,
                "start": start,
                "end": end,
                "columns": "true" if with_column_names else "false",
            },
        )
        for row in csv.reader(io.StringIO(r.text), dialect="unix"):
            yield row

    def get_table_blocks(
        self,
        table_sum: str,
        start: int = None,
        end: int = None,
        with_column_names: bool = True,
    ) -> Iterator[List[str]]:
        """Fetchs blocks with table checksum.

        Calling this with default `start`, `end`, and `with_column_names` will return the entire table.

        :param str table_sum: table checksum
        :param int start: index of the first block to fetch. Defaults to 0.
        :param int end: index of the last block to fetch. If not set, fetch til the end.
        :param bool with_column_names: prepend column names to the resulting CSV, which in effect producing a CSV with header.

        :rtype: typing.Iterator[list[str]]
        """
        r = self._client.get(
            "/tables/%s/blocks/" % table_sum,
            params={
                "start": start,
                "end": end,
                "columns": "true" if with_column_names else "false",
            },
        )
        for row in csv.reader(io.StringIO(r.text), dialect="unix"):
            yield row

    def get_rows(self, commit: str, offsets: List[int]) -> Iterator[List[str]]:
        """Get rows at certain offsets. Each row will be returned as a list of strings.

        This is usually used in tandem with row offsets from :class:`DiffResult` to fetch changed rows.

        :param str commit: either commit checksum or reference e.g. "heads/main"
        :param list[int] offsets: the offsets of the rows to fetch

        :rtype: typing.Iterator[list[str]]
        """
        r = self._client.get(
            "/rows/",
            params={"head": commit, "offsets": ",".join([str(v) for v in offsets])},
        )
        for row in csv.reader(io.StringIO(r.text), dialect="unix"):
            yield row

    def get_table_rows(self, table_sum: str, offsets: List[int]) -> Iterator[List[str]]:
        """Get rows at certain offsets with table checksum.

        This is usually used in tandem with row offsets from :class:`DiffResult` to fetch changed rows.

        :param str table_sum: table checksum
        :param list[int] offsets: the offsets of the rows to fetch

        :rtype: typing.Iterator[list[str]]
        """
        r = self._client.get(
            "/tables/%s/rows/" % table_sum,
            params={"offsets": ",".join([str(v) for v in offsets])},
        )
        for row in csv.reader(io.StringIO(r.text), dialect="unix"):
            yield row

    def diff(self, sum1: str, sum2: str) -> DiffResult:
        """Compares two commits and returns their differences.

        :param str sum1: checksum of the first commit
        :param str sum2: checksum of the second commit

        :rtype: DiffResult
        """
        r = self._client.get("/diff/%s/%s/" % (sum1, sum2))
        return json_loads(r.content, DiffResult)

    def diff_reader(
        self, sum1: str, sum2: str, fetch_size: int = 100
    ) -> diffreader.DiffReader:
        """Compares two commits and interpret their differences.

        This method is higher level than :func:`Repository.diff` and should
        be preferred for 99% of use cases.

        :param str sum1: checksum of the first commit
        :param str sum2: checksum of the second commit

        :rtype: DiffReader
        """
        return diffreader.DiffReader(self, sum1, sum2, fetch_size)
