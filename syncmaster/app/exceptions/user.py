from app.exceptions.base import SyncmasterException


class UsernameAlreadyExists(SyncmasterException):
    pass


class UserNotFound(SyncmasterException):
    pass
