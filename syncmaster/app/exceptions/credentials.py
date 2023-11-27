from app.exceptions import SyncmasterError


class AuthDataNotFoundError(SyncmasterError):
    def __init__(self, message: str) -> None:
        self.message = message
