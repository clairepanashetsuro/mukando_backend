from app.repositories.base import BaseRepository
from app.models.loan import Loan
class LoanRepository(BaseRepository):
    def __init__(self): super().__init__(Loan)
loan_repository = LoanRepository()
