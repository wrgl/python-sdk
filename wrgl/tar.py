import os
import tarfile
from typing import IO

def is_within_directory(directory, target):

    abs_directory = os.path.abspath(directory)
    abs_target = os.path.abspath(target)

    prefix = os.path.commonprefix([abs_directory, abs_target])

    return prefix == abs_directory

def safe_extractall(fileobj: IO[bytes], path=".", members=None, *, numeric_owner=False):
    with tarfile.open(mode='r:gz', fileobj=fileobj) as tar:
        for member in tar.getmembers():
            member_path = os.path.join(path, member.name)
            if not is_within_directory(path, member_path):
                raise Exception("Attempted Path Traversal in Tar File")

        tar.extractall(path, members, numeric_owner=numeric_owner) 