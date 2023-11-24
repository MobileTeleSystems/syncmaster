from app.exceptions.base import EntityNotFound, SyncmasterException


class QueueNotFoundException(EntityNotFound):
    pass


class QueueDeleteException(SyncmasterException):
    def __init__(self, message: str) -> None:
        self.message = message


class DifferentTransferAndQueueGroups(SyncmasterException):
    pass
