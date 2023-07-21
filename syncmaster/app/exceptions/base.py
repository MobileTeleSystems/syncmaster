class SyncmasterException(Exception):
    pass


class EntityNotFound(SyncmasterException):
    pass


class ActionNotAllowed(SyncmasterException):
    pass
