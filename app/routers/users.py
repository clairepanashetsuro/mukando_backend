from math import ceil
from fastapi import APIRouter, Query
from sqlalchemy import select
from app.dependencies import DB, CurrentUser
from app.models.user import User, UserRole
from app.schemas.user import UserRead, UserUpdate, PasswordChange, MemberCreate
from app.services.user_service import update_profile, change_password, create_member
router=APIRouter(prefix='/users',tags=['users'])
@router.get('/me',response_model=UserRead)
def me(user:CurrentUser): return user
@router.patch('/me',response_model=UserRead)
def edit_me(data:UserUpdate,db:DB,user:CurrentUser): return update_profile(db,user,data)
@router.post('/me/password',status_code=204)
def password(data:PasswordChange,db:DB,user:CurrentUser): change_password(db,user,data.current_password,data.new_password)
@router.post('/members',response_model=UserRead)
def add_member(data:MemberCreate,db:DB,user:CurrentUser):
    if user.role != UserRole.TREASURER: from fastapi import HTTPException; raise HTTPException(403,'Treasurer access required')
    return create_member(db,user,data)
@router.get('/members',response_model=dict)
def members(db:DB,user:CurrentUser,page:int=Query(1,ge=1),size:int=Query(20,ge=1,le=100)):
    from fastapi import HTTPException
    if user.role != UserRole.TREASURER: raise HTTPException(403,'Treasurer access required')
    q=select(User).where(User.group_id==user.group_id,User.role==UserRole.MEMBER)
    total=len((db.execute(q)).scalars().all()); items=(db.execute(q.offset((page-1)*size).limit(size))).scalars().all()
    return {'items':items,'total':total,'page':page,'size':size,'pages':ceil(total/size) if total else 0}
@router.get('/members/{member_id}',response_model=UserRead)
def get_member(member_id:int,db:DB,user:CurrentUser):
    from fastapi import HTTPException
    if user.role!=UserRole.TREASURER: raise HTTPException(403,'Treasurer access required')
    obj=db.get(User,member_id)
    if not obj or obj.group_id!=user.group_id or obj.role!=UserRole.MEMBER: raise HTTPException(404,'Member not found')
    return obj
@router.patch('/members/{member_id}',response_model=UserRead)
def update_member(member_id:int,data:UserUpdate,db:DB,user:CurrentUser):
    from fastapi import HTTPException
    if user.role!=UserRole.TREASURER: raise HTTPException(403,'Treasurer access required')
    obj=db.get(User,member_id)
    if not obj or obj.group_id!=user.group_id or obj.role!=UserRole.MEMBER: raise HTTPException(404,'Member not found')
    return update_profile(db,obj,data)
@router.delete('/members/{member_id}',status_code=204)
def delete_member(member_id:int,db:DB,user:CurrentUser):
    from fastapi import HTTPException
    if user.role!=UserRole.TREASURER: raise HTTPException(403,'Treasurer access required')
    obj=db.get(User,member_id)
    if not obj or obj.group_id!=user.group_id or obj.role!=UserRole.MEMBER: raise HTTPException(404,'Member not found')
    obj.is_active=False; db.commit()
