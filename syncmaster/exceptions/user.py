# SPDX-FileCopyrightText: 2023-2025 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from syncmaster.exceptions.base import SyncmasterError


class UsernameAlreadyExistsError(SyncmasterError):
    pass


class UserNotFoundError(SyncmasterError):
    pass
