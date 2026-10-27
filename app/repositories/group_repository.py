from app.models.group import Group
from app.repositories.base import BaseRepository


class GroupRepository(BaseRepository):
    def __init__(self):
        super().__init__(Group)


group_repository = GroupRepository()
