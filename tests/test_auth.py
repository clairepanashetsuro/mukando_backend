def test_treasurer_signup_and_login(client):
    payload = {
        "full_name": "Treasurer One",
        "email": "treasurer@example.com",
        "password": "StrongPass123!",
        "group_name": "Ubuntu Women",
        "weekly_contribution": 100,
    }

    r = client.post(
        "/api/v1/auth/signup",
        json=payload,
    )
    assert r.status_code == 200

    data = r.json()

    assert data["user"]["role"] == "TREASURER"
    assert data["tokens"]["access_token"]
    assert data["tokens"]["refresh_token"]

    r = client.post(
        "/api/v1/auth/login",
        data={
            "username": payload["email"],
            "password": payload["password"],
        },
    )
    assert r.status_code == 200


def test_login_rejects_unknown_user(client):
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "unknown@example.com",
            "password": "WrongPass123!",
        },
    )

    assert response.status_code == 401


def test_login_rejects_incorrect_password(client):
    payload = {
        "full_name": "Treasurer One",
        "email": "treasurer@example.com",
        "password": "StrongPass123!",
        "group_name": "Ubuntu Women",
        "weekly_contribution": 100,
    }

    signup = client.post("/api/v1/auth/signup", json=payload)
    assert signup.status_code == 200

    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": payload["email"],
            "password": "WrongPass123!",
        },
    )

    assert response.status_code == 401


def test_signup_rejects_missing_required_fields(client):
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": "incomplete@example.com",
        },
    )

    assert response.status_code == 422


def test_protected_endpoint_rejects_missing_token(client):
    response = client.get("/api/v1/users/members")

    assert response.status_code == 401


def test_protected_endpoint_rejects_invalid_token(client):
    response = client.get(
        "/api/v1/users/members",
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert response.status_code == 401
