from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.dependencies import DB, CurrentUser
from app.models.group import Group
from app.models.user import UserRole
from app.schemas.group import GroupRead, GroupUpdate
from app.repositories.group_repository import group_repository

router = APIRouter(prefix="/groups", tags=["groups"])


@router.get("/me", response_model=GroupRead)
def get_group(db: DB, user: CurrentUser):
    if not user.group_id:
        raise HTTPException(404, "No group")
    group = group_repository.get(db, user.group_id)
    if not group:
        raise HTTPException(404, "Group not found")
    return group


@router.patch("/me", response_model=GroupRead)
def update_group(data: GroupUpdate, db: DB, user: CurrentUser):
    if user.role != UserRole.TREASURER:
        raise HTTPException(403, "Treasurer access required")
    group = group_repository.get(db, user.group_id)
    if not group:
        raise HTTPException(404, "Group not found")

    values = data.model_dump(exclude_unset=True)
    if "name" in values and values["name"] != group.name:
        duplicate = db.execute(
            select(Group).where(Group.name == values["name"], Group.id != group.id)
        ).scalar_one_or_none()
        if duplicate:
            raise HTTPException(409, "Group name already exists")

    obj = group_repository.update(db, group, values)
    db.commit()
    db.refresh(obj)
    return obj
