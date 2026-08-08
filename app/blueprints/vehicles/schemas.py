from app.extensions import ma
from app.models import Vehicle
from marshmallow import fields


class VehicleSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Vehicle
        include_fk = True
        load_instance = True

    # Explicitly define required fields for better validation
    VIN = fields.String(required=True)
    make = fields.String(required=True)
    model = fields.String(required=True)
    year = fields.Integer(required=True)
    customer_id = fields.Integer(required=True)


vehicle_schema = VehicleSchema()
vehicles_schema = VehicleSchema(many=True)
