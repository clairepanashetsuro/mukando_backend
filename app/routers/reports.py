from fastapi import APIRouter, HTTPException
from sqlalchemy import func, select

from app.dependencies import DB, CurrentUser
from app.models.contribution import Contribution
from app.models.loan import Loan, LoanStatus
from app.models.repayment import Repayment
from app.models.user import User, UserRole
from app.services.loan_service import loan_balance

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/summary")
def summary(db: DB, user: CurrentUser):
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

    outstanding = sum((float(loan_balance(db, loan)) for loan in active_loans), start=0.0)
    members = int(db.execute(
        select(func.count()).select_from(User).where(
            User.group_id == user.group_id, User.role == UserRole.MEMBER
        )
    ).scalar_one())

    return {
        "members": members,
        "total_contributions": contributions,
        "total_repayments": repayments,
        "outstanding_loans": round(outstanding, 2),
        "active_loans": len(active_loans),
    }
