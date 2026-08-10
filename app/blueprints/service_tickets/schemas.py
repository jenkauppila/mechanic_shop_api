from app.extensions import ma
from app.models import ServiceTicket
from marshmallow import fields


# Flattened view of a ServiceInventory association: item details + quantity used
class InventoryEntrySchema(ma.Schema):
    id = fields.Integer(attribute="item.id")
    name = fields.String(attribute="item.name")
    price = fields.Float(attribute="item.price")
    quantity = fields.Integer()

    class Meta:
        fields = ("id", "name", "price", "quantity")


class ServiceTicketSchema(ma.SQLAlchemyAutoSchema):
    customer_id = fields.Integer(required=True)
    vehicle_id = fields.Integer(required=True)
    service_desc = fields.String(required=True)
    service_date = fields.Date(required=True)

    class Meta:
        model = ServiceTicket
        include_fk = True
        load_instance = True
        fields = (
            "id",
            "vehicle_id",
            "service_date",
            "service_desc",
            "customer_id",
            "mechanics",
            "inventory_items",
        )

    mechanics = fields.Nested("MechanicSchema", only=("id", "name"), many=True)
    inventory_items = fields.Nested(
        InventoryEntrySchema, many=True, attribute="inventory_entries"
    )
    customer = fields.Nested("CustomerSchema", only=("id", "name", "email", "phone"))


# Item + quantity pair used when adding an item to a ticket via add_item_ids
class AddItemEntrySchema(ma.Schema):
    item_id = fields.Integer(required=True)
    quantity = fields.Integer(required=False, load_default=1)

    class Meta:
        fields = ("item_id", "quantity")


class EditServiceTicketSchema(ma.Schema):
    add_mechanic_ids = fields.List(fields.Int(), required=False, load_default=[])
    remove_mechanic_ids = fields.List(fields.Int(), required=False, load_default=[])
    add_item_ids = fields.List(
        fields.Nested(AddItemEntrySchema), required=False, load_default=[]
    )
    remove_item_ids = fields.List(fields.Int(), required=False, load_default=[])

    class Meta:
        fields = (
            "add_mechanic_ids",
            "remove_mechanic_ids",
            "add_item_ids",
            "remove_item_ids",
        )


service_ticket_schema = ServiceTicketSchema()
service_tickets_schema = ServiceTicketSchema(many=True)
edit_service_ticket_schema = EditServiceTicketSchema()
