from datetime import date
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from typing import List
from sqlalchemy import Numeric


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)  # Instantiate SQLAlchemy database


# Define association tables BEFORE models
service_mechanics = db.Table(
    "service_mechanics",
    Base.metadata,
    db.Column("service_id", db.ForeignKey("service_tickets.id")),
    db.Column("mechanic_id", db.ForeignKey("mechanics.id")),
)

# service_inventory needs a quantity column, so it's a proper association
# object model instead of a plain secondary Table (which can't hold extra columns).


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    email: Mapped[str] = mapped_column(db.String(250), nullable=False, unique=True)
    phone: Mapped[str] = mapped_column(db.String(15), nullable=False)
    password: Mapped[str] = mapped_column(db.String(255), nullable=False)

    service_tickets: Mapped[List["ServiceTicket"]] = db.relationship(
        back_populates="customer", cascade="all, delete"
    )  # removes associated service tickets when a customer is deleted


class Vehicle(Base):
    __tablename__ = "vehicles"

    id: Mapped[int] = mapped_column(primary_key=True)
    VIN: Mapped[str] = mapped_column(db.String(17), nullable=False, unique=True)
    make: Mapped[str] = mapped_column(db.String(50), nullable=False)
    model: Mapped[str] = mapped_column(db.String(50), nullable=False)
    year: Mapped[int] = mapped_column(db.Integer, nullable=False)
    customer_id: Mapped[int] = mapped_column(
        db.ForeignKey("customers.id"), nullable=False
    )

    customer: Mapped["Customer"] = db.relationship("Customer", backref="vehicles")


class ServiceTicket(Base):
    __tablename__ = "service_tickets"

    id: Mapped[int] = mapped_column(primary_key=True)
    vehicle_id: Mapped[int] = mapped_column(
        db.ForeignKey("vehicles.id"), nullable=False
    )
    service_date: Mapped[date] = mapped_column(db.Date)
    service_desc: Mapped[str] = mapped_column(db.String(500), nullable=False)
    customer_id: Mapped[int] = mapped_column(db.ForeignKey("customers.id"))

    customer: Mapped["Customer"] = db.relationship(
        "Customer", back_populates="service_tickets"
    )
    vehicle: Mapped["Vehicle"] = db.relationship("Vehicle", backref="service_tickets")
    mechanics: Mapped[List["Mechanic"]] = db.relationship(
        "Mechanic", secondary=service_mechanics, back_populates="service_tickets"
    )

    inventory_entries: Mapped[List["ServiceInventory"]] = db.relationship(
        "ServiceInventory",
        back_populates="service_ticket",
        cascade="all, delete-orphan",
    )


class Mechanic(Base):
    __tablename__ = "mechanics"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    email: Mapped[str] = mapped_column(db.String(250), nullable=False, unique=True)
    phone: Mapped[str] = mapped_column(db.String(15), nullable=False)
    salary: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    service_tickets: Mapped[List["ServiceTicket"]] = db.relationship(
        secondary=service_mechanics, back_populates="mechanics"
    )


class InventoryItem(Base):
    __tablename__ = "inventory_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    price: Mapped[float] = mapped_column(db.Float(), nullable=False)
    # price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    # item_desc: Mapped[str] = mapped_column(db.String(500), nullable=False)

    service_entries: Mapped[List["ServiceInventory"]] = db.relationship(
        "ServiceInventory", back_populates="item"
    )


class ServiceInventory(Base):
    """Association object linking a ServiceTicket to an InventoryItem, with quantity used."""

    __tablename__ = "service_inventory"

    service_id: Mapped[int] = mapped_column(
        db.ForeignKey("service_tickets.id"), primary_key=True
    )
    item_id: Mapped[int] = mapped_column(
        db.ForeignKey("inventory_items.id"), primary_key=True
    )
    quantity: Mapped[int] = mapped_column(db.Integer, nullable=False, default=1)

    service_ticket: Mapped["ServiceTicket"] = db.relationship(
        "ServiceTicket", back_populates="inventory_entries"
    )
    item: Mapped["InventoryItem"] = db.relationship(
        "InventoryItem", back_populates="service_entries"
    )
