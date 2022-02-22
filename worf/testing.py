from functools import partialmethod

from django.core.files import File
from django.test.client import MULTIPART_CONTENT, Client

JSON_CONTENT = "application/json"


class ApiClient(Client):
    def generic(self, method, path, data=None, content_type=None, **kwargs):
        content_type = content_type or guess_content_type(data)
        data = self._encode_multipart(data, content_type)
        return super().generic(method, path, data, content_type, **kwargs)

    delete = partialmethod(generic, "DELETE")
    patch = partialmethod(generic, "PATCH")
    post = partialmethod(generic, "POST")
    put = partialmethod(generic, "PUT")

    def _encode_multipart(self, data, content_type):
        post_data = self._encode_json({} if data is None else data, content_type)
        return self._encode_data(post_data, content_type)


def guess_content_type(data):
    return MULTIPART_CONTENT if should_multipart(data) else JSON_CONTENT


def has_files(data):
    return any(isinstance(value, File) for value in data.values())


def should_multipart(data):
    return isinstance(data, dict) and has_files(data)
