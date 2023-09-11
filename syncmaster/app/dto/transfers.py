from dataclasses import dataclass


@dataclass
class PostgresTransferParamsDTO:
    table_name: str


@dataclass
class OracleTransferParamsDTO:
    table_name: str
