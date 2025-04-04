# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from syncmaster.exceptions import SyncmasterError


class AuthDataNotFoundError(SyncmasterError):
    def __init__(self, message: str) -> None:
        self.message = message
