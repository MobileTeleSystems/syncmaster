# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from pydantic import BaseModel, ConfigDict, Field


class RabbitMQSettings(BaseModel):
    """RabbitMQ connection settings.

    You can pass any extra options supported by the RabbitMQ client.

    Examples
    --------

    .. code-block:: bash

        # Set the RabbitMQ connection URL
        SYNCMASTER__BROKER__URL=amqp://guest:guest@rabbitmq:5672/

        # Pass custom options directly
        SYNCMASTER__BROKER__CONNECTION_TIMEOUT=30
    """

    url: str = Field(
        description=(
            "RabbitMQ connection URL.\n\n" "See the `RabbitMQ documentation <https://www.rabbitmq.com/uri-spec.html>`_ "
        ),
    )

    model_config = ConfigDict(extra="allow")
