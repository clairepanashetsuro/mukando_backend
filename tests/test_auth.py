
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

