# CLI for managing superusers { #manage-superusers-cli }

There are two ways to manage users:

- automatic:

  [REST API Server][server] Docker container entrypoint will automatically create users with `is_superuser=True` in database
  during startup.

  Usernames can be passed via config file:

  ```yaml title="config.yml"
  superusers:
    - user1
    - user2
  ```

  Or via environment variable:

  ```bash
  export 'SYNCMASTER__SUPERUSERS=["user1", "user2"]'
  ```

- manual, via CLI described below.

## CLI

```text
usage: python -m syncmaster.server.scripts.manage_superusers
       [-h] {add,remove,list} ...

Manage superusers.

positional arguments:
  {add,remove,list}
    add              Add superuser privileges to users
    remove           Remove superuser privileges from users
    list             List all superusers

options:
  -h, --help         show this help message and exit
```

### `add`

Add superuser privileges to users:

```bash
python -m syncmaster.server.scripts.manage_superusers add [usernames]
```

### `remove`

Remove superuser privileges from users:

```bash
python -m syncmaster.server.scripts.manage_superusers remove [usernames]
```

### `list`

List all superusers:

```bash
python -m syncmaster.server.scripts.manage_superusers list
```
