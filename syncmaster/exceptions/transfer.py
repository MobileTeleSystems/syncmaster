# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from typing import Literal

from syncmaster.exceptions.base import SyncmasterError


class TransferOwnerError(SyncmasterError):
    pass


class TransferNotFoundError(SyncmasterError):
    pass


class DuplicatedTransferNameError(SyncmasterError):
    pass


class DifferentTransferAndConnectionsGroupsError(SyncmasterError):
    pass


class DifferentTypeConnectionsAndParamsError(SyncmasterError):
    def __init__(
        self,
        connection_type: str,
        params_type: str,
        conn: Literal["source", "target"],
    ):
        self.connection_type = connection_type
        self.params_type = params_type
        self.conn = conn.capitalize()

    @property
    def message(self) -> str:
        return (
            f"{self.conn} connection has type `{self.connection_type}` " f"but its params has `{self.params_type}` type"
        )
