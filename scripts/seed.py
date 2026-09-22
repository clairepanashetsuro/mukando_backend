from app.database import Base, SessionLocal, engine
from app.schemas.user import TreasurerSignup
from app.services.auth_service import signup_treasurer


def main():
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        try:
            signup_treasurer(
                db,
                TreasurerSignup(
                    full_name="Demo Treasurer",
                    email="treasurer@example.com",
                    password="StrongPass123!",
                    group_name="Demo Group",
                    weekly_contribution=100,
                ),
            )
            print("Demo data created.")
        except Exception as exc:
            db.rollback()
            print(exc)


if __name__ == "__main__":
    main()
