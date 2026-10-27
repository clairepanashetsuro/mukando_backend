from app.models.password_reset_token import PasswordResetToken
from app.repositories.base import BaseRepository


class PasswordResetTokenRepository(BaseRepository):
    def __init__(self): super().__init__(PasswordResetToken)
password_reset_token_repository = PasswordResetTokenRepository()
