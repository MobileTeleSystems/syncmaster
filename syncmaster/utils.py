# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0


from jinja2 import Template

from syncmaster.db.models import Run
from syncmaster.settings import Settings


def render_log_url(run: Run, correlation_id: str):
    template = Template(Settings().LOG_URL_TEMPLATE)

    log_url = template.render(
        run=run,
        correlation_id=correlation_id,
    )

    return log_url.strip()
