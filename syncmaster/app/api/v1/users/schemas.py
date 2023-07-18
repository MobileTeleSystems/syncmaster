from string import ascii_lowercase, digits

from pydantic import BaseModel, validator

from app.api.v1.schemas import PageSchema


class UpdateUserSchema(BaseModel):
    username: str

    @validator("username")
    def username_validator(cls, value):
        alph = ascii_lowercase + digits + "_"
        if any(filter(lambda x: x not in alph, value)):
            raise ValueError("Invalid username")
        return value


class ReadUserSchema(BaseModel):
    id: int
    username: str
    is_superuser: bool

    class Config:
        orm_mode = True


class FullUserSchema(ReadUserSchema):
    is_active: bool

    class Config:
        orm_mode = True


class UserPageSchema(PageSchema):
    items: list[ReadUserSchema]
