from worf.exceptions import HTTP401, HTTP404


class Authenticated:
    def __call__(self, request, **kwargs):
        if request.user.is_authenticated:
            return

        raise HTTP401()


class PublicEndpoint:
    def __call__(self, request, **kwargs):
        pass


class Staff:
    def __call__(self, request, **kwargs):
        if request.user.is_authenticated and request.user.is_staff:
            return

        raise HTTP404()
