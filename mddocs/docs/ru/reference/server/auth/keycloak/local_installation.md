# Локальная установка и тестирование { #local_installation }

Вы можете протестировать аутентификацию Keycloak локально с помощью docker compose:

```console
$ docker compose -f docker-compose.test.yml up keycloak -d
...
```

## Авторизация в keycloak

Сначала вам нужно перейти по адресу [http://localhost:8080/admin](http://localhost:8080/admin) и войти, используя логин: `admin`, пароль: `admin` (по умолчанию), чтобы создать области.

![image](images/keycloak-login.png)

## Создание новой области

![image](images/keycloak-new-realm.png)

## Создание нового имени области

Передайте значение имени области. Затем передайте его в переменную окружения `SYNCMASTER__AUTH__KEYCLOAK__REALM_NAME`:

```console
$ export SYNCMASTER__AUTH__KEYCLOAK__REALM_NAME=fastapi_realm  # as on screen below
...
```

![image](images/keycloak-new-realm_name.png)

## Создание нового клиента

![image](images/keycloak-new-client.png)

## Создание нового имени клиента

В созданной области передайте значение имени клиента. Затем передайте его в переменную окружения `SYNCMASTER__AUTH__KEYCLOAK__CLIENT_ID`:

```console
$ export SYNCMASTER__AUTH__KEYCLOAK__CLIENT_ID=fastapi_client  # as on screen below
...
```

![image](images/keycloak-new-client_name.png)

## Установка `client_authentication` **ON** для получения client_secret

![image](images/keycloak-client-authentication.png)

## Настройка URI перенаправления

Чтобы настроить URI перенаправления, куда браузер будет перенаправлять пользователя для обмена кода, предоставленного Keycloak, на токен доступа, нужно установить переменную окружения `SYNCMASTER__AUTH__KEYCLOAK__REDIRECT_URI`. Значение по умолчанию для локальной разработки — `http://localhost:8000/auth/callback`.

```console
$ export SYNCMASTER__AUTH__KEYCLOAK__REDIRECT_URI=http://localhost:8000/auth/callback
...
```

## Настройка URI перенаправления клиента

Убедитесь, что этот URI также настроен как допустимый URI перенаправления в настройках клиента Keycloak. Это позволит браузеру перенаправлять пользователя в ваше приложение после успешной аутентификации в Keycloak.

![image](images/keycloak-client-redirect_uri.png)

## Настройка секрета клиента

Теперь перейдите на вкладку **Учетные данные** и добавьте секрет клиента в переменную среды `SYNCMASTER__AUTH__KEYCLOAK__CLIENT_SECRET`:

```console
$ export SYNCMASTER__AUTH__KEYCLOAK__CLIENT_SECRET=6x6gn8uJdWSBmP8FqbNRSoGdvaoaFeez   # as on screen below
...
```

![image](images/keycloak-client-secret.png)

Теперь вы можете создавать пользователей в этих сферах. Ознакомьтесь с [документацией keycloak](https://www.keycloak.org/docs/latest/server_admin/#assembly-managing-users_server_administration_guide) на предмет того, как управлять созданием пользователей.

## ПЕРЕМЕННЫЕ СРЕДЫ

После этого вы можете использовать `KeycloakAuthProvider` в своем приложении с предоставленными переменными среды:

```console
$ export SYNCMASTER__AUTH__KEYCLOAK__SERVER_URL=http://keycloak:8080
$ export SYNCMASTER__AUTH__KEYCLOAK__REDIRECT_URI=http://localhost:8000/auth/callback
$ export SYNCMASTER__AUTH__KEYCLOAK__REALM_NAME=fastapi_realm
$ export SYNCMASTER__AUTH__KEYCLOAK__CLIENT_ID=fastapi_client
$ export SYNCMASTER__AUTH__KEYCLOAK__CLIENT_SECRET=6x6gn8uJdWSBmP8FqbNRSoGdvaoaFeez
$ export SYNCMASTER__AUTH__KEYCLOAK__SCOPE=email
$ export SYNCMASTER__AUTH__KEYCLOAK__VERIFY_SSL=False
$ export SYNCMASTER__AUTH__PROVIDER=syncmaster.server.providers.auth.keycloak_provider.KeycloakAuthProvider
...
```
