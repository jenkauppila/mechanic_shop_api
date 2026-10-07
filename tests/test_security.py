import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app import create_app
from app.models import db


@pytest.fixture
def client():
    app = create_app("TestingConfig")
    app.config["TESTING"] = True
    with app.app_context():
        db.drop_all()
        db.create_all()
        yield app.test_client()


def register(client, n):
    return client.post(
        "/customers/",
        json={
            "name": f"Rate Test {n}",
            "email": f"rate{n}@test.com",
            "phone": "555-123-4567",
            "password": "securepassword",
        },
    )


# PASSWORD HASH SHOULD NEVER BE RETURNED
def test_password_not_returned_on_create(client):
    response = register(client, 1)
    assert response.status_code == 201
    assert "password" not in response.json


def test_password_not_returned_on_list(client):
    register(client, 1)
    response = client.get("/customers/")
    assert response.status_code == 200
    assert len(response.json) == 1
    assert all("password" not in customer for customer in response.json)


# LOGIN RATE LIMIT (slows password guessing)
def test_login_is_rate_limited(client):
    register(client, 1)
    credentials = {"email": "rate1@test.com", "password": "wrong-password"}
    statuses = [
        client.post("/customers/login", json=credentials).status_code for _ in range(6)
    ]
    assert statuses[:5] == [401] * 5
    assert statuses[5] == 429


# REGISTRATION RATE LIMIT (limits scripted account creation)
def test_registration_is_rate_limited(client):
    statuses = [register(client, n).status_code for n in range(6)]
    assert statuses[:5] == [201] * 5
    assert statuses[5] == 429


# GLOBAL DEFAULT LIMIT (routes with no limit of their own)
def test_default_limit_applies_to_unlimited_routes(client):
    statuses = [client.get("/vehicles/").status_code for _ in range(61)]
    assert statuses[:60] == [200] * 60
    assert statuses[60] == 429


# UPTIME CHECK AND API DOCS SHOULD NOT BE THROTTLED BY THE DEFAULT LIMIT
def test_health_check_is_exempt_from_default_limit(client):
    statuses = {client.get("/health").status_code for _ in range(70)}
    assert statuses == {200}


def test_swagger_ui_is_exempt_from_default_limit(client):
    statuses = {client.get("/api/docs/").status_code for _ in range(70)}
    assert 429 not in statuses


# UNPROTECTED WRITE ROUTES NOW HAVE THEIR OWN LIMITS
def test_service_ticket_delete_is_rate_limited(client):
    statuses = [client.delete(f"/service_tickets/{i}").status_code for i in range(6)]
    assert statuses[:5] == [404] * 5
    assert statuses[5] == 429


def test_mechanic_create_is_rate_limited(client):
    statuses = [
        client.post(
            "/mechanics/",
            json={
                "name": f"Mech {n}",
                "email": f"mech{n}@test.com",
                "phone": "555-123-4567",
                "salary": 50000,
            },
        ).status_code
        for n in range(21)
    ]
    assert statuses[:20] == [201] * 20
    assert statuses[20] == 429
