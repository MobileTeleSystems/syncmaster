from app.exceptions.base import EntityNotFound, SyncmasterException


class ConnectionNotFound(EntityNotFound):
    pass


class ConnectionOwnerException(SyncmasterException):
    pass


class ConnectionTypeNotRecognizedException(SyncmasterException):
    pass


class UserDoNotHaveRightsInTheTargetGroup(SyncmasterException):
    pass


class ConnectionDeleteException(SyncmasterException):
    def __init__(self, message: str) -> None:
        self.message = message
