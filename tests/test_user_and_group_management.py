import pytest


def create_treasurer(client, email="treasurer@example.com", group_name="Test Group"):
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "full_name": "Test Treasurer",
            "email": email,
            "password": "StrongPass123!",
            "group_name": group_name,
            "weekly_contribution": 100,
        },
    )
    assert response.status_code in (200, 201)
    token = response.json()["tokens"]["access_token"]
    return {"Authorization": f"Bearer {token}"}, response.json()


def create_member(client, headers, email="member@example.com"):
    response = client.post(
        "/api/v1/users/members",
        headers=headers,
        json={
            "full_name": "Test Member",
            "email": email,
            "temporary_password": "TempPass123!",
        },
    )
    assert response.status_code == 200
    return response.json()


def test_treasurer_can_view_own_group(client):
    headers, signup = create_treasurer(client)

    response = client.get("/api/v1/groups/me", headers=headers)

    assert response.status_code == 200
    assert response.json()["id"] == signup["user"]["group_id"] if "user" in signup else response.json()["id"] > 0
    assert response.json()["name"] == "Test Group"
    assert response.json()["weekly_contribution"] == 100


def test_treasurer_can_update_group_name(client):
    headers, _ = create_treasurer(client)

    response = client.patch(
        "/api/v1/groups/me",
        headers=headers,
        json={"name": "Updated Group"},
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Updated Group"


def test_treasurer_can_update_weekly_contribution(client):
    headers, _ = create_treasurer(client)

    response = client.patch(
        "/api/v1/groups/me",
        headers=headers,
        json={"weekly_contribution": 250},
    )

    assert response.status_code == 200
    assert response.json()["weekly_contribution"] == 250


def test_treasurer_cannot_use_duplicate_group_name(client):
    headers, _ = create_treasurer(client)
    create_treasurer(client, email="other@example.com", group_name="Other Group")

    response = client.patch(
        "/api/v1/groups/me",
        headers=headers,
        json={"name": "Other Group"},
    )

    assert response.status_code == 409


def test_member_cannot_update_group(client):
    treasurer_headers, _ = create_treasurer(client)
    member = create_member(client, treasurer_headers)

    login = client.post(
        "/api/v1/auth/login",
        data={
            "username": member["email"],
            "password": "TempPass123!",
        },
    )
    assert login.status_code == 200
    member_headers = {
        "Authorization": f"Bearer {login.json()['access_token']}"
    }

    response = client.patch(
        "/api/v1/groups/me",
        headers=member_headers,
        json={"name": "Unauthorized Group"},
    )

    assert response.status_code == 403


def test_treasurer_can_view_and_update_own_profile(client):
    headers, signup = create_treasurer(client)

    profile = client.get("/api/v1/users/me", headers=headers)
    assert profile.status_code == 200
    assert profile.json()["email"] == "treasurer@example.com"

    updated = client.patch(
        "/api/v1/users/me",
        headers=headers,
        json={"full_name": "Updated Treasurer"},
    )

    assert updated.status_code == 200
    assert updated.json()["full_name"] == "Updated Treasurer"


def test_member_email_must_be_unique(client):
    headers, _ = create_treasurer(client)
    create_member(client, headers)

    response = client.post(
        "/api/v1/users/members",
        headers=headers,
        json={
            "full_name": "Another Member",
            "email": "member@example.com",
            "temporary_password": "AnotherPass123!",
        },
    )

    assert response.status_code == 409


def test_treasurer_can_list_members(client):
    headers, _ = create_treasurer(client)
    create_member(client, headers, "first@example.com")
    create_member(client, headers, "second@example.com")

    response = client.get("/api/v1/users/members", headers=headers)

    assert response.status_code == 200
    assert response.json()["total"] == 2
    assert len(response.json()["items"]) == 2


def test_treasurer_can_get_member(client):
    headers, _ = create_treasurer(client)
    member = create_member(client, headers)

    response = client.get(
        f"/api/v1/users/members/{member['id']}",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["id"] == member["id"]


def test_treasurer_can_update_member(client):
    headers, _ = create_treasurer(client)
    member = create_member(client, headers)

    response = client.patch(
        f"/api/v1/users/members/{member['id']}",
        headers=headers,
        json={"full_name": "Updated Member"},
    )

    assert response.status_code == 200
    assert response.json()["full_name"] == "Updated Member"


def test_treasurer_can_deactivate_member(client):
    headers, _ = create_treasurer(client)
    member = create_member(client, headers)

    response = client.delete(
        f"/api/v1/users/members/{member['id']}",
        headers=headers,
    )

    assert response.status_code == 204

    profile = client.get(
        f"/api/v1/users/members/{member['id']}",
        headers=headers,
    )
    assert profile.status_code == 200
    assert profile.json()["is_active"] is False


def test_member_cannot_list_members(client):
    treasurer_headers, _ = create_treasurer(client)
    member = create_member(client, treasurer_headers)

    login = client.post(
        "/api/v1/auth/login",
        data={
            "username": member["email"],
            "password": "TempPass123!",
        },
    )
    assert login.status_code == 200
    member_headers = {
        "Authorization": f"Bearer {login.json()['access_token']}"
    }

    response = client.get("/api/v1/users/members", headers=member_headers)

    assert response.status_code == 403


def test_member_cannot_access_another_groups_member(client):
    first_headers, _ = create_treasurer(client, "first-treasurer@example.com", "First Group")
    second_headers, _ = create_treasurer(client, "second-treasurer@example.com", "Second Group")
    member = create_member(client, second_headers, "second-member@example.com")

    response = client.get(
        f"/api/v1/users/members/{member['id']}",
        headers=first_headers,
    )

    assert response.status_code == 404


def test_user_cannot_change_password_with_wrong_current_password(client):
    headers, _ = create_treasurer(client)

    response = client.post(
        "/api/v1/users/me/change-password",
        headers=headers,
        json={
            "current_password": "WrongPassword123!",
            "new_password": "NewStrongPass123!",
        },
    )

    assert response.status_code == 400


def test_user_can_change_password(client):
    headers, _ = create_treasurer(client)

    response = client.post(
        "/api/v1/users/me/change-password",
        headers=headers,
        json={
            "current_password": "StrongPass123!",
            "new_password": "NewStrongPass123!",
        },
    )

    assert response.status_code == 204
