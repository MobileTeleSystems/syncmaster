# SPDX-FileCopyrightText: 2023-2024 MTS (Mobile Telesystems)
# SPDX-License-Identifier: Apache-2.0
from syncmaster.schemas.v1.transfers import CreateTransferSchema, UpdateTransferSchema


def process_file_transfer_directory_path(
    transfer_data: UpdateTransferSchema | CreateTransferSchema,
) -> UpdateTransferSchema | CreateTransferSchema:
    if transfer_data.source_params is not None:
        if hasattr(transfer_data.source_params, "directory_path"):  # s3 or hdfs connection
            transfer_data.source_params.directory_path = str(transfer_data.source_params.directory_path)

    if transfer_data.target_params is not None:
        if hasattr(transfer_data.source_params, "directory_path"):  # s3 or hdfs connection
            transfer_data.target_params.directory_path = str(transfer_data.target_params.directory_path)  # type: ignore

    return transfer_data
