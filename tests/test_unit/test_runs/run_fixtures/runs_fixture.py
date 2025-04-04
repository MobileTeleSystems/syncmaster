from datetime import datetime, timedelta, timezone

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from syncmaster.db.models import Run, Status
from tests.mocks import MockRun


@pytest_asyncio.fixture
async def group_runs(group_run: MockRun, session: AsyncSession) -> list[MockRun]:
    # extract necessary data from the existing group_run fixture
    transfer = group_run.transfer.transfer
    mock_transfer = group_run.transfer
    transfer_id = transfer.id

    # start with the run from group_run fixture
    runs = [group_run]
    base_time = datetime.now(tz=timezone.utc)
    statuses = list(Status)

    # since group_run already created a run, we start from index 1
    for idx, status in enumerate(statuses[1:], start=1):
        started_at = base_time - timedelta(days=idx)
        ended_at = started_at + timedelta(hours=idx)
        created_at = started_at - timedelta(minutes=10)
        updated_at = ended_at + timedelta(minutes=5)

        run = Run(
            transfer_id=transfer_id,
            status=status,
            started_at=started_at,
            ended_at=ended_at,
            created_at=created_at,
            updated_at=updated_at,
            transfer_dump={},
        )

        session.add(run)
        mock_run = MockRun(run=run, transfer=mock_transfer)
        runs.append(mock_run)

    await session.commit()

    yield runs

    for mock_run in runs[1:]:
        await session.delete(mock_run.run)
    await session.commit()
