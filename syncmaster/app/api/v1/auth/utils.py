import time

from jose import JWTError, jwt
from pydantic import ValidationError

from app.api.v1.auth.schemas import TokenPayloadSchema
from app.config import Settings


def sign_jwt(user_id: int, settings: Settings) -> str:
    """This method authentication for dev version without keycloak"""
    payload = {
        "user_id": user_id,
        "expires": time.time() + settings.TOKEN_EXPIRED_TIME,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.SECURITY_ALGORITHM)


def decode_jwt(token: str, settings: Settings) -> TokenPayloadSchema | None:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.SECURITY_ALGORITHM])
        return TokenPayloadSchema(**payload)
    except (JWTError, ValidationError):
        return None
