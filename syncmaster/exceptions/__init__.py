# SPDX-FileCopyrightText: 2023-2024 MTS (Mobile Telesystems)
# SPDX-License-Identifier: Apache-2.0
from exceptions.base import ActionNotAllowedError, EntityNotFoundError, SyncmasterError
from exceptions.connection import (
    ConnectionDeleteError,
    ConnectionNotFoundError,
    ConnectionOwnerError,
    ConnectionTypeNotRecognizedError,
    DuplicatedConnectionNameError,
)
from exceptions.credentials import AuthDataNotFoundError
from exceptions.group import (
    AlreadyIsGroupMemberError,
    AlreadyIsNotGroupMemberError,
    GroupAdminNotFoundError,
    GroupAlreadyExistsError,
    GroupNameAlreadyExistsError,
    GroupNotFoundError,
)
from exceptions.queue import (
    DifferentTransferAndQueueGroupError,
    QueueDeleteError,
    QueueNotFoundError,
)
from exceptions.run import (
    CannotConnectToTaskQueueError,
    CannotStopRunError,
    RunNotFoundError,
)
from exceptions.transfer import (
    DifferentTransferAndConnectionsGroupsError,
    DifferentTypeConnectionsAndParamsError,
    DuplicatedTransferNameError,
    TransferNotFoundError,
    TransferOwnerError,
)
from exceptions.user import UsernameAlreadyExistsError, UserNotFoundError

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
    "DuplicatedConnectionNameError",
    "DuplicatedTransferNameError",
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
