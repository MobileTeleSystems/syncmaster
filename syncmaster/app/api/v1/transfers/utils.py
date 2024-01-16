# SPDX-FileCopyrightText: 2023-2024 MTS (Mobile Telesystems)
# SPDX-License-Identifier: Apache-2.0
from app.api.v1.transfers.schemas.transfer import (
    CreateTransferSchema,
    UpdateTransferSchema,
)


def process_s3_directory_path(
    transfer_data: UpdateTransferSchema | CreateTransferSchema,
) -> UpdateTransferSchema | CreateTransferSchema:
    if transfer_data.source_params is not None:
        if transfer_data.source_params.type == "s3":
            transfer_data.source_params.directory_path = str(transfer_data.source_params.directory_path)  # type: ignore

    if transfer_data.target_params is not None:
        if transfer_data.target_params.type == "s3":
            transfer_data.target_params.directory_path = str(transfer_data.target_params.directory_path)  # type: ignore

    return transfer_data
