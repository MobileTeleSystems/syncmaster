from app.exceptions.acl import AclNotFound
from app.exceptions.base import ActionNotAllowed, EntityNotFound, SyncmasterException
from app.exceptions.connection import (
    ConnectionDeleteException,
    ConnectionNotFound,
    ConnectionOwnerException,
    ConnectionTypeNotRecognizedException,
)
from app.exceptions.group import (
    AlreadyIsGroupMember,
    AlreadyIsNotGroupMember,
    GroupAdminNotFound,
    GroupAlreadyExists,
    GroupNameAlreadyExists,
    GroupNotFound,
)
from app.exceptions.queue import QueueDeleteException, QueueNotFound
from app.exceptions.run import (
    CannotConnectToTaskQueueError,
    CannotStopRunException,
    RunNotFoundException,
)
from app.exceptions.transfer import (
    DifferentConnectionsOwners,
    DifferentSourceAndTargetQueueException,
    DifferentTypeConnectionsAndParams,
    TransferNotFound,
    TransferOwnerException,
)
from app.exceptions.user import UsernameAlreadyExists, UserNotFound

__all__ = [
    "AclNotFound",
    "ActionNotAllowed",
    "AlreadyIsGroupMember",
    "AlreadyIsNotGroupMember",
    "CannotConnectToTaskQueueError",
    "CannotStopRunException",
    "ConnectionDeleteException",
    "ConnectionNotFound",
    "ConnectionOwnerException",
    "ConnectionTypeNotRecognizedException",
    "DifferentConnectionsOwners",
    "DifferentSourceAndTargetQueueException",
    "DifferentTypeConnectionsAndParams",
    "EntityNotFound",
    "GroupAdminNotFound",
    "GroupAlreadyExists",
    "GroupNameAlreadyExists",
    "GroupNotFound",
    "QueueDeleteException",
    "QueueNotFound",
    "RunNotFoundException",
    "SyncmasterException",
    "TransferNotFound",
    "TransferOwnerException",
    "UserNotFound",
    "UsernameAlreadyExists",
]
