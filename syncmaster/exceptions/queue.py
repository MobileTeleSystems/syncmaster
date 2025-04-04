# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from syncmaster.exceptions.base import EntityNotFoundError, SyncmasterError


class QueueNotFoundError(EntityNotFoundError):
    pass


class QueueDeleteError(SyncmasterError):
    def __init__(self, message: str) -> None:
        self.message = message


class DifferentTransferAndQueueGroupError(SyncmasterError):
    pass


class DuplicatedQueueNameError(SyncmasterError):
    pass
