# SPDX-License-Identifier: Apache-2.0
# Copyright © 2021 Wrangle Ltd

from datetime import datetime
from unittest import TestCase
import io
import tempfile
import pathlib
import tarfile
import socket
import re
import time
import os
import subprocess
import csv

import requests

from wrgl.config import Config, Receive
from wrgl.repository import Repository

OS = 'darwin'


def read_version():
    pat = re.compile(r'^version = (\d+\.\d+\.\d+)')
    with open(pathlib.Path(__file__).parent.parent / 'setup.cfg', 'r') as f:
        for line in f:
            m = pat.match(line)
            if m is not None:
                return m.group(1)
    raise ValueError('cannot read version from file setup.cfg')


def download_wrgl(version):
    ver_dir = pathlib.Path(__file__).parent / '__testcache__' / version
    if not ver_dir.exists():
        ver_dir.mkdir(parents=True)
        url = "https://github.com/wrgl/wrgl/releases/download/v%s/wrgl-%s-amd64.tar.gz" % (
            version, OS
        )
        with requests.get(url, stream=True) as r:
            with tarfile.open(mode='r:gz', fileobj=r.raw) as tar:
                tar.extractall(ver_dir)
    return ver_dir / ('wrgl-%s-amd64' % OS) / 'bin'


def get_open_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("", 0))
    s.listen(1)
    port = s.getsockname()[1]
    s.close()
    return str(port)


class RepositoryTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.version = read_version()
        cls.bin_dir = download_wrgl(cls.version)

    def wrgl(self, *args):
        try:
            result = subprocess.run(
                [self.bin_dir / 'wrgl']+list(args), check=True)
        except subprocess.CalledProcessError as e:
            print(e.stdout)
            print(e.stderr)
            raise
        return result

    def start_wrgld(self, *args):
        proc = subprocess.Popen(
            [self.bin_dir / 'wrgld']+list(args), stdout=subprocess.PIPE)
        time.sleep(1)
        return proc

    def test_commit(self):
        with tempfile.TemporaryDirectory() as repo_dir:
            self.wrgl("init", "--wrgl-dir", repo_dir)
            with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
                writer = csv.writer(f)
                writer.writerow(['a', 'b', 'c'])
                writer.writerow(['1', 'q', 'w'])
                writer.writerow(['2', 'a', 's'])
            self.wrgl(
                "commit", "--wrgl-dir", repo_dir, "main", f.name, "initial commit", "-p", "a"
            )
            email = "johndoe@domain.com"
            name = "John Doe"
            password = "password"
            self.wrgl(
                "config", "--wrgl-dir", repo_dir, "set", "receive.denyNonFastForwards", "true"
            )
            self.wrgl(
                "auth", "--wrgl-dir", repo_dir, "add-user", email, "--name", name, "--password", password
            )
            self.wrgl(
                "auth", "--wrgl-dir", repo_dir, "add-scope", email, "--all"
            )
            port = get_open_port()
            wrgld = self.start_wrgld(repo_dir, "-p", port)

            repo = Repository("http://localhost:%s" % port)
            repo.authenticate(email, password)
            cfg = repo.get_config()
            self.assertEqual(cfg, Config(
                receive=Receive(deny_non_fast_forwards=True)
            ))
            cfg.receive.deny_deletes = True
            repo.put_config(cfg)
            cfg = repo.get_config()
            self.assertEqual(cfg, Config(
                receive=Receive(deny_non_fast_forwards=True, deny_deletes=True)
            ))

            refs = repo.get_refs()
            self.assertEqual(len(refs), 1)
            commit1 = repo.get_commit(refs['heads/main'])
            self.assertIsInstance(commit1.time, datetime)
            commit2 = repo.get_branch('main')
            print(commit2)
            self.assertEqual(commit1, commit2)

            b = io.StringIO()
            writer = csv.writer(b)
            writer.writerow(['a', 'b', 'c'])
            writer.writerow(['1', 'e', 'w'])
            writer.writerow(['2', 'c', 's'])
            cr = repo.commit(
                branch='main',
                message='second commit',
                file=io.BytesIO(b.getvalue().encode('utf8')),
                primary_key=['a']
            )
            print(cr.sum)
            self.assertIsNotNone(cr.sum)
            self.assertIsNotNone(cr.table)

            com_tree = repo.get_commit_tree(cr.sum, 2)
            self.assertIsNotNone(
                com_tree.root.parent_commits[commit1.sum].table
            )

            tbl = repo.get_table(cr.table)
            self.assertEqual(tbl.columns, ['a', 'b', 'c'])
            self.assertEqual(list(repo.get_blocks(cr.table)), [
                ['a', 'b', 'c'], ['1', 'e', 'w'], ['2', 'c', 's']
            ])
            self.assertEqual(list(repo.get_rows(cr.table, [0])), [
                ['1', 'e', 'w']
            ])
            dr = repo.diff(cr.sum, commit1.sum)
            self.assertTrue(dr.primary_key == dr.old_primary_key)
            self.assertGreater(len(dr.row_diff), 0)

            wrgld.terminate()
            os.remove(f.name)
