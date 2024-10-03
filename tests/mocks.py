import enum
import logging
from typing import Any

from syncmaster.db.models import Connection, Group, Run, Transfer, User

logger = logging.getLogger(__name__)


class UserTestRoles(enum.StrEnum):
    Owner = "Owner"
    Maintainer = "Maintainer"
    Developer = "Developer"
    Guest = "Guest"
    _Superuser = "Superuser"


class MockUser:
    def __init__(self, user: User, auth_token: str, role: str) -> None:
        self.user = user
        self.token = auth_token
        self.role = role

    def __getattr__(self, attr: str) -> Any:
        return getattr(self.user, attr)


class MockGroup:
    def __init__(
        self,
        group: Group,
        owner: MockUser,
        members: list[MockUser],
    ):
        self.group = group
        self._owner = owner

        if members:
            self._maintainer = members[0]
            self._developer = members[1]
            self._guest = members[2]

    def get_member_of_role(self, role_name: str) -> MockUser:
        if role_name == UserTestRoles.Maintainer:
            return self._maintainer
        if role_name == UserTestRoles.Developer:
            return self._developer
        if role_name == UserTestRoles.Guest:
            return self._guest
        if role_name == UserTestRoles.Owner:
            return self._owner

        raise ValueError(f"Unknown role name: {role_name}.")

    def __getattr__(self, attr: str) -> Any:
        return getattr(self.group, attr)


class MockCredentials:
    def __init__(
        self,
        value: dict,
        connection_id: int,
    ):
        self.value = value
        self.connection_id = connection_id


class MockConnection:
    def __init__(
        self,
        connection: Connection,
        owner_group: MockGroup,
        credentials: MockCredentials | None = None,
    ):
        self.connection = connection
        self.owner_group = owner_group
        self.credentials = credentials

    def __getattr__(self, attr: str) -> Any:
        return getattr(self.connection, attr)


class MockTransfer:
    def __init__(
        self,
        transfer: Transfer,
        source_connection: MockConnection,
        target_connection: MockConnection,
        owner_group: MockGroup,
    ):
        self.transfer = transfer
        self.source_connection = source_connection
        self.target_connection = target_connection
        self.owner_group = owner_group

    def __getattr__(self, attr: str) -> Any:
        return getattr(self.transfer, attr)


class MockRun:
    def __init__(
        self,
        run: Run,
        transfer: MockTransfer,
    ):
        self.run = run
        self.transfer = transfer

    def __getattr__(self, attr: str) -> Any:
        return getattr(self.run, attr)
