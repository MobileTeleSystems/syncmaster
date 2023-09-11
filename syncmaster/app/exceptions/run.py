from app.exceptions.base import EntityNotFound, SyncmasterException


class RunNotFoundException(EntityNotFound):
    pass


class CannotStopRunException(SyncmasterException):
    pass
