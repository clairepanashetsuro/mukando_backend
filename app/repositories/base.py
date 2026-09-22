from sqlalchemy import func, select


class BaseRepository:
    def __init__(self, model):
        self.model = model

    def get(self, db, item_id):
        return db.get(self.model, item_id)

    def list(self, db, *, filters=None, page=1, size=20):
        filters = filters or []
        count_q = select(func.count()).select_from(self.model).where(*filters)
        total = db.execute(count_q).scalar_one()
        q = (
            select(self.model)
            .where(*filters)
            .offset((page - 1) * size)
            .limit(size)
        )
        items = db.execute(q).scalars().all()
        return items, total

    def create(self, db, obj):
        db.add(obj)
        db.flush()
        return obj

    def update(self, db, obj, values):
        for key, value in values.items():
            setattr(obj, key, value)
        db.flush()
        return obj

    def delete(self, db, obj):
        db.delete(obj)
        db.flush()
