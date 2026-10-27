from datetime import date


def create_treasurer(client, email="treasurer@example.com", group="Test Group"):
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "full_name": "Treasurer",
            "email": email,
            "password": "StrongPass123!",
            "group_name": group,
            "weekly_contribution": 100,
        },
    )
    assert response.status_code == 200
    data = response.json()
    return {
        "headers": {"Authorization": f"Bearer {data['tokens']['access_token']}"},
        "user": data["user"],
    }


def create_member(client, treasurer_headers, email="member@example.com"):
    response = client.post(
        "/api/v1/users/members",
        headers=treasurer_headers,
        json={
            "full_name": "Test Member",
            "email": email,
            "temporary_password": "TempPass123!",
        },
    )
    assert response.status_code == 200
    return response.json()


def test_treasurer_records_contribution(client):
    treasurer = create_treasurer(client)
    member = create_member(client, treasurer["headers"])

    response = client.post(
        "/api/v1/contributions",
        headers=treasurer["headers"],
        json={
            "member_id": member["id"],
            "amount": 100,
            "paid_at": str(date.today()),
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["member_id"] == member["id"]
    assert data["amount"] == 100
    assert data["group_id"] == treasurer["user"]["group_id"]


def test_contribution_rejects_nonexistent_member(client):
    treasurer = create_treasurer(client)

    response = client.post(
        "/api/v1/contributions",
        headers=treasurer["headers"],
        json={
            "member_id": 9999,
            "amount": 100,
            "paid_at": str(date.today()),
        },
    )

    assert response.status_code == 404


def test_contribution_rejects_nonpositive_amount(client):
    treasurer = create_treasurer(client)
    member = create_member(client, treasurer["headers"])

    response = client.post(
        "/api/v1/contributions",
        headers=treasurer["headers"],
        json={
            "member_id": member["id"],
            "amount": 0,
            "paid_at": str(date.today()),
        },
    )

    assert response.status_code == 422


def test_treasurer_can_create_loan_within_limits(client):
    treasurer = create_treasurer(client)
    member = create_member(client, treasurer["headers"])

    contribution = client.post(
        "/api/v1/contributions",
        headers=treasurer["headers"],
        json={
            "member_id": member["id"],
            "amount": 500,
            "paid_at": str(date.today()),
        },
    )
    assert contribution.status_code == 200

    response = client.post(
        "/api/v1/loans",
        headers=treasurer["headers"],
        json={
            "member_id": member["id"],
            "principal": 200,
            "due_date": str(date.today()),
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["member_id"] == member["id"]
    assert data["principal"] == 200
    assert data["interest_rate"] == 10
    assert data["interest_amount"] == 20


def test_loan_rejects_amount_above_member_limit(client):
    treasurer = create_treasurer(client)
    member = create_member(client, treasurer["headers"])

    contribution = client.post(
        "/api/v1/contributions",
        headers=treasurer["headers"],
        json={
            "member_id": member["id"],
            "amount": 100,
            "paid_at": str(date.today()),
        },
    )
    assert contribution.status_code == 200

    response = client.post(
        "/api/v1/loans",
        headers=treasurer["headers"],
        json={
            "member_id": member["id"],
            "principal": 300,
            "due_date": str(date.today()),
        },
    )

    assert response.status_code == 400


def test_loan_rejects_nonexistent_member(client):
    treasurer = create_treasurer(client)

    response = client.post(
        "/api/v1/loans",
        headers=treasurer["headers"],
        json={
            "member_id": 9999,
            "principal": 100,
            "due_date": str(date.today()),
        },
    )

    assert response.status_code == 404


def test_member_cannot_create_loan(client):
    treasurer = create_treasurer(client)
    member = create_member(client, treasurer["headers"])

    login = client.post(
        "/api/v1/auth/login",
        data={
            "username": member["email"],
            "password": "TempPass123!",
        },
    )
    assert login.status_code == 200

    response = client.post(
        "/api/v1/loans",
        headers={"Authorization": f"Bearer {login.json()['access_token']}"},
        json={
            "member_id": member["id"],
            "principal": 100,
            "due_date": str(date.today()),
        },
    )

    assert response.status_code == 403


def test_treasurer_records_repayment(client):
    treasurer = create_treasurer(client)
    member = create_member(client, treasurer["headers"])

    contribution = client.post(
        "/api/v1/contributions",
        headers=treasurer["headers"],
        json={
            "member_id": member["id"],
            "amount": 500,
            "paid_at": str(date.today()),
        },
    )
    assert contribution.status_code == 200

    loan = client.post(
        "/api/v1/loans",
        headers=treasurer["headers"],
        json={
            "member_id": member["id"],
            "principal": 200,
            "due_date": str(date.today()),
        },
    )
    assert loan.status_code == 200

    response = client.post(
        "/api/v1/repayments",
        headers=treasurer["headers"],
        json={
            "loan_id": loan.json()["id"],
            "amount": 50,
            "paid_at": str(date.today()),
        },
    )

    assert response.status_code == 200
    assert response.json()["amount"] == 50
    assert response.json()["loan_id"] == loan.json()["id"]


def test_repayment_rejects_amount_above_balance(client):
    treasurer = create_treasurer(client)
    member = create_member(client, treasurer["headers"])

    client.post(
        "/api/v1/contributions",
        headers=treasurer["headers"],
        json={
            "member_id": member["id"],
            "amount": 500,
            "paid_at": str(date.today()),
        },
    )

    loan = client.post(
        "/api/v1/loans",
        headers=treasurer["headers"],
        json={
            "member_id": member["id"],
            "principal": 200,
            "due_date": str(date.today()),
        },
    )
    assert loan.status_code == 200

    response = client.post(
        "/api/v1/repayments",
        headers=treasurer["headers"],
        json={
            "loan_id": loan.json()["id"],
            "amount": 1000,
            "paid_at": str(date.today()),
        },
    )

    assert response.status_code == 400


def test_repayment_rejects_nonexistent_loan(client):
    treasurer = create_treasurer(client)

    response = client.post(
        "/api/v1/repayments",
        headers=treasurer["headers"],
        json={
            "loan_id": 9999,
            "amount": 50,
            "paid_at": str(date.today()),
        },
    )

    assert response.status_code == 404


def test_loan_balance_decreases_after_repayment(client):
    treasurer = create_treasurer(client)
    member = create_member(client, treasurer["headers"])

    client.post(
        "/api/v1/contributions",
        headers=treasurer["headers"],
        json={
            "member_id": member["id"],
            "amount": 500,
            "paid_at": str(date.today()),
        },
    )

    loan = client.post(
        "/api/v1/loans",
        headers=treasurer["headers"],
        json={
            "member_id": member["id"],
            "principal": 200,
            "due_date": str(date.today()),
        },
    )
    assert loan.status_code == 200

    loan_id = loan.json()["id"]
    headers = treasurer["headers"]

    before = client.get(
        f"/api/v1/loans/{loan_id}/balance",
        headers=headers,
    )
    assert before.status_code == 200

    repayment = client.post(
        "/api/v1/repayments",
        headers=headers,
        json={
            "loan_id": loan_id,
            "amount": 50,
            "paid_at": str(date.today()),
        },
    )
    assert repayment.status_code == 200

    after = client.get(
        f"/api/v1/loans/{loan_id}/balance",
        headers=headers,
    )
    assert after.status_code == 200
    assert after.json()["balance"] < before.json()["balance"]


def test_available_funds_reflect_contributions_and_loans(client):
    treasurer = create_treasurer(client)
    member = create_member(client, treasurer["headers"])
    headers = treasurer["headers"]

    client.post(
        "/api/v1/contributions",
        headers=headers,
        json={
            "member_id": member["id"],
            "amount": 500,
            "paid_at": str(date.today()),
        },
    )

    loan = client.post(
        "/api/v1/loans",
        headers=headers,
        json={
            "member_id": member["id"],
            "principal": 200,
            "due_date": str(date.today()),
        },
    )
    assert loan.status_code == 200

    response = client.get(
        "/api/v1/finance/available-funds",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["available_funds"] == 300
