import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app import create_app
from app.models import db
from app.utils.util import encode_token
import uuid


@pytest.fixture
def client():
    app = create_app("TestingConfig")
    app.config["TESTING"] = True
    with app.app_context():
        db.drop_all()
        db.create_all()
        yield app.test_client()


# HELPER TO BUILD AUTH HEADERS FOR A CUSTOMER (mints a token directly so tests
# do not use up the login rate limit)
def auth_headers(customer_id):
    return {"Authorization": f"Bearer {encode_token(customer_id)}"}


# HELPER TO CREATE CUSTOMER
def create_customer(client):
    email = f"user_{uuid.uuid4().hex[:6]}@test.com"
    response = client.post(
        "/customers/",
        json={
            "name": "Test User",
            "email": email,
            "phone": "555-123-4567",
            "password": "securepassword",
        },
    )
    assert response.status_code == 201
    return response.json["id"], email


# HELPER TO CREATE VEHICLE
def create_test_vehicle(customer_id):
    return {
        "VIN": f"1HGCM82633A{uuid.uuid4().hex[:6].upper()}",
        "make": "Honda",
        "model": "Accord",
        "year": 2020,
        "customer_id": customer_id,
    }


# CREATE VEHICLE TESTS
def test_create_vehicle(client):
    customer_id, _ = create_customer(client)
    response = client.post(
        "/vehicles/",
        json=create_test_vehicle(customer_id),
        headers=auth_headers(customer_id),
    )
    assert response.status_code == 201
    assert response.json["make"] == "Honda"
    assert response.json["customer_id"] == customer_id


def test_create_vehicle_invalid_customer(client):
    response = client.post(
        "/vehicles/", json=create_test_vehicle(9999), headers=auth_headers(9999)
    )
    assert response.status_code == 404
    assert "customer" in response.json.get("error", "").lower()


def test_create_vehicle_duplicate_vin(client):
    customer_id, _ = create_customer(client)
    vehicle_data = create_test_vehicle(customer_id)
    headers = auth_headers(customer_id)
    client.post("/vehicles/", json=vehicle_data, headers=headers)
    response = client.post("/vehicles/", json=vehicle_data, headers=headers)
    assert response.status_code == 400
    assert "already exists" in response.json.get("error", "").lower()


# SERVICE TICKET WITH VEHICLE_ID
def test_create_ticket_with_valid_vehicle_id(client):
    customer_id, _ = create_customer(client)
    vehicle_res = client.post(
        "/vehicles/",
        json=create_test_vehicle(customer_id),
        headers=auth_headers(customer_id),
    )
    vehicle_id = vehicle_res.json["id"]

    ticket_data = {
        "vehicle_id": vehicle_id,
        "service_desc": "Oil change",
        "service_date": "2025-07-15",
        "customer_id": customer_id,
    }
    response = client.post("/service_tickets/", json=ticket_data)
    assert response.status_code == 201
    assert response.json["vehicle_id"] == vehicle_id


def test_create_ticket_with_invalid_vehicle_id(client):
    customer_id, _ = create_customer(client)

    ticket_data = {
        "vehicle_id": 9999,
        "service_desc": "Oil change",
        "service_date": "2025-07-15",
        "customer_id": customer_id,
    }
    response = client.post("/service_tickets/", json=ticket_data)
    assert response.status_code == 404
    assert "vehicle" in response.json.get("error", "").lower()


# VEHICLE AUTH AND OWNERSHIP TESTS
def test_create_vehicle_requires_token(client):
    customer_id, _ = create_customer(client)
    response = client.post("/vehicles/", json=create_test_vehicle(customer_id))
    assert response.status_code == 401


def test_create_vehicle_for_another_customer_forbidden(client):
    owner_id, _ = create_customer(client)
    other_id, _ = create_customer(client)
    response = client.post(
        "/vehicles/",
        json=create_test_vehicle(owner_id),
        headers=auth_headers(other_id),
    )
    assert response.status_code == 403


def test_update_and_delete_own_vehicle(client):
    customer_id, _ = create_customer(client)
    headers = auth_headers(customer_id)
    created = client.post(
        "/vehicles/", json=create_test_vehicle(customer_id), headers=headers
    )
    vehicle_id = created.json["id"]

    updated_data = create_test_vehicle(customer_id)
    updated_data["make"] = "Toyota"
    update = client.put(f"/vehicles/{vehicle_id}", json=updated_data, headers=headers)
    assert update.status_code == 200
    assert update.json["make"] == "Toyota"

    delete = client.delete(f"/vehicles/{vehicle_id}", headers=headers)
    assert delete.status_code == 200


def test_update_and_delete_vehicle_require_token(client):
    customer_id, _ = create_customer(client)
    created = client.post(
        "/vehicles/",
        json=create_test_vehicle(customer_id),
        headers=auth_headers(customer_id),
    )
    vehicle_id = created.json["id"]

    update = client.put(
        f"/vehicles/{vehicle_id}", json=create_test_vehicle(customer_id)
    )
    delete = client.delete(f"/vehicles/{vehicle_id}")
    assert update.status_code == 401
    assert delete.status_code == 401


def test_cannot_modify_or_delete_another_customers_vehicle(client):
    owner_id, _ = create_customer(client)
    other_id, _ = create_customer(client)
    created = client.post(
        "/vehicles/",
        json=create_test_vehicle(owner_id),
        headers=auth_headers(owner_id),
    )
    vehicle_id = created.json["id"]

    update = client.put(
        f"/vehicles/{vehicle_id}",
        json=create_test_vehicle(other_id),
        headers=auth_headers(other_id),
    )
    delete = client.delete(f"/vehicles/{vehicle_id}", headers=auth_headers(other_id))
    assert update.status_code == 403
    assert delete.status_code == 403


def test_cannot_reassign_own_vehicle_to_another_customer(client):
    customer_id, _ = create_customer(client)
    other_id, _ = create_customer(client)
    headers = auth_headers(customer_id)
    created = client.post(
        "/vehicles/", json=create_test_vehicle(customer_id), headers=headers
    )
    vehicle_id = created.json["id"]

    response = client.put(
        f"/vehicles/{vehicle_id}",
        json=create_test_vehicle(other_id),
        headers=headers,
    )
    assert response.status_code == 403
