from functools import partialmethod

from django.test.client import Client

JSON_CONTENT = "application/json"


class ApiClient(Client):
    delete = partialmethod(Client.delete, content_type=JSON_CONTENT)

    def post(self, path, data=None, content_type=JSON_CONTENT, secure=False, **kwargs):
        data = self._encode_multipart(data, content_type)
        return self.generic("POST", path, data, content_type, secure=secure, **kwargs)

    def put(self, path, data=None, content_type=JSON_CONTENT, secure=False, **kwargs):
        data = self._encode_multipart(data, content_type)
        return self.generic("PUT", path, data, content_type, secure=secure, **kwargs)

    def patch(self, path, data=None, content_type=JSON_CONTENT, secure=False, **kwargs):
        data = self._encode_multipart(data, content_type)
        return self.generic("PATCH", path, data, content_type, secure=secure, **kwargs)

    def _encode_multipart(self, data, content_type):
        data = self._encode_json({} if data is None else data, content_type)
        return self._encode_data(data, content_type)
