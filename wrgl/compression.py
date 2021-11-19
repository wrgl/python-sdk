from gzip import GzipFile
from collections import deque


CHUNK = 16 * 1024


class Buffer (object):
    def __init__(self):
        self.__buf = deque()
        self.__size = 0

    def __len__(self):
        return self.__size

    def write(self, data):
        self.__buf.append(data)
        self.__size += len(data)

    def read(self, size=-1):
        if size < 0:
            size = self.__size
        ret_list = []
        while size > 0 and len(self.__buf):
            s = self.__buf.popleft()
            size -= len(s)
            ret_list.append(s)
        if size < 0:
            ret_list[-1], remainder = ret_list[-1][:size], ret_list[-1][size:]
            self.__buf.appendleft(remainder)
        ret = ''.join(ret_list)
        self.__size -= len(ret)
        return ret

    def flush(self):
        pass

    def close(self):
        pass


class GzipCompressReadStream (object):
    """Streaming gzipped reader

    credits to https://stackoverflow.com/a/31566082/390370
    """

    def __init__(self, fileobj):
        self.__input = fileobj
        self.__buf = Buffer()
        self.__gzip = GzipFile(None, mode='wb', fileobj=self.__buf)

    def read(self, size=-1):
        while size < 0 or len(self.__buf) < size:
            s = self.__input.read(CHUNK)
            if not s:
                self.__gzip.close()
                break
            self.__gzip.write(s)
        return self.__buf.read(size)
