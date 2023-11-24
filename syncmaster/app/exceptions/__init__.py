from app.exceptions.base import ActionNotAllowed, EntityNotFound, SyncmasterException
from app.exceptions.connection import (
    ConnectionDeleteException,
    ConnectionNotFound,
    ConnectionOwnerException,
    ConnectionTypeNotRecognizedException,
)
from app.exceptions.credentials import AuthDataNotFound
from app.exceptions.group import (
    AlreadyIsGroupMember,
    AlreadyIsNotGroupMember,
    GroupAdminNotFound,
    GroupAlreadyExists,
    GroupNameAlreadyExists,
    GroupNotFound,
)
from app.exceptions.queue import (
    DifferentTransferAndQueueGroups,
    QueueDeleteException,
    QueueNotFoundException,
)
from app.exceptions.run import (
    CannotConnectToTaskQueueError,
    CannotStopRunException,
    RunNotFoundException,
)
from app.exceptions.transfer import (
    DifferentTransferAndConnectionsGroups,
    DifferentTypeConnectionsAndParams,
    TransferNotFound,
    TransferOwnerException,
)
from app.exceptions.user import UsernameAlreadyExists, UserNotFound

__all__ = [
    "ActionNotAllowed",
    "AlreadyIsGroupMember",
    "AlreadyIsNotGroupMember",
    "AuthDataNotFound",
    "CannotConnectToTaskQueueError",
    "CannotStopRunException",
    "ConnectionDeleteException",
    "ConnectionNotFound",
    "ConnectionOwnerException",
    "ConnectionTypeNotRecognizedException",
    "DifferentTransferAndConnectionsGroups",
    "DifferentTransferAndQueueGroups",
    "DifferentTypeConnectionsAndParams",
    "EntityNotFound",
    "GroupAdminNotFound",
    "GroupAlreadyExists",
    "GroupNameAlreadyExists",
    "GroupNotFound",
    "QueueDeleteException",
    "QueueNotFoundException",
    "RunNotFoundException",
    "SyncmasterException",
    "TransferNotFound",
    "TransferOwnerException",
    "UserNotFound",
    "UsernameAlreadyExists",
]
