# Сущности { #entities }

## Пользователь

SyncMaster поддерживает многопользовательскую систему и доступ на основе ролей (см. [Роли и разрешения][role-permissions]).
Для любого взаимодействия требуется аутентификация пользователя, анонимный доступ не допускается.

Пользователи автоматически получают доступ после успешного входа в систему, специальной регистрации не требуется.

## Группа

Все типы сущностей (Подключение, Передача, Выполнение, Очередь) могут быть созданы только внутри определенной группы.
Группы независимы друг от друга и имеют глобально уникальное имя.

![image](group_list.png)![image](group_info.png)

Группу может создать любой пользователь, которому автоматически назначается роль `OWNER`.
Эта роль позволяет добавлять участников в группу и назначать им определенные роли:

![image](group_add_member.png)

## Подключение

Подключение описывает, как SyncMaster может получить доступ к конкретной базе данных или файловой системе. Оно включает тип (например, `s3`, `hive`, `postgres`),
параметры подключения (например, `host`, `port`, `protocol`) и данные авторизации (комбинация `user` / `password`).

Подключения имеют уникальные имена в пределах группы.

![image](connection_list.png)![image](connection_info_db.png)![image](connection_info_fs.png)

## Трансфер

Трансфер — это сердце SyncMaster. Он описывает, какие данные следует извлечь из источника (подключение к БД + имя таблицы, подключение к файловой системе + путь к каталогу),
и какова цель (БД или файловая система).

Передачи имеют уникальное имя в пределах группы.

![image](transfer_list.png)![image](create_transfer_head.png)![image](create_transfer_source_target.png)![image](create_transfer_advanced.png)

Можно добавить преобразования между этапами чтения и записи:

![image](create_transfer_advanced_filter_files.png)![image](create_transfer_advanced_filter_rows.png)![image](create_transfer_advanced_filter_columns.png)

Другие возможности переноса:

- Выбор различных стратегий чтения (`полный`, `пошаговый`)
- Выполнение переноса по расписанию (ежечасно, ежедневно, еженедельно и т. д.)
- Задание определённых ресурсов (ЦП, ОЗУ) для каждого выполнения переноса

![image](create_transfer_footer.png)

## Запуск

Каждый раз при запуске передачи (вручную или по расписанию) SyncMaster создаёт отдельный запуск,
который отслеживает состояние процесса ETL, URL-адрес журналов рабочих процессов и т. д.

![image](run_list.png)![image](run_info.png)

## Очередь

Очередь позволяет привязать определённую передачу к набору SyncMaster [Worker][reference-worker]

Очередь имеет уникальное имя в пределах группы и глобально уникальное поле `slug`, которое генерируется при создании очереди.

![image](queue_list.png)![image](queue_info.png)

Передачи невозможно создать без очереди. Если к очереди не привязан ни один исполнитель, созданные запуски не будут выполнены.

## Диаграмма сущностей

```plantuml

    @startuml
    title Entity Diagram

    left to right direction

    entity User {
        * id
        ----
        username
        is_active
        is_superuser
        created_at
        updated_at
    }

    entity Group {
        * id
        ----
        name
        description
        owner_id
        created_at
        updated_at
    }

    entity Connection {
        * id
        ----
        group_id
        type
        name
        description
        data
        created_at
        updated_at
    }

    entity Queue {
        * id
        ----
        name
        slug
        group_id
        description
        created_at
        updated_at
    }

    entity Transfer {
        * id
        ----
        group_id
        name
        source_connection_id
        target_connection_id
        strategy_params
        target_params
        transformations
        resources
        is_scheduled
        schedule
        queue_id
        created_at
        updated_at
    }

    entity Run {
        * id
        ----
        transfer_id
        started_at
        ended_at
        status
        type
        log_url
        transfer_dump
        created_at
        updated_at
    }

    Run ||--o{ Transfer
    Transfer ||--o{ Queue
    Transfer ||--o{ Connection
    Transfer ||--o{ Group
    Connection ||--o{ Group
    Queue ||--o{ Group
    Group }o--o{ User
    Group "owner_id" ||--o{ User

    @enduml
```
