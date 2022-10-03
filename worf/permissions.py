from worf.exceptions import AuthenticationError, NotFound


class Authenticated:
    def __call__(self, request, **kwargs):
        if not request.user.is_authenticated:
            raise AuthenticationError()


class PublicEndpoint:
    def __call__(self, request, **kwargs):
        pass


class Staff:
    def __call__(self, request, **kwargs):
        if not request.user.is_authenticated or not request.user.is_staff:
            raise NotFound()
