from typing import Literal

from app.exceptions.base import SyncmasterException


class TransferOwnerException(SyncmasterException):
    pass


class TransferNotFound(SyncmasterException):
    pass


class DifferentConnectionsOwners(SyncmasterException):
    pass


class DifferentTypeConnectionsAndParams(SyncmasterException):
    def __init__(
        self,
        connection_type: str,
        params_type: str,
        conn: Literal["source", "target"],
    ):
        self.connection_type = connection_type
        self.params_type = params_type
        self.conn = conn.capitalize()

    @property
    def message(self) -> str:
        return (
            f"{self.conn} connection has type `{self.connection_type}` "
            f"but its params has `{self.params_type}` type"
        )


class DifferentSourceAndTargetQueueException(SyncmasterException):
    pass
