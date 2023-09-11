from onetl.connection import Postgres
from onetl.db import DBReader, DBWriter

from app.celery.handlers.base import Handler
from app.dto.connections import PostgresConnectionDTO
from app.dto.transfers import PostgresTransferParamsDTO


class PostgresHandler(Handler):
    connection: PostgresConnectionDTO
    transfer_params: PostgresTransferParamsDTO

    def init_connection(self):
        self.connection = Postgres(
            host=self.connection.host,
            user=self.connection.user,
            password=self.connection.password.get_secret_value(),
            port=self.connection.port,
            database=self.connection.database_name,
            extra=self.connection.additional_params,
            spark=self.spark,
        ).check()

    def init_reader(self):
        super().init_reader()
        self.reader = DBReader(
            connection=self.connection,
            source=self.transfer_params.table_name,
        )

    def init_writer(self):
        super().init_writer()
        self.writer = DBWriter(
            connection=self.connection, table=self.transfer_params.table_name
        )
