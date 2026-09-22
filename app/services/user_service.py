from fastapi import HTTPException
from sqlalchemy import select
from app.models.user import User, UserRole
from app.core.security import hash_password, verify_password
def create_member(db, treasurer, data):
    if (db.execute(select(User).where(User.email==data.email))).scalar_one_or_none(): raise HTTPException(409,"Email already registered")
    user=User(full_name=data.full_name,email=data.email,password_hash=hash_password(data.temporary_password),role=UserRole.MEMBER,group_id=treasurer.group_id,must_change_password=True); db.add(user); db.commit(); db.refresh(user); return user
def update_profile(db,user,data):
    if data.email and data.email != user.email and (db.execute(select(User).where(User.email==data.email,User.id!=user.id))).scalar_one_or_none(): raise HTTPException(409,"Email already registered")
    for k,v in data.model_dump(exclude_unset=True).items(): setattr(user,k,v)
    db.commit(); db.refresh(user); return user
def change_password(db,user,current,new):
    if not verify_password(current,user.password_hash): raise HTTPException(400,"Current password is incorrect")
    user.password_hash=hash_password(new); user.must_change_password=False; db.commit()
