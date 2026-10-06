from .schemas import vehicle_schema, vehicles_schema
from flask import request, jsonify
from marshmallow import ValidationError
from sqlalchemy import select
from app.models import db, Vehicle, Customer
from app.extensions import limiter
from app.utils.util import token_required
from . import vehicles_bp


# ADD VEHICLE
@vehicles_bp.route("/", methods=["POST"])
@limiter.limit("20 per hour")  # Limit to avoid scripted record creation
@token_required  # Only a logged-in customer can add a vehicle
def create_vehicle(current_customer_id):
    try:
        vehicle_data = vehicle_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400

    # A customer can only add vehicles to their own account
    if vehicle_data.customer_id != int(current_customer_id):
        return jsonify({"error": "You can only add vehicles to your own account"}), 403

    customer = db.session.get(Customer, vehicle_data.customer_id)
    if not customer:
        return jsonify({"error": "Customer not found"}), 404

    query = select(Vehicle).where(Vehicle.VIN == vehicle_data.VIN)
    existing_vehicle = db.session.execute(query).scalars().first()
    if existing_vehicle:
        return jsonify({"error": "Vehicle with this VIN already exists"}), 400

    db.session.add(vehicle_data)
    db.session.commit()
    return vehicle_schema.jsonify(vehicle_data), 201


# GET ALL VEHICLES
@vehicles_bp.route("/", methods=["GET"])
def get_all_vehicles():
    query = select(Vehicle)
    vehicles = db.session.execute(query).scalars().all()
    return vehicles_schema.jsonify(vehicles), 200


# GET SPECIFIC VEHICLE
@vehicles_bp.route("/<int:vehicle_id>", methods=["GET"])
def get_vehicle(vehicle_id):
    vehicle = db.session.get(Vehicle, vehicle_id)

    if vehicle:
        return vehicle_schema.jsonify(vehicle), 200
    return jsonify({"error": "Vehicle not found"}), 404


# UPDATE VEHICLE
@vehicles_bp.route("/<int:vehicle_id>", methods=["PUT"])
@limiter.limit("20 per hour")
@token_required
def update_vehicle(current_customer_id, vehicle_id):
    vehicle = db.session.get(Vehicle, vehicle_id)

    if not vehicle:
        return jsonify({"error": "Vehicle not found"}), 404

    # A customer can only change their own vehicles
    if vehicle.customer_id != int(current_customer_id):
        return jsonify({"error": "You can only modify your own vehicles"}), 403

    try:
        updated_vehicle = vehicle_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400

    # ...and cannot hand a vehicle to another customer
    if updated_vehicle.customer_id != int(current_customer_id):
        return jsonify({"error": "You can only assign vehicles to your own account"}), 403

    customer = db.session.get(Customer, updated_vehicle.customer_id)
    if not customer:
        return jsonify({"error": "Customer not found"}), 404

    # if new VIN, verify it does not already exist in DB
    if updated_vehicle.VIN != vehicle.VIN:
        query = select(Vehicle).where(Vehicle.VIN == updated_vehicle.VIN)
        existing_vehicle = db.session.execute(query).scalars().first()
        if existing_vehicle:
            return jsonify({"error": "Vehicle with this VIN already exists"}), 400

    vehicle.VIN = updated_vehicle.VIN
    vehicle.make = updated_vehicle.make
    vehicle.model = updated_vehicle.model
    vehicle.year = updated_vehicle.year
    vehicle.customer_id = updated_vehicle.customer_id

    db.session.commit()
    return vehicle_schema.jsonify(vehicle), 200


# DELETE VEHICLE
@vehicles_bp.route("/<int:vehicle_id>", methods=["DELETE"])
@limiter.limit("5 per day")  # Same cap as other delete routes
@token_required
def delete_vehicle(current_customer_id, vehicle_id):
    vehicle = db.session.get(Vehicle, vehicle_id)

    if not vehicle:
        return jsonify({"error": "Vehicle not found"}), 404

    # A customer can only delete their own vehicles
    if vehicle.customer_id != int(current_customer_id):
        return jsonify({"error": "You can only delete your own vehicles"}), 403

    db.session.delete(vehicle)
    db.session.commit()
    return (
        jsonify({"message": f"Vehicle id: {vehicle_id} deleted successfully"}),
        200,
    )
