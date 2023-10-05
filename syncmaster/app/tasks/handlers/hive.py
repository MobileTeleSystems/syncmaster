from onetl.connection import Hive
from onetl.db import DBReader, DBWriter

from app.dto.connections import HiveConnectionDTO
from app.dto.transfers import HiveTransferParamsDTO
from app.tasks.handlers.base import Handler


class HiveHandler(Handler):
    connection: Hive
    connection_dto: HiveConnectionDTO
    transfer_params: HiveTransferParamsDTO

    def init_connection(self):
        self.connection = Hive(
            cluster=self.connection_dto.cluster,
            spark=self.spark,
        ).check()

    def init_reader(self):
        super().init_reader()
        self.spark.catalog.refreshTable(self.transfer_params.table_name)
        self.reader = DBReader(
            connection=self.connection,
            table=self.transfer_params.table_name,
        )

    def init_writer(self):
        super().init_writer()
        self.writer = DBWriter(
            connection=self.connection,
            table=self.transfer_params.table_name,
        )
