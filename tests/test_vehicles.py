import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app import create_app
from app.models import db
import uuid


@pytest.fixture
def client():
    app = create_app("TestingConfig")
    app.config["TESTING"] = True
    with app.app_context():
        db.drop_all()
        db.create_all()
        yield app.test_client()


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
    response = client.post("/vehicles/", json=create_test_vehicle(customer_id))
    assert response.status_code == 201
    assert response.json["make"] == "Honda"
    assert response.json["customer_id"] == customer_id


def test_create_vehicle_invalid_customer(client):
    response = client.post("/vehicles/", json=create_test_vehicle(9999))
    assert response.status_code == 404
    assert "customer" in response.json.get("error", "").lower()


def test_create_vehicle_duplicate_vin(client):
    customer_id, _ = create_customer(client)
    vehicle_data = create_test_vehicle(customer_id)
    client.post("/vehicles/", json=vehicle_data)
    response = client.post("/vehicles/", json=vehicle_data)
    assert response.status_code == 400
    assert "already exists" in response.json.get("error", "").lower()


# SERVICE TICKET WITH VEHICLE_ID
def test_create_ticket_with_valid_vehicle_id(client):
    customer_id, _ = create_customer(client)
    vehicle_res = client.post("/vehicles/", json=create_test_vehicle(customer_id))
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
