from math import ceil
from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select
from app.dependencies import DB, CurrentUser
from app.models.repayment import Repayment
from app.models.user import UserRole
from app.schemas.repayment import RepaymentCreate, RepaymentRead, RepaymentUpdate
from app.services.repayment_service import create
router=APIRouter(prefix='/repayments',tags=['repayments'])
@router.post('',response_model=RepaymentRead)
def create_repayment(data:RepaymentCreate,db:DB,user:CurrentUser):
    if user.role!=UserRole.TREASURER: raise HTTPException(403,'Treasurer access required')
    return create(db,user,data)
@router.get('',response_model=dict)
def list_repayments(db:DB,user:CurrentUser,page:int=Query(1,ge=1),size:int=Query(20,ge=1,le=100)):
    q=select(Repayment).where(Repayment.group_id==user.group_id).order_by(Repayment.paid_at.desc(), Repayment.id.desc());
    if user.role==UserRole.MEMBER: q=q.where(Repayment.member_id==user.id)
    all_items=(db.execute(q)).scalars().all(); total=len(all_items); items=(db.execute(q.offset((page-1)*size).limit(size))).scalars().all()
    return {'items':items,'total':total,'page':page,'size':size,'pages':ceil(total/size) if total else 0}
@router.get('/{repayment_id}',response_model=RepaymentRead)
def get_repayment(repayment_id:int,db:DB,user:CurrentUser):
    obj=db.get(Repayment,repayment_id)
    if not obj or obj.group_id!=user.group_id or (user.role==UserRole.MEMBER and obj.member_id!=user.id): raise HTTPException(404,'Repayment not found')
    return obj
@router.patch('/{repayment_id}',response_model=RepaymentRead)
def update_repayment(repayment_id:int,data:RepaymentUpdate,db:DB,user:CurrentUser):
    if user.role!=UserRole.TREASURER: raise HTTPException(403,'Treasurer access required')
    obj=db.get(Repayment,repayment_id)
    if not obj or obj.group_id!=user.group_id or (user.role==UserRole.MEMBER and obj.member_id!=user.id): raise HTTPException(404,'Repayment not found')
    for k,v in data.model_dump(exclude_unset=True).items(): setattr(obj,k,v)
    db.commit(); db.refresh(obj); return obj
@router.delete('/{repayment_id}',status_code=204)
def delete_repayment(repayment_id:int,db:DB,user:CurrentUser):
    if user.role!=UserRole.TREASURER: raise HTTPException(403,'Treasurer access required')
    obj=db.get(Repayment,repayment_id)
    if not obj or obj.group_id!=user.group_id or (user.role==UserRole.MEMBER and obj.member_id!=user.id): raise HTTPException(404,'Repayment not found')
    db.delete(obj); db.commit()
