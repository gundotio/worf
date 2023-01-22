from dataclasses import dataclass


@dataclass(frozen=True)
class WorfError(Exception):
    message: str


@dataclass(frozen=True)
class ActionError(WorfError):
    message: str


@dataclass(frozen=True)
class AuthenticationError(WorfError):
    message: str = "Unauthorized"


@dataclass(frozen=True)
class DataConflict(WorfError):
    message: str = "Conflict"


@dataclass(frozen=True)
class NamingThingsError(WorfError, ValueError):
    message: str


@dataclass(frozen=True)
class NotFound(WorfError):
    message: str = "Not found"


@dataclass(frozen=True)
class FieldError(WorfError, ValueError):
    message: str
