# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0


from jinja2 import Template

from syncmaster.config import Settings
from syncmaster.db.models import Run

settings = Settings()


def render_log_url(run: Run, correlation_id: str):
    template = Template(settings.LOG_URL_TEMPLATE)

    log_url = template.render(
        run=run,
        correlation_id=correlation_id,
        logging_system=settings.LOGGING_SYSTEM.lower(),
        kibana_host=settings.KIBANA_HOST,
        grafana_host=settings.GRAFANA_HOST,
    )

    return log_url.strip()
