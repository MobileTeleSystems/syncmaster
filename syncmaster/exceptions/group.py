# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from syncmaster.exceptions.base import SyncmasterError


class GroupNameAlreadyExistsError(SyncmasterError):
    pass


class GroupAlreadyExistsError(SyncmasterError):
    pass


class AlreadyIsGroupMemberError(SyncmasterError):
    pass


class AlreadyIsNotGroupMemberError(SyncmasterError):
    pass


class AlreadyIsGroupOwnerError(SyncmasterError):
    pass


class GroupNotFoundError(SyncmasterError):
    pass
