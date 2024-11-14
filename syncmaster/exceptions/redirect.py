# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0

from syncmaster.exceptions.base import SyncmasterError


class RedirectException(SyncmasterError):
    def __init__(self, redirect_url: str):
        self.redirect_url = redirect_url
