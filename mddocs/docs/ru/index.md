# Data.SyncMaster

[![Статус репозитория](https://www.repostatus.org/badges/latest/wip.svg)](https://www.repostatus.org/#wip) [![Docker образ](https://img.shields.io/docker/v/mtsrus/syncmaster-server?sort=semver&label=docker)](https://hub.docker.com/r/mtsrus/syncmaster-server) [![PyPI](https://img.shields.io/pypi/v/data-syncmaster)](https://pypi.org/project/data-syncmaster/) [![PyPI лицензия](https://img.shields.io/pypi/l/data-syncmaster.svg)](https://github.com/MobileTeleSystems/syncmaster/blob/develop/LICENSE.txt) [![PyPI Python версия](https://img.shields.io/pypi/pyversions/data-syncmaster.svg)](https://badge.fury.io/py/data-syncmaster) [![Документация](https://readthedocs.org/projects/syncmaster/badge/?version=stable)](https://syncmaster.readthedocs.io)
[![Статус сборки](https://github.com/MobileTeleSystems/syncmaster/workflows/Run%20All%20Tests/badge.svg)](https://github.com/MobileTeleSystems/syncmaster/actions) [![Охват](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/MTSOnGithub/03e73a82ecc4709934540ce8201cc3b4/raw/syncmaster_badge.json)](https://github.com/MobileTeleSystems/syncmaster/actions) [![pre-commit.ci](https://results.pre-commit.ci/badge/github/MobileTeleSystems/syncmaster/develop.svg)](https://results.pre-commit.ci/latest/github/MobileTeleSystems/syncmaster/develop)

## Описание Data.SyncMaster

**Data.SyncMaster** - это no-code ETL для переноса данных между различными хранилищами, включающими в себя множество видов БД и файловых источников.

Сейчас список поддерживаемых поддерживаемых хранилищ включает в себя:

- Apache Hive
- Clickhouse
- Postgres
- Oracle
- MSSQL
- MySQL
- HDFS
- S3
- FTP
- FTPS
- SFTP
- Samba
- WebDAV

## Отличительные особенности Data.SyncMaster

- **Простота** Перенос данных между различными хранилищами без единой строчки кода
- **Разнообразие** Множество встроенных коннекторов для переноса данных в гетерогенной среде
- **Подходит для любой орг.структуры** Благодаря поддержке RBAC и многотенантности SyncMaster можно использовать в организациях любого размера
- **Безопасность** Поддержка промышленных средств обеспечения безопасности

**Сделано дата-инженерами для дата-инженеров**

## Зачем использовать Data.SyncMaster?

Чтобы иметь возможность:

1. Легко мигрировать данные между базами данных и файловыми системами
2. Работать с большим количеством источников в одном продукте
3. Получить проверенное решение, ежедневно применяемое в одной из крупнейших корпораций

## Чем SyncMaster не является?

1. Обработчиком потоковых данных
2. Системой резервного копирования

Высокоуровневое проектирование

- [Сущности][entities]
- [Разрешения][role-permissions]

Reference

- [Архитектура][reference-architecture]
- [База данных][database]
- [Брокер][message-broker]
- [Сервер][server]
- [Фронтенд][frontend]
- [Рабочий процесс][worker]
- [Планировщик][scheduler]

Development

- [Журнал изменений][changelog]
- [Участие][contributing]
- [Безопасность][security]
