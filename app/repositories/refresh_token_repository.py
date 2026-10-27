from app.models.refresh_token import RefreshToken
from app.repositories.base import BaseRepository


class RefreshTokenRepository(BaseRepository):
    def __init__(self): super().__init__(RefreshToken)
refresh_token_repository = RefreshTokenRepository()
