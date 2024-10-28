# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import enum


class Status(enum.StrEnum):
    CREATED = "CREATED"
    STARTED = "STARTED"
    FAILED = "FAILED"
    SEND_STOP_SIGNAL = "SEND_STOP_SIGNAL"
    STOPPED = "STOPPED"
    FINISHED = "FINISHED"


class GroupMemberRole(enum.StrEnum):
    Maintainer = "Maintainer"
    Developer = "Developer"
    Owner = "Owner"
    Guest = "Guest"
    Superuser = "Superuser"

    @classmethod
    def public_roles(cls) -> list[GroupMemberRole]:
        return [cls.Maintainer, cls.Developer, cls.Guest]

    @classmethod
    def public_roles_str(cls) -> str:
        return ", ".join([role.value for role in cls.public_roles()])

    @classmethod
    def is_public_role(cls, role: str) -> bool:
        try:
            role_enum = cls(role)
            return role_enum in cls.public_roles()
        except ValueError:
            return False

    @classmethod
    def role_hierarchy(cls) -> dict[GroupMemberRole, int]:
        return {
            cls.Guest: 1,
            cls.Developer: 2,
            cls.Maintainer: 3,
            cls.Owner: 4,
            cls.Superuser: 5,
        }

    @classmethod
    def is_at_least_privilege_level(
        cls,
        role1: str | GroupMemberRole,
        role2: str | GroupMemberRole,
    ) -> bool:
        role1_enum = cls(role1) if isinstance(role1, str) else role1
        role2_enum = cls(role2) if isinstance(role2, str) else role2
        hierarchy = cls.role_hierarchy()
        return hierarchy.get(role1_enum, 0) >= hierarchy.get(role2_enum, 0)

    @classmethod
    def roles_at_least(cls, role: str | GroupMemberRole) -> list[str]:
        role_enum = cls(role) if isinstance(role, str) else role
        required_level = cls.role_hierarchy()[role_enum]
        return [r.value for r, level in cls.role_hierarchy().items() if level >= required_level]
