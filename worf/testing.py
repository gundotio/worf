from functools import partialmethod

from django.core.files import File
from django.test.client import Client, MULTIPART_CONTENT

JSON_CONTENT = "application/json"


class ApiClient(Client):
    def generic_multipart(self, method, path, data=None, content_type=None, **kwargs):
        content_type = content_type or self._guess_content_type(data)
        data = self._encode_multipart(data, content_type)
        return self.generic(method, path, data, content_type, **kwargs)

    patch = partialmethod(generic_multipart, "PATCH")
    post = partialmethod(generic_multipart, "POST")
    put = partialmethod(generic_multipart, "PUT")

    def _contains_files(self, data):
        return any(isinstance(value, File) for value in data.values())

    def _encode_multipart(self, data, content_type):
        post_data = self._encode_json({} if data is None else data, content_type)
        return self._encode_data(post_data, content_type)

    def _guess_content_type(self, data):
        return (
            MULTIPART_CONTENT
            if isinstance(data, dict) and self._contains_files(data)
            else JSON_CONTENT
        )
