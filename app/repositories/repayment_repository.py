from app.repositories.base import BaseRepository
from app.models.repayment import Repayment
class RepaymentRepository(BaseRepository):
    def __init__(self): super().__init__(Repayment)
repayment_repository = RepaymentRepository()
