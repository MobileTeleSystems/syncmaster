# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from fastapi import APIRouter

from syncmaster.errors.registration import get_error_responses
from syncmaster.schemas import PingResponse

router = APIRouter(tags=["Monitoring"], prefix="/monitoring", responses=get_error_responses())


@router.get("/ping")
async def ping() -> PingResponse:
    return PingResponse()
