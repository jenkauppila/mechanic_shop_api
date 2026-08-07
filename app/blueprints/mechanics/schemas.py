from app.extensions import ma
from app.models import Mechanic
from marshmallow import fields, validate


class MechanicSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Mechanic
        load_instance = True  # This helps with validation

    # Explicitly define required fields
    name = fields.String(required=True)
    email = fields.Email(required=True)
    phone = fields.String(
        required=True,
        validate=validate.Regexp(
            r'^(\+1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}$',
            error="Phone number must be a valid 10-digit US phone number"
        )
    )
    salary = fields.Float(required=True)


mechanic_schema = MechanicSchema()
mechanics_schema = MechanicSchema(many=True)
