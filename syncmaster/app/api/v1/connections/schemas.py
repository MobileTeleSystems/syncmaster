from pydantic import BaseModel, Field, SecretStr, root_validator

from app.api.v1.schemas import HIVE_TYPE, ORACLE_TYPE, POSTGRES_TYPE, PageSchema


class ReadHiveConnectionSchema(BaseModel):
    type: HIVE_TYPE
    cluster: str
    additional_params: dict = Field(default_factory=dict)


class ReadHiveAuthSchema(BaseModel):
    type: HIVE_TYPE
    user: str


class ReadPostgresConnectionSchema(BaseModel):
    type: POSTGRES_TYPE
    host: str
    port: int = Field(gt=0, le=65535)
    database_name: str
    additional_params: dict = Field(default_factory=dict)


class ReadPostgresAuthSchema(BaseModel):
    type: POSTGRES_TYPE
    user: str


class ReadOracleConnectionSchema(BaseModel):
    type: ORACLE_TYPE
    host: str
    port: int
    service_name: str | None = None
    sid: str | None = None
    additional_params: dict = Field(default_factory=dict)


class ReadOracleAuthSchema(BaseModel):
    type: ORACLE_TYPE
    user: str


class ReadConnectionSchema(BaseModel):
    id: int
    group_id: int
    name: str
    description: str
    auth_data: ReadHiveAuthSchema | ReadOracleAuthSchema | ReadPostgresAuthSchema | None
    data: ReadHiveConnectionSchema | ReadOracleConnectionSchema | ReadPostgresConnectionSchema = Field(
        ...,
        discriminator="type",
        alias="connection_data",
    )

    class Config:
        orm_mode = True
        allow_population_by_field_name = True


class ConnectionPageSchema(PageSchema):
    items: list[ReadConnectionSchema]


class UpdateOracleConnectionSchema(BaseModel):
    type: ORACLE_TYPE
    host: str | None = None
    sid: str | None = None
    service_name: str | None = None
    additional_params: dict | None = Field(default_factory=dict)


class UpdateOracleAuthSchema(BaseModel):
    type: ORACLE_TYPE
    user: str | None = None
    password: SecretStr | None = None


class UpdatePostgresConnectionSchema(BaseModel):
    type: POSTGRES_TYPE
    host: str | None = None
    port: int | None = None
    database_name: str | None
    additional_params: dict | None = Field(default_factory=dict)


class UpdatePostgresAuthSchema(BaseModel):
    type: POSTGRES_TYPE
    user: str | None = None
    password: SecretStr | None = None


class UpdateHiveConnectionSchema(BaseModel):
    type: HIVE_TYPE
    cluster: str | None
    additional_params: dict | None = Field(default_factory=dict)


class UpdateHiveAuthSchema(BaseModel):
    type: HIVE_TYPE


class UpdateConnectionSchema(BaseModel):
    name: str | None = None
    description: str | None = None
    auth_data: UpdateHiveAuthSchema | UpdateOracleAuthSchema | UpdatePostgresAuthSchema | None = Field(
        discriminator="type", default=None
    )
    data: UpdateHiveConnectionSchema | UpdatePostgresConnectionSchema | UpdateOracleConnectionSchema | None = Field(
        discriminator="type", alias="connection_data", default=None
    )

    @root_validator
    def check_types(cls, values):
        data, auth_data = values.get("connection_data"), values.get("auth_data")
        if data and auth_data and data.get("type") != auth_data.get("type"):
            raise ValueError("Connection data and auth data must have same types")
        return values


class CreateHiveConnectionSchema(BaseModel):
    additional_params: dict = Field(default_factory=dict)
    type: HIVE_TYPE
    cluster: str


class CreateHiveAuthSchema(BaseModel):
    type: HIVE_TYPE
    user: str
    password: SecretStr


class CreateOracleConnectionSchema(BaseModel):
    type: ORACLE_TYPE
    host: str
    port: int
    service_name: str | None = None
    sid: str | None = None
    additional_params: dict = Field(default_factory=dict)

    @root_validator
    def check_owner_id(cls, values):
        sid, service_name = values.get("sid"), values.get("service_name")
        if sid and service_name:
            raise ValueError("You must specify either sid or service_name but not both")
        return values


class CreateOracleAuthSchema(BaseModel):
    type: ORACLE_TYPE
    user: str
    password: SecretStr


class CreatePostgresConnectionSchema(BaseModel):
    type: POSTGRES_TYPE
    host: str
    port: int
    database_name: str
    additional_params: dict = Field(default_factory=dict)


class CreatePostgresAuthSchema(BaseModel):
    type: POSTGRES_TYPE
    user: str
    password: SecretStr


class CreateConnectionSchema(BaseModel):
    group_id: int
    name: str
    description: str
    data: CreateHiveConnectionSchema | CreateOracleConnectionSchema | CreatePostgresConnectionSchema = Field(
        ...,
        discriminator="type",
        alias="connection_data",
    )
    auth_data: CreateHiveAuthSchema | CreateOracleAuthSchema | CreatePostgresAuthSchema = Field(
        ...,
        discriminator="type",
    )

    @root_validator
    def check_types(cls, values):
        data, auth_data = values.get("data"), values.get("auth_data")
        if data and auth_data and data.type != auth_data.type:
            raise ValueError("Connection data and auth data must have same types")
        return values


class ConnectionCopySchema(BaseModel):
    new_group_id: int
    remove_source: bool = False
