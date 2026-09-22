from fastapi import HTTPException
from sqlalchemy import select
from app.models.user import User, UserRole
from app.models.contribution import Contribution
def create(db,treasurer,data):
    member=(db.execute(select(User).where(User.id==data.member_id,User.group_id==treasurer.group_id,User.role==UserRole.MEMBER))).scalar_one_or_none()
    if not member: raise HTTPException(404,"Member not found in your group")
    if data.amount <= 0: raise HTTPException(400,"Amount must be positive")
    obj=Contribution(member_id=member.id,group_id=treasurer.group_id,amount=data.amount,paid_at=data.paid_at,recorded_by=treasurer.id); db.add(obj); db.commit(); db.refresh(obj); return obj
