
from collections import defaultdict
from datetime import date, datetime, time, timedelta

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import func, select

from app.dependencies import DB, CurrentUser
from app.models.contribution import Contribution
from app.models.loan import Loan, LoanStatus
from app.models.repayment import Repayment
from app.models.user import User, UserRole
from app.services.loan_service import loan_balance

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/me")
def member_report(db: DB, user: CurrentUser):
    if user.role != UserRole.MEMBER:
        raise HTTPException(403, "Member access required")

    contributions = float(
        db.execute(
            select(func.coalesce(func.sum(Contribution.amount), 0)).where(
                Contribution.member_id == user.id,
                Contribution.group_id == user.group_id,
            )
        ).scalar_one()
    )

    repayments = float(
        db.execute(
            select(func.coalesce(func.sum(Repayment.amount), 0)).where(
                Repayment.member_id == user.id,
                Repayment.group_id == user.group_id,
            )
        ).scalar_one()
    )

    loans = (
        db.execute(
            select(Loan).where(
                Loan.member_id == user.id,
                Loan.group_id == user.group_id,
                Loan.status == LoanStatus.ACTIVE,
            )
        )
        .scalars()
        .all()
    )

    outstanding = sum(
        (loan_balance(db, loan) for loan in loans),
        start=0,
    )

    return {
        "total_contributions": contributions,
        "total_repayments": repayments,
        "outstanding_balance": float(outstanding),
        "outstanding_loans": len(loans),
    }


@router.get("/summary")
def summary(db: DB, user: CurrentUser):
    if user.role != UserRole.TREASURER:
        raise HTTPException(403, "Treasurer access required")

    contributions = float(
        db.execute(
            select(func.coalesce(func.sum(Contribution.amount), 0)).where(
                Contribution.group_id == user.group_id
            )
        ).scalar_one()
    )

    repayments = float(
        db.execute(
            select(func.coalesce(func.sum(Repayment.amount), 0)).where(
                Repayment.group_id == user.group_id
            )
        ).scalar_one()
    )

    active_loans = (
        db.execute(
            select(Loan).where(
                Loan.group_id == user.group_id,
                Loan.status == LoanStatus.ACTIVE,
            )
        )
        .scalars()
        .all()
    )

    outstanding = sum(
        (float(loan_balance(db, loan)) for loan in active_loans),
        start=0.0,
    )

    members = int(
        db.execute(
            select(func.count())
            .select_from(User)
            .where(
                User.group_id == user.group_id,
                User.role == UserRole.MEMBER,
            )
        ).scalar_one()
    )

    return {
        "members": members,
        "total_contributions": contributions,
        "total_repayments": repayments,
        "outstanding_loans": round(outstanding, 2),
        "active_loans": len(active_loans),
    }


@router.get("/analytics")
def analytics(
    db: DB,
    user: CurrentUser,
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
):
    if user.role != UserRole.TREASURER:
        raise HTTPException(403, "Treasurer access required")

    if start_date and end_date and start_date > end_date:
        raise HTTPException(400, "Start date cannot be after end date")

    group_id = user.group_id

    contribution_filters = [Contribution.group_id == group_id]
    repayment_filters = [Repayment.group_id == group_id]
    loan_filters = [Loan.group_id == group_id]

    if start_date:
        contribution_filters.append(
            Contribution.paid_at >= start_date
        )
        repayment_filters.append(
            Repayment.paid_at >= start_date
        )
        loan_filters.append(
            Loan.created_at >= datetime.combine(start_date, time.min)
        )

    if end_date:
        contribution_filters.append(
            Contribution.paid_at <= end_date
        )
        repayment_filters.append(
            Repayment.paid_at <= end_date
        )
        loan_filters.append(
            Loan.created_at < datetime.combine(
                end_date + timedelta(days=1),
                time.min,
            )
        )

    contributions = db.execute(
        select(func.coalesce(func.sum(Contribution.amount), 0))
        .where(*contribution_filters)
    ).scalar_one()

    repayments = db.execute(
        select(func.coalesce(func.sum(Repayment.amount), 0))
        .where(*repayment_filters)
    ).scalar_one()

    loans_issued = db.execute(
        select(func.coalesce(func.sum(Loan.principal), 0))
        .where(*loan_filters)
    ).scalar_one()

    members = db.execute(
        select(User).where(
            User.group_id == group_id,
            User.role == UserRole.MEMBER,
        )
    ).scalars().all()

    member_data = {
        member.id: {
            "member_id": member.id,
            "member_name": member.full_name,
            "contributions": 0.0,
            "loans_issued": 0.0,
            "repayments": 0.0,
        }
        for member in members
    }

    monthly_data = defaultdict(
        lambda: {
            "contributions": 0.0,
            "loans_issued": 0.0,
            "repayments": 0.0,
        }
    )

    contribution_rows = db.execute(
        select(
            Contribution.member_id,
            Contribution.paid_at,
            func.sum(Contribution.amount),
        )
        .where(*contribution_filters)
        .group_by(
            Contribution.member_id,
            Contribution.paid_at,
        )
    ).all()

    for member_id, paid_at, amount in contribution_rows:
        value = float(amount)
        month = paid_at.strftime("%Y-%m")

        monthly_data[month]["contributions"] += value
        member_data[member_id]["contributions"] += value

    loan_month = func.date_trunc("month", Loan.created_at)

    loan_rows = db.execute(
        select(
            Loan.member_id,
            loan_month,
            func.sum(Loan.principal),
        )
        .where(*loan_filters)
        .group_by(
            Loan.member_id,
            loan_month,
        )
    ).all()

    for member_id, month_date, amount in loan_rows:
        value = float(amount)
        month = month_date.strftime("%Y-%m")

        monthly_data[month]["loans_issued"] += value
        member_data[member_id]["loans_issued"] += value

    repayment_rows = db.execute(
        select(
            Repayment.member_id,
            Repayment.paid_at,
            func.sum(Repayment.amount),
        )
        .where(*repayment_filters)
        .group_by(
            Repayment.member_id,
            Repayment.paid_at,
        )
    ).all()

    for member_id, paid_at, amount in repayment_rows:
        value = float(amount)
        month = paid_at.strftime("%Y-%m")

        monthly_data[month]["repayments"] += value
        member_data[member_id]["repayments"] += value

    monthly = [
        {
            "month": month,
            **{
                key: round(value, 2)
                for key, value in values.items()
            },
        }
        for month, values in sorted(monthly_data.items())
    ]

    active_loans = db.execute(
        select(Loan).where(
            Loan.group_id == group_id,
            Loan.status == LoanStatus.ACTIVE,
        )
    ).scalars().all()

    outstanding_balance = sum(
        (
            float(loan_balance(db, loan))
            for loan in active_loans
        ),
        start=0.0,
    )

    return {
        "period": {
            "start_date": (
                start_date.isoformat() if start_date else None
            ),
            "end_date": (
                end_date.isoformat() if end_date else None
            ),
        },
        "totals": {
            "contributions": round(float(contributions), 2),
            "loans_issued": round(float(loans_issued), 2),
            "repayments": round(float(repayments), 2),
        },
        "monthly": monthly,
        "members": [
            {
                **member,
                "contributions": round(member["contributions"], 2),
                "loans_issued": round(member["loans_issued"], 2),
                "repayments": round(member["repayments"], 2),
            }
            for member in member_data.values()
        ],
        "current_outstanding_balance": round(
            outstanding_balance, 2
        ),
    }
