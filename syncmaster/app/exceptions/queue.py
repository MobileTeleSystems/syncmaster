from app.exceptions.base import EntityNotFoundError, SyncmasterError


class QueueNotFoundError(EntityNotFoundError):
    pass


class QueueDeleteError(SyncmasterError):
    def __init__(self, message: str) -> None:
        self.message = message


class DifferentTransferAndQueueGroupError(SyncmasterError):
    pass
