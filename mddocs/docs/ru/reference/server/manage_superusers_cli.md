# CLI для управления суперпользователями { #manage-superusers-cli }

Управление пользователями осуществляется двумя способами:

- автоматически:

Установите `SYNCMASTER__ENTRYPOINT__SUPERUSERS=user1,user2` и [REST API Server][server] Docker-точку входа

Флаг `is_superuser=True` для них будет установлен автоматически, а для остальных пользователей в базе данных — сброшен.

- вручную через CLI:

```{eval-rst}
.. argparse::
   :module: syncmaster.server.scripts.manage_superusers
   :func: create_parser
   :prog: python -m syncmaster.server.scripts.manage_superusers
```
