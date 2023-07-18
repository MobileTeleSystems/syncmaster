from pydantic import BaseModel


class TokenPayloadSchema(BaseModel):
    user_id: int | None = None


class AuthTokenSchema(BaseModel):
    access_token: str
    refresh_token: str
