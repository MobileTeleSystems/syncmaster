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
from app.exceptions.run import (
    CannotConnectToTaskQueueError,
    CannotStopRunException,
    RunNotFoundException,
)
from app.exceptions.transfer import (
    DifferentConnectionsOwners,
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
    "DifferentTypeConnectionsAndParams",
    "EntityNotFound",
    "GroupAdminNotFound",
    "GroupAlreadyExists",
    "GroupNameAlreadyExists",
    "GroupNotFound",
    "RunNotFoundException",
    "SyncmasterException",
    "TransferNotFound",
    "TransferOwnerException",
    "UserNotFound",
    "UsernameAlreadyExists",
]
