from typing import Iterator, List
import requests
import csv
import io
from requests_toolbelt.multipart.encoder import MultipartEncoder

from wrgl.commit import Commit, CommitResult, Table
from wrgl.diff import DiffResponse
from wrgl.serialize import json_dumps, json_loads
from wrgl.compression import GzipCompressReadStream
from wrgl.config import Config


class Repository(object):
    def __init__(self, endpoint, id_token=None):
        self.endpoint = endpoint.rstrip("/")
        self._id_token = id_token

    def authenticate(self, email, password):
        if self.endpoint.startswith("https://hub.wrgl.co/"):
            endpoint = "https://hub.wrgl.co/api/authenticate/"
        else:
            endpoint = self.endpoint + "/authenticate/"
        r = requests.post(endpoint, json={
            'email': email,
            'password': password
        })
        r.raise_for_status()
        self._id_token = r.json()['idToken']

    def _headers(self, extra_headers=dict()):
        if self._id_token is None:
            raise ValueError('id_token is not set')
        return dict([
            ('Authorization', 'Bearer %s' % self._id_token)
        ] + list(extra_headers.items()))

    def _get(self, path, params=None):
        if params is not None:
            params = {k: v for k, v in params.items() if v}
        r = requests.get(
            self.endpoint+path, params=params, headers=self._headers(),
        )
        r.raise_for_status()
        return r

    def _put_json(self, path, obj):
        r = requests.put(
            self.endpoint+path,
            data=json_dumps(obj),
            headers=self._headers({
                'Content-Type': 'application/json'
            }),
        )
        r.raise_for_status()
        return r

    def _post_json(self, path, obj):
        r = requests.post(
            self.endpoint+path,
            data=json_dumps(obj),
            headers=self._headers({
                'Content-Type': 'application/json'
            }),
        )
        r.raise_for_status()
        return r

    def get_config(self) -> Config:
        r = self._get("/config/")
        return json_loads(r.content, Config)

    def put_config(self, config) -> None:
        if not isinstance(config, Config):
            raise TypeError('config argument must be instance of %s' % Config)
        self._put_json("/config/", config)

    def get_refs(self) -> dict:
        r = self._get("/refs/")
        obj = r.json()
        return obj["refs"]

    def get_branch(self, branch) -> Commit:
        r = self._get("/refs/heads/%s/" % branch)
        return json_loads(r.content, Commit)

    def commit(self, branch, message, file, primary_key) -> CommitResult:
        reader = GzipCompressReadStream(file)
        m = MultipartEncoder(
            fields={
                'branch': branch,
                'message': message,
                'primaryKey': primary_key,
                'file': ('data.csv.gz', reader, 'text/csv')}
        )
        r = requests.post(
            self.endpoint+"/commits/",
            data=m,
            headers=self._headers({'Content-Type': m.content_type}),
        )
        r.raise_for_status()
        return json_loads(r.content, CommitResult)

    def get_commit_tree(self, head, max_depth) -> Commit:
        r = self._get(
            "/commits/", params={'head': head, 'maxDepth': max_depth}
        )
        return json_loads(r.content, Commit)

    def get_commit(self, commit_sum) -> Commit:
        r = self._get("/commits/%s/" % commit_sum)
        return json_loads(r.content, Commit)

    def get_table(self, table_sum) -> Table:
        r = self._get("/tables/%s/" % table_sum)
        return json_loads(r.content, Table)

    def get_blocks(self, table_sum, start=None, end=None, with_column_names=True) -> Iterator[List[str]]:
        r = self._get(
            "/tables/%s/blocks/" % table_sum,
            params={
                'start': start,
                'end': end,
                'columns': 'true' if with_column_names else 'false'
            }
        )
        for row in csv.reader(io.BytesIO(r.content), dialect='unix'):
            yield row

    def get_rows(self, table_sum, offsets) -> Iterator[List[str]]:
        r = self._get(
            "/tables/%s/rows/" % table_sum,
            params={
                'offsets': ','.join([str(v) for v in offsets])
            }
        )
        for row in csv.reader(io.BytesIO(r.content), dialect='unix'):
            yield row

    def diff(self, sum1, sum2) -> DiffResponse:
        r = self._get(
            "/diff/%s/%s/" % (sum1, sum2)
        )
        return json_loads(r.content, DiffResponse)
