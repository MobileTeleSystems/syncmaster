from app.exceptions.base import SyncmasterError


class GroupNameAlreadyExistsError(SyncmasterError):
    pass


class GroupAdminNotFoundError(SyncmasterError):
    pass


class GroupAlreadyExistsError(SyncmasterError):
    pass


class AlreadyIsGroupMemberError(SyncmasterError):
    pass


class AlreadyIsNotGroupMemberError(SyncmasterError):
    pass


class GroupNotFoundError(SyncmasterError):
    pass
