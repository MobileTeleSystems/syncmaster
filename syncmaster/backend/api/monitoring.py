# SPDX-FileCopyrightText: 2023-2024 MTS (Mobile Telesystems)
# SPDX-License-Identifier: Apache-2.0
from fastapi import APIRouter

router = APIRouter(tags=["monitoring"], prefix="/monitoring")


@router.get("/ping")
async def ping():
    return {"status": "ok"}
