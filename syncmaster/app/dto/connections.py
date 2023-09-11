from dataclasses import dataclass


@dataclass
class PostgresConnectionDTO:
    host: str
    port: int
    user: str
    password: str
    database_name: str
    additional_params: dict


@dataclass
class OracleConnectionDTO:
    host: str
    port: int
    user: str
    password: str
    sid: str
    additional_params: dict
