from functools import partialmethod

from django.test.client import Client


class ApiClient(Client):
    delete = partialmethod(Client.delete, content_type="application/json")
    patch = partialmethod(Client.patch, content_type="application/json")
    post = partialmethod(Client.post, content_type="application/json")
    put = partialmethod(Client.put, content_type="application/json")
