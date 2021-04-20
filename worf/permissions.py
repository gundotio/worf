from worf.exceptions import HTTP401, HTTP404


def Authenticated(self, request):
    if not request.user.is_authenticated:
        return HTTP401()
    return 200


def Staff(self, request):
    if not request.user.is_authenticated or not request.user.is_staff:
        return HTTP404()
    return 200


def PublicEndpoint(self, request):
    return 200
