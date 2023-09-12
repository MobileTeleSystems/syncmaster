from dataclasses import dataclass


@dataclass
class ConnectionDTO:
    type: str


@dataclass
class PostgresConnectionDTO(ConnectionDTO):
    host: str
    port: int
    user: str
    password: str
    database_name: str
    additional_params: dict


@dataclass
class OracleConnectionDTO(ConnectionDTO):
    host: str
    port: int
    user: str
    password: str
    sid: str
    additional_params: dict
