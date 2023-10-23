from app.exceptions.base import EntityNotFound, SyncmasterException


class QueueNotFound(EntityNotFound):
    pass


class QueueDeleteException(SyncmasterException):
    def __init__(self, message: str) -> None:
        self.message = message
