import tempfile
import io
import os
import tarfile
from typing import IO

import requests

def is_within_directory(directory, target):

    abs_directory = os.path.abspath(directory)
    abs_target = os.path.abspath(target)

    prefix = os.path.commonprefix([abs_directory, abs_target])

    return prefix == abs_directory

def safe_download_extractall(url:str, path=".", members=None, *, numeric_owner=False):
    with tempfile.TemporaryFile() as f:
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            for chunk in r.iter_content(chunk_size=4096): 
                f.write(chunk)
        f.seek(0)
        with tarfile.open(mode='r:gz', fileobj=f) as tar:
            for member in tar.getmembers():
                member_path = os.path.join(path, member.name)
                if not is_within_directory(path, member_path):
                    raise Exception("Attempted Path Traversal in Tar File")

            tar.extractall(path, members, numeric_owner=numeric_owner) 