# SPDX-FileCopyrightText: 2023-2024 MTS (Mobile Telesystems)
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from typing import NoReturn

from sqlalchemy import ScalarResult, delete, insert, select
from sqlalchemy.exc import DBAPIError, IntegrityError, NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from syncmaster.config import Settings
from syncmaster.db.models import AuthData
from syncmaster.db.repositories.base import Repository
from syncmaster.db.repositories.utils import decrypt_auth_data, encrypt_auth_data
from syncmaster.exceptions import SyncmasterError
from syncmaster.exceptions.credentials import AuthDataNotFoundError


class CredentialsRepository(Repository[AuthData]):
    def __init__(
        self,
        session: AsyncSession,
        settings: Settings,
        model: type[AuthData],
    ):
        super().__init__(model=model, session=session)
        self._settings = settings

    async def get_for_connection(
        self,
        connection_id: int,
    ) -> dict:
        query = select(AuthData).where(AuthData.connection_id == connection_id)
        try:
            result: ScalarResult[AuthData] = await self._session.scalars(query)
            return decrypt_auth_data(result.one().value, settings=self._settings)
        except NoResultFound as e:
            raise AuthDataNotFoundError(f"Connection id = {connection_id}") from e

    async def add_to_connection(self, connection_id: int, data: dict) -> AuthData:
        query = (
            insert(AuthData)
            .values(
                value=encrypt_auth_data(value=data, settings=self._settings),
                connection_id=connection_id,
            )
            .returning(AuthData)
        )
        try:
            result: ScalarResult[AuthData] = await self._session.scalars(query)
        except IntegrityError as e:
            self._raise_error(e)
        else:
            await self._session.flush()
            return result.one()

    async def delete_from_connection(self, connection_id: int) -> AuthData:
        query = delete(AuthData).where(AuthData.connection_id == connection_id).returning(AuthData)

        try:
            result: ScalarResult[AuthData] = await self._session.scalars(query)
        except IntegrityError as e:
            self._raise_error(e)
        else:
            await self._session.flush()
            return result.one()

    async def update(
        self,
        connection_id: int,
        credential_data: dict,
    ) -> AuthData:
        creds = await self.get_for_connection(connection_id)
        try:
            for key in creds:
                if key not in credential_data or credential_data[key] is None:
                    credential_data[key] = creds[key]

            return await self._update(
                AuthData.connection_id == connection_id,
                value=encrypt_auth_data(value=credential_data, settings=self._settings),
            )
        except IntegrityError as e:
            self._raise_error(e)

    def _raise_error(self, err: DBAPIError) -> NoReturn:
        raise SyncmasterError from err
