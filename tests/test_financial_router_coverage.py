from datetime import date, timedelta


def create_treasurer(client, email="router.treasurer@example.com", group="Router Test Group"):
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
        "headers": {
            "Authorization": f"Bearer {data['tokens']['access_token']}"
        },
        "user": data["user"],
    }


def create_member(client, headers, email="router.member@example.com"):
    response = client.post(
        "/api/v1/users/members",
        headers=headers,
        json={
            "full_name": "Router Test Member",
            "email": email,
            "temporary_password": "TempPass123!",
        },
    )
    assert response.status_code == 200
    return response.json()


def login_member(client, member):
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": member["email"],
            "password": "TempPass123!",
        },
    )
    assert response.status_code == 200
    return {
        "Authorization": f"Bearer {response.json()['access_token']}"
    }


def create_contribution(client, headers, member_id, amount=500):
    response = client.post(
        "/api/v1/contributions",
        headers=headers,
        json={
            "member_id": member_id,
            "amount": amount,
            "paid_at": str(date.today()),
        },
    )
    assert response.status_code == 200
    return response.json()


def create_loan(client, headers, member_id, principal=200):
    response = client.post(
        "/api/v1/loans",
        headers=headers,
        json={
            "member_id": member_id,
            "principal": principal,
            "due_date": str(date.today() + timedelta(days=30)),
        },
    )
    assert response.status_code == 200
    return response.json()


def create_repayment(client, headers, loan_id, amount=50):
    response = client.post(
        "/api/v1/repayments",
        headers=headers,
        json={
            "loan_id": loan_id,
            "amount": amount,
            "paid_at": str(date.today()),
        },
    )
    assert response.status_code == 200
    return response.json()


def test_contributions_list_and_pagination(client):
    treasurer = create_treasurer(client)
    headers = treasurer["headers"]
    member = create_member(client, headers)

    create_contribution(client, headers, member["id"], 100)
    create_contribution(client, headers, member["id"], 200)

    response = client.get("/api/v1/contributions", headers=headers)

    assert response.status_code == 200
    assert response.json()["total"] == 2
    assert len(response.json()["items"]) == 2
    assert response.json()["pages"] == 1

    response = client.get(
        "/api/v1/contributions?page=1&size=1",
        headers=headers,
    )

    assert response.status_code == 200
    assert len(response.json()["items"]) == 1
    assert response.json()["total"] == 2
    assert response.json()["size"] == 1


def test_contribution_retrieve_update_and_delete(client):
    treasurer = create_treasurer(client)
    headers = treasurer["headers"]
    member = create_member(client, headers)
    contribution = create_contribution(client, headers, member["id"])

    contribution_id = contribution["id"]

    response = client.get(
        f"/api/v1/contributions/{contribution_id}",
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["id"] == contribution_id

    response = client.patch(
        f"/api/v1/contributions/{contribution_id}",
        headers=headers,
        json={"amount": 125},
    )
    assert response.status_code == 200
    assert response.json()["amount"] == 125

    response = client.delete(
        f"/api/v1/contributions/{contribution_id}",
        headers=headers,
    )
    assert response.status_code == 204

    response = client.get(
        f"/api/v1/contributions/{contribution_id}",
        headers=headers,
    )
    assert response.status_code == 404


def test_contribution_missing_record_returns_404(client):
    treasurer = create_treasurer(client)
    headers = treasurer["headers"]

    response = client.get("/api/v1/contributions/9999", headers=headers)
    assert response.status_code == 404

    response = client.patch(
        "/api/v1/contributions/9999",
        headers=headers,
        json={"amount": 125},
    )
    assert response.status_code == 404

    response = client.delete("/api/v1/contributions/9999", headers=headers)
    assert response.status_code == 404


def test_member_only_sees_own_contributions(client):
    treasurer = create_treasurer(client)
    headers = treasurer["headers"]
    first_member = create_member(
        client, headers, "first.router.member@example.com"
    )
    second_member = create_member(
        client, headers, "second.router.member@example.com"
    )

    create_contribution(client, headers, first_member["id"], 100)
    create_contribution(client, headers, second_member["id"], 200)

    member_headers = login_member(client, first_member)

    response = client.get(
        "/api/v1/contributions",
        headers=member_headers,
    )

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["member_id"] == first_member["id"]

    other_contribution = client.post(
        "/api/v1/contributions",
        headers=headers,
        json={
            "member_id": second_member["id"],
            "amount": 300,
            "paid_at": str(date.today()),
        },
    )
    assert other_contribution.status_code == 200

    response = client.get(
        f"/api/v1/contributions/{other_contribution.json()['id']}",
        headers=member_headers,
    )
    assert response.status_code == 404


def test_member_cannot_update_or_delete_contributions(client):
    treasurer = create_treasurer(client)
    headers = treasurer["headers"]
    member = create_member(client, headers)
    contribution = create_contribution(client, headers, member["id"])
    member_headers = login_member(client, member)
    contribution_id = contribution["id"]

    response = client.patch(
        f"/api/v1/contributions/{contribution_id}",
        headers=member_headers,
        json={"amount": 150},
    )
    assert response.status_code == 403

    response = client.delete(
        f"/api/v1/contributions/{contribution_id}",
        headers=member_headers,
    )
    assert response.status_code == 403


def test_contribution_pagination_validation(client):
    treasurer = create_treasurer(client)

    response = client.get(
        "/api/v1/contributions?page=0",
        headers=treasurer["headers"],
    )
    assert response.status_code == 422

    response = client.get(
        "/api/v1/contributions?size=101",
        headers=treasurer["headers"],
    )
    assert response.status_code == 422


def test_loans_list_and_pagination(client):
    treasurer = create_treasurer(client)
    headers = treasurer["headers"]
    member = create_member(client, headers)
    create_contribution(client, headers, member["id"], 1000)

    create_loan(client, headers, member["id"], 100)
    create_loan(client, headers, member["id"], 200)

    response = client.get("/api/v1/loans", headers=headers)

    assert response.status_code == 200
    assert response.json()["total"] == 2
    assert len(response.json()["items"]) == 2
    assert response.json()["pages"] == 1

    response = client.get(
        "/api/v1/loans?page=1&size=1",
        headers=headers,
    )

    assert response.status_code == 200
    assert len(response.json()["items"]) == 1
    assert response.json()["total"] == 2


def test_loan_retrieve_balance_update_and_delete(client):
    treasurer = create_treasurer(client)
    headers = treasurer["headers"]
    member = create_member(client, headers)
    create_contribution(client, headers, member["id"], 1000)
    loan = create_loan(client, headers, member["id"])
    loan_id = loan["id"]

    response = client.get(f"/api/v1/loans/{loan_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["id"] == loan_id

    response = client.get(
        f"/api/v1/loans/{loan_id}/balance",
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["loan_id"] == loan_id
    assert response.json()["balance"] > 0

    new_due_date = str(date.today() + timedelta(days=60))
    response = client.patch(
        f"/api/v1/loans/{loan_id}",
        headers=headers,
        json={"due_date": new_due_date},
    )
    assert response.status_code == 200
    assert response.json()["due_date"] == new_due_date

    response = client.delete(f"/api/v1/loans/{loan_id}", headers=headers)
    assert response.status_code == 204

    response = client.get(f"/api/v1/loans/{loan_id}", headers=headers)
    assert response.status_code == 404


def test_loan_missing_record_returns_404(client):
    treasurer = create_treasurer(client)
    headers = treasurer["headers"]

    response = client.get("/api/v1/loans/9999", headers=headers)
    assert response.status_code == 404

    response = client.get("/api/v1/loans/9999/balance", headers=headers)
    assert response.status_code == 404

    response = client.patch(
        "/api/v1/loans/9999",
        headers=headers,
        json={"due_date": str(date.today() + timedelta(days=30))},
    )
    assert response.status_code == 404

    response = client.delete("/api/v1/loans/9999", headers=headers)
    assert response.status_code == 404


def test_member_only_sees_own_loans(client):
    treasurer = create_treasurer(client)
    headers = treasurer["headers"]
    first_member = create_member(
        client, headers, "first.loan.member@example.com"
    )
    second_member = create_member(
        client, headers, "second.loan.member@example.com"
    )

    create_contribution(client, headers, first_member["id"], 1000)
    create_contribution(client, headers, second_member["id"], 1000)
    create_loan(client, headers, first_member["id"], 100)
    other_loan = create_loan(client, headers, second_member["id"], 100)

    member_headers = login_member(client, first_member)

    response = client.get("/api/v1/loans", headers=member_headers)

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["member_id"] == first_member["id"]

    response = client.get(
        f"/api/v1/loans/{other_loan['id']}",
        headers=member_headers,
    )
    assert response.status_code == 404

    response = client.get(
        f"/api/v1/loans/{other_loan['id']}/balance",
        headers=member_headers,
    )
    assert response.status_code == 404


def test_member_cannot_update_or_delete_loans(client):
    treasurer = create_treasurer(client)
    headers = treasurer["headers"]
    member = create_member(client, headers)
    create_contribution(client, headers, member["id"], 1000)
    loan = create_loan(client, headers, member["id"])
    member_headers = login_member(client, member)
    loan_id = loan["id"]

    response = client.patch(
        f"/api/v1/loans/{loan_id}",
        headers=member_headers,
        json={"due_date": str(date.today() + timedelta(days=60))},
    )
    assert response.status_code == 403

    response = client.delete(
        f"/api/v1/loans/{loan_id}",
        headers=member_headers,
    )
    assert response.status_code == 403


def test_loan_pagination_validation(client):
    treasurer = create_treasurer(client)
    headers = treasurer["headers"]

    response = client.get("/api/v1/loans?page=0", headers=headers)
    assert response.status_code == 422

    response = client.get("/api/v1/loans?size=101", headers=headers)
    assert response.status_code == 422


def test_repayments_list_and_pagination(client):
    treasurer = create_treasurer(client)
    headers = treasurer["headers"]
    member = create_member(client, headers)
    create_contribution(client, headers, member["id"], 1000)
    loan = create_loan(client, headers, member["id"])

    create_repayment(client, headers, loan["id"], 25)
    create_repayment(client, headers, loan["id"], 35)

    response = client.get("/api/v1/repayments", headers=headers)

    assert response.status_code == 200
    assert response.json()["total"] == 2
    assert len(response.json()["items"]) == 2
    assert response.json()["pages"] == 1

    response = client.get(
        "/api/v1/repayments?page=1&size=1",
        headers=headers,
    )

    assert response.status_code == 200
    assert len(response.json()["items"]) == 1
    assert response.json()["total"] == 2


def test_repayment_retrieve_update_and_delete(client):
    treasurer = create_treasurer(client)
    headers = treasurer["headers"]
    member = create_member(client, headers)
    create_contribution(client, headers, member["id"], 1000)
    loan = create_loan(client, headers, member["id"])
    repayment = create_repayment(client, headers, loan["id"])
    repayment_id = repayment["id"]

    response = client.get(
        f"/api/v1/repayments/{repayment_id}",
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["id"] == repayment_id

    response = client.patch(
        f"/api/v1/repayments/{repayment_id}",
        headers=headers,
        json={"amount": 40},
    )
    assert response.status_code == 200
    assert response.json()["amount"] == 40

    response = client.delete(
        f"/api/v1/repayments/{repayment_id}",
        headers=headers,
    )
    assert response.status_code == 204

    response = client.get(
        f"/api/v1/repayments/{repayment_id}",
        headers=headers,
    )
    assert response.status_code == 404


def test_repayment_missing_record_returns_404(client):
    treasurer = create_treasurer(client)
    headers = treasurer["headers"]

    response = client.get("/api/v1/repayments/9999", headers=headers)
    assert response.status_code == 404

    response = client.patch(
        "/api/v1/repayments/9999",
        headers=headers,
        json={"amount": 40},
    )
    assert response.status_code == 404

    response = client.delete("/api/v1/repayments/9999", headers=headers)
    assert response.status_code == 404


def test_member_only_sees_own_repayments(client):
    treasurer = create_treasurer(client)
    headers = treasurer["headers"]
    first_member = create_member(
        client, headers, "first.repayment.member@example.com"
    )
    second_member = create_member(
        client, headers, "second.repayment.member@example.com"
    )

    create_contribution(client, headers, first_member["id"], 1000)
    create_contribution(client, headers, second_member["id"], 1000)
    first_loan = create_loan(client, headers, first_member["id"], 200)
    second_loan = create_loan(client, headers, second_member["id"], 200)
    create_repayment(client, headers, first_loan["id"], 25)
    other_repayment = create_repayment(
        client, headers, second_loan["id"], 35
    )

    member_headers = login_member(client, first_member)

    response = client.get("/api/v1/repayments", headers=member_headers)

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["member_id"] == first_member["id"]

    response = client.get(
        f"/api/v1/repayments/{other_repayment['id']}",
        headers=member_headers,
    )
    assert response.status_code == 404


def test_member_cannot_update_or_delete_repayments(client):
    treasurer = create_treasurer(client)
    headers = treasurer["headers"]
    member = create_member(client, headers)
    create_contribution(client, headers, member["id"], 1000)
    loan = create_loan(client, headers, member["id"])
    repayment = create_repayment(client, headers, loan["id"])
    member_headers = login_member(client, member)
    repayment_id = repayment["id"]

    response = client.patch(
        f"/api/v1/repayments/{repayment_id}",
        headers=member_headers,
        json={"amount": 40},
    )
    assert response.status_code == 403

    response = client.delete(
        f"/api/v1/repayments/{repayment_id}",
        headers=member_headers,
    )
    assert response.status_code == 403


def test_repayment_pagination_validation(client):
    treasurer = create_treasurer(client)
    headers = treasurer["headers"]

    response = client.get("/api/v1/repayments?page=0", headers=headers)
    assert response.status_code == 422

    response = client.get("/api/v1/repayments?size=101", headers=headers)
    assert response.status_code == 422


def test_financial_records_are_isolated_between_groups(client):
    first_treasurer = create_treasurer(
        client,
        email="first.group.treasurer@example.com",
        group="First Router Group",
    )
    second_treasurer = create_treasurer(
        client,
        email="second.group.treasurer@example.com",
        group="Second Router Group",
    )

    first_headers = first_treasurer["headers"]
    second_headers = second_treasurer["headers"]

    first_member = create_member(
        client, first_headers, "first.group.member@example.com"
    )
    create_contribution(client, first_headers, first_member["id"], 500)
    first_loan = create_loan(client, first_headers, first_member["id"])
    first_repayment = create_repayment(
        client, first_headers, first_loan["id"]
    )

    contribution = client.get(
        "/api/v1/contributions/1",
        headers=second_headers,
    )
    assert contribution.status_code == 404

    loan = client.get(
        f"/api/v1/loans/{first_loan['id']}",
        headers=second_headers,
    )
    assert loan.status_code == 404

    balance = client.get(
        f"/api/v1/loans/{first_loan['id']}/balance",
        headers=second_headers,
    )
    assert balance.status_code == 404

    repayment = client.get(
        f"/api/v1/repayments/{first_repayment['id']}",
        headers=second_headers,
    )
    assert repayment.status_code == 404
