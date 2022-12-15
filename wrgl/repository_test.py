# SPDX-License-Identifier: Apache-2.0
# Copyright © 2022 Wrangle Ltd

from datetime import datetime
import typing
import platform
import _csv
from unittest import TestCase
from contextlib import contextmanager
import io
import tempfile
import pathlib
import socket
import re
import time
import os
import subprocess
import csv

from wrgl.diffreader import ColumnChanges
from wrgl.repository import Repository
from wrgl import tar
from wrgl.vcr_test import use_vcr


def get_open_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("", 0))
    s.listen(1)
    port = s.getsockname()[1]
    s.close()
    return str(port)


class RepositoryTestCase(TestCase):
    maxDiff = None
    repo_uri = "http://localhost:8081"
    client_id = "wrgl-python-sdk"
    client_secret = "my-secret"

    def setUp(self):
        super().setUp()
        self.repo = Repository(self.repo_uri, self.client_id, self.client_secret)

    @contextmanager
    def commit(
        self, branch: str, message: str, primary_key: typing.List[str]
    ) -> typing.Iterator["_csv._writer"]:
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            writer = csv.writer(f)
            yield writer
        try:
            with open(f.name, "rb") as f2:
                self.repo.commit(branch, message, f2, primary_key)
        finally:
            os.remove(f.name)

    @use_vcr
    def test_commit(self):
        with self.commit("test_commit", "initial commit", ["a"]) as writer:
            writer.writerow(["a", "b", "c"])
            writer.writerow(["1", "q", "w"])
            writer.writerow(["2", "a", "s"])

        refs = self.repo.get_refs()
        self.assertEqual(len(refs), 1)
        commit1 = self.repo.get_commit(refs["heads/test_commit"])
        self.assertIsInstance(commit1.time, datetime)
        commit2 = self.repo.get_branch("test_commit")
        self.assertEqual(commit1, commit2)

        b = io.StringIO()
        writer = csv.writer(b)
        writer.writerow(["a", "b", "c"])
        writer.writerow(["1", "e", "w"])
        writer.writerow(["2", "c", "s"])
        cr = self.repo.commit(
            branch="test_commit",
            message="second commit",
            file=io.BytesIO(b.getvalue().encode("utf8")),
            primary_key=["a"],
        )
        self.assertIsNotNone(cr.sum)
        self.assertIsNotNone(cr.table)

        com_tree = self.repo.get_commit_tree(cr.sum, 2)
        self.assertEqual(com_tree.sum, cr.sum)
        self.assertIn(commit1.sum, com_tree.root.parents)
        self.assertIn(commit1.sum, com_tree.root.parent_commits)
        self.assertIsNotNone(com_tree.root.parent_commits[commit1.sum].table)

        tbl = self.repo.get_table(cr.table)
        self.assertEqual(tbl.columns, ["a", "b", "c"])
        self.assertEqual(
            list(self.repo.get_blocks(cr.sum)),
            [["a", "b", "c"], ["1", "e", "w"], ["2", "c", "s"]],
        )
        self.assertEqual(
            list(self.repo.get_table_blocks(cr.table)),
            [["a", "b", "c"], ["1", "e", "w"], ["2", "c", "s"]],
        )
        self.assertEqual(list(self.repo.get_rows(cr.sum, [0])), [["1", "e", "w"]])
        self.assertEqual(
            list(self.repo.get_table_rows(cr.table, [0])), [["1", "e", "w"]]
        )
        dr = self.repo.diff(cr.sum, commit1.sum)
        self.assertTrue(dr.primary_key == dr.old_primary_key)
        self.assertGreater(len(dr.row_diff), 0)

    @use_vcr
    def test_diff_reader(self):
        with self.commit("test_diff_reader", "initial commit", ["a"]) as writer:
            writer.writerow(["a", "b", "c", "d"])
            writer.writerow(["1", "q", "w", "e"])
            writer.writerow(["2", "a", "s", "d"])
            writer.writerow(["3", "z", "x", "c"])

        with self.commit("test_diff_reader", "second commit", ["a"]) as writer:
            writer.writerow(["a", "b", "c", "e"])
            writer.writerow(["1", "q", "u", "r"])
            writer.writerow(["2", "a", "s", "f"])
            writer.writerow(["4", "y", "u", "i"])

        com_tree = self.repo.get_commit_tree("heads/test_diff_reader", 2)
        dr = self.repo.diff_reader(com_tree.sum, com_tree.root.parents[0])
        self.assertEqual(
            dr.column_changes,
            ColumnChanges(
                new_values=["a", "b", "c", "e"],
                old_values=["a", "b", "c", "d"],
                unchanged=set(["a", "b", "c"]),
                added=set(["e"]),
                removed=set(["d"]),
            ),
        )
        self.assertEqual(
            dr.pk_changes,
            ColumnChanges(
                new_values=["a"],
                old_values=["a"],
                unchanged=set(["a"]),
                added=set([]),
                removed=set([]),
            ),
        )
        self.assertEqual(len(dr.added_rows), 1)
        self.assertEqual(dr.added_rows.columns, ["a", "b", "c", "e"])
        self.assertEqual(dr.added_rows.primary_key, ["a"])
        self.assertEqual(list(dr.added_rows), [["4", "y", "u", "i"]])
        self.assertEqual(len(dr.removed_rows), 1)
        self.assertEqual(dr.removed_rows.columns, ["a", "b", "c", "d"])
        self.assertEqual(dr.removed_rows.primary_key, ["a"])
        self.assertEqual(list(dr.removed_rows), [["3", "z", "x", "c"]])
        self.assertEqual(len(dr.modified_rows), 2)
        self.assertEqual(dr.modified_rows.columns, ["a", "b", "c", "d", "e"])
        self.assertEqual(dr.modified_rows.primary_key, ["a"])
        self.assertEqual(
            list(dr.modified_rows),
            [
                [("1", "1"), ("q", "q"), ("u", "w"), (None, "e"), ("r", None)],
                [("2", "2"), ("a", "a"), ("s", "s"), (None, "d"), ("f", None)],
            ],
        )
        self.assertIsNotNone(dr.data_profile)
        self.assertEqual(dr.data_profile.old_rows_count, 3)
        self.assertEqual(dr.data_profile.new_rows_count, 3)
        self.assertEqual(len(dr.data_profile.columns), 5)

    @use_vcr
    def test_diff_reader_no_changes(self):
        with self.commit(
            "test_diff_reader_no_changes", "initial commit", ["a"]
        ) as writer:
            writer.writerow(["a", "b", "c", "d"])
            writer.writerow(["1", "q", "w", "e"])
            writer.writerow(["2", "a", "s", "d"])
            writer.writerow(["3", "z", "x", "c"])

        with self.commit(
            "test_diff_reader_no_changes", "second commit", ["a"]
        ) as writer:
            writer.writerow(["a", "b", "c", "d"])
            writer.writerow(["1", "q", "w", "e"])
            writer.writerow(["2", "a", "s", "d"])
            writer.writerow(["3", "z", "x", "c"])

        com_tree = self.repo.get_commit_tree("heads/test_diff_reader_no_changes", 2)
        dr = self.repo.diff_reader(com_tree.sum, com_tree.root.parents[0])
        self.assertEqual(
            dr.column_changes,
            ColumnChanges(
                new_values=["a", "b", "c", "d"],
                old_values=["a", "b", "c", "d"],
                unchanged=set(["a", "b", "c", "d"]),
                added=set([]),
                removed=set([]),
            ),
        )
        self.assertEqual(
            dr.pk_changes,
            ColumnChanges(
                new_values=["a"],
                old_values=["a"],
                unchanged=set(["a"]),
                added=set([]),
                removed=set([]),
            ),
        )
        self.assertIsNone(dr.added_rows)
        self.assertIsNone(dr.removed_rows)
        self.assertIsNone(dr.modified_rows)
