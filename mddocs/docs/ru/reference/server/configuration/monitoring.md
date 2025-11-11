# Мониторинг сервера { #server-configuration-monitoring }

Сервер REST API предоставляет следующие эндпоинты с метриками, совместимыми с Prometheus:

- `GET /monitoring/metrics` - метрики сервера, такие как количество запросов на каждый путь и статус ответа, использование CPU и RAM(оперативной памяти) и т. д.

Эти эндпоинты включаются и настраиваются с помощью следующих параметров:

::: syncmaster.server.settings.server.monitoring.MonitoringSettings
