# SPDX-FileCopyrightText: 2023-2024 MTS (Mobile Telesystems)
# SPDX-License-Identifier: Apache-2.0
from exceptions.base import SyncmasterError


class GroupNameAlreadyExistsError(SyncmasterError):
    pass


class GroupAdminNotFoundError(SyncmasterError):
    pass


class GroupAlreadyExistsError(SyncmasterError):
    pass


class AlreadyIsGroupMemberError(SyncmasterError):
    pass


class AlreadyIsNotGroupMemberError(SyncmasterError):
    pass


class GroupNotFoundError(SyncmasterError):
    pass
