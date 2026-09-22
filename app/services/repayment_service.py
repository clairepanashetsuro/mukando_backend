from decimal import Decimal
from datetime import date
from fastapi import HTTPException
from sqlalchemy import select, func
from app.models.loan import Loan, LoanStatus
from app.models.repayment import Repayment
from app.services.loan_service import loan_balance
def create(db,treasurer,data):
    loan=(db.execute(select(Loan).where(Loan.id==data.loan_id,Loan.group_id==treasurer.group_id))).scalar_one_or_none()
    if not loan: raise HTTPException(404,"Loan not found in your group")
    balance=loan_balance(db,loan)
    if data.amount <= 0 or Decimal(str(data.amount)) > balance: raise HTTPException(400,f"Repayment must be positive and not exceed balance ({balance})")
    obj=Repayment(loan_id=loan.id,member_id=loan.member_id,group_id=loan.group_id,amount=data.amount,paid_at=data.paid_at,recorded_by=treasurer.id); db.add(obj)
    remaining=balance-Decimal(str(data.amount))
    if remaining <= 0: loan.status=LoanStatus.PAID
    db.commit(); db.refresh(obj); return obj
