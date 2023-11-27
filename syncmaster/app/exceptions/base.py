class SyncmasterError(Exception):
    pass


class EntityNotFoundError(SyncmasterError):
    pass


class ActionNotAllowedError(SyncmasterError):
    pass
