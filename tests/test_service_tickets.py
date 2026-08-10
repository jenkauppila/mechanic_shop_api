from urllib import response
import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app import create_app
from app.models import db
from flask import current_app
import uuid  # is this necessary?

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


# HELPER TO CREATE MECHANIC
def create_mechanic(client):
    response = client.post(
        "/mechanics/",
        json={
            "name": "Jane Wrench",
            "email": f"mech_{uuid.uuid4().hex[:6]}@test.com",
            "phone": "555-987-6543",
            "salary": 60000,
        },
    )
    assert response.status_code == 201
    return response.json["id"]


# HELPER TO CREATE INVENTORY ITEM
def create_inventory_item(client):
    response = client.post(
        "/inventory/",
        json={
            "name": "Oil Filter",
            "price": 19.99,
        },
    )
    assert response.status_code == 201
    return response.json["id"]


# HELPER TO CREATE VEHICLE
def create_vehicle(client, customer_id):
    response = client.post(
        "/vehicles/",
        json={
            "VIN": f"1HGCM82633A{uuid.uuid4().hex[:6].upper()}",
            "make": "Honda",
            "model": "Accord",
            "year": 2020,
            "customer_id": customer_id,
        },
    )
    assert response.status_code == 201
    return response.json["id"]


# HELPER TO CREATE SERVICE TICKET
def create_ticket(customer_id, vehicle_id):
    return {
        "vehicle_id": vehicle_id,
        "service_desc": "Oil change",
        "service_date": "2025-07-15",
        "customer_id": customer_id,
    }


# ADD SERVICE TICKET
def test_create_ticket(client):
    customer_id, _ = create_customer(client)
    vehicle_id = create_vehicle(client, customer_id)
    response = client.post(
        "/service_tickets/", json=create_ticket(customer_id, vehicle_id)
    )
    assert response.status_code == 201
    assert "id" in response.json


def test_create_ticket_missing_fields(client):
    customer_id, _ = create_customer(client)
    vehicle_id = create_vehicle(client, customer_id)
    data = create_ticket(customer_id, vehicle_id)
    for key in ["vehicle_id", "service_desc", "service_date", "customer_id"]:
        payload = dict(data)
        payload.pop(key)
        res = client.post("/service_tickets/", json=payload)
        assert res.status_code == 400


def test_create_ticket_invalid_customer(client):
    data = create_ticket(9999, 9999)  # Invalid customer and vehicle IDs
    res = client.post("/service_tickets/", json=data)
    assert res.status_code == 404


# GET/SERVICE TICKETS
def test_get_all_tickets_empty(client):
    res = client.get("/service_tickets/")
    assert res.status_code == 200
    assert res.json == []


def test_get_all_tickets(client):
    customer_id, _ = create_customer(client)
    vehicle_id = create_vehicle(client, customer_id)
    client.post("/service_tickets/", json=create_ticket(customer_id, vehicle_id))
    res = client.get("/service_tickets/")
    assert res.status_code == 200
    assert isinstance(res.json, list)


def test_get_ticket_by_id(client):
    customer_id, _ = create_customer(client)
    vehicle_id = create_vehicle(client, customer_id)
    res = client.post("/service_tickets/", json=create_ticket(customer_id, vehicle_id))
    ticket_id = res.json["id"]
    response = client.get(f"/service_tickets/{ticket_id}")
    assert response.status_code == 200
    assert response.json["id"] == ticket_id


def test_get_ticket_invalid_id(client):
    res = client.get("/service_tickets/99999")
    assert res.status_code == 404


def test_get_my_tickets_with_token(client):
    customer_id, email = create_customer(client)
    vehicle_id = create_vehicle(client, customer_id)
    login = client.post(
        "/customers/login", json={"email": email, "password": "securepassword"}
    )
    token = login.json.get("auth_token")
    assert token
    client.post("/service_tickets/", json=create_ticket(customer_id, vehicle_id))
    res = client.get(
        "/service_tickets/my-tickets", headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 200
    assert isinstance(res.json, list)


def test_get_my_tickets_no_open_tickets(client):
    _, email = create_customer(client)
    login = client.post(
        "/customers/login", json={"email": email, "password": "securepassword"}
    )
    token = login.json.get("auth_token")
    assert token
    res = client.get(
        "/service_tickets/my-tickets", headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 200
    assert res.json["message"] == "No open service tickets found for this customer."


def test_get_my_tickets_invalid_token(client):
    response = client.get(
        "/service_tickets/my-tickets", headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401
    assert "invalid" in response.json.get("message", "").lower()


# UPDATE SERVICE TICKET - ADD/REMOVE MECHANICS AND INVENTORY
def test_update_ticket_combined_mechanics_inventory(client):
    customer_id, _ = create_customer(client)
    vehicle_id = create_vehicle(client, customer_id)
    ticket_data = create_ticket(customer_id, vehicle_id)
    res = client.post("/service_tickets/", json=ticket_data)
    ticket_id = res.json["id"]

    mechanic_id = create_mechanic(client)
    item_id = create_inventory_item(client)

    update_data = {
        "add_mechanic_ids": [mechanic_id],
        "remove_mechanic_ids": [],
        "add_item_ids": [{"item_id": item_id, "quantity": 3}],
        "remove_item_ids": [],
    }

    update_res = client.put(f"/service_tickets/{ticket_id}/edit", json=update_data)
    assert update_res.status_code == 200
    response = update_res.json["service_ticket"]

    # Assert mechanic and inventory item were added
    assert mechanic_id in [m["id"] for m in response["mechanics"]]
    assert item_id in [i["id"] for i in response["inventory_items"]]


def test_update_ticket_add_item_with_quantity(client):
    customer_id, _ = create_customer(client)
    vehicle_id = create_vehicle(client, customer_id)
    ticket_data = create_ticket(customer_id, vehicle_id)
    res = client.post("/service_tickets/", json=ticket_data)
    ticket_id = res.json["id"]

    item_id = create_inventory_item(client)

    update_data = {"add_item_ids": [{"item_id": item_id, "quantity": 4}]}
    update_res = client.put(f"/service_tickets/{ticket_id}/edit", json=update_data)
    assert update_res.status_code == 200
    response = update_res.json["service_ticket"]

    added_item = next(i for i in response["inventory_items"] if i["id"] == item_id)
    assert added_item["quantity"] == 4

    # Confirm the quantity is also reflected on a fresh GET, not just the edit response
    get_res = client.get(f"/service_tickets/{ticket_id}")
    assert get_res.status_code == 200
    fetched_item = next(
        i for i in get_res.json["inventory_items"] if i["id"] == item_id
    )
    assert fetched_item["quantity"] == 4


def test_update_ticket_combined_invalid_ids(client):
    customer_id, _ = create_customer(client)
    vehicle_id = create_vehicle(client, customer_id)
    ticket_data = create_ticket(customer_id, vehicle_id)
    res = client.post("/service_tickets/", json=ticket_data)
    ticket_id = res.json["id"]

    update_data = {
        "add_mechanic_ids": [9999],  # invalid mechanic
        "remove_mechanic_ids": [],
        "add_item_ids": [{"item_id": 8888, "quantity": 1}],  # invalid inventory item
        "remove_item_ids": [],
    }

    update_res = client.put(f"/service_tickets/{ticket_id}/edit", json=update_data)
    assert update_res.status_code == 200
    notes = update_res.json.get("notes", [])
    assert any("mechanic" in note.lower() for note in notes)
    assert any("inventory" in note.lower() for note in notes)


def test_update_ticket_combined_invalid_ticket(client):
    mechanic_id = create_mechanic(client)
    item_id = create_inventory_item(client)
    update_data = {
        "add_mechanic_ids": [mechanic_id],
        "remove_mechanic_ids": [],
        "add_item_ids": [{"item_id": item_id, "quantity": 1}],
        "remove_item_ids": [],
    }
    res = client.put("/service_tickets/9999/edit", json=update_data)
    assert res.status_code == 404
    assert "not found" in res.json.get("error", "").lower()


# DELETE SERVICE TICKET
def test_delete_ticket(client):
    customer_id, _ = create_customer(client)
    vehicle_id = create_vehicle(client, customer_id)
    res = client.post("/service_tickets/", json=create_ticket(customer_id, vehicle_id))
    ticket_id = res.json["id"]
    del_res = client.delete(f"/service_tickets/{ticket_id}")
    assert del_res.status_code == 200
    assert "deleted" in del_res.json["message"].lower()


def test_delete_ticket_not_found(client):
    res = client.delete("/service_tickets/9999")
    assert res.status_code == 404


def test_delete_ticket_blocked_by_mechanic(client):
    customer_id, _ = create_customer(client)
    vehicle_id = create_vehicle(client, customer_id)
    ticket_res = client.post(
        "/service_tickets/", json=create_ticket(customer_id, vehicle_id)
    )
    ticket_id = ticket_res.json["id"]

    mechanic_id = create_mechanic(client)

    client.put(
        f"/service_tickets/{ticket_id}/edit",
        json={"add_mechanic_ids": [mechanic_id]},
    )

    del_res = client.delete(f"/service_tickets/{ticket_id}")
    assert del_res.status_code == 400
    assert "mechanic" in del_res.json["error"].lower()


def test_delete_ticket_blocked_by_inventory(client):
    customer_id, _ = create_customer(client)
    vehicle_id = create_vehicle(client, customer_id)
    ticket_res = client.post(
        "/service_tickets/", json=create_ticket(customer_id, vehicle_id)
    )
    ticket_id = ticket_res.json["id"]

    item_id = create_inventory_item(client)

    # No quantity specified - should default to 1 and still block deletion
    client.put(
        f"/service_tickets/{ticket_id}/edit",
        json={"add_item_ids": [{"item_id": item_id}]},
    )

    del_res = client.delete(f"/service_tickets/{ticket_id}")
    assert del_res.status_code == 400
    assert "inventory" in del_res.json["error"].lower()
