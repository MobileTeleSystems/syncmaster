from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.connection import ConnectionRepository
from app.db.repositories.group import GroupRepository
from app.db.repositories.queue import QueueRepository
from app.db.repositories.run import RunRepository
from app.db.repositories.transfer import TransferRepository
from app.db.repositories.user import UserRepository


class DatabaseProvider:
    def __init__(self, session: AsyncSession):
        self.user = UserRepository(session=session)
        self.group = GroupRepository(session=session)
        self.connection = ConnectionRepository(session=session)
        self.transfer = TransferRepository(session=session)
        self.run = RunRepository(session=session)
        self.queue = QueueRepository(session=session)
