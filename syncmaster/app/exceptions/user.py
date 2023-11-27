from app.exceptions.base import SyncmasterError


class UsernameAlreadyExistsError(SyncmasterError):
    pass


class UserNotFoundError(SyncmasterError):
    pass
