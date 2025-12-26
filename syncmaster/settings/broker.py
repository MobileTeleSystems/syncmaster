# SPDX-FileCopyrightText: 2023-present MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from pydantic import BaseModel, ConfigDict, Field


class RabbitMQSettings(BaseModel):
    """RabbitMQ connection settings.

    You can pass any extra options supported by the RabbitMQ client.

    Examples
    --------

    .. code-block:: yaml
        :caption: config.yml

        broker:
            url: amqp://guest:guest@rabbitmq:5672/

            # custom option passed directly to RabbitMQ client
            connection_timeout: 30
    """

    url: str = Field(
        description=(
            "RabbitMQ connection URL.\n\nSee the `RabbitMQ documentation <https://www.rabbitmq.com/uri-spec.html>`_ "
        ),
    )

    model_config = ConfigDict(extra="allow")
