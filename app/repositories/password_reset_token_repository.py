from app.repositories.base import BaseRepository
from app.models.password_reset_token import PasswordResetToken
class PasswordResetTokenRepository(BaseRepository):
    def __init__(self): super().__init__(PasswordResetToken)
password_reset_token_repository = PasswordResetTokenRepository()
