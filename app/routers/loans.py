from math import ceil
from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select
from app.dependencies import DB, CurrentUser
from app.models.loan import Loan, LoanStatus
from app.models.user import UserRole
from app.schemas.loan import LoanCreate, LoanRead, LoanUpdate
from app.services.loan_service import create, loan_balance
router=APIRouter(prefix='/loans',tags=['loans'])
@router.post('',response_model=LoanRead)
def create_loan(data:LoanCreate,db:DB,user:CurrentUser):
    if user.role!=UserRole.TREASURER: raise HTTPException(403,'Treasurer access required')
    return create(db,user,data)
@router.get('',response_model=dict)
def list_loans(db:DB,user:CurrentUser,page:int=Query(1,ge=1),size:int=Query(20,ge=1,le=100)):
    q=select(Loan).where(Loan.group_id==user.group_id).order_by(Loan.id.desc());
    if user.role==UserRole.MEMBER: q=q.where(Loan.member_id==user.id)
    all_items=(db.execute(q)).scalars().all(); total=len(all_items); items=(db.execute(q.offset((page-1)*size).limit(size))).scalars().all()
    return {'items':items,'total':total,'page':page,'size':size,'pages':ceil(total/size) if total else 0}
@router.get('/{loan_id}',response_model=LoanRead)
def get_loan(loan_id:int,db:DB,user:CurrentUser):
    obj=db.get(Loan,loan_id)
    if not obj or obj.group_id!=user.group_id or (user.role==UserRole.MEMBER and obj.member_id!=user.id): raise HTTPException(404,'Loan not found')
    return obj
@router.get('/{loan_id}/balance')
def get_balance(loan_id:int,db:DB,user:CurrentUser):
    obj=db.get(Loan,loan_id)
    if not obj or obj.group_id!=user.group_id or (user.role==UserRole.MEMBER and obj.member_id!=user.id): raise HTTPException(404,'Loan not found')
    return {'loan_id':loan_id,'balance':float(loan_balance(db,obj))}
@router.patch('/{loan_id}',response_model=LoanRead)
def update_loan(loan_id:int,data:LoanUpdate,db:DB,user:CurrentUser):
    if user.role!=UserRole.TREASURER: raise HTTPException(403,'Treasurer access required')
    obj=db.get(Loan,loan_id)
    if not obj or obj.group_id!=user.group_id or (user.role==UserRole.MEMBER and obj.member_id!=user.id): raise HTTPException(404,'Loan not found')
    for k,v in data.model_dump(exclude_unset=True).items(): setattr(obj,k,v)
    db.commit(); db.refresh(obj); return obj
@router.delete('/{loan_id}',status_code=204)
def delete_loan(loan_id:int,db:DB,user:CurrentUser):
    if user.role!=UserRole.TREASURER: raise HTTPException(403,'Treasurer access required')
    obj=db.get(Loan,loan_id)
    if not obj or obj.group_id!=user.group_id or (user.role==UserRole.MEMBER and obj.member_id!=user.id): raise HTTPException(404,'Loan not found')
    db.delete(obj); db.commit()
