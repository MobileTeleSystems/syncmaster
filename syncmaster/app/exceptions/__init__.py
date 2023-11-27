from app.exceptions.base import (
    ActionNotAllowedError,
    EntityNotFoundError,
    SyncmasterError,
)
from app.exceptions.connection import (
    ConnectionDeleteError,
    ConnectionNotFoundError,
    ConnectionOwnerError,
    ConnectionTypeNotRecognizedError,
)
from app.exceptions.credentials import AuthDataNotFoundError
from app.exceptions.group import (
    AlreadyIsGroupMemberError,
    AlreadyIsNotGroupMemberError,
    GroupAdminNotFoundError,
    GroupAlreadyExistsError,
    GroupNameAlreadyExistsError,
    GroupNotFoundError,
)
from app.exceptions.queue import (
    DifferentTransferAndQueueGroupError,
    QueueDeleteError,
    QueueNotFoundError,
)
from app.exceptions.run import (
    CannotConnectToTaskQueueError,
    CannotStopRunError,
    RunNotFoundError,
)
from app.exceptions.transfer import (
    DifferentTransferAndConnectionsGroupsError,
    DifferentTypeConnectionsAndParamsError,
    TransferNotFoundError,
    TransferOwnerError,
)
from app.exceptions.user import UsernameAlreadyExistsError, UserNotFoundError

__all__ = [
    "ActionNotAllowedError",
    "AlreadyIsGroupMemberError",
    "AlreadyIsNotGroupMemberError",
    "AuthDataNotFoundError",
    "CannotConnectToTaskQueueError",
    "CannotStopRunError",
    "ConnectionDeleteError",
    "ConnectionNotFoundError",
    "ConnectionOwnerError",
    "ConnectionTypeNotRecognizedError",
    "DifferentTransferAndConnectionsGroupsError",
    "DifferentTransferAndQueueGroupError",
    "DifferentTypeConnectionsAndParamsError",
    "EntityNotFoundError",
    "GroupAdminNotFoundError",
    "GroupAlreadyExistsError",
    "GroupNameAlreadyExistsError",
    "GroupNotFoundError",
    "QueueDeleteError",
    "QueueNotFoundError",
    "RunNotFoundError",
    "SyncmasterError",
    "TransferNotFoundError",
    "TransferOwnerError",
    "UserNotFoundError",
    "UsernameAlreadyExistsError",
]
