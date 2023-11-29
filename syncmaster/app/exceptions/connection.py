from app.exceptions.base import EntityNotFoundError, SyncmasterError


class ConnectionNotFoundError(EntityNotFoundError):
    pass


class ConnectionOwnerError(SyncmasterError):
    pass


class ConnectionTypeNotRecognizedError(SyncmasterError):
    pass


class UserDoNotHaveRightsInTheTargetGroupError(SyncmasterError):
    pass


class DuplicatedConnectionNameError(SyncmasterError):
    pass


class ConnectionDeleteError(SyncmasterError):
    def __init__(self, message: str) -> None:
        self.message = message
