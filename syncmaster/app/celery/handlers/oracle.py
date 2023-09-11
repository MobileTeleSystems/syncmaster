from onetl.connection import Oracle
from onetl.db import DBReader, DBWriter

from app.celery.handlers.base import Handler
from app.dto.connections import OracleConnectionDTO
from app.dto.transfers import OracleTransferParamsDTO


class OracleHandler(Handler):
    connection: OracleConnectionDTO
    transfer_params: OracleTransferParamsDTO

    def init_connection(self):
        self.connection = Oracle(
            host=self.connection.host,
            port=self.connection.port,
            user=self.connection.user,
            password=self.connection.password,
            sid=self.connection.sid,
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
            connection=self.connection,
            table=self.transfer_params.table_name,
        )
