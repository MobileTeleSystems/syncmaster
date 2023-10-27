from app.exceptions import SyncmasterException


class AuthDataNotFound(SyncmasterException):
    def __init__(self, message: str) -> None:
        self.message = message
