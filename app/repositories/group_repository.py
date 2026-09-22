from app.repositories.base import BaseRepository
from app.models.group import Group
class GroupRepository(BaseRepository):
    def __init__(self): super().__init__(Group)
group_repository = GroupRepository()
