# Провайдеры аутентификации { #server-auth-providers }

Syncmaster поддерживает различные реализации провайдера аутентификации. Вы можете изменить реализацию в настройках:

::: syncmaster.server.settings.auth.AuthSettings

## Провайдеры аутентификации

* [Фиктивный провайдер аутентификации][server-auth-dummy]
  * [Описание][server-auth-dummy-description]
  * [Схема взаимодействия][server-auth-dummy-interaction-shema]
  * [Конфигурация][server-auth-dummy-configuration]
* [Провайдер аутентификации KeyCloak][keycloak-auth-provider]
  * [Описание][keycloak-auth-provider-description]
  * [Схема взаимодействия][keycloak-auth-provider-interaction-schema]
  * [Базовая конфигурация][keycloak-auth-provider-basic-configuration]

## Для разработчиков

* [Пользовательский провайдер аутентификации][server-auth-custom]
