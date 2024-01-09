# SPDX-FileCopyrightText: 2023-2024 MTS (Mobile Telesystems)
# SPDX-License-Identifier: Apache-2.0
from app.exceptions.base import SyncmasterError


class UsernameAlreadyExistsError(SyncmasterError):
    pass


class UserNotFoundError(SyncmasterError):
    pass
