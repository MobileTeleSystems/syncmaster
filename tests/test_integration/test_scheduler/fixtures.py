import asyncio

import pytest
from apscheduler.triggers.cron import CronTrigger
from pytest_mock import MockerFixture

from syncmaster.scheduler.transfer_job_manager import TransferJobManager
from syncmaster.worker.config import celery


@pytest.fixture(
    scope="session",
    params=[pytest.param("scheduler", marks=[pytest.mark.scheduler])],
)
def mock_send_task_to_tick(mocker: MockerFixture):
    original_to_thread = asyncio.to_thread
    return mocker.patch(
        "asyncio.to_thread",
        new=lambda func, *args, **kwargs: original_to_thread(celery.send_task, "tick", *args[1:], **kwargs),
    )


@pytest.fixture(
    scope="session",
    params=[pytest.param("scheduler", marks=[pytest.mark.scheduler])],
)
def mock_add_job(mocker: MockerFixture, transfer_job_manager: TransferJobManager):
    original_add_job = transfer_job_manager.scheduler.add_job
    return mocker.patch.object(
        transfer_job_manager.scheduler,
        "add_job",
        side_effect=lambda func, id, trigger, misfire_grace_time, args: original_add_job(
            func=func,
            id=id,
            trigger=CronTrigger(second="*"),
            misfire_grace_time=misfire_grace_time,
            args=args,
        ),
    )
