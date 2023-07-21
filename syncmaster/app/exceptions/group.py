from app.exceptions.base import SyncmasterException


class GroupNameAlreadyExists(SyncmasterException):
    pass


class GroupAdminNotFound(SyncmasterException):
    pass


class GroupAlreadyExists(SyncmasterException):
    pass


class AlreadyIsGroupMember(SyncmasterException):
    pass


class AlreadyIsNotGroupMember(SyncmasterException):
    pass
