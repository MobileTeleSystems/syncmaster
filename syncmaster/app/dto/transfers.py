from dataclasses import dataclass


@dataclass
class PostgresTransferParamsDTO:
    table_name: str
    type: str = "postgres"


@dataclass
class OracleTransferParamsDTO:
    table_name: str
    type: str = "oracle"


@dataclass
class HiveTransferParamsDTO:
    table_name: str
    type: str = "hive"
