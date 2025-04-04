import asyncio

import pytest
from apscheduler.triggers.cron import CronTrigger
from celery import Celery
from pytest_mock import MockerFixture, MockType

from syncmaster.scheduler.transfer_job_manager import TransferJobManager


@pytest.fixture
def mock_send_task_to_tick(mocker: MockerFixture, celery: Celery) -> MockType:
    original_to_thread = asyncio.to_thread
    return mocker.patch(
        "asyncio.to_thread",
        new=lambda func, *args, **kwargs: original_to_thread(celery.send_task, "tick", *args[1:], **kwargs),
    )


@pytest.fixture
def mock_add_job(mocker: MockerFixture, transfer_job_manager: TransferJobManager) -> MockType:
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
