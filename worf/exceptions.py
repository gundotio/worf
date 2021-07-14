class HTTPException(Exception):
    def __init__(self, message=None):
        super().__init__(message)
        if message is not None:
            self.message = message


class HTTP400(HTTPException):
    message = "Bad Request"
    status = 400


class HTTP401(HTTPException):
    message = "Unauthorized"
    status = 401


class HTTP404(HTTPException):
    message = "Not Found"
    status = 404


class HTTP409(HTTPException):
    message = "Conflict"
    status = 409


class HTTP410(HTTPException):
    message = "Gone"
    status = 410


class HTTP420(HTTPException):
    message = "Enhance Your Calm"
    status = 420


class HTTP422(HTTPException):
    message = "Unprocessable Entity"
    status = 422


HTTP_EXCEPTIONS = (HTTP400, HTTP401, HTTP404, HTTP409, HTTP410, HTTP420, HTTP422)


class NamingThingsError(ValueError):
    pass


class PermissionsException(Exception):
    pass


class NotImplementedInWorfYet(NotImplementedError):
    pass
