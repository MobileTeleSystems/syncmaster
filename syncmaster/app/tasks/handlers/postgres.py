from onetl.connection import Postgres
from onetl.db import DBReader, DBWriter

from app.dto.connections import PostgresConnectionDTO
from app.dto.transfers import PostgresTransferParamsDTO
from app.tasks.handlers.base import Handler


class PostgresHandler(Handler):
    connection: Postgres
    connection_dto: PostgresConnectionDTO
    transfer_params: PostgresTransferParamsDTO

    def init_connection(self):
        self.connection = Postgres(
            host=self.connection_dto.host,
            user=self.connection_dto.user,
            password=self.connection_dto.password,
            port=self.connection_dto.port,
            database=self.connection_dto.database_name,
            extra=self.connection_dto.additional_params,
            spark=self.spark,
        ).check()

    def init_reader(self):
        super().init_reader()
        df = self.connection.get_df_schema(self.transfer_params.table_name)
        self.reader = DBReader(
            connection=self.connection,
            table=self.transfer_params.table_name,
            columns=[f'"{f}"' for f in df.fieldNames()],
        )

    def init_writer(self):
        super().init_writer()
        self.writer = DBWriter(
            connection=self.connection,
            table=self.transfer_params.table_name,
        )
