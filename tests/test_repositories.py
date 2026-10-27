from types import SimpleNamespace
from unittest.mock import MagicMock

from app.models.contribution import Contribution
from app.models.loan import Loan
from app.models.password_reset_token import PasswordResetToken
from app.models.refresh_token import RefreshToken
from app.models.repayment import Repayment
from app.repositories.base import BaseRepository
from app.repositories.contribution_repository import contribution_repository
from app.repositories.loan_repository import loan_repository
from app.repositories.password_reset_token_repository import (
    password_reset_token_repository,
)
from app.repositories.refresh_token_repository import refresh_token_repository
from app.repositories.repayment_repository import repayment_repository


def test_base_repository_get_returns_record():
    repository = BaseRepository(Contribution)
    db = MagicMock()
    record = Contribution()
    db.get.return_value = record

    result = repository.get(db, 1)

    assert result is record
    db.get.assert_called_once_with(Contribution, 1)


def test_base_repository_get_returns_none_when_missing():
    repository = BaseRepository(Contribution)
    db = MagicMock()
    db.get.return_value = None

    result = repository.get(db, 999)

    assert result is None
    db.get.assert_called_once_with(Contribution, 999)


def test_base_repository_list_returns_items_and_total():
    repository = BaseRepository(Contribution)
    db = MagicMock()
    records = [Contribution(), Contribution()]

    count_result = MagicMock()
    count_result.scalar_one.return_value = 5

    items_result = MagicMock()
    items_result.scalars.return_value.all.return_value = records

    db.execute.side_effect = [count_result, items_result]

    items, total = repository.list(db, page=2, size=2)

    assert items == records
    assert total == 5
    assert db.execute.call_count == 2


def test_base_repository_list_accepts_filters():
    repository = BaseRepository(Contribution)
    db = MagicMock()

    count_result = MagicMock()
    count_result.scalar_one.return_value = 1

    items_result = MagicMock()
    items_result.scalars.return_value.all.return_value = [Contribution()]

    db.execute.side_effect = [count_result, items_result]

    items, total = repository.list(
        db,
        filters=[],
        page=1,
        size=10,
    )

    assert len(items) == 1
    assert total == 1
    assert db.execute.call_count == 2


def test_base_repository_list_uses_default_pagination():
    repository = BaseRepository(Contribution)
    db = MagicMock()

    count_result = MagicMock()
    count_result.scalar_one.return_value = 0

    items_result = MagicMock()
    items_result.scalars.return_value.all.return_value = []

    db.execute.side_effect = [count_result, items_result]

    items, total = repository.list(db)

    assert items == []
    assert total == 0
    assert db.execute.call_count == 2


def test_base_repository_create_adds_and_flushes_object():
    repository = BaseRepository(Contribution)
    db = MagicMock()
    record = SimpleNamespace(amount=500)

    result = repository.create(db, record)

    assert result is record
    db.add.assert_called_once_with(record)
    db.flush.assert_called_once_with()


def test_base_repository_update_sets_attributes_and_flushes():
    repository = BaseRepository(Contribution)
    db = MagicMock()
    record = SimpleNamespace(amount=500, description="Original")

    result = repository.update(
        db,
        record,
        {"amount": 750, "description": "Updated"},
    )

    assert result is record
    assert record.amount == 750
    assert record.description == "Updated"
    db.flush.assert_called_once_with()


def test_base_repository_update_accepts_empty_values():
    repository = BaseRepository(Contribution)
    db = MagicMock()
    record = SimpleNamespace(amount=500)

    result = repository.update(db, record, {})

    assert result is record
    assert record.amount == 500
    db.flush.assert_called_once_with()


def test_base_repository_delete_deletes_and_flushes():
    repository = BaseRepository(Contribution)
    db = MagicMock()
    record = Contribution()

    repository.delete(db, record)

    db.delete.assert_called_once_with(record)
    db.flush.assert_called_once_with()


def test_contribution_repository_uses_contribution_model():
    assert isinstance(contribution_repository, BaseRepository)
    assert contribution_repository.model is Contribution


def test_loan_repository_uses_loan_model():
    assert isinstance(loan_repository, BaseRepository)
    assert loan_repository.model is Loan


def test_password_reset_token_repository_uses_correct_model():
    assert isinstance(password_reset_token_repository, BaseRepository)
    assert password_reset_token_repository.model is PasswordResetToken


def test_refresh_token_repository_uses_correct_model():
    assert isinstance(refresh_token_repository, BaseRepository)
    assert refresh_token_repository.model is RefreshToken


def test_repayment_repository_uses_repayment_model():
    assert isinstance(repayment_repository, BaseRepository)
    assert repayment_repository.model is Repayment
