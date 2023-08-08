from app.exceptions.base import EntityNotFound, SyncmasterException


class ConnectionNotFound(EntityNotFound):
    pass


class ConnectionOwnerException(SyncmasterException):
    pass
