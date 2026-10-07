from app.extensions import ma
from app.models import Customer
from marshmallow import fields, validate


class CustomerSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Customer

    # Explicitly define required fields for better validation
    name = fields.String(required=True)
    email = fields.Email(required=True)
    phone = fields.String(
        required=True,
        validate=validate.Regexp(
            r'^(\+1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}$',
            error="Phone number must be a valid 10-digit US phone number"
        )
    )
    # load_only: accepted on input, never included in API responses
    # (previously the password hash was returned by GET and POST /customers/)
    password = fields.String(required=True, load_only=True)


customer_schema = CustomerSchema()
customers_schema = CustomerSchema(many=True)
login_schema = CustomerSchema(only=("email", "password"))  # For login purposes
