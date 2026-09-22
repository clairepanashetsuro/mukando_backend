from math import ceil
from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select
from app.dependencies import DB, CurrentUser
from app.models.contribution import Contribution
from app.models.user import UserRole
from app.schemas.contribution import ContributionCreate, ContributionRead, ContributionUpdate
from app.services.contribution_service import create
router=APIRouter(prefix='/contributions',tags=['contributions'])
@router.post('',response_model=ContributionRead)
def create_contribution(data:ContributionCreate,db:DB,user:CurrentUser):
    if user.role!=UserRole.TREASURER: raise HTTPException(403,'Only the treasurer can record contributions')
    return create(db,user,data)
@router.get('',response_model=dict)
def list_contributions(db:DB,user:CurrentUser,page:int=Query(1,ge=1),size:int=Query(20,ge=1,le=100)):
    q=select(Contribution).where(Contribution.group_id==user.group_id).order_by(Contribution.paid_at.desc(), Contribution.id.desc());
    if user.role==UserRole.MEMBER: q=q.where(Contribution.member_id==user.id)
    all_items=(db.execute(q)).scalars().all(); total=len(all_items); items=(db.execute(q.offset((page-1)*size).limit(size))).scalars().all()
    return {'items':items,'total':total,'page':page,'size':size,'pages':ceil(total/size) if total else 0}
@router.get('/{contribution_id}',response_model=ContributionRead)
def get_contribution(contribution_id:int,db:DB,user:CurrentUser):
    obj=db.get(Contribution,contribution_id)
    if not obj or obj.group_id!=user.group_id or (user.role==UserRole.MEMBER and obj.member_id!=user.id): raise HTTPException(404,'Contribution not found')
    return obj
@router.patch('/{contribution_id}',response_model=ContributionRead)
def update_contribution(contribution_id:int,data:ContributionUpdate,db:DB,user:CurrentUser):
    if user.role!=UserRole.TREASURER: raise HTTPException(403,'Treasurer access required')
    obj=db.get(Contribution,contribution_id)
    if not obj or obj.group_id!=user.group_id or (user.role==UserRole.MEMBER and obj.member_id!=user.id): raise HTTPException(404,'Contribution not found')
    for k,v in data.model_dump(exclude_unset=True).items(): setattr(obj,k,v)
    db.commit(); db.refresh(obj); return obj
@router.delete('/{contribution_id}',status_code=204)
def delete_contribution(contribution_id:int,db:DB,user:CurrentUser):
    if user.role!=UserRole.TREASURER: raise HTTPException(403,'Treasurer access required')
    obj=db.get(Contribution,contribution_id)
    if not obj or obj.group_id!=user.group_id or (user.role==UserRole.MEMBER and obj.member_id!=user.id): raise HTTPException(404,'Contribution not found')
    db.delete(obj); db.commit()
