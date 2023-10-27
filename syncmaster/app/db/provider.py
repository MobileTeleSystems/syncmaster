from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.db.models import AuthData
from app.db.repositories.connection import ConnectionRepository
from app.db.repositories.credentials_repository import CredentialsRepository
from app.db.repositories.group import GroupRepository
from app.db.repositories.run import RunRepository
from app.db.repositories.transfer import TransferRepository
from app.db.repositories.user import UserRepository


class DatabaseProvider:
    def __init__(self, session: AsyncSession, settings: Settings):
        self.user = UserRepository(session=session)
        self.group = GroupRepository(session=session)
        self.connection = ConnectionRepository(session=session)
        self.transfer = TransferRepository(session=session)
        self.run = RunRepository(session=session)
        self.credentials_repository = CredentialsRepository(
            session=session,
            settings=settings,
            model=AuthData,
        )
