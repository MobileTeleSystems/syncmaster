from fastapi import APIRouter

router = APIRouter(tags=["monitoring"], prefix="/monitoring")


@router.get("/ping")
async def ping():
    return {"status": "ok"}
