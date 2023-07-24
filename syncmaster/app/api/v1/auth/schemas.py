from pydantic import BaseModel


class TokenPayloadSchema(BaseModel):
    user_id: int


class AuthTokenSchema(BaseModel):
    access_token: str
    refresh_token: str
