from app.db.models import Status
from app.exceptions.base import EntityNotFoundError, SyncmasterError


class RunNotFoundError(EntityNotFoundError):
    pass


class CannotStopRunError(SyncmasterError):
    def __init__(self, run_id: int, current_status: Status):
        self.run_id = run_id
        self.current_status = current_status


class CannotConnectToTaskQueueError(SyncmasterError):
    def __init__(self, run_id: int):
        self.run_id = run_id
