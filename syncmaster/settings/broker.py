# SPDX-FileCopyrightText: 2023-present MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from typing import Annotated
from urllib.parse import urlsplit

from pydantic import AfterValidator, AnyUrl, BaseModel, ConfigDict, Field, UrlConstraints
from sqlalchemy import make_url


def validate_url(value: AnyUrl):
    split = urlsplit(str(value))
    if not split.username or not split.password:
        msg = "RabbitMQ URL must contain username and password"
        raise ValueError(msg)

    return value


RabbitMQURL = Annotated[
    AnyUrl,
    UrlConstraints(allowed_schemes=["amqp"], host_required=True, preserve_empty_path=False),
    AfterValidator(validate_url),
]


class RabbitMQSettings(BaseModel):
    """RabbitMQ connection settings.

    You can pass any extra options supported by the RabbitMQ client.

    Examples
    --------

    ```yaml title="config.yml"
    broker:
        url: amqp://guest:guest@rabbitmq:5672/

        # custom option passed directly to RabbitMQ client
        connection_timeout: 30
    ```
    """

    url: RabbitMQURL = Field(
        description=(
            "RabbitMQ connection URL.\n\nSee the [RabbitMQ documentation](https://www.rabbitmq.com/uri-spec.html) "
        ),
    )

    model_config = ConfigDict(extra="allow")

    def __repr_args__(self):
        safe_url = make_url(str(self.url)).render_as_string(
            hide_password=True,
        )
        extra = super().__repr_args__()
        return [
            ("url", safe_url),
            *[item for item in extra if item[0] != "url"],
        ]
