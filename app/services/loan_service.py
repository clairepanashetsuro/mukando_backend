from decimal import Decimal
from datetime import date
from fastapi import HTTPException
from sqlalchemy import select, func
from app.models.user import User, UserRole
from app.models.contribution import Contribution
from app.models.loan import Loan, LoanStatus
from app.models.repayment import Repayment
def loan_balance(db,loan):
    paid=(db.execute(select(func.coalesce(func.sum(Repayment.amount),0)).where(Repayment.loan_id==loan.id))).scalar_one()
    base=Decimal(str(loan.principal))+Decimal(str(loan.interest_amount))-Decimal(str(paid))
    if base <= 0: return Decimal('0.00')
    today=date.today()
    weeks=max(0,(today-loan.due_date).days//7) if today>loan.due_date else 0
    return (base*(Decimal('1.05')**weeks)).quantize(Decimal('0.01'))
def create(db,treasurer,data):
    member=(db.execute(select(User).where(User.id==data.member_id,User.group_id==treasurer.group_id,User.role==UserRole.MEMBER))).scalar_one_or_none()
    if not member: raise HTTPException(404,"Member not found in your group")
    contributions=Decimal(str((db.execute(select(func.coalesce(func.sum(Contribution.amount),0)).where(Contribution.member_id==member.id))).scalar_one()))
    max_loan=contributions*Decimal('2')
    active=(db.execute(select(Loan).where(Loan.member_id==member.id,Loan.status==LoanStatus.ACTIVE))).scalars().all()
    existing=Decimal('0')
    for l in active: existing += loan_balance(db,l)
    principal=Decimal(str(data.principal))
    if principal <= 0: raise HTTPException(400,"Principal must be positive")
    if principal + existing > max_loan: raise HTTPException(400,f"Total outstanding borrowing would exceed 2x contributions ({max_loan})")
    group_total=Decimal(str((db.execute(select(func.coalesce(func.sum(Contribution.amount),0)).where(Contribution.group_id==treasurer.group_id))).scalar_one()))
    group_paid=Decimal(str((db.execute(select(func.coalesce(func.sum(Repayment.amount),0)).where(Repayment.group_id==treasurer.group_id))).scalar_one()))
    active_loans=(db.execute(select(Loan).where(Loan.group_id==treasurer.group_id,Loan.status==LoanStatus.ACTIVE))).scalars().all()
    active_principal=sum(Decimal(str(l.principal)) for l in active_loans)
    available=group_total+group_paid-active_principal
    if principal > available: raise HTTPException(400,f"Loan exceeds available group funds ({available})")
    interest=(principal*Decimal('0.10')).quantize(Decimal('0.01'))
    obj=Loan(member_id=member.id,group_id=treasurer.group_id,principal=principal,interest_rate=10,interest_amount=interest,due_date=data.due_date); db.add(obj); db.commit(); db.refresh(obj); return obj
