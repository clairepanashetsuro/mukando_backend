from fastapi import APIRouter, HTTPException
from sqlalchemy import func, select

from app.dependencies import DB, CurrentUser
from app.models.contribution import Contribution
from app.models.loan import Loan, LoanStatus
from app.models.repayment import Repayment
from app.models.user import UserRole

router = APIRouter(prefix="/finance", tags=["finance"])


@router.get("/available-funds")
def available_funds(db: DB, user: CurrentUser):
    if user.role != UserRole.TREASURER:
        raise HTTPException(403, "Treasurer access required")

    contributions = float(db.execute(
        select(func.coalesce(func.sum(Contribution.amount), 0)).where(Contribution.group_id == user.group_id)
    ).scalar_one())
    repayments = float(db.execute(
        select(func.coalesce(func.sum(Repayment.amount), 0)).where(Repayment.group_id == user.group_id)
    ).scalar_one())
    active_loans = db.execute(
        select(Loan).where(Loan.group_id == user.group_id, Loan.status == LoanStatus.ACTIVE)
    ).scalars().all()
    active_principal = sum(float(loan.principal) for loan in active_loans)
    available = contributions + repayments - active_principal
    return {"available_funds": round(max(available, 0), 2)}
