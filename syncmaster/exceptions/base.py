# SPDX-FileCopyrightText: 2023-present MTS PJSC
# SPDX-License-Identifier: Apache-2.0
class SyncmasterError(Exception):
    pass


class EntityNotFoundError(SyncmasterError):
    pass


class ActionNotAllowedError(SyncmasterError):
    pass
