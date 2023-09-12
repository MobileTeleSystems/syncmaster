from pydantic import BaseModel, Field, SecretStr, root_validator

from app.api.v1.schemas import ORACLE_TYPE, POSTGRES_TYPE, PageSchema


class ReadPostgresConnectionData(BaseModel):
    type: POSTGRES_TYPE
    host: str
    port: int = Field(gt=0, le=65535)
    user: str
    database_name: str
    additional_params: dict = Field(default_factory=dict)


class ReadOracleConnectionData(BaseModel):
    type: ORACLE_TYPE
    host: str
    user: str
    sid: str | None = None
    service_name: str | None = None
    additional_params: dict = Field(default_factory=dict)


class ReadConnectionSchema(BaseModel):
    id: int
    user_id: int | None = None
    group_id: int | None = None
    name: str
    description: str
    data: ReadPostgresConnectionData | ReadOracleConnectionData = Field(
        ..., discriminator="type", alias="connection_data"
    )

    class Config:
        orm_mode = True
        allow_population_by_field_name = True


class ConnectionPageSchema(PageSchema):
    items: list[ReadConnectionSchema]


class UpdatePostgresConnectionData(BaseModel):
    type: POSTGRES_TYPE
    host: str | None = None
    port: int | None = None
    user: str | None = None
    password: SecretStr | None = None
    database_name: str | None
    additional_params: dict | None = Field(default_factory=dict)


class UpdateOracleConnectionData(BaseModel):
    type: ORACLE_TYPE
    host: str | None = None
    user: str | None = None
    password: SecretStr | None = None
    sid: str | None = None
    service_name: str | None = None
    additional_params: dict | None = Field(default_factory=dict)


class UpdateConnectionSchema(BaseModel):
    name: str | None = None
    description: str | None = None
    data: UpdatePostgresConnectionData | UpdateOracleConnectionData | None = Field(
        discriminator="type", alias="connection_data", default=None
    )


class CreatePostgresConnectionData(BaseModel):
    type: POSTGRES_TYPE
    host: str
    port: int
    user: str
    password: SecretStr
    database_name: str
    additional_params: dict = Field(default_factory=dict)


class CreateOracleConnectionData(BaseModel):
    type: ORACLE_TYPE
    host: str
    user: str
    password: SecretStr
    sid: str | None = None
    service_name: str | None = None
    additional_params: dict = Field(default_factory=dict)


class CreateConnectionSchema(BaseModel):
    user_id: int | None
    group_id: int | None
    name: str
    description: str
    data: CreatePostgresConnectionData | CreateOracleConnectionData = Field(
        ..., discriminator="type", alias="connection_data"
    )

    @root_validator
    def check_owner_id(cls, values):
        user_id, group_id = values.get("user_id"), values.get("group_id")
        if (user_id is None) == (group_id is None):
            raise ValueError("Connection must have one owner: group or user")
        return values


class NewOwnerSchema(BaseModel):
    new_user_id: int | None = None
    new_group_id: int | None = None

    @root_validator
    def check_new_owner_id(cls, values):
        user_id, group_id = values.get("new_user_id"), values.get("new_group_id")
        if (user_id is None) == (group_id is None):
            raise ValueError("Connection must have one owner: group or user")
        return values
