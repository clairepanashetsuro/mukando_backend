from app.repositories.base import BaseRepository
from app.models.contribution import Contribution
class ContributionRepository(BaseRepository):
    def __init__(self): super().__init__(Contribution)
contribution_repository = ContributionRepository()
