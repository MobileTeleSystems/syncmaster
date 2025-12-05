#!/bin/env python3

# SPDX-FileCopyrightText: 2023-present MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import argparse
import asyncio
import logging

from pydantic import Field
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.future import select

from syncmaster.db.models.user import User
from syncmaster.server.settings import (
    DEFAULT_LOGGING_SETTINGS,
    BaseSettings,
    DatabaseSettings,
    LoggingSettings,
)
from syncmaster.settings.logging import setup_logging


class SuperuserAppSettings(BaseSettings):
    database: DatabaseSettings = Field(
        default_factory=DatabaseSettings,  # type: ignore[arg-type]
        description="Database settings",
    )
    logging: LoggingSettings = Field(
        default=DEFAULT_LOGGING_SETTINGS,
        description="Logging settings",
    )
    superusers: list[str] = Field(
        default_factory=list,
        description="List of superuser usernames",
    )


async def add_superusers(session: AsyncSession, usernames: list[str]) -> None:
    logging.info("Adding superusers:")
    result = await session.execute(select(User).where(User.username.in_(usernames)).order_by(User.username))
    users = result.scalars().all()

    not_found = set(usernames)
    for user in users:
        user.is_superuser = True
        logging.info("    %r", user.username)
        not_found.discard(user.username)

    if not_found:
        for username in not_found:
            session.add(User(username=username, is_superuser=True))
            logging.info("    %r (new user)", username)

    await session.commit()
    logging.info("Done.")


async def remove_superusers(session: AsyncSession, usernames: list[str]) -> None:
    logging.info("Removing superusers:")
    result = await session.execute(select(User).where(User.username.in_(usernames)).order_by(User.username))
    users = result.scalars().all()

    not_found = set(usernames)
    for user in users:
        logging.info("    %r", user.username)
        user.is_superuser = False
        not_found.discard(user.username)

    if not_found:
        logging.info("Not found:")
        for username in not_found:
            logging.info("    %r", username)

    await session.commit()
    logging.info("Done.")


async def list_superusers(session: AsyncSession) -> None:
    result = await session.execute(select(User).filter_by(is_superuser=True).order_by(User.username))
    superusers = result.scalars().all()
    logging.info("Listing users with SUPERUSER role:")
    for superuser in superusers:
        logging.info("    %r", superuser.username)
    logging.info("Done.")


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage superusers.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    parser_add = subparsers.add_parser("add", help="Add superuser privileges to users")
    parser_add.add_argument("usernames", nargs="?", help="Usernames to add as superusers")
    parser_add.set_defaults(func=add_superusers)

    parser_remove = subparsers.add_parser("remove", help="Remove superuser privileges from users")
    parser_remove.add_argument("usernames", nargs="?", help="Usernames to remove from superusers")
    parser_remove.set_defaults(func=remove_superusers)

    parser_list = subparsers.add_parser("list", help="List all superusers")
    parser_list.set_defaults(func=list_superusers)

    return parser


async def main(args: argparse.Namespace, session: AsyncSession) -> None:
    async with session:
        if args.command == "list":
            # 'list' command does not take additional arguments
            await args.func(session)
        else:
            await args.func(session, args.usernames)


if __name__ == "__main__":
    settings = SuperuserAppSettings()
    setup_logging(settings.logging)

    engine = create_async_engine(settings.database.url)
    SessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)
    parser = create_parser()
    args = parser.parse_args()

    if args.command == "add" and not args.usernames:
        args.usernames = settings.superusers

    session = SessionLocal()
    asyncio.run(main(args, session))
