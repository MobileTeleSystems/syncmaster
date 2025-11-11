# Конфигуранция фронтенда { #configuration-frontend }

## Ссылка на API

Для работы SyncMaster UI требуется доступ к REST API из браузера. URL-адрес API настраивается с помощью переменной окружения:

```bash
SYNCMASTER__UI__API_BROWSER_URL=http://localhost:8000
```

Если и REST API, и фронтенд обслуживаются на одном домене (например, через обратный прокси-сервер Nginx), например:

- REST API → `/api`
- Frontend → `/`

Тогда вы можете использовать относительный путь:

```bash
SYNCMASTER__UI__API_BROWSER_URL=/api
```
