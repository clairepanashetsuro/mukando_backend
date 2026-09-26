
def test_member_cannot_record_contribution(client):
    payload = {
        "full_name": "Treasurer",
        "email": "t@example.com",
        "password": "StrongPass123!",
        "group_name": "Group Test",
        "weekly_contribution": 100,
    }

    signup = client.post(
        "/api/v1/auth/signup",
        json=payload,
    )

    assert signup.status_code == 200

    auth = signup.json()

    headers = {
        "Authorization": f"Bearer {auth['tokens']['access_token']}"
    }

    member_response = client.post(
        "/api/v1/users/members",
        headers=headers,
        json={
            "full_name": "Member",
            "email": "m@example.com",
            "temporary_password": "TempPass123!",
        },
    )

    assert member_response.status_code == 200

    member = member_response.json()

    login = client.post(
        "/api/v1/auth/login",
        data={
            "username": "m@example.com",
            "password": "TempPass123!",
        },
    )

    assert login.status_code == 200

    member_auth = login.json()

    member_headers = {
        "Authorization": f"Bearer {member_auth['access_token']}"
    }

    response = client.post(
        "/api/v1/contributions",
        headers=member_headers,
        json={
            "member_id": member["id"],
            "amount": 100,
            "paid_at": "2026-09-20",
        },
    )

    assert response.status_code == 403

