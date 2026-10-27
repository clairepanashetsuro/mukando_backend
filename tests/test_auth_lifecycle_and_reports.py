import pytest


def create_treasurer(client, email="treasurer@example.com"):
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "full_name": "Test Treasurer",
            "email": email,
            "password": "StrongPass123!",
            "group_name": f"Group {email}",
            "weekly_contribution": 100,
        },
    )
    assert response.status_code == 200
    data = response.json()
    return data, {
        "Authorization": f"Bearer {data['tokens']['access_token']}"
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


def login_member(client, email="member@example.com"):
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": email,
            "password": "TempPass123!",
        },
    )
    assert response.status_code == 200
    return {
        "Authorization": f"Bearer {response.json()['access_token']}"
    }


def test_refresh_token_returns_new_tokens(client):
    signup, _ = create_treasurer(client)

    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": signup["tokens"]["refresh_token"]},
    )

    assert response.status_code == 200
    assert response.json()["access_token"]
    assert response.json()["refresh_token"]


def test_refresh_token_cannot_be_reused(client):
    signup, _ = create_treasurer(client)
    old_refresh_token = signup["tokens"]["refresh_token"]

    first = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": old_refresh_token},
    )
    assert first.status_code == 200

    second = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": old_refresh_token},
    )

    assert second.status_code == 401


def test_refresh_rejects_access_token(client):
    signup, _ = create_treasurer(client)

    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": signup["tokens"]["access_token"]},
    )

    assert response.status_code == 401


def test_refresh_rejects_invalid_token(client):
    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "invalid-refresh-token"},
    )

    assert response.status_code == 401


def test_logout_revokes_refresh_token(client):
    signup, _ = create_treasurer(client)
    refresh_token = signup["tokens"]["refresh_token"]

    logout = client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": refresh_token},
    )
    assert logout.status_code == 204

    refresh = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )

    assert refresh.status_code == 401


def test_forgot_password_unknown_email_returns_accepted(client):
    response = client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "unknown@example.com"},
    )

    assert response.status_code == 202


def test_forgot_password_sends_reset_email(client, monkeypatch):
    import app.services.auth_service as auth_service

    sent_emails = []

    monkeypatch.setattr(
        auth_service,
        "new_random_token",
        lambda: "test-reset-token",
    )
    monkeypatch.setattr(
        auth_service,
        "send_password_reset_email",
        lambda email, token: sent_emails.append((email, token)),
    )

    create_treasurer(client)

    response = client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "treasurer@example.com"},
    )

    assert response.status_code == 202
    assert sent_emails == [
        ("treasurer@example.com", "test-reset-token")
    ]


def test_reset_password_allows_login_with_new_password(client, monkeypatch):
    import app.services.auth_service as auth_service

    monkeypatch.setattr(
        auth_service,
        "new_random_token",
        lambda: "test-reset-token",
    )
    monkeypatch.setattr(
        auth_service,
        "send_password_reset_email",
        lambda email, token: None,
    )

    create_treasurer(client)

    forgot = client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "treasurer@example.com"},
    )
    assert forgot.status_code == 202

    reset = client.post(
        "/api/v1/auth/reset-password",
        json={
            "token": "test-reset-token",
            "new_password": "NewStrongPass123!",
        },
    )
    assert reset.status_code == 204

    login = client.post(
        "/api/v1/auth/login",
        data={
            "username": "treasurer@example.com",
            "password": "NewStrongPass123!",
        },
    )

    assert login.status_code == 200


def test_reset_password_token_cannot_be_reused(client, monkeypatch):
    import app.services.auth_service as auth_service

    monkeypatch.setattr(
        auth_service,
        "new_random_token",
        lambda: "single-use-reset-token",
    )
    monkeypatch.setattr(
        auth_service,
        "send_password_reset_email",
        lambda email, token: None,
    )

    create_treasurer(client)

    client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "treasurer@example.com"},
    )

    payload = {
        "token": "single-use-reset-token",
        "new_password": "NewStrongPass123!",
    }

    first = client.post("/api/v1/auth/reset-password", json=payload)
    assert first.status_code == 204

    second = client.post("/api/v1/auth/reset-password", json=payload)
    assert second.status_code == 400


def test_reset_password_rejects_invalid_token(client):
    response = client.post(
        "/api/v1/auth/reset-password",
        json={
            "token": "invalid-reset-token",
            "new_password": "NewStrongPass123!",
        },
    )

    assert response.status_code == 400


def test_treasurer_can_view_group_summary(client):
    _, headers = create_treasurer(client)

    response = client.get(
        "/api/v1/reports/summary",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["members"] == 0
    assert response.json()["total_contributions"] == 0
    assert response.json()["total_repayments"] == 0
    assert response.json()["outstanding_loans"] == 0
    assert response.json()["active_loans"] == 0


def test_member_cannot_view_group_summary(client):
    _, treasurer_headers = create_treasurer(client)
    create_member(client, treasurer_headers)

    member_headers = login_member(client)

    response = client.get(
        "/api/v1/reports/summary",
        headers=member_headers,
    )

    assert response.status_code == 403


def test_member_can_view_personal_report(client):
    _, treasurer_headers = create_treasurer(client)
    member = create_member(client, treasurer_headers)

    response = client.get(
        "/api/v1/reports/me",
        headers=login_member(client),
    )

    assert response.status_code == 200
    assert response.json() == {
        "total_contributions": 0,
        "total_repayments": 0,
        "outstanding_balance": 0,
        "outstanding_loans": 0,
    }


def test_treasurer_cannot_view_member_report(client):
    _, headers = create_treasurer(client)

    response = client.get(
        "/api/v1/reports/me",
        headers=headers,
    )

    assert response.status_code == 403
